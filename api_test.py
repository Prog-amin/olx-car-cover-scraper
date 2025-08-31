import importlib.util
import os
import sys
import traceback

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_PATH = os.path.join(PROJECT_DIR, 'car-cover.py')

try:
    spec = importlib.util.spec_from_file_location("car_cover_module", MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore
except Exception as e:
    print(f"Failed to load module from {MODULE_PATH}: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    scraper = mod.ImprovedOLXScraper(headless=True)
    print("Running API-only fetch...")
    items = scraper.fetch_via_relevance_api(query="car cover", size=80, location=1000001)
    print(f"API returned {len(items)} items")
    if items:
        # Save quick results for inspection
        scraper.save_results(items, filename_prefix="olx_car_covers_api_only")
        # Print a brief preview
        for i, it in enumerate(items[:5], 1):
            print(f"{i}. {it.get('title')} | {it.get('price_formatted') or it.get('price')} | {it.get('location')}")
    else:
        print("No items from API. Consider changing location or headers.")
except Exception as e:
    print(f"Error during API test: {e}")
    traceback.print_exc()
    sys.exit(2)
