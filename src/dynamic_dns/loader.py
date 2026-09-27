# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass, fields

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

    def __post_init__(self):
        # YAML reads unquoted no/on/1 as bool/int, which would reach Porkbun as "False" etc.
        # bool is an int subclass, and no field is a bool
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, bool) or not isinstance(value, field.type):
                expected = getattr(field.type, "__name__", field.type)
                hint = "" if field.type is int else "; quote it in the YAML"
                raise TypeError(f"{self.name}: {field.name} must be {expected}, got {value!r}{hint}")


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
            subdomains = item.get("subdomains", [None])
            if not isinstance(subdomains, list):
                raise TypeError(f"subdomains must be a list, got {subdomains!r}")
            for subdomain in subdomains:
                data.append(
                    DomainConfig(
                        item.get("name"),
                        subdomain,
                        item.get("hostname"),
                        item.get("ip"),
                        item.get("ttl", DNS_RECORD_TTL),
                    )
                )
    return data
