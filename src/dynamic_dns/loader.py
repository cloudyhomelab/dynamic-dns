# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass

import yaml

from dynamic_dns.config import DNS_RECORD_TTL


@dataclass
class DomainConfig:
    """Class for keeping track of domain configurations."""

    name: str
    subdomain: str | None
    hostname: str | None
    ip: str | None
    ttl: int


@dataclass
class ApiKeys:
    """Porkbun API credentials."""

    apikey: str
    secretapikey: str


def load_secrets(secret_file_path):
    with open(secret_file_path) as secret_file:
        secret = yaml.safe_load(secret_file)
    return ApiKeys(secret["apikey"], secret["secretapikey"])


def load_domains(domains_file_path):
    with open(domains_file_path) as domains_file:
        domains = yaml.safe_load(domains_file)
        data = []
        for item in domains:
            # no subdomains key means the apex record
            for subdomain in item.get("subdomains", [None]):
                data.append(
                    DomainConfig(
                        item["name"],
                        subdomain,
                        item.get("hostname"),
                        item.get("ip"),
                        item.get("ttl", DNS_RECORD_TTL),
                    )
                )
    return data
