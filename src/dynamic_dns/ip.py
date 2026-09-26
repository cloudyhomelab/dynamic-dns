import requests

from dynamic_dns.config import PUBLIC_IP_URL


def public_ip():
    response = requests.request("GET", PUBLIC_IP_URL)

    if response.status_code == requests.codes.ok:
        return response.text.strip()

    print(
        "Request to fetch the public ip failed with status code:", response.status_code
    )
    return None
