# SPDX-License-Identifier: GPL-3.0-or-later

PORKBUN_API_BASE_URL = "https://api.porkbun.com/api/json/v3/dns"
PORKBUN_EDIT_URL = PORKBUN_API_BASE_URL + "/editByNameType/{domain}/{type}/{subdomain}"
PORKBUN_CREATE_URL = PORKBUN_API_BASE_URL + "/create/{domain}"
PORKBUN_RETRIEVE_URL = PORKBUN_API_BASE_URL + "/retrieveByNameType/{domain}/{type}/{subdomain}"
PORKBUN_DELETE_URL = PORKBUN_API_BASE_URL + "/deleteByNameType/{domain}/{type}/{subdomain}"
PUBLIC_IPV4_URL = "https://checkip.amazonaws.com/"
# IPv6-only host, so the request goes out over IPv6
PUBLIC_IPV6_URL = "https://api6.ipify.org/"
# used when a domain entry has no ttl
DNS_RECORD_TTL = 600
REQUEST_TIMEOUT_SECONDS = 10
