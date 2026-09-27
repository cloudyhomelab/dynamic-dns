# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import asdict, dataclass

import requests

from dynamic_dns.config import (
    PORKBUN_CREATE_URL,
    PORKBUN_DELETE_BY_ID_URL,
    PORKBUN_DELETE_URL,
    PORKBUN_EDIT_URL,
    PORKBUN_RETRIEVE_URL,
    REQUEST_TIMEOUT_SECONDS,
)
from dynamic_dns.loader import ApiKeys


@dataclass
class DnsRecord:
    """An existing record as Porkbun reports it."""

    id: str
    content: str
    ttl: int


def edit_dns_record(
    domain: str, record_id: str, sub_domain: str | None, record_type: str, public_ip: str, ttl: int, secret: ApiKeys
) -> bool:
    url = PORKBUN_EDIT_URL.format(domain=domain, id=record_id)

    data = {
        **asdict(secret),
        # edit by id rewrites the whole record, so name and type are required
        "name": sub_domain or "",
        "type": record_type,
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


def delete_dns_record_by_id(domain: str, record_id: str, secret: ApiKeys) -> bool:
    url = PORKBUN_DELETE_BY_ID_URL.format(domain=domain, id=record_id)

    response = requests.post(url, json=asdict(secret), timeout=REQUEST_TIMEOUT_SECONDS)

    if response.status_code == requests.codes.ok:
        print("DNS records deleted")
        return True

    print("Request to delete dns record failed with status code:", response.status_code)
    print("Reason:", response.reason)
    return False


def get_records(domain: str, sub_domain: str | None, record_type: str, secret: ApiKeys) -> list[DnsRecord]:
    url = PORKBUN_RETRIEVE_URL.format(domain=domain, type=record_type, subdomain=sub_domain or "").rstrip("/")

    response = requests.post(url, json=asdict(secret), timeout=REQUEST_TIMEOUT_SECONDS)
    # raise on errors so that [] only ever means "no record"; otherwise a failed lookup creates a duplicate
    response.raise_for_status()
    return [DnsRecord(r["id"], r["content"], int(r["ttl"])) for r in response.json()["records"]]
