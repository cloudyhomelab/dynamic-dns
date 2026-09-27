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


def _require_str(value, what):
    # YAML reads unquoted no/on/1 as bool/int, which would reach Porkbun as "False" etc.
    if not isinstance(value, str):
        raise TypeError(f"{what} must be a string, got {value!r}; quote it in the YAML")


def load_domains(domains_file_path):
    with open(domains_file_path) as domains_file:
        domains = yaml.safe_load(domains_file)
        data = []
        for item in domains:
            name = item.get("name")
            if name is None:
                raise TypeError(f"entry has no name: {item!r}")
            _require_str(name, "name")
            # no subdomains key means the apex record
            subdomains = item.get("subdomains", [None])
            if not isinstance(subdomains, list):
                raise TypeError(f"subdomains of {name} must be a list, got {subdomains!r}")
            for subdomain in subdomains:
                if subdomain is not None:
                    _require_str(subdomain, f"subdomain of {name}")
                data.append(
                    DomainConfig(
                        name,
                        subdomain,
                        item.get("hostname"),
                        item.get("ip"),
                        item.get("ttl", DNS_RECORD_TTL),
                    )
                )
    return data
