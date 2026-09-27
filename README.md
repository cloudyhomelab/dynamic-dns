# dynamic-dns

Sync DNS A and AAAA records for domains hosted with Porkbun.

For each configured domain or subdomain, dynamic-dns looks up the current record in Porkbun. It creates the record if it is missing and updates it if the IP address has changed.

The record type follows the IP address: an IPv4 address sets an A record, an IPv6 address an AAAA record. When the IP source has both (a dual-stack `hostname`, or a public IPv6 address), both records are synced.

## Install

```sh
uv tool install git+https://github.com/cloudyhomelab/dynamic-dns
```

## Usage

```sh
dynamic-dns --api-keys-path api-keys.yaml --domains-path domains.yaml
```

| Option | Description |
|---|---|
| `-a`, `--api-keys-path` | YAML file with your Porkbun API keys |
| `-d`, `--domains-path` | YAML file listing the domains and subdomains to sync |

## Configuration

### API keys

Create an API key in the Porkbun dashboard and enable API access for each domain you want to manage (sample: [`examples/api-keys.yaml`](examples/api-keys.yaml)).

```yaml
apikey: pk1_...
secretapikey: sk1_...
```

This file holds credentials; keep it readable only by you (`chmod 600 api-keys.yaml`).

### Domains

A YAML list of entries (sample: [`examples/domains.yaml`](examples/domains.yaml)):

```yaml
- name: example.com
  subdomains:
    - home
    - vpn

- name: example.org
  hostname: router.example.net
  ttl: 3600
  delete_stale: true

- name: example.net
  subdomains:
    - nas
  ip: 192.168.1.10

- name: example.net
  subdomains:
    - nas6
  ip: "2001:db8::10"
```

| Field | Required | Description |
|---|---|---|
| `name` | yes | Domain registered with Porkbun |
| `subdomains` | no | Subdomains to sync. Omit to sync the domain itself (`example.org`); an empty list is rejected. |
| `hostname` | no | Use the addresses this hostname resolves to: its first IPv4 (A) and first IPv6 (AAAA) address |
| `ip` | no | Use this fixed IPv4 or IPv6 address. Quote IPv6 addresses. |
| `ttl` | no | Record TTL in seconds (default 600, the Porkbun minimum) |
| `delete_stale` | no | `true` to delete the A or AAAA record when that address family is gone (default `false`) |

Quote subdomains that YAML would read as booleans or numbers, such as `"no"`, `"on"` or `"1"`; unquoted, the config is rejected.

Where the IP addresses come from, in order:

1. `hostname`, if set
2. `ip`, if set
3. otherwise, this machine's public IPv4 address (from `checkip.amazonaws.com`, required) and public IPv6 address (from `api6.ipify.org`, skipped with a note if the machine has no IPv6)

With `delete_stale: true`, the entry owns both its A and AAAA records. When its `hostname` resolves without an IPv6 address, or its fixed `ip` is IPv4, the existing AAAA record is deleted (and the other way round for A). Entries that use the public IP never delete: a failed IPv6 lookup may be temporary. Leave it off if you manage some of these records by hand.

## Run periodically with systemd

[`examples/systemd/`](examples/systemd) has a user service and timer that sync every 5 minutes. They expect the binary in `~/.local/bin` (where `uv tool install` puts it) and the config in `~/.config/dynamic-dns/`.

```sh
mkdir -p ~/.config/dynamic-dns ~/.config/systemd/user
cp api-keys.yaml domains.yaml ~/.config/dynamic-dns/
cp examples/systemd/dynamic-dns.service examples/systemd/dynamic-dns.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now dynamic-dns.timer
```

User timers only run while you are logged in. To keep them running after logout and start them at boot:

```sh
loginctl enable-linger
```

Check the logs with `journalctl --user -u dynamic-dns`.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
