# SPDX-License-Identifier: GPL-3.0-or-later

from dynamic_dns.config import DNS_RECORD_TTL, PUBLIC_IPV4_URL, PUBLIC_IPV6_URL


def test_creates_missing_records_for_subdomains_and_apex(run, porkbun):
    assert run([{"name": "example.com", "subdomains": ["home", "vpn"]}, {"name": "example.org"}]) == 0

    assert porkbun.get("example.com", "A", "home") == [("203.0.113.7", DNS_RECORD_TTL)]
    assert porkbun.get("example.com", "A", "vpn") == [("203.0.113.7", DNS_RECORD_TTL)]
    assert porkbun.get("example.org", "A") == [("203.0.113.7", DNS_RECORD_TTL)]


def test_up_to_date_record_is_left_alone(run, porkbun):
    porkbun.add("example.com", "A", "", "203.0.113.7")

    assert run([{"name": "example.com"}]) == 0
    assert porkbun.writes() == []


def test_changed_ip_edits_the_record_by_id(run, porkbun):
    record_id = porkbun.add("example.com", "A", "home", "198.51.100.1")

    assert run([{"name": "example.com", "subdomains": ["home"]}]) == 0

    assert porkbun.writes() == [
        ("edit", ["example.com", record_id], {"name": "home", "type": "A", "content": "203.0.113.7", "ttl": "600"})
    ]


def test_ttl_change_alone_updates_the_record(run, porkbun):
    porkbun.add("example.com", "A", "", "203.0.113.7", ttl=600)

    assert run([{"name": "example.com", "ttl": 3600}]) == 0
    assert porkbun.get("example.com", "A") == [("203.0.113.7", 3600)]


def test_equal_ipv6_in_another_spelling_is_not_rewritten(run, porkbun):
    porkbun.add("example.com", "AAAA", "", "2001:0db8:0000:0000:0000:0000:0000:0001")

    assert run([{"name": "example.com", "ip": "2001:db8::1"}]) == 0
    assert porkbun.writes() == []


def test_fixed_ipv6_ip_manages_an_aaaa_record(run, porkbun, network):
    assert run([{"name": "example.com", "ip": "2001:db8::10"}]) == 0

    assert porkbun.get("example.com", "AAAA") == [("2001:db8::10", DNS_RECORD_TTL)]
    assert porkbun.get("example.com", "A") == []
    assert network.lookups == []


def test_dual_stack_public_ip_syncs_a_and_aaaa(run, porkbun, network):
    network.public_ipv6 = "2001:db8::42"

    assert run([{"name": "example.com"}]) == 0

    assert porkbun.get("example.com", "A") == [("203.0.113.7", DNS_RECORD_TTL)]
    assert porkbun.get("example.com", "AAAA") == [("2001:db8::42", DNS_RECORD_TTL)]


def test_missing_public_ipv6_skips_aaaa_without_failing(run, porkbun, capsys):
    assert run([{"name": "example.com"}]) == 0

    assert porkbun.get("example.com", "AAAA") == []
    assert "No public IPv6 address, skipping AAAA records" in capsys.readouterr().out


def test_hostname_uses_first_address_of_each_family(run, porkbun, network):
    network.hosts["router.test"] = ["10.0.0.1", "10.0.0.2", "2001:db8::5", "2001:db8::6"]

    assert run([{"name": "example.com", "hostname": "router.test"}]) == 0

    assert porkbun.get("example.com", "A") == [("10.0.0.1", DNS_RECORD_TTL)]
    assert porkbun.get("example.com", "AAAA") == [("2001:db8::5", DNS_RECORD_TTL)]


def test_lookups_happen_once_per_run_even_when_they_fail(run, network):
    network.hosts["router.test"] = ["10.0.0.1"]
    domains = [
        {"name": "example.com", "subdomains": ["a", "b"]},
        {"name": "example.org", "subdomains": ["x", "y"], "hostname": "router.test"},
        {"name": "example.net", "subdomains": ["p", "q"], "hostname": "missing.test"},
    ]

    assert run(domains) == 1
    assert sorted(network.lookups) == sorted([PUBLIC_IPV4_URL, PUBLIC_IPV6_URL, "router.test", "missing.test"])


def test_unresolvable_hostname_fails_only_its_own_record(run, porkbun, capsys):
    assert run([{"name": "example.com", "hostname": "missing.test"}, {"name": "example.org"}]) == 1

    assert porkbun.get("example.org", "A") == [("203.0.113.7", DNS_RECORD_TTL)]
    assert "Failed to sync example.com" in capsys.readouterr().out


def test_captive_portal_page_is_not_pushed_as_an_ip(run, porkbun, network, capsys):
    network.public_ipv4 = "<html>Please log in to the hotel wifi</html>"

    assert run([{"name": "example.com"}]) == 1
    assert porkbun.writes() == []
    assert "does not appear to be an IPv4 or IPv6 address" in capsys.readouterr().out


def test_public_ipv4_service_error_fails_the_record(run, porkbun, network):
    network.public_ipv4_status = 503

    assert run([{"name": "example.com"}]) == 1
    assert porkbun.writes() == []


def test_failed_lookup_does_not_create_a_duplicate(run, porkbun):
    porkbun.add("example.com", "A", "", "198.51.100.1")
    porkbun.failing.add("retrieveByNameType")

    assert run([{"name": "example.com"}]) == 1
    assert porkbun.writes() == []


def test_failed_create_exits_1(run, porkbun):
    porkbun.failing.add("create")

    assert run([{"name": "example.com"}]) == 1


def test_extra_records_are_deleted_keeping_the_matching_one(run, porkbun):
    porkbun.add("example.com", "A", "", "198.51.100.1")
    porkbun.add("example.com", "A", "", "203.0.113.7")
    porkbun.add("example.com", "A", "", "198.51.100.2")

    assert run([{"name": "example.com"}]) == 0

    assert porkbun.get("example.com", "A") == [("203.0.113.7", DNS_RECORD_TTL)]
    assert [c[0] for c in porkbun.writes()] == ["delete", "delete"]


def test_matching_record_is_found_among_extras_despite_ipv6_spelling(run, porkbun):
    porkbun.add("example.com", "AAAA", "", "2001:db8::99")
    porkbun.add("example.com", "AAAA", "", "2001:0db8:0000:0000:0000:0000:0000:0010")

    assert run([{"name": "example.com", "ip": "2001:db8::10"}]) == 0

    assert porkbun.get("example.com", "AAAA") == [("2001:0db8:0000:0000:0000:0000:0000:0010", 600)]
    assert [c[0] for c in porkbun.writes()] == ["delete"]


def test_extra_records_without_a_match_edit_the_first_then_delete_the_rest(run, porkbun):
    first = porkbun.add("example.com", "A", "", "198.51.100.1")
    porkbun.add("example.com", "A", "", "198.51.100.2")

    assert run([{"name": "example.com"}]) == 0

    assert porkbun.get("example.com", "A") == [("203.0.113.7", DNS_RECORD_TTL)]
    assert porkbun.writes()[0][:2] == ("edit", ["example.com", first])


def test_delete_extra_false_keeps_extra_records_and_warns(run, porkbun, capsys):
    porkbun.add("example.com", "A", "", "198.51.100.1")
    porkbun.add("example.com", "A", "", "198.51.100.2")

    assert run([{"name": "example.com", "delete_extra": False}]) == 0

    assert porkbun.get("example.com", "A") == [("203.0.113.7", 600), ("198.51.100.2", 600)]
    assert "1 other A record(s) exist for example.com" in capsys.readouterr().out


def test_extra_records_survive_a_failed_edit(run, porkbun):
    porkbun.add("example.com", "A", "", "198.51.100.1")
    porkbun.add("example.com", "A", "", "198.51.100.2")
    porkbun.failing.add("edit")

    assert run([{"name": "example.com"}]) == 1
    assert len(porkbun.get("example.com", "A")) == 2
    assert [c[0] for c in porkbun.writes()] == ["edit"]


def test_delete_stale_removes_aaaa_when_hostname_has_no_ipv6(run, porkbun, network):
    network.hosts["router.test"] = ["10.0.0.1"]
    porkbun.add("example.com", "A", "", "10.0.0.1")
    porkbun.add("example.com", "AAAA", "", "2001:db8::99")

    assert run([{"name": "example.com", "hostname": "router.test", "delete_stale": True}]) == 0

    assert porkbun.get("example.com", "AAAA") == []
    assert porkbun.get("example.com", "A") == [("10.0.0.1", 600)]


def test_delete_stale_removes_a_when_fixed_ip_is_ipv6(run, porkbun):
    porkbun.add("example.com", "A", "", "198.51.100.1")

    assert run([{"name": "example.com", "ip": "2001:db8::10", "delete_stale": True}]) == 0
    assert porkbun.get("example.com", "A") == []


def test_stale_records_are_kept_without_delete_stale(run, porkbun, network):
    network.hosts["router.test"] = ["10.0.0.1"]
    porkbun.add("example.com", "AAAA", "", "2001:db8::99")

    assert run([{"name": "example.com", "hostname": "router.test"}]) == 0
    assert porkbun.get("example.com", "AAAA") == [("2001:db8::99", 600)]


def test_public_ip_entries_never_delete_stale_records(run, porkbun):
    porkbun.add("example.com", "AAAA", "", "2001:db8::99")

    assert run([{"name": "example.com", "delete_stale": True}]) == 0
    assert porkbun.get("example.com", "AAAA") == [("2001:db8::99", 600)]


def test_invalid_config_exits_1_before_any_network_call(run, porkbun, network, capsys):
    assert run([{"name": "example.com", "subdomains": [False]}]) == 1

    assert porkbun.calls == [] and network.lookups == []
    assert "Invalid domains config" in capsys.readouterr().out


def test_invalid_api_keys_exit_1_before_any_network_call(run, porkbun, network, capsys):
    assert run([{"name": "example.com"}], api_keys={"apikey": "pk1_test"}) == 1

    assert porkbun.calls == [] and network.lookups == []
    assert "Invalid api keys config" in capsys.readouterr().out
