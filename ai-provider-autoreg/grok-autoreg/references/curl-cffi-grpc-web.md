# GrokRegister: curl_cffi + gRPC-web Registration

**Location**: `C:\Users\User\tmp\grok_register\grok-register\grok.py`

## Architecture

The registration uses **curl_cffi** (TLS fingerprint emulation, not a real browser) and direct **gRPC-web** API calls to x.ai's Next.js backend.

## Key Components

### 1. Action ID Discovery
```python
html = session.get("https://accounts.x.ai/sign-up").text
js_urls = [urljoin(start_url, m.group(0))
           for m in re.finditer(r"/_next/static/chunks/[^\"'\s>]+\.js", html)]
for js_url in js_urls:
    js_content = session.get(js_url, timeout=15).text
    match = re.search(r'7f[a-fA-F0-9]{40}', js_content)
    if match:
        action_id = match.group(0)
        break
```

### 2. gRPC-web OTP Sending
```python
def encode_grpc_message(field_id, string_value):
    key = (field_id << 3) | 2
    value_bytes = string_value.encode('utf-8')
    length = len(value_bytes)
    payload = struct.pack('B', key) + struct.pack('B', length) + value_bytes
    return b'\x00' + struct.pack('>I', len(payload)) + payload

session.post(f"{site_url}/auth_mgmt.AuthManagement/CreateEmailValidationCode",
    data=encode_grpc_message(1, email),
    headers={"content-type": "application/grpc-web+proto", "x-grpc-web": "1",
             "x-user-agent": "connect-es/2.1.1", "origin": site_url})
```

### 3. Registration Submission
```python
headers = {
    "user-agent": user_agent, "accept": "text/x-component",
    "content-type": "text/plain;charset=UTF-8", "origin": site_url,
    "referer": f"{site_url}/sign-up",
    "next-router-state-tree": state_tree, "next-action": action_id,
}
payload = [{
    "emailValidationCode": verify_code,
    "createUserAndSessionRequest": {
        "email": email, "givenName": name, "familyName": surname,
        "clearTextPassword": password, "tosAcceptedVersion": "$undefined"
    },
    "turnstileToken": token, "promptOnDuplicateEmail": True
}]
res = session.post(f"{site_url}/sign-up", json=payload, headers=headers)
```

### 4. SSO Cookie Extraction
```python
match = re.search(r'(https://[^"\s]+set-cookie\?q=[^:"\s]+)1:', res.text)
if match:
    verify_url = match.group(1)
    session.get(verify_url, allow_redirects=True)
    sso = session.cookies.get("sso")
```

## Key Insights
- gRPC-web endpoint: `{site_url}/auth_mgmt.AuthManagement/CreateEmailValidationCode`
- Content-type: `application/grpc-web+proto` (not JSON)
- `x-grpc-web: 1` header required
- `next-action` = action_id from JS chunks
- `next-router-state-tree` = state tree from HTML
- Turnstile sitekey: `0x4AAAAAAAhr9JGVDZbrZOo0`
- SSO from `set-cookie?q=` redirect URL in response