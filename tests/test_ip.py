# SPDX-License-Identifier: GPL-3.0-or-later

import ipaddress
import socket

import pytest
import requests

from dynamic_dns.ip import IpLookup, public_ips, resolve_hostname
from tests.fakes import FakeNetwork


def test_public_ips_includes_ipv6_when_available(network: FakeNetwork) -> None:
    network.public_ipv6 = "2001:db8::42"
    assert public_ips() == [ipaddress.ip_address("203.0.113.7"), ipaddress.ip_address("2001:db8::42")]


def test_public_ips_skips_ipv6_without_connectivity(network: FakeNetwork) -> None:
    assert public_ips() == [ipaddress.ip_address("203.0.113.7")]


def test_ipv6_service_returning_ipv4_counts_as_no_ipv6(network: FakeNetwork) -> None:
    network.public_ipv6 = "203.0.113.7"
    assert public_ips() == [ipaddress.ip_address("203.0.113.7")]


def test_public_ipv4_garbage_raises(network: FakeNetwork) -> None:
    network.public_ipv4 = "<html>login</html>"
    with pytest.raises(ValueError):
        public_ips()


def test_resolve_hostname_returns_first_of_each_family_ipv4_first(network: FakeNetwork) -> None:
    network.hosts["dual.test"] = ["2001:db8::5", "10.0.0.1", "10.0.0.2"]
    assert resolve_hostname("dual.test") == [ipaddress.ip_address("10.0.0.1"), ipaddress.ip_address("2001:db8::5")]


def test_lookup_caches_results_and_failures(network: FakeNetwork) -> None:
    network.hosts["router.test"] = ["10.0.0.1"]
    lookup = IpLookup()

    for _ in range(3):
        assert lookup.resolve("router.test") == [ipaddress.ip_address("10.0.0.1")]
        with pytest.raises(socket.gaierror):
            lookup.resolve("missing.test")

    assert network.lookups == ["router.test", "missing.test"]


def test_lookup_caches_public_ip_failure(network: FakeNetwork) -> None:
    network.public_ipv4_status = 503
    lookup = IpLookup()

    for _ in range(2):
        with pytest.raises(requests.HTTPError):
            lookup.resolve()

    assert network.lookups.count("https://checkip.amazonaws.com/") == 1
