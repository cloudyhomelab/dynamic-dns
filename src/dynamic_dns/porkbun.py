# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import asdict

import requests

from dynamic_dns.config import (
    PORKBUN_CREATE_URL,
    PORKBUN_EDIT_URL,
    PORKBUN_RETRIEVE_URL,
    REQUEST_TIMEOUT_SECONDS,
)


def update_dns_record(domain, sub_domain, public_ip, ttl, secret):
    url = PORKBUN_EDIT_URL.format(domain=domain, subdomain=sub_domain or "").rstrip("/")

    data = {
        **asdict(secret),
        "content": public_ip,
        "ttl": str(ttl),
    }

    response = requests.post(url, json=data, timeout=REQUEST_TIMEOUT_SECONDS)

    if response.status_code == requests.codes.ok:
        print("DNS records updated")
        return True
    else:
        print(
            "Request to update dns record failed with status code:",
            response.status_code,
        )
        print("Reason: ", response.reason)

    return False


def create_dns_record(domain, sub_domain, public_ip, ttl, secret):
    url = PORKBUN_CREATE_URL.format(domain=domain)

    data = {
        **asdict(secret),
        "name": sub_domain or "",
        "type": "A",
        "content": public_ip,
        "ttl": str(ttl),
    }

    response = requests.post(url, json=data, timeout=REQUEST_TIMEOUT_SECONDS)

    if response.status_code == requests.codes.ok:
        print("DNS records created")
        return True
    else:
        print(
            "Request to create dns record failed with status code:",
            response.status_code,
        )
        print("Reason: ", response.reason)

    return False


def get_current_ip(domain, sub_domain, secret):
    url = PORKBUN_RETRIEVE_URL.format(domain=domain, subdomain=sub_domain or "").rstrip("/")

    response = requests.post(url, json=asdict(secret), timeout=REQUEST_TIMEOUT_SECONDS)
    if response.status_code == requests.codes.ok:
        records = response.json()["records"]
        if records:
            return records[0]["content"]
        else:
            fqdn = f"{sub_domain}.{domain}" if sub_domain else domain
            print(f"No records entry exists for {fqdn}")
            return None

    print("Request to fetch existing dns failed with status code:", response.status_code)
    print("Reason:", response.reason)
    return None
