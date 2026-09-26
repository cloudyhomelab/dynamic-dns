from dataclasses import dataclass
import requests
import json
import argparse
import socket

# sync dns records for domains hosted with porkbun
PROKBUN_API_BASE_URL="https://api.porkbun.com/api/json/v3/dns"

@dataclass
class DomainConfig:
    """Class for keeping track of domain configurations."""
    name: str
    subdomain: str
    hostname: str
    ip: str


def load_secrets(secret_file_path):
    # expects json structure
    # {'secretapikey': 'xxx', 'apikey': 'xxx'}
    with open(secret_file_path) as secret_file:
        secret = json.load(secret_file)
    return secret


def load_domains(domains_file_path):
    # expects json structure
    # [{'name': 'xxx', 'subdomains': ['xxx', 'xxx', ...]} , 'hostname': 'xxxx', 'ip': 'x.x.x.x' ...]
    with open(domains_file_path) as domains_file:
        domains = json.load(domains_file)
        data = []
        for item in domains:
            if "subdomains" in item:
                data.extend([DomainConfig (item["name"],subdomain,item.get("hostname"),item.get("ip")) for subdomain in item.get("subdomains")])
            else:
                data.append(DomainConfig (item["name"],None,item.get("hostname"),item.get("ip")))
    return data


def public_ip():
    response = requests.request("GET", "https://checkip.amazonaws.com/")

    if response.status_code == requests.codes.ok:
        return response.text.strip()

    print(
        "Request to fetch the public ip failed with status code:", response.status_code
    )
    return None


def update_dns_record(domain, sub_domain, public_ip, secret):
    url = f"{PROKBUN_API_BASE_URL}/editByNameType/{domain}/A/{sub_domain}" if sub_domain else f"{PROKBUN_API_BASE_URL}/editByNameType/{domain}/A"

    data = {
        "secretapikey": secret["secretapikey"],
        "apikey": secret["apikey"],
        "content": public_ip,
        "ttl": "600",
    }

    response = requests.post(url, data=json.dumps(data))

    if response.status_code == requests.codes.ok:
        print(f"DNS records updated")
        return True
    else:
        print(
            "Request to update dns record failed with status code:",
            response.status_code,
        )
        print("Reason: ", response.reason)

    return False

def create_dns_record(domain, sub_domain, public_ip, secret):
    url = f"{PROKBUN_API_BASE_URL}/create/{domain}"

    data = {
        "secretapikey": secret["secretapikey"],
        "apikey": secret["apikey"],
        "name": sub_domain or "",
        "type": "A",
        "content": public_ip,
        "ttl": "600",
    }

    response = requests.post(url, data=json.dumps(data))

    if response.status_code == requests.codes.ok:
        print(f"DNS records created")
        return True
    else:
        print(
            "Request to create dns record failed with status code:",
            response.status_code,
        )
        print("Reason: ", response.reason)

    return False


def get_current_ip(domain, sub_domain, secret):
    url = f"{PROKBUN_API_BASE_URL}/retrieveByNameType/{domain}/A/{sub_domain}" if sub_domain else f"{PROKBUN_API_BASE_URL}/retrieveByNameType/{domain}/A"

    response = requests.post(url, data=json.dumps(secret))
    if response.status_code == requests.codes.ok:
        records = response.json()["records"]
        if records:
            return records[0]["content"]
        else:
            print(f"No records entry exists for {sub_domain}.{domain}")
            return None

    print(
        "Request to fetch existing dns failed with status code:", response.status_code
    )
    print("Reason:", response.reason)
    return None


def change_my_dns(domain, sub_domain, config_ip, secret):
    # if config_ip is not present then sync the public ip
    my_ip = config_ip or public_ip()
    prev_ip = get_current_ip(domain, sub_domain, secret)

    if my_ip is not None:
        if prev_ip is not None:
            if my_ip != prev_ip:
                update_dns_record(domain, sub_domain, my_ip, secret)
            else:
                print("No changes to update")
        else:
            create_dns_record(domain, sub_domain, my_ip, secret)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync DNS records in Porkbun")
    parser.add_argument(
        "-a",
        "--api-keys-path",
        dest="api_file",
        type=str,
        required=True,
        help="path of the json file containing the porkbun api keys",
    )
    parser.add_argument(
        "-d",
        "--domains-path",
        dest="domain_file",
        type=str,
        required=True,
        help="path of the json file containing the domain/sub-domains to sync",
    )
    args = parser.parse_args()

    secret = load_secrets(args.api_file)
    domains = load_domains(args.domain_file)

    for item in domains:
            item.ip = socket.gethostbyname(item.hostname) if item.hostname else item.ip
            if item.subdomain:
                print(f"setting up {item.subdomain}.{item.name} for hostname {item.hostname} or ip {item.ip}")
            else:
                print(f"setting up {item.name} for hostname {item.hostname} or ip {item.ip}")
            change_my_dns(item.name, item.subdomain, item.ip, secret)
