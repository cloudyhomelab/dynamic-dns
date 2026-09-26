# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass

import yaml


@dataclass
class DomainConfig:
    """Class for keeping track of domain configurations."""

    name: str
    subdomain: str | None
    hostname: str | None
    ip: str | None


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
            if "subdomains" in item:
                data.extend(
                    [
                        DomainConfig(item["name"], subdomain, item.get("hostname"), item.get("ip"))
                        for subdomain in item.get("subdomains")
                    ]
                )
            else:
                data.append(DomainConfig(item["name"], None, item.get("hostname"), item.get("ip")))
    return data
