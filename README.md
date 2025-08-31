# OLX Car Cover Scraper

A Python scraper that fetches car-cover related listings from OLX India using the relevance API first (fast, structured), with Selenium fallbacks if needed. Saves results as JSON, CSV, and a human-readable report.

## Features
- API-first extraction via `relevance/v4/search` (fast and robust)
- Optional Selenium fallback for HTML parsing
- Car-cover filtering or full UI-parity mode (no filtering)
- Rich fields: price (numeric/formatted), location, locality, city, image, featured flag, posted time
- Client-side sorting: quality, date (published), price, with featured-first option
- Clean outputs in `olx_scraping_results/`

## Requirements
- Python 3.9+ (tested on 3.11)
- Google Chrome installed (for Selenium fallback)

Install packages:
```bash
pip install undetected-chromedriver selenium fake-useragent pandas beautifulsoup4 requests webdriver-manager
```

## Common Run Modes
- UI-parity (match OLX UI ordering/content better):
```bash
python "car-cover.py" --api-only --headless --query "car cover" --size 120 --location 1000001 --no-filter --sort date --featured-first --no-pause
```
- Car-cover-only (clean results, filtered):
```bash
python "car-cover.py" --api-only --headless --query "car cover" --size 100 --location 1000001 --sort quality --no-pause
```
- City-specific (replace with a city/location ID when known):
```bash
python "car-cover.py" --api-only --headless --query "car cover" --location 1000001 --size 120 --no-pause
```
Outputs are saved to `olx_scraping_results/` as:
- `olx_car_covers_enhanced_<timestamp>.json`
- `olx_car_covers_enhanced_<timestamp>.csv`
- `olx_car_covers_enhanced_<timestamp>_report.txt`

## Output Schema (JSON `listings[]`)
Each listing includes most of:
- `id` (string), `title`
- `price` (display), `price_numeric`, `price_formatted`
- `location` (broad), `locality` (UI-like), `city`
- `url`, `image_url`, `description`, `category`
- `featured` (bool), `posted_at` (str), `posted_at_ts` (epoch seconds)
- `scraped_at`, `source`, `quality_score`

## CLI Options
- `--headless` Run browser headless (Selenium only)
- `--no-pause` Do not wait for Enter at the end
- `--query <text>` Override API query (default: `car cover`)
- `--size <N>` API size (default: 80; capped to 120)
- `--location <ID>` OLX location ID (default: 1000001 = India)
- `--api-only` Use only API extraction and skip Selenium
- `--no-filter` Bypass car-cover filtering to mirror UI results (includes non-car ads like covered parking)
- `--sort {quality|date|price|relevance}` Sort output (default: `quality`)
- `--featured-first` Place featured/promoted items first (best-effort)

## Notes
- The UI can include non-car items (e.g., flats with "covered car parking"). Use `--no-filter` to mirror that.
- When using Selenium fallback, Chrome must be installed. The tool attempts `undetected-chromedriver` first, then `webdriver-manager` if available.

## Troubleshooting
- HTTP 403/Cloudflare: retry later, try non-headless mode, or use a residential/VPN network.
- Empty results: verify OLX is reachable in your region.
- Driver errors: update Chrome, `pip install webdriver-manager`.

## Legal
This project is for educational/research purposes. Respect OLX Terms of Service and robots.txt. Avoid excessive request rates and do not republish scraped data without permission.
