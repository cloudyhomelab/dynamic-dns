# SPDX-License-Identifier: GPL-3.0-or-later

import socket

import requests

from dynamic_dns.config import PUBLIC_IP_URL, REQUEST_TIMEOUT_SECONDS


def public_ip():
    response = requests.request("GET", PUBLIC_IP_URL, timeout=REQUEST_TIMEOUT_SECONDS)

    if response.status_code == requests.codes.ok:
        return response.text.strip()

    print("Request to fetch the public ip failed with status code:", response.status_code)
    return None


class IpLookup:
    """Resolves hostnames and the public IP at most once per run."""

    def __init__(self):
        # hostname (None for the public IP) -> ip, or the error the lookup raised
        self._cache = {}

    def resolve(self, hostname=None):
        if hostname not in self._cache:
            try:
                self._cache[hostname] = socket.gethostbyname(hostname) if hostname else public_ip()
            except (requests.RequestException, OSError) as e:
                self._cache[hostname] = e
        result = self._cache[hostname]
        if isinstance(result, Exception):
            raise result
        return result
