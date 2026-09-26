# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import socket

from dynamic_dns.ip import public_ip
from dynamic_dns.loader import load_domains, load_secrets
from dynamic_dns.porkbun import create_dns_record, get_current_ip, update_dns_record


def change_my_dns(domain, sub_domain, config_ip, secret):
    # if config_ip is not present then sync the public ip
    my_ip = config_ip or public_ip()
    prev_ip = get_current_ip(domain, sub_domain, secret)

    if my_ip is not None:
        if prev_ip is not None:
            if my_ip != prev_ip:
                update_dns_record(domain, sub_domain, my_ip, secret)
            else:
                print("No changes to update")
        else:
            create_dns_record(domain, sub_domain, my_ip, secret)


def main():
    parser = argparse.ArgumentParser(prog="dynamic-dns", description="Sync DNS records in Porkbun")
    parser.add_argument(
        "-a",
        "--api-keys-path",
        dest="api_file",
        type=str,
        required=True,
        help="path of the json file containing the porkbun api keys",
    )
    parser.add_argument(
        "-d",
        "--domains-path",
        dest="domain_file",
        type=str,
        required=True,
        help="path of the json file containing the domain/sub-domains to sync",
    )
    args = parser.parse_args()

    secret = load_secrets(args.api_file)
    domains = load_domains(args.domain_file)

    for item in domains:
        item.ip = socket.gethostbyname(item.hostname) if item.hostname else item.ip
        if item.subdomain:
            print(f"setting up {item.subdomain}.{item.name} for hostname {item.hostname} or ip {item.ip}")
        else:
            print(f"setting up {item.name} for hostname {item.hostname} or ip {item.ip}")
        change_my_dns(item.name, item.subdomain, item.ip, secret)
