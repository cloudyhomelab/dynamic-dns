# SPDX-License-Identifier: GPL-3.0-or-later

import argparse

import requests

from dynamic_dns.ip import IpLookup
from dynamic_dns.loader import load_domains, load_secrets
from dynamic_dns.porkbun import create_dns_record, get_current_ip, update_dns_record


def change_my_dns(domain, sub_domain, my_ip, ttl, secret):
    prev_ip = get_current_ip(domain, sub_domain, secret)

    if my_ip is not None:
        if prev_ip is not None:
            if my_ip != prev_ip:
                return update_dns_record(domain, sub_domain, my_ip, ttl, secret)
            else:
                print("No changes to update")
                return True
        else:
            return create_dns_record(domain, sub_domain, my_ip, ttl, secret)

    print("No IP address to set")
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
    except TypeError as e:
        print(f"Invalid domains config {args.domain_file}: {e}")
        return 1

    lookup = IpLookup()
    failed = 0
    for item in domains:
        fqdn = f"{item.subdomain}.{item.name}" if item.subdomain else item.name
        # socket.gaierror (unresolvable hostname) is an OSError
        try:
            ip = lookup.resolve(item.hostname) if item.hostname else item.ip or lookup.resolve()
            print(f"setting up {fqdn} for hostname {item.hostname} or ip {ip}")
            if not change_my_dns(item.name, item.subdomain, ip, item.ttl, secret):
                failed += 1
        except (requests.RequestException, OSError) as e:
            print(f"Failed to sync {fqdn}: {e}")
            failed += 1

    return 1 if failed else 0
