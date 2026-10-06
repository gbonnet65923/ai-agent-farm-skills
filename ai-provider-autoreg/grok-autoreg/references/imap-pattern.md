# IMAP Verification Code Extraction Pattern

## Key Lessons
- `mail.search(None, "ALL")` HANGS on large mailboxes (5000+ emails)
- **Fix**: Use `mail.search(None, '(UNSEEN FROM "x.ai")')` with fallback to `mail.search(None, "UNSEEN")`
- **Socket timeout**: Always set `mail = imaplib.IMAP4_SSL(host, port, timeout=30)` and `mail.socket().settimeout(30)`
- Wrap each search in try/except

## Working Code Snippet
```python
def get_verification_code(email_addr, password, timeout=180):
    import socket
    mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, timeout=30)
    mail.socket().settimeout(30)
    mail.login(email_addr, password)
    mail.select("INBOX")
    
    start = time.time()
    while time.time() - start < timeout:
        try:
            typ, data = mail.search(None, '(UNSEEN FROM "x.ai")')
            if typ != "OK":
                typ, data = mail.search(None, "UNSEEN")
            if typ == "OK" and data[0]:
                ids = data[0].split()
                for mid in reversed(ids):
                    # fetch and parse message
                    ...
                    if "x.ai" in sender.lower():
                        code_match = re.search(r'\b([A-Z0-9]{3}-[A-Z0-9]{3})\b', body)
                        if code_match:
                            return code_match.group(1)
        except Exception as e:
            print(f"IMAP search error: {e}")
        time.sleep(5)
```