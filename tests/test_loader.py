# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path

import pytest

from dynamic_dns.config import DNS_RECORD_TTL
from dynamic_dns.loader import ApiKeys, DomainConfig, load_domains, load_secrets

EXAMPLES = Path(__file__).parent.parent / "examples"


def write(tmp_path: Path, text: str) -> str:
    path = tmp_path / "config.yaml"
    path.write_text(text)
    return str(path)


def test_examples_load() -> None:
    assert load_secrets(str(EXAMPLES / "api-keys.yaml")) == ApiKeys("pk1_...", "sk1_...")
    assert len(load_domains(str(EXAMPLES / "domains.yaml"))) == 5


def test_entries_expand_to_one_record_per_subdomain_with_defaults(tmp_path: Path) -> None:
    path = write(tmp_path, "- name: example.com\n  subdomains: [home, vpn]\n  ttl: 3600\n- name: example.org\n")

    assert load_domains(path) == [
        DomainConfig("example.com", "home", None, None, 3600, False, True),
        DomainConfig("example.com", "vpn", None, None, 3600, False, True),
        DomainConfig("example.org", None, None, None, DNS_RECORD_TTL, False, True),
    ]


def test_null_subdomains_means_the_apex(tmp_path: Path) -> None:
    assert [d.subdomain for d in load_domains(write(tmp_path, "- name: example.com\n  subdomains:\n"))] == [None]


def test_json_config_still_loads(tmp_path: Path) -> None:
    assert load_domains(write(tmp_path, '[{"name": "example.com", "ip": "1.2.3.4"}]'))[0].ip == "1.2.3.4"


@pytest.mark.parametrize(
    ("yaml_text", "message"),
    [
        ("- name: example.com\n  subdomains: [home, no]\n", "subdomains must be str, got False; quote it"),
        ("- name: example.com\n  subdomains: [1]\n", "subdomains must be str, got 1"),
        ("- name: example.com\n  subdomains: home\n", "subdomains must be list[str] | None, got 'home'"),
        ("- name: example.com\n  subdomains: []\n", "subdomains is empty"),
        ("- subdomains: [home]\n", "name is missing"),
        ("- name: example.com\n  hostname: 12345\n", "hostname must be str | None, got 12345"),
        ("- name: example.com\n  ip: 300.1.1.1\n", "ip '300.1.1.1' is not an IPv4 or IPv6 address"),
        ("- name: example.com\n  ip: 1:2:3:4:5:6:7:8\n", "ip must be str | None"),
        ("- name: example.com\n  ttl: yes\n", "ttl must be int, got True"),
        ("- name: example.com\n  ttl: '3600'\n", "ttl must be int, got '3600'"),
        ("- name: example.com\n  delete_stale: 'yes'\n", "delete_stale must be bool"),
        ("- name: example.com\n  delete_extra: 'no'\n", "delete_extra must be bool"),
        ("name: example.com\n", "expected a list of entries"),
        ("", "expected a list of entries"),
        ("- name: example.com\n- example.org\n", "entry 2: expected a mapping"),
    ],
)
def test_invalid_domains_are_rejected(tmp_path: Path, yaml_text: str, message: str) -> None:
    with pytest.raises((TypeError, ValueError), match=message.replace("|", r"\|").replace("[", r"\[")):
        load_domains(write(tmp_path, yaml_text))


@pytest.mark.parametrize(
    ("yaml_text", "message"),
    [
        ("apikey: pk1_abc\n", "secretapikey is missing"),
        ("apikey: 12345678901234\nsecretapikey: sk1_abc\n", "apikey must be str, got int"),
        ("apikey: ''\nsecretapikey: sk1_abc\n", "apikey is empty"),
        ("- apikey: pk1_abc\n", "expected apikey and secretapikey, got list"),
        ("", "expected apikey and secretapikey, got NoneType"),
    ],
)
def test_invalid_api_keys_are_rejected(tmp_path: Path, yaml_text: str, message: str) -> None:
    with pytest.raises((TypeError, ValueError), match=message) as error:
        load_secrets(write(tmp_path, yaml_text))
    assert "12345678901234" not in str(error.value)
