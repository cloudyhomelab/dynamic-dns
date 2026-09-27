# SPDX-License-Identifier: GPL-3.0-or-later

import itertools
import socket
import sys
from dataclasses import dataclass, field

import pytest
import requests
import yaml

from dynamic_dns import main as main_module
from dynamic_dns.config import PORKBUN_API_BASE_URL, PUBLIC_IPV4_URL, PUBLIC_IPV6_URL

API_KEYS = {"apikey": "pk1_test", "secretapikey": "sk1_test"}


class FakeResponse:
    def __init__(self, url, status_code=200, payload=None, text=""):
        self.url = url
        self.status_code = status_code
        self.reason = "OK" if status_code == 200 else "Bad Request"
        self.text = text
        self._payload = payload or {"status": "SUCCESS"}

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.HTTPError(f"{self.status_code} {self.reason} for url: {self.url}")

    def json(self):
        return self._payload


@dataclass
class FakePorkbun:
    """In-memory Porkbun DNS: records keyed by (domain, type, subdomain), where "" is the apex."""

    records: dict = field(default_factory=dict)
    calls: list = field(default_factory=list)
    # endpoint names ("retrieveByNameType", "edit", ...) that answer with HTTP 400
    failing: set = field(default_factory=set)
    _ids: itertools.count = field(default_factory=lambda: itertools.count(1000))

    def add(self, domain, record_type, subdomain, content, ttl=600):
        record = {"id": str(next(self._ids)), "content": content, "ttl": str(ttl)}
        self.records.setdefault((domain, record_type, subdomain), []).append(record)
        return record["id"]

    def get(self, domain, record_type, subdomain=""):
        return [(r["content"], int(r["ttl"])) for r in self.records.get((domain, record_type, subdomain), [])]

    def writes(self):
        return [c for c in self.calls if c[0] != "retrieveByNameType"]

    def post(self, url, json, timeout):
        assert url.startswith(PORKBUN_API_BASE_URL + "/"), url
        assert json["apikey"] == API_KEYS["apikey"] and json["secretapikey"] == API_KEYS["secretapikey"]
        assert timeout
        endpoint, *parts = url.removeprefix(PORKBUN_API_BASE_URL + "/").split("/")
        body = {k: v for k, v in json.items() if k not in API_KEYS}
        self.calls.append((endpoint, parts, body))
        if endpoint in self.failing:
            return FakeResponse(url, status_code=400)
        return getattr(self, "_" + endpoint)(url, *parts, **body)

    def _retrieveByNameType(self, url, domain, record_type, subdomain=""):
        return FakeResponse(
            url, payload={"status": "SUCCESS", "records": self.records.get((domain, record_type, subdomain), [])}
        )

    def _create(self, url, domain, name, type, content, ttl):
        self.add(domain, type, name, content, int(ttl))
        return FakeResponse(url)

    def _find(self, domain, record_id):
        for key, records in self.records.items():
            for record in records:
                if key[0] == domain and record["id"] == record_id:
                    return key, record
        raise AssertionError(f"no record {record_id} in {domain}")

    def _edit(self, url, domain, record_id, name, type, content, ttl):
        key, record = self._find(domain, record_id)
        assert key == (domain, type, name), "edit by id must keep name and type"
        record.update(content=content, ttl=str(ttl))
        return FakeResponse(url)

    def _delete(self, url, domain, record_id):
        key, record = self._find(domain, record_id)
        self.records[key].remove(record)
        return FakeResponse(url)

    def _deleteByNameType(self, url, domain, record_type, subdomain=""):
        self.records.pop((domain, record_type, subdomain), None)
        return FakeResponse(url)


@dataclass
class FakeNetwork:
    """Public IP services and DNS resolution. None for public_ipv6 means no IPv6 connectivity."""

    public_ipv4: str | None = "203.0.113.7"
    public_ipv6: str | None = None
    public_ipv4_status: int = 200
    hosts: dict = field(default_factory=dict)
    lookups: list = field(default_factory=list)

    def request(self, method, url, timeout):
        assert method == "GET" and timeout
        self.lookups.append(url)
        if url == PUBLIC_IPV4_URL:
            return FakeResponse(url, status_code=self.public_ipv4_status, text=f"{self.public_ipv4}\n")
        if url == PUBLIC_IPV6_URL:
            if self.public_ipv6 is None:
                raise requests.ConnectionError("[Errno 101] Network is unreachable")
            return FakeResponse(url, text=f"{self.public_ipv6}\n")
        raise AssertionError(f"unexpected GET {url}")

    def getaddrinfo(self, host, port, proto=0, **kwargs):
        self.lookups.append(host)
        addresses = self.hosts.get(host)
        if not addresses:
            raise socket.gaierror(socket.EAI_NONAME, "Name or service not known")
        return [
            (socket.AF_INET6 if ":" in ip else socket.AF_INET, socket.SOCK_STREAM, proto, "", (ip, 0))
            for ip in addresses
        ]


@pytest.fixture
def porkbun(monkeypatch):
    fake = FakePorkbun()
    monkeypatch.setattr(requests, "post", fake.post)
    return fake


@pytest.fixture
def network(monkeypatch):
    fake = FakeNetwork()
    monkeypatch.setattr(requests, "request", fake.request)
    monkeypatch.setattr(socket, "getaddrinfo", fake.getaddrinfo)
    return fake


@pytest.fixture
def run(tmp_path, monkeypatch, porkbun, network):
    """Write the config files and run the CLI; returns the exit code."""

    def _run(domains, api_keys=API_KEYS):
        keys_file = tmp_path / "api-keys.yaml"
        domains_file = tmp_path / "domains.yaml"
        keys_file.write_text(api_keys if isinstance(api_keys, str) else yaml.safe_dump(api_keys))
        domains_file.write_text(domains if isinstance(domains, str) else yaml.safe_dump(domains))
        monkeypatch.setattr(sys, "argv", ["dynamic-dns", "-a", str(keys_file), "-d", str(domains_file)])
        return main_module.main()

    return _run
