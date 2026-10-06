#!/usr/bin/env python3
"""
RSI AI Auto-Reg — mass account registration via Playwright + Outlook IMAP
Registers accounts, extracts API keys.

Requirements: pip install playwright httpx
Run: PYTHONPATH="" python rsiai_autoreg.py
"""

import asyncio
import random
import string
import time
import imaplib
import email
import re
import json
import httpx
from pathlib import Path
from playwright.async_api import async_playwright

# === CONFIG ===
SIGNUP_URL = "https://www.rsiai.net/sign-up"
DASHBOARD_URL = "https://www.rsiai.net/dashboard"
TOKEN_URL = "https://www.rsiai.net/token"
OUTPUT_FILE = Path.home() / "Desktop" / "_SCRIPTS" / "rsiai_keys.json"

# Outlook IMAP config
IMAP_SERVER = "outlook.office365.com"
IMAP_PORT = 993
IMAP_EMAIL = "your_email@outlook.com"  # CHANGE THIS
IMAP_PASS = "your_app_password"        # CHANGE THIS


def randid(k=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=k))


def randid_email(base="gothbreach"):
    """Generate Outlook alias: base+rand@outlook.com"""
    return f"{base}+{randid(8)}@outlook.com"


async def get_verification_code(email_addr, timeout=120):
    """Poll Outlook IMAP for verification code from RSI AI"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
            mail.login(IMAP_EMAIL, IMAP_PASS)
            mail.select("inbox")
            status, msgs = mail.search(None, '(FROM "rsiai" UNSEEN)')
            if not status == "OK" or not msgs[0]:
                status, msgs = mail.search(None, '(FROM "noreply" UNSEEN)')
            if status != "OK" or not msgs[0]:
                mail.logout()
                await asyncio.sleep(5)
                continue
            msg_ids = msgs[0].split()
            latest = msg_ids[-1]
            status, data = mail.fetch(latest, "(RFC822)")
            if status != "OK":
                mail.logout()
                continue
            raw = data[0][1]
            msg = email.message_from_bytes(raw)
            subject = msg.get("Subject", "")
            code_match = re.search(r'(\d{4,8})', subject)
            if code_match:
                mail.logout()
                return code_match.group(1)
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors='ignore')
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors='ignore')
            code_match = re.search(r'(\d{4,8})', body)
            if code_match:
                mail.logout()
                return code_match.group(1)
            mail.logout()
        except Exception as e:
            print(f"  IMAP error: {e}")
        await asyncio.sleep(5)
    return None


async def register_account(playwright, email_addr, username, password):
    """Register one account via Playwright"""
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    page = await context.new_page()

    try:
        await page.goto(SIGNUP_URL, wait_until="networkidle")
        await asyncio.sleep(2)

        await page.fill('input[name="username"]', username)
        await page.fill('input[name="password"]', password)
        await page.fill('input[name="password2"]', password)
        await page.fill('input[name="email"]', email_addr)
        await asyncio.sleep(0.5)

        send_btn = page.locator('button:has-text("Send code")')
        await send_btn.click()
        await asyncio.sleep(0.5)
        print(f"  [+] Sent code to {email_addr}")

        code = await get_verification_code(email_addr)
        if not code:
            print(f"  [-] No code received for {email_addr}")
            return None
        print(f"  [+] Code: {code}")

        await page.fill('input[name="code"]', code)
        agree = page.locator('input[type="checkbox"]').first
        await agree.check()

        create_btn = page.locator('button:has-text("Create account")')
        await create_btn.click()
        await asyncio.sleep(3)

        if "dashboard" in page.url.lower() or "sign-up" not in page.url:
            print(f"  [+] Registered: {username}")

            await page.goto(TOKEN_URL, wait_until="networkidle", timeout=15000)
            await asyncio.sleep(2)

            api_key = await page.evaluate("""() => {
                const el = document.querySelector('input[value*="sk-"]');
                if (el) return el.value;
                const text = document.body.innerText;
                const m = text.match(/sk-[a-zA-Z0-9]{20,}/);
                return m ? m[0] : null;
            }""")

            if not api_key:
                create_key_btn = page.locator('button:has-text("Create"), button:has-text("New"), button:has-text("Generate")').first
                try:
                    await create_key_btn.click(timeout=5000)
                    await asyncio.sleep(2)
                    api_key = await page.evaluate("""() => {
                        const el = document.querySelector('input[value*="sk-"]');
                        return el ? el.value : null;
                    }""")
                except:
                    pass

            result = {
                "username": username,
                "email": email_addr,
                "password": password,
                "api_key": api_key,
                "created": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            print(f"  [+] API key: {api_key[:20] if api_key else 'N/A'}...")
            return result
        else:
            print(f"  [-] Registration failed for {username}")
            return None

    except Exception as e:
        print(f"  [!] Error: {e}")
        return None
    finally:
        await browser.close()


async def main():
    COUNT = int(input("How many accounts? ") or "3")
    results = []

    async with async_playwright() as p:
        for i in range(COUNT):
            email_addr = randid_email()
            username = f"{randid(6)}{randid(4)}"
            password = f"{randid(6)}{random.choice('!@#')}{randid(4)}"

            print(f"\n[{i+1}/{COUNT}] Registering {username} ({email_addr})")
            result = await register_account(p, email_addr, username, password)

            if result:
                results.append(result)
                OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(OUTPUT_FILE, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"  Saved to {OUTPUT_FILE}")

            if i < COUNT - 1:
                delay = random.uniform(15, 30)
                print(f"  Cooldown {delay:.0f}s...")
                await asyncio.sleep(delay)

    print(f"\nDone. {len(results)}/{COUNT} accounts registered.")
    print(f"Keys saved to: {OUTPUT_FILE}")

    for r in results:
        key_preview = r['api_key'][:20] + '...' if r['api_key'] else 'NONE'
        print(f"  {r['username']} -> {key_preview}")


if __name__ == "__main__":
    asyncio.run(main())