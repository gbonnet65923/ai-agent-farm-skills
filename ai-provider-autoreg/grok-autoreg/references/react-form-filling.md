# React Form Filling Pattern for Browser Automation

## Problem
React controlled inputs ignore `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set` — the form validation sees empty values and refuses to submit.

## Solution
Use `locator.fill()` + dispatch `input` event after each fill.

## Working Code Snippet
```python
# Fill name
name_input = page.locator("input[autocomplete='given-name']").first
await name_input.click()
await name_input.fill("Max")
await page.evaluate("""
    document.querySelector('input[autocomplete="given-name"]')
        ?.dispatchEvent(new Event('input', {bubbles: true}));
""")

# Fill surname
surname_input = page.locator("input[autocomplete='family-name']").first
await surname_input.click()
await surname_input.fill("Mustermann")
await page.evaluate("""
    document.querySelector('input[autocomplete="family-name"]')
        ?.dispatchEvent(new Event('input', {bubbles: true}));
""")

# Fill password (use fill() NOT JS value setter!)
pwd_input = page.locator("input[type='password']").first
await pwd_input.click()
await pwd_input.fill(password)
await page.evaluate("""
    document.querySelector('input[type="password"]')
        ?.dispatchEvent(new Event('input', {bubbles: true}));
""")

# Click submit — use Playwright locator, NOT JS querySelector with :has-text()
btn = page.locator("button:has-text('Завершить регистрацию')").first
await btn.click()
```

## Pitfalls
- **`:has-text()` in JS**: `document.querySelector('button:has-text("...")')` throws SyntaxError. `:has-text()` is a Playwright pseudo-selector, not valid CSS.
- **JS fallback**: Use `textContent.includes()` loop if JS click is needed
- **OneTrust buttons**: `button:has-text('Подтвердить')` matches cookie consent buttons. Check `class` attribute for "onetrust" and skip.