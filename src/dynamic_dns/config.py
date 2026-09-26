from dataclasses import dataclass
import json


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
