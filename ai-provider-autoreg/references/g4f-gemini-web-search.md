# g4f Gemini Web Search — `tools=[["google_search"]]`

## Discovery

g4f's `Provider.Gemini` (URL: `https://gemini.google.com`, uses COOKIES, not API key) supports Google Search through the `tools` parameter passed to `build_request`.

## How it works

1. `Gemini.create_async_generator` accepts `tools=kwargs.get("tools")` (line 663)
2. `Gemini.build_request` accepts `tools: list[list[str]]` and sets `request[9] = tools` (lines 988-1017)
3. The web protocol expects `[["google_search"]]` format

## Usage

```python
import g4f

response = g4f.ChatCompletion.create(
    model="gemini",
    provider=g4f.Provider.Gemini,
    cookies=cookies_dict,
    tools=[["google_search"]],  # enables Google Search in web interface
    messages=[{"role": "user", "content": "What's the current Bitcoin price?"}]
)
```

## Verified

- g4f version: 8.1.6
- Source: `g4f/Provider/needs_auth/Gemini.py`
- `build_request` parameter: `tools: list[list[str]] = None` → `request[9] = tools`
- No other g4f providers support this parameter (searched entire `g4f/Provider/` directory — 0 matches for `google_search`)

## Pitfalls

- The format `[["google_search"]]` is a best guess — the exact web protocol format is undocumented
- Gemini web interface may not always honor the tools parameter
- No error is thrown if the format is wrong — Gemini just ignores it silently
- Test with a query that requires real-time data to verify it's working

## Real-world usage: Calorie-Counter-AI bot (2026-08-16)

### Architecture

```
gemini_web.py (wrapper) → g4f.ChatCompletion.create(
    provider=g4f.Provider.Gemini,
    cookies=gemini_cookies.json,
    tools=[["google_search"]]
) → gemini.google.com
```

### System prompt pattern for structured search results

Instruct Gemini to return search results as structured JSON fields:

```json
{
  "prices": [{"product": "куриное филе", "price_uah": 189, "store": "АТБ"}],
  "promotions": [{"store": "Сільпо", "title": "Скидка 30%", "valid_until": "2026-08-20"}]
}
```

Prompt snippet:
```
ИНСТРУМЕНТЫ: У тебя есть доступ к Google Search (google_search). Используй его чтобы:
1. Найти актуальные цены в гривнах на КАЖДЫЙ продукт из shopping_list в 2-3 магазинах
2. Найти текущие АКЦИИ и скидки на продукты
```

### Multi-store comparison pattern

Request multiple store prices per product. Post-process by grouping and sorting:

```python
from collections import defaultdict
by_product = defaultdict(list)
for p in prices:
    by_product[p["product"]].append((p["price_uah"], p["store"]))
# Display best price first, show alternatives
```

### Fallback chain

1. Gemini Google Search → `prices` field
2. If empty → DuckDuckGo scraping (`price_search.py`)
3. If both fail → no price block shown

### Verified behavior

- Gemini with `tools=[["google_search"]]` returns real-time search results through g4f cookies
- The search tool is invoked automatically by Gemini when the prompt asks for current prices
- DuckDuckGo fallback catches cases where Gemini doesn't search (rate limits, silent failures)

## Related

- `gemini_web.py` in Calorie-Counter-AI project: wraps g4f Gemini with SDK-like interface
- Cookie file: `gemini_cookies.json` (extracted from browser)