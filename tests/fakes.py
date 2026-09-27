# SPDX-License-Identifier: GPL-3.0-or-later

import itertools
import socket
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any, Protocol

import requests

from dynamic_dns.config import PORKBUN_API_BASE_URL, PUBLIC_IPV4_URL, PUBLIC_IPV6_URL

API_KEYS = {"apikey": "pk1_test", "secretapikey": "sk1_test"}

type RecordKey = tuple[str, str, str]


class Run(Protocol):
    """The `run` fixture: writes the config files, runs the CLI and returns the exit code."""

    def __call__(self, domains: object, api_keys: object = ...) -> int: ...


class FakeResponse:
    def __init__(self, url: str, status_code: int = 200, payload: dict[str, Any] | None = None, text: str = ""):
        self.url = url
        self.status_code = status_code
        self.reason = "OK" if status_code == 200 else "Bad Request"
        self.text = text
        self._payload = payload or {"status": "SUCCESS"}

    def raise_for_status(self) -> None:
        if self.status_code != 200:
            raise requests.HTTPError(f"{self.status_code} {self.reason} for url: {self.url}")

    def json(self) -> dict[str, Any]:
        return self._payload


@dataclass
class FakePorkbun:
    """In-memory Porkbun DNS: records keyed by (domain, type, subdomain), where "" is the apex."""

    records: dict[RecordKey, list[dict[str, str]]] = field(default_factory=dict)
    calls: list[tuple[str, list[str], dict[str, Any]]] = field(default_factory=list)
    # endpoint names ("retrieveByNameType", "edit", ...) that answer with HTTP 400
    failing: set[str] = field(default_factory=set)
    _ids: Iterator[int] = field(default_factory=lambda: itertools.count(1000))

    def add(self, domain: str, record_type: str, subdomain: str, content: str, ttl: int = 600) -> str:
        record = {"id": str(next(self._ids)), "content": content, "ttl": str(ttl)}
        self.records.setdefault((domain, record_type, subdomain), []).append(record)
        return record["id"]

    def get(self, domain: str, record_type: str, subdomain: str = "") -> list[tuple[str, int]]:
        return [(r["content"], int(r["ttl"])) for r in self.records.get((domain, record_type, subdomain), [])]

    def writes(self) -> list[tuple[str, list[str], dict[str, Any]]]:
        return [c for c in self.calls if c[0] != "retrieveByNameType"]

    def post(self, url: str, json: dict[str, Any], timeout: float) -> FakeResponse:
        assert url.startswith(PORKBUN_API_BASE_URL + "/"), url
        assert json["apikey"] == API_KEYS["apikey"] and json["secretapikey"] == API_KEYS["secretapikey"]
        assert timeout
        endpoint, *parts = url.removeprefix(PORKBUN_API_BASE_URL + "/").split("/")
        body = {k: v for k, v in json.items() if k not in API_KEYS}
        self.calls.append((endpoint, parts, body))
        if endpoint in self.failing:
            return FakeResponse(url, status_code=400)
        handler: Callable[..., FakeResponse] = getattr(self, "_" + endpoint)
        return handler(url, *parts, **body)

    def _retrieveByNameType(self, url: str, domain: str, record_type: str, subdomain: str = "") -> FakeResponse:
        return FakeResponse(
            url, payload={"status": "SUCCESS", "records": self.records.get((domain, record_type, subdomain), [])}
        )

    def _create(self, url: str, domain: str, name: str, type: str, content: str, ttl: str) -> FakeResponse:
        self.add(domain, type, name, content, int(ttl))
        return FakeResponse(url)

    def _find(self, domain: str, record_id: str) -> tuple[RecordKey, dict[str, str]]:
        for key, records in self.records.items():
            for record in records:
                if key[0] == domain and record["id"] == record_id:
                    return key, record
        raise AssertionError(f"no record {record_id} in {domain}")

    def _edit(
        self, url: str, domain: str, record_id: str, name: str, type: str, content: str, ttl: str
    ) -> FakeResponse:
        key, record = self._find(domain, record_id)
        assert key == (domain, type, name), "edit by id must keep name and type"
        record.update(content=content, ttl=str(ttl))
        return FakeResponse(url)

    def _delete(self, url: str, domain: str, record_id: str) -> FakeResponse:
        key, record = self._find(domain, record_id)
        self.records[key].remove(record)
        return FakeResponse(url)

    def _deleteByNameType(self, url: str, domain: str, record_type: str, subdomain: str = "") -> FakeResponse:
        self.records.pop((domain, record_type, subdomain), None)
        return FakeResponse(url)


@dataclass
class FakeNetwork:
    """Public IP services and DNS resolution. None for public_ipv6 means no IPv6 connectivity."""

    public_ipv4: str | None = "203.0.113.7"
    public_ipv6: str | None = None
    public_ipv4_status: int = 200
    hosts: dict[str, list[str]] = field(default_factory=dict)
    lookups: list[str] = field(default_factory=list)

    def request(self, method: str, url: str, timeout: float) -> FakeResponse:
        assert method == "GET" and timeout
        self.lookups.append(url)
        if url == PUBLIC_IPV4_URL:
            return FakeResponse(url, status_code=self.public_ipv4_status, text=f"{self.public_ipv4}\n")
        if url == PUBLIC_IPV6_URL:
            if self.public_ipv6 is None:
                raise requests.ConnectionError("[Errno 101] Network is unreachable")
            return FakeResponse(url, text=f"{self.public_ipv6}\n")
        raise AssertionError(f"unexpected GET {url}")

    def getaddrinfo(
        self, host: str, port: int | None, proto: int = 0, **kwargs: Any
    ) -> list[tuple[socket.AddressFamily, socket.SocketKind, int, str, tuple[str, int]]]:
        self.lookups.append(host)
        addresses = self.hosts.get(host)
        if not addresses:
            raise socket.gaierror(socket.EAI_NONAME, "Name or service not known")
        return [
            (socket.AF_INET6 if ":" in ip else socket.AF_INET, socket.SOCK_STREAM, proto, "", (ip, 0))
            for ip in addresses
        ]
