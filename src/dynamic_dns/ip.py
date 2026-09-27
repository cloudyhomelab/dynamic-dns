# SPDX-License-Identifier: GPL-3.0-or-later

import ipaddress
import socket

import requests

from dynamic_dns.config import PUBLIC_IPV4_URL, PUBLIC_IPV6_URL, REQUEST_TIMEOUT_SECONDS


def _fetch_ip(url, version):
    response = requests.request("GET", url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    # ValueError for anything that is not an IP, e.g. a captive portal page
    address = ipaddress.ip_address(response.text.strip())
    if address.version != version:
        raise ValueError(f"{url} returned {address}, expected an IPv{version} address")
    return address


def public_ipv4():
    return _fetch_ip(PUBLIC_IPV4_URL, 4)


def public_ipv6():
    return _fetch_ip(PUBLIC_IPV6_URL, 6)


def public_ips():
    addresses = [public_ipv4()]
    # many connections have no IPv6; skip the AAAA records instead of failing
    try:
        addresses.append(public_ipv6())
    except (requests.RequestException, ValueError) as e:
        print(f"No public IPv6 address, skipping AAAA records: {e}")
    return addresses


def resolve_hostname(hostname):
    # first address of each family, IPv4 before IPv6
    by_family = {}
    for family, _, _, _, sockaddr in socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP):
        by_family.setdefault(family, ipaddress.ip_address(sockaddr[0]))
    return [by_family[family] for family in (socket.AF_INET, socket.AF_INET6) if family in by_family]


class IpLookup:
    """Resolves hostnames and the public IPs at most once per run, at most one address per family."""

    def __init__(self):
        # hostname (None for the public IPs) -> list of addresses, or the error the lookup raised
        self._cache = {}

    def resolve(self, hostname=None):
        if hostname not in self._cache:
            try:
                self._cache[hostname] = resolve_hostname(hostname) if hostname else public_ips()
            except (requests.RequestException, OSError, ValueError) as e:
                self._cache[hostname] = e
        result = self._cache[hostname]
        if isinstance(result, Exception):
            raise result
        return result
