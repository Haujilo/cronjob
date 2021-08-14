#! /usr/bin/python3

import os
import json
from urllib import request, parse


def api_call(path, data=None,  url_prefix="https://api.netlify.com/api/v1"):
    """https://www.netlify.com/docs/api/"""
    url = "%s%s" % (url_prefix, path)
    token = os.getenv("NETLIFY_API_TOKEN")
    headers = {"Authorization": "Bearer %s" % token}
    data = parse.urlencode(data).encode() if data else None
    with request.urlopen(request.Request(url, data, headers)) as response:
        return json.loads(response.read().decode())


def upload_sert(domain, acme_install_dir):
    cert_dir = os.path.expanduser(os.path.join(acme_install_dir, domain))
    data = {
        "site_id": "www.%s" % domain,
    }
    with open(os.path.join(cert_dir, "%s.cer" % domain)) as f:
        data["certificate"] = f.read()
    with open(os.path.join(cert_dir, "%s.key" % domain)) as f:
        data["key"] = f.read()
    with open(os.path.join(cert_dir, "ca.cer")) as f:
        data["ca_certificates"] = f.read()
    return api_call("/sites/%s/ssl" % data["site_id"], data)


def main():
    upload_sert(os.getenv("DOMAIN"), os.getenv("ACME_INSTALL_DIR"))
    print("Renew netlify https cert done.")


if __name__ == "__main__":
    main()
