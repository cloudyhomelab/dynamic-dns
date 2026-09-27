# SPDX-License-Identifier: GPL-3.0-or-later

import socket
import sys
from pathlib import Path

import pytest
import requests
import yaml

from dynamic_dns import main as main_module
from tests.fakes import API_KEYS, FakeNetwork, FakePorkbun, Run


@pytest.fixture
def porkbun(monkeypatch: pytest.MonkeyPatch) -> FakePorkbun:
    fake = FakePorkbun()
    monkeypatch.setattr(requests, "post", fake.post)
    return fake


@pytest.fixture
def network(monkeypatch: pytest.MonkeyPatch) -> FakeNetwork:
    fake = FakeNetwork()
    monkeypatch.setattr(requests, "request", fake.request)
    monkeypatch.setattr(socket, "getaddrinfo", fake.getaddrinfo)
    return fake


@pytest.fixture
def run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, porkbun: FakePorkbun, network: FakeNetwork) -> Run:
    def _run(domains: object, api_keys: object = API_KEYS) -> int:
        keys_file = tmp_path / "api-keys.yaml"
        domains_file = tmp_path / "domains.yaml"
        keys_file.write_text(api_keys if isinstance(api_keys, str) else yaml.safe_dump(api_keys))
        domains_file.write_text(domains if isinstance(domains, str) else yaml.safe_dump(domains))
        monkeypatch.setattr(sys, "argv", ["dynamic-dns", "-a", str(keys_file), "-d", str(domains_file)])
        return main_module.main()

    return _run
