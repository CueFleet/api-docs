"""Query authorized CueFleet accounts with the Python standard library."""

import json
import os
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    key = os.environ.get("CUEFLEET_API_KEY")
    if not key:
        raise SystemExit("Set CUEFLEET_API_KEY to the key generated in CueFleet.")

    base = os.environ.get("CUEFLEET_API_URL", "http://127.0.0.1:17687")
    url = urlsplit(base)
    if (url.scheme != "http" or url.hostname != "127.0.0.1"
            or url.username is not None or url.password is not None
            or url.path not in ("", "/") or url.query or url.fragment):
        raise SystemExit("Use the IPv4 loopback address shown in CueFleet.")

    request = Request(base.rstrip("/") + "/v1/accounts", headers={"Authorization": "Bearer " + key})
    opener = build_opener(ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=35) as response:
            result = json.load(response)
    except HTTPError as error:
        raise SystemExit(f"CueFleet request failed with HTTP {error.code}.") from None
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
