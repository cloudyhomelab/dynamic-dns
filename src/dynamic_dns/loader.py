# SPDX-License-Identifier: GPL-3.0-or-later

import ipaddress
from dataclasses import dataclass, fields

import yaml

from dynamic_dns.config import DNS_RECORD_TTL


@dataclass
class DomainEntry:
    """One entry of the domains YAML, validated on construction."""

    name: str
    # None means the apex record
    subdomains: list | None
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
                hint = "; quote it in the YAML" if field.type in (str, str | None) else ""
                raise TypeError(f"{self.name}: {field.name} must be {expected}, got {value!r}{hint}")
        for subdomain in self.subdomains or []:
            if not isinstance(subdomain, str):
                raise TypeError(f"{self.name}: subdomains must be str, got {subdomain!r}; quote it in the YAML")
        if self.ip is not None:
            try:
                ipaddress.ip_address(self.ip)
            except ValueError:
                raise ValueError(f"{self.name}: ip {self.ip!r} is not an IPv4 or IPv6 address") from None


@dataclass
class DomainConfig:
    """One DNS record to sync."""

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
    entries = [
        DomainEntry(
            item.get("name"),
            item.get("subdomains"),
            item.get("hostname"),
            item.get("ip"),
            item.get("ttl", DNS_RECORD_TTL),
        )
        for item in domains
    ]
    return [
        DomainConfig(entry.name, subdomain, entry.hostname, entry.ip, entry.ttl)
        for entry in entries
        for subdomain in (entry.subdomains if entry.subdomains is not None else [None])
    ]
