# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import ipaddress

import requests

from dynamic_dns.ip import IpLookup
from dynamic_dns.loader import load_domains, load_secrets
from dynamic_dns.porkbun import create_dns_record, get_current_ip, update_dns_record


def change_my_dns(domain, sub_domain, my_ip, ttl, secret):
    if my_ip is None:
        print("No IP address to set")
        return False

    # ValueError for anything that is not an IP, e.g. a captive portal page from checkip
    address = ipaddress.ip_address(my_ip)
    record_type = "AAAA" if address.version == 6 else "A"
    prev_ip = get_current_ip(domain, sub_domain, record_type, secret)

    if prev_ip is not None:
        # compare parsed addresses: one IPv6 address has several spellings
        if ipaddress.ip_address(prev_ip) != address:
            return update_dns_record(domain, sub_domain, record_type, my_ip, ttl, secret)
        print("No changes to update")
        return True
    return create_dns_record(domain, sub_domain, record_type, my_ip, ttl, secret)


def sync_record(record, lookup, secret):
    fqdn = f"{record.subdomain}.{record.name}" if record.subdomain else record.name
    # socket.gaierror (unresolvable hostname) is an OSError
    try:
        ip = lookup.resolve(record.hostname) if record.hostname else record.ip or lookup.resolve()
        print(f"setting up {fqdn} for hostname {record.hostname} or ip {ip}")
        return change_my_dns(record.name, record.subdomain, ip, record.ttl, secret)
    except (requests.RequestException, OSError, ValueError) as e:
        print(f"Failed to sync {fqdn}: {e}")
        return False


def main():
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

    secret = load_secrets(args.api_file)
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
