# SPDX-License-Identifier: GPL-3.0-or-later

PORKBUN_API_BASE_URL = "https://api.porkbun.com/api/json/v3/dns"
PORKBUN_EDIT_URL = PORKBUN_API_BASE_URL + "/editByNameType/{domain}/A/{subdomain}"
PORKBUN_CREATE_URL = PORKBUN_API_BASE_URL + "/create/{domain}"
PORKBUN_RETRIEVE_URL = PORKBUN_API_BASE_URL + "/retrieveByNameType/{domain}/A/{subdomain}"
PUBLIC_IP_URL = "https://checkip.amazonaws.com/"
DNS_RECORD_TTL = "600"
REQUEST_TIMEOUT_SECONDS = 10
