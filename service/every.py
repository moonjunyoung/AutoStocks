from pprint import pprint
from urllib.parse import urljoin

import requests


api_token = "155fba0b42e78962695d01dcd1d46d41369883ae"
headers = {"Authorization": f"Token {api_token}"}

username = "hingu"  # update to match your USERNAME!

pythonanywhere_host = "www.pythonanywhere.com"  # or "eu.pythonanywhere.com" if your account is hosted on our EU servers
pythonanywhere_domain = "pythonanywhere.com"  # or "eu.pythonanywhere.com"

# make sure you don't use this domain already!
domain_name = f"{username}.{pythonanywhere_domain}"

api_base = f"https://{pythonanywhere_host}/api/v1/user/{username}/"
command = (
    f"/home/{username}/.virtualenvs/fast_venv/bin/uvicorn "
    "--uds $DOMAIN_SOCKET "
    "test.main:app "
)

response = requests.post(
    urljoin(api_base, "websites/"),
    headers=headers,
    json={
        "domain_name": domain_name,
        "enabled": True,
        "webapp": {"command": command}
    },
)
pprint(response.json())