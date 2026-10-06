# t-online.de Email Pool

## Location
`C:/Users/User/Desktop/_PROJECTS/GPT-AUTOREG/emails.txt`

## Count
17,893 t-online.de email accounts with IMAP passwords.

## Format
```
email@t-online.de:password
```

Comments start with `#`. Separator lines with `---` are skipped.

## IMAP Settings
- **Server**: `secureimap.t-online.de`
- **Port**: `993`
- **SSL**: Yes

## Code Extraction Pattern
```python
import imaplib, email, re

mail = imaplib.IMAP4_SSL("secureimap.t-online.de", 993)
mail.login(addr, pw)
mail.select("inbox")
_, msgs = mail.search(None, "UNSEEN")
if not msgs[0]:
    _, msgs = mail.search(None, "ALL")
for num in msgs[0].split()[-5:]:  # Check last 5 messages
    _, data = mail.fetch(num, "(RFC822)")
    for part in data:
        if not isinstance(part, tuple): continue
        msg = email.message_from_bytes(part[1])
        # Extract body...
        codes = re.findall(r"\b(\d{6,8})\b", body)
        if codes and codes[0] != "000000":  # Filter false positives
            return codes[0]
```

## Pitfalls
- **False positive "000000"**: Some emails contain this string (timestamps, IDs). Filter it out.
- **UNSEEN filter**: Use `UNSEEN` first, fall back to `ALL` (last 5 messages) to avoid scanning thousands of messages.
- **Gmail accounts are dead**: The Gmail accounts from `C:/Users/User/Desktop/_PROJECTS/tusk-gateway/tusk_gmail_accounts.json` have expired 2FA app passwords. Do NOT use them for IMAP.