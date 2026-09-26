import requests
import json

from dynamic_dns.config import DNS_RECORD_TTL, PORKBUN_CREATE_URL, PORKBUN_EDIT_URL, PORKBUN_RETRIEVE_URL


def update_dns_record(domain, sub_domain, public_ip, secret):
    url = PORKBUN_EDIT_URL.format(domain=domain, subdomain=sub_domain or "").rstrip("/")

    data = {
        "secretapikey": secret["secretapikey"],
        "apikey": secret["apikey"],
        "content": public_ip,
        "ttl": DNS_RECORD_TTL,
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
    url = PORKBUN_CREATE_URL.format(domain=domain)

    data = {
        "secretapikey": secret["secretapikey"],
        "apikey": secret["apikey"],
        "name": sub_domain or "",
        "type": "A",
        "content": public_ip,
        "ttl": DNS_RECORD_TTL,
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
    url = PORKBUN_RETRIEVE_URL.format(domain=domain, subdomain=sub_domain or "").rstrip("/")

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
