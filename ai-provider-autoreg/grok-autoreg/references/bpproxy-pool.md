# bpproxy Residential Proxy Pool

## Location
`C:/Users/User/tmp/bpproxy_hardsession_pool.txt`

## Format
```
# Account: <account_id>
http://bpuser-<user>:<password>_hardsession-<session>@residential-x.bpproxy.at:1000
http://bpuser-<user>:<password>_hardsession-<session>@datacenter-x.bpproxy.at:2000
```

## Usage
- **Residential proxies** (port 1000): Use these for Cloudflare-bypass. They rotate IPs and look like real residential connections.
- **Datacenter proxies** (port 2000): Do NOT use for Cloudflare-protected sites. They get blocked.

## Filtering
```python
def load_proxies():
    proxies = []
    with open("C:/Users/User/tmp/bpproxy_hardsession_pool.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("http://") and "residential" in line:
                proxies.append(line)
    return proxies
```

## Playwright Usage
```python
browser = await p.chromium.launch(
    headless=True,
    proxy={"server": proxy_url},
    args=["--no-sandbox"]
)
```

## ZTE Proxy (DO NOT USE for Playwright)
- The ZTE HTTP forward proxy at `127.0.0.1:8888` (`C:/Users/User/Desktop/gh-autoreg/zte_proxy.py`) routes through ZTE MF935 USB modem
- It works for HTTP requests (curl) but fails for Playwright's CONNECT tunnels
- Playwright reports `net::ERR_PROXY_CONNECTION_FAILED`
- Use bpproxy instead for Playwright-based automation