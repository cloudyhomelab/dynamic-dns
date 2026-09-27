# SPDX-License-Identifier: GPL-3.0-or-later

import ipaddress
from dataclasses import dataclass
from types import UnionType
from typing import Any, cast, get_args, get_origin, get_type_hints

import yaml

from dynamic_dns.config import DNS_RECORD_TTL


def _matches(value: object, expected: Any) -> bool:
    # isinstance() rejects parameterized generics such as list[str], so check their base type
    options = get_args(expected) if isinstance(expected, UnionType) else (expected,)
    return any(isinstance(value, get_origin(option) or option) for option in options)


@dataclass
class _Validated:
    """Checks every field against its type annotation on construction."""

    def _prefix(self) -> str:
        return ""

    def _describe(self, value: object) -> str:
        return repr(value)

    def __post_init__(self) -> None:
        # YAML reads unquoted no/on/1 as bool/int, which would reach Porkbun as "False" etc.
        # bool is an int subclass, so reject it for non-bool fields explicitly
        for name, expected in get_type_hints(type(self)).items():
            value = getattr(self, name)
            if value is None and not _matches(value, expected):
                raise TypeError(f"{self._prefix()}{name} is missing")
            if (isinstance(value, bool) and expected is not bool) or not _matches(value, expected):
                hint = "; quote it in the YAML" if expected in (str, str | None) else ""
                raise TypeError(
                    f"{self._prefix()}{name} must be {getattr(expected, '__name__', expected)}, "
                    f"got {self._describe(value)}{hint}"
                )


@dataclass
class DomainEntry(_Validated):
    """One entry of the domains YAML, validated on construction."""

    name: str
    # None means the apex record
    subdomains: list[str] | None
    hostname: str | None
    ip: str | None
    ttl: int
    delete_stale: bool
    delete_extra: bool

    def _prefix(self) -> str:
        return f"{self.name}: " if isinstance(self.name, str) else ""

    def __post_init__(self) -> None:
        super().__post_init__()
        # an empty list is likely unfinished config; don't guess the apex and overwrite it
        if self.subdomains == []:
            raise ValueError(f"{self.name}: subdomains is empty; remove it to sync the domain itself")
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
    delete_stale: bool
    delete_extra: bool


@dataclass
class ApiKeys(_Validated):
    """Porkbun API credentials."""

    apikey: str
    secretapikey: str

    def _describe(self, value: object) -> str:
        # never echo credentials into the terminal or the journal
        return type(value).__name__

    def __post_init__(self) -> None:
        super().__post_init__()
        for name in ("apikey", "secretapikey"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is empty")


def load_secrets(secret_file_path: str) -> ApiKeys:
    with open(secret_file_path) as secret_file:
        secret = yaml.safe_load(secret_file)
    if not isinstance(secret, dict):
        raise TypeError(f"expected apikey and secretapikey, got {type(secret).__name__}")
    # a missing key arrives as None and is rejected by ApiKeys.__post_init__
    return ApiKeys(cast(str, secret.get("apikey")), cast(str, secret.get("secretapikey")))


def load_domains(domains_file_path: str) -> list[DomainConfig]:
    with open(domains_file_path) as domains_file:
        domains = yaml.safe_load(domains_file)
    if not isinstance(domains, list):
        raise TypeError(f"expected a list of entries (each starting with '- name:'), got {type(domains).__name__}")
    for index, item in enumerate(domains, 1):
        if not isinstance(item, dict):
            raise TypeError(f"entry {index}: expected a mapping with name, got {item!r}")
    entries = [
        DomainEntry(
            item.get("name"),
            item.get("subdomains"),
            item.get("hostname"),
            item.get("ip"),
            item.get("ttl", DNS_RECORD_TTL),
            item.get("delete_stale", False),
            item.get("delete_extra", True),
        )
        for item in domains
    ]
    return [
        DomainConfig(entry.name, subdomain, entry.hostname, entry.ip, entry.ttl, entry.delete_stale, entry.delete_extra)
        for entry in entries
        for subdomain in (entry.subdomains if entry.subdomains is not None else [None])
    ]
