# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import ipaddress

import requests

from dynamic_dns.ip import IpAddress, IpLookup
from dynamic_dns.loader import ApiKeys, DomainConfig, load_domains, load_secrets
from dynamic_dns.porkbun import (
    create_dns_record,
    delete_dns_record,
    delete_dns_record_by_id,
    edit_dns_record,
    get_records,
)

RECORD_TYPES = {4: "A", 6: "AAAA"}


def change_my_dns(
    domain: str, sub_domain: str | None, address: IpAddress, ttl: int, delete_extra: bool, secret: ApiKeys
) -> bool:
    record_type = RECORD_TYPES[address.version]
    fqdn = f"{sub_domain}.{domain}" if sub_domain else domain
    records = get_records(domain, sub_domain, record_type, secret)
    if not records:
        print(f"No {record_type} record exists for {fqdn}")
        return create_dns_record(domain, sub_domain, record_type, str(address), ttl, secret)

    # keep the record that already has our IP, else reuse the first; compare parsed addresses since
    # one IPv6 address has several spellings
    keep = next((r for r in records if ipaddress.ip_address(r.content) == address), records[0])
    if ipaddress.ip_address(keep.content) != address or keep.ttl != ttl:
        ok = edit_dns_record(domain, keep.id, sub_domain, record_type, str(address), ttl, secret)
    else:
        print("No changes to update")
        ok = True

    extras = [r for r in records if r is not keep]
    if extras and not delete_extra:
        print(f"{len(extras)} other {record_type} record(s) exist for {fqdn}; set delete_extra to remove them")
    elif extras and ok:
        # only once a correct record exists, so the name never goes without one
        for extra in extras:
            print(f"Deleting extra {record_type} record {extra.content} for {fqdn}")
            ok = delete_dns_record_by_id(domain, extra.id, secret) and ok
    return ok


def delete_stale_record(domain: str, sub_domain: str | None, record_type: str, secret: ApiKeys) -> bool:
    if not get_records(domain, sub_domain, record_type, secret):
        return True
    fqdn = f"{sub_domain}.{domain}" if sub_domain else domain
    print(f"Deleting stale {record_type} record for {fqdn}")
    return delete_dns_record(domain, sub_domain, record_type, secret)


def sync_record(record: DomainConfig, lookup: IpLookup, secret: ApiKeys) -> bool:
    fqdn = f"{record.subdomain}.{record.name}" if record.subdomain else record.name
    # socket.gaierror (unresolvable hostname) is an OSError
    try:
        addresses: list[IpAddress]
        if record.hostname:
            addresses = lookup.resolve(record.hostname)
        elif record.ip:
            addresses = [ipaddress.ip_address(record.ip)]
        else:
            addresses = lookup.resolve()
        # one record per address family (A and/or AAAA); keep going if one fails
        results: list[bool] = []
        for address in addresses:
            print(f"setting up {fqdn} for hostname {record.hostname} or ip {address}")
            results.append(
                change_my_dns(record.name, record.subdomain, address, record.ttl, record.delete_extra, secret)
            )
        # a missing family is only certain for hostname and ip; a failed public IPv6 lookup may be transient
        if record.delete_stale and (record.hostname or record.ip):
            synced = {address.version for address in addresses}
            for version, record_type in RECORD_TYPES.items():
                if version not in synced:
                    results.append(delete_stale_record(record.name, record.subdomain, record_type, secret))
        return all(results)
    except (requests.RequestException, OSError, ValueError) as e:
        print(f"Failed to sync {fqdn}: {e}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(prog="dynamic-dns", description="Sync DNS records in Porkbun")
    parser.add_argument(
        "-a",
        "--api-keys-path",
        dest="api_file",
        type=str,
        required=True,
        help="path of the yaml file containing the porkbun api keys",
    )
    parser.add_argument(
        "-d",
        "--domains-path",
        dest="domain_file",
        type=str,
        required=True,
        help="path of the yaml file containing the domain/sub-domains to sync",
    )
    args = parser.parse_args()

    try:
        secret = load_secrets(args.api_file)
    except (TypeError, ValueError) as e:
        print(f"Invalid api keys config {args.api_file}: {e}")
        return 1
    try:
        domains = load_domains(args.domain_file)
    except (TypeError, ValueError) as e:
        print(f"Invalid domains config {args.domain_file}: {e}")
        return 1

    lookup = IpLookup()
    failed = 0
    for record in domains:
        if not sync_record(record, lookup, secret):
            failed += 1

    return 1 if failed else 0
