# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import asdict

import requests

from dynamic_dns.config import (
    PORKBUN_CREATE_URL,
    PORKBUN_DELETE_URL,
    PORKBUN_EDIT_URL,
    PORKBUN_RETRIEVE_URL,
    REQUEST_TIMEOUT_SECONDS,
)
from dynamic_dns.loader import ApiKeys


def update_dns_record(
    domain: str, sub_domain: str | None, record_type: str, public_ip: str, ttl: int, secret: ApiKeys
) -> bool:
    url = PORKBUN_EDIT_URL.format(domain=domain, type=record_type, subdomain=sub_domain or "").rstrip("/")

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


def create_dns_record(
    domain: str, sub_domain: str | None, record_type: str, public_ip: str, ttl: int, secret: ApiKeys
) -> bool:
    url = PORKBUN_CREATE_URL.format(domain=domain)

    data = {
        **asdict(secret),
        "name": sub_domain or "",
        "type": record_type,
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


def delete_dns_record(domain: str, sub_domain: str | None, record_type: str, secret: ApiKeys) -> bool:
    url = PORKBUN_DELETE_URL.format(domain=domain, type=record_type, subdomain=sub_domain or "").rstrip("/")

    response = requests.post(url, json=asdict(secret), timeout=REQUEST_TIMEOUT_SECONDS)

    if response.status_code == requests.codes.ok:
        print("DNS records deleted")
        return True

    print("Request to delete dns record failed with status code:", response.status_code)
    print("Reason:", response.reason)
    return False


def get_current_ip(domain: str, sub_domain: str | None, record_type: str, secret: ApiKeys) -> str | None:
    url = PORKBUN_RETRIEVE_URL.format(domain=domain, type=record_type, subdomain=sub_domain or "").rstrip("/")

    response = requests.post(url, json=asdict(secret), timeout=REQUEST_TIMEOUT_SECONDS)
    # raise on errors so that None only ever means "no record"; otherwise a failed lookup creates a duplicate
    response.raise_for_status()
    records = response.json()["records"]
    if records:
        content: str = records[0]["content"]
        return content
    return None
