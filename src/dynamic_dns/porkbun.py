import requests
import json

# sync dns records for domains hosted with porkbun
PROKBUN_API_BASE_URL="https://api.porkbun.com/api/json/v3/dns"


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
