# dynamic-dns

Sync DNS A records for domains hosted with Porkbun.

For each configured domain or subdomain, dynamic-dns looks up the current A record in Porkbun. It creates the record if it is missing and updates it if the IP address has changed.

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

- name: example.net
  subdomains:
    - nas
  ip: 192.168.1.10
```

| Field | Required | Description |
|---|---|---|
| `name` | yes | Domain registered with Porkbun |
| `subdomains` | no | Subdomains to sync. Omit to sync the domain itself (`example.org`). |
| `hostname` | no | Use the IPv4 address this hostname resolves to |
| `ip` | no | Use this fixed IP address |

Quote subdomains that YAML would read as booleans or numbers, such as `"no"`, `"on"` or `"1"`.

Where the IP address comes from, in order:

1. `hostname`, if set
2. `ip`, if set
3. otherwise, this machine's public IP address (from `checkip.amazonaws.com`)

Records are created with a TTL of 600 seconds.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
