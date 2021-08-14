#! /usr/bin/python3

import os
import time
import random
import base64
import hmac
import hashlib
import json
import urllib.request
from datetime import datetime


def api_sign(method, host, params, uri):
    sign_str = "%s%s%s?%s" % (method, host, uri, "&".join(
        "%s=%s" % item for item in sorted(params.items(), key=lambda item: item[0])))
    return base64.b64encode(hmac.new(
        os.getenv('TENCENT_SECRET_KEY').encode(),
        sign_str.encode(), hashlib.sha256).digest()).decode()


def api_call(host, params={}, uri="/v2/index.php"):
    params.setdefault("SignatureMethod", "HmacSHA256")
    params.setdefault("Timestamp", int(time.time()))
    params.setdefault("Nonce", random.randint(0, 10000))
    params.setdefault("Region", "ap-hongkong-1")
    params.setdefault("SecretId", os.getenv("TENCENT_SECRET_ID"))
    params["Signature"] = api_sign("GET", host, params, uri)

    url = 'https://%s%s?%s' % (host, uri, urllib.parse.urlencode(params))
    with urllib.request.urlopen(url) as response:
        r = json.loads(response.read().decode())
    if r["code"] != 0:
        raise Exception("Api call fail, %s" % r["codeDesc"])
    return r


def upload_cert(domain, acme_install_dir):
    """https://cloud.tencent.com/document/product/400/9078"""
    cert_dir = os.path.expanduser(os.path.join(acme_install_dir, domain))
    params = {
        "alias": "%s.%s.%s" % (
            domain, datetime.utcnow().strftime("%Y%m%d"), int(time.time())),
        "Action": "CertUpload",
        "certType": "SVR",
    }
    with open(os.path.join(cert_dir, "fullchain.cer")) as f:
        params["cert"] = f.read()
    with open(os.path.join(cert_dir, "%s.key" % domain)) as f:
        params["key"] = f.read()

    return api_call("wss.api.qcloud.com", params)["data"]["id"]


def config_cdn_cert(cert_id, domain):
    """https://cloud.tencent.com/document/product/228/12965"""
    params = {"Action": "SetHttpsInfo", "host": domain, "http2": "on",
              "certId": cert_id, "httpsType": 4}
    return api_call("cdn.api.qcloud.com", params)


def list_cert_ids():
    """https://cloud.tencent.com/document/product/400/13675"""
    params = {"Action": "CertGetList"}
    r = api_call("wss.api.qcloud.com", {"Action": "CertGetList"})
    return [i["id"] for i in r["data"]["list"]]


def delete_cert(cert_id):
    """https://cloud.tencent.com/document/product/400/13696"""
    params = {"Action": "CertDelete", "id": cert_id}
    return api_call("wss.api.qcloud.com", params)


def main():
    domain = os.getenv("DOMAIN")

    cert_id = upload_cert(domain, os.getenv("ACME_INSTALL_DIR"))

    config_cdn_cert(cert_id, "www.%s" % domain)

    cert_ids = list_cert_ids()
    cert_ids.remove(cert_id)
    for cert_id in cert_ids:
        delete_cert(cert_id)

    print("Renew tencent cdn https cert done.")


if __name__ == "__main__":
    main()
