import requests


def public_ip():
    response = requests.request("GET", "https://checkip.amazonaws.com/")

    if response.status_code == requests.codes.ok:
        return response.text.strip()

    print(
        "Request to fetch the public ip failed with status code:", response.status_code
    )
    return None
