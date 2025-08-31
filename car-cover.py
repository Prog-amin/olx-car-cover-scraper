import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
import json
import csv
import time
import random
import re
import os
from fake_useragent import UserAgent
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import argparse

# Try to import webdriver manager (fallback option)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False
    print("⚠️ webdriver-manager not available. Install with: pip install webdriver-manager")

class ImprovedOLXScraper:
    def __init__(self, headless=False):
        self.base_url = "https://www.olx.in"
        # Try alternative URLs if main one fails
        self.search_urls = [
            "https://www.olx.in/items/q-car-cover",
            "https://www.olx.in/cars_c84/q-car-cover",
            "https://www.olx.in/all-india/q-car-cover",
        ]
        self.current_url_index = 0
        self.headless = headless
        self.driver = None
        self.wait = None
        self.ua = UserAgent()
        self.session = requests.Session()
        # API parameters (overridable via CLI)
        self.api_query = "car cover"
        self.api_size = 80
        self.api_location = 1000001
        self.api_only = False
        # Output behavior controls
        self.no_filter = False  # when True, bypass car-cover filtering to mirror UI results
        self.sort_by = 'quality'  # one of: quality, date, price, relevance (relevance falls back to quality)
        self.featured_first = False
        
    def setup_driver(self):
        """Setup Chrome driver with compatible configurations"""
        try:
            options = uc.ChromeOptions()
            
            # Basic essential options only
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-extensions')
            options.add_argument('--no-first-run')
            options.add_argument('--ignore-certificate-errors')
            
            # Random realistic window size
            sizes = ['1366,768', '1920,1080', '1440,900', '1280,720']
            selected_size = random.choice(sizes)
            options.add_argument(f'--window-size={selected_size}')
            
            if self.headless:
                options.add_argument('--headless')
                
            # Try to set user agent
            try:
                user_agent = self.ua.random
                options.add_argument(f'--user-agent={user_agent}')
            except:
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                options.add_argument(f'--user-agent={user_agent}')
            
            # Try experimental options with error handling
            try:
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
            except Exception as exp_error:
                print(f"⚠️ Experimental options skipped: {exp_error}")
            
            # Create driver with error handling
            try:
                self.driver = uc.Chrome(options=options, version_main=None)
                print("✅ Driver created with undetected-chromedriver")
            except Exception as uc_error:
                print(f"⚠️ Undetected ChromeDriver failed: {uc_error}")
                print("🔄 Trying regular ChromeDriver...")
                
                # Fallback to regular ChromeDriver only if webdriver manager is available
                if not WEBDRIVER_MANAGER_AVAILABLE:
                    print("❌ webdriver-manager not available for fallback")
                    return False
                
                # Simple options for regular driver
                simple_options = webdriver.ChromeOptions()
                simple_options.add_argument('--no-sandbox')
                simple_options.add_argument('--disable-dev-shm-usage')
                simple_options.add_argument(f'--window-size={selected_size}')
                
                if self.headless:
                    simple_options.add_argument('--headless')
                
                try:
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=simple_options)
                    print("✅ Regular ChromeDriver setup successful")
                except Exception as regular_error:
                    print(f"❌ Regular ChromeDriver also failed: {regular_error}")
                    return False
            
            # Execute anti-detection script if possible
            try:
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            except:
                pass
            
            self.driver.implicitly_wait(10)
            self.wait = WebDriverWait(self.driver, 20)
            
            print("✅ Chrome driver setup successful")
            print(f"   📐 Window Size: {selected_size}")
            
            return True
            
        except Exception as e:
            print(f"❌ Driver setup failed: {e}")
            print("💡 Suggestions:")
            print("   • Install/update Chrome browser")
            print("   • Install webdriver-manager: pip install webdriver-manager")
            print("   • Check if Chrome is in PATH")
            return False
    
    def try_requests_fallback(self, url):
        """Try to get data using requests as fallback"""
        try:
            print("🔄 Trying requests fallback...")
            
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            if response.status_code == 200:
                print(f"✅ Requests successful: {len(response.text)} chars")
                return response.text
            else:
                print(f"⚠️ Requests returned status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Requests fallback failed: {e}")
            return None
    
    def advanced_protection_bypass(self):
        """Advanced protection bypass with multiple strategies"""
        try:
            print("🛡️ Attempting advanced protection bypass...")
            
            # Wait for initial page load
            time.sleep(random.uniform(5, 8))
            
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            
            # Check for various protection systems
            protection_indicators = [
                'cloudflare', 'checking your browser', 'ddos-guard', 
                'captcha', 'bot protection', 'security check',
                'please wait', 'loading', 'verifying'
            ]
            
            is_protected = any(indicator in page_source for indicator in protection_indicators)
            
            if is_protected:
                print("🔄 Protection detected, trying bypass strategies...")
                
                # Strategy 1: Wait and let it auto-resolve
                print("   ⏳ Waiting for auto-bypass (30s)...")
                time.sleep(30)
                
                # Strategy 2: Try human-like interactions
                try:
                    print("   🖱️ Simulating human interactions...")
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    
                    # Move mouse and click randomly
                    ActionChains(self.driver).move_to_element(body).perform()
                    time.sleep(2)
                    ActionChains(self.driver).click().perform()
                    time.sleep(3)
                    
                    # Random key presses
                    ActionChains(self.driver).send_keys(Keys.TAB).perform()
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"   ⚠️ Interaction simulation failed: {e}")
                
                # Strategy 3: Refresh and retry
                if 'cloudflare' in self.driver.page_source.lower():
                    print("   🔄 Refreshing page...")
                    self.driver.refresh()
                    time.sleep(15)
                
                # Check if bypass was successful
                new_page_source = self.driver.page_source.lower()
                new_url = self.driver.current_url
                
                still_protected = any(indicator in new_page_source for indicator in protection_indicators)
                
                if not still_protected and 'olx.in' in new_url:
                    print("   ✅ Protection bypassed successfully!")
                    return True
                else:
                    print("   ⚠️ Still protected, but continuing with current page...")
                    return True
            else:
                print("✅ No protection detected")
                return True
                
        except Exception as e:
            print(f"❌ Protection bypass error: {e}")
            return False
    
    def smart_wait_for_content(self):
        """Smart waiting for content to load"""
        try:
            print("⏳ Waiting for content to load...")
            
            # Wait for basic page structure
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                print("   ✅ Basic page structure loaded")
            except TimeoutException:
                print("   ⚠️ Basic page structure timeout")
                return False
            
            # Wait for potential listing containers
            potential_selectors = [
                '[data-aut-id="itemBox"]',
                '.item', '.listing', '.ad-item',
                '[class*="item"]', '[class*="listing"]',
                'article', '.card'
            ]
            
            content_found = False
            for selector in potential_selectors:
                try:
                    elements = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    if len(elements) > 1:
                        print(f"   ✅ Found content with selector: {selector}")
                        content_found = True
                        break
                except:
                    continue
            
            if not content_found:
                print("   ⚠️ No specific content containers found, but continuing...")
            
            # Additional wait for dynamic content
            time.sleep(5)
            return True
            
        except Exception as e:
            print(f"⚠️ Smart content wait error: {e}")
            return False
    
    def enhanced_human_simulation(self):
        """Enhanced human behavior simulation"""
        try:
            print("🤖 Simulating enhanced human behavior...")
            
            # Get page dimensions
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            # Gradual scroll with realistic patterns
            scroll_positions = []
            current_pos = 0
            
            while current_pos < total_height * 0.9:  # Don't scroll to very bottom
                # Variable scroll amounts (realistic reading behavior)
                if random.random() < 0.7:  # 70% small scrolls
                    scroll_amount = random.randint(100, 300)
                else:  # 30% larger scrolls
                    scroll_amount = random.randint(400, 600)
                
                current_pos += scroll_amount
                scroll_positions.append(min(current_pos, total_height))
            
            # Execute scrolling
            for pos in scroll_positions:
                self.driver.execute_script(f"window.scrollTo(0, {pos});")
                
                # Realistic pause times
                if random.random() < 0.3:  # 30% chance of longer pause (reading)
                    pause_time = random.uniform(2, 5)
                else:
                    pause_time = random.uniform(0.5, 2)
                
                time.sleep(pause_time)
                
                # Occasional mouse movements
                if random.random() < 0.2:  # 20% chance
                    try:
                        body = self.driver.find_element(By.TAG_NAME, "body")
                        ActionChains(self.driver).move_to_element(body).perform()
                    except:
                        pass
            
            # Scroll back up (realistic behavior)
            middle_pos = total_height // 2
            self.driver.execute_script(f"window.scrollTo(0, {middle_pos});")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(3)
            
            print("   ✅ Enhanced human simulation completed")
            return True
            
        except Exception as e:
            print(f"⚠️ Human simulation error: {e}")
            return False
    
    def comprehensive_extraction(self):
        """Comprehensive data extraction with multiple strategies"""
        print("🔍 Starting comprehensive extraction...")
        
        all_listings = []
        
        # Strategy 0: Prefer official relevance API (fast, structured)
        api_listings = self.fetch_via_relevance_api(query=self.api_query, size=self.api_size, location=self.api_location)
        if api_listings:
            all_listings.extend(api_listings)
            print(f"   ✅ API extraction: {len(api_listings)} items")
        
        # Strategy 1: Modern OLX selectors (fallback)
        if len(all_listings) < 10:
            modern_listings = self.extract_modern_listings()
            if modern_listings:
                all_listings.extend(modern_listings)
                print(f"   ✅ Modern extraction: {len(modern_listings)} items")
        
        # Strategy 2: Generic selectors (fallback)
        if len(all_listings) < 10:
            generic_listings = self.extract_generic_listings()
            if generic_listings:
                all_listings.extend(generic_listings)
                print(f"   ✅ Generic extraction: {len(generic_listings)} items")
        
        # Strategy 3: BeautifulSoup parsing (fallback)
        if len(all_listings) < 10:
            bs_listings = self.extract_with_beautifulsoup()
            if bs_listings:
                all_listings.extend(bs_listings)
                print(f"   ✅ BeautifulSoup extraction: {len(bs_listings)} items")
        
        # Strategy 4: Text pattern matching (last resort)
        if len(all_listings) < 5:
            pattern_listings = self.extract_with_patterns()
            if pattern_listings:
                all_listings.extend(pattern_listings)
                print(f"   ✅ Pattern extraction: {len(pattern_listings)} items")
        
        # Normalize price fields and filter to true car body covers only
        normalized = []
        for item in all_listings:
            # Ensure price fields
            price_text = item.get('price') or ''
            price_num, price_fmt = self.parse_price_fields(price_text)
            if price_num and not item.get('price_numeric'):
                item['price_numeric'] = price_num
            if price_fmt and not item.get('price_formatted'):
                item['price_formatted'] = price_fmt
            
            if self.filter_to_car_cover(item):
                normalized.append(item)
        
        # Remove duplicates
        unique_listings = self.remove_duplicates(normalized)
        
        if unique_listings:
            print(f"✅ Total unique listings extracted: {len(unique_listings)}")
        else:
            print("⚠️ No listings extracted - creating diagnostic info...")
            unique_listings = self.create_diagnostic_info()
        
        return unique_listings
    
    def extract_modern_listings(self):
        """Extract using modern OLX selectors"""
        listings = []
        
        modern_selectors = [
            '[data-aut-id="itemBox"]',
            '.EIR5N',
            '._2vNpn',
            '[data-testid="listing-card"]',
            '.listing-card',
            '[class*="ItemCard"]'
        ]
        
        for selector in modern_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if len(elements) > 2:
                    for i, element in enumerate(elements[:20]):  # Limit to prevent timeouts
                        listing = self.parse_listing_element(element, f"modern_{i+1}")
                        if listing and listing.get('title'):
                            listings.append(listing)
                    break
            except Exception as e:
                continue
        
        return listings
    
    def extract_generic_listings(self):
        """Extract using generic selectors"""
        listings = []
        
        generic_selectors = [
            '.item', '.listing', '.ad-item', '.product-item',
            'article', '.card', '[class*="item"]',
            'div[class*="listing"]', 'li[class*="item"]'
        ]
        
        for selector in generic_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if len(elements) > 3:
                    for i, element in enumerate(elements[:15]):
                        listing = self.parse_listing_element(element, f"generic_{i+1}")
                        if listing and listing.get('title') and len(listing['title']) > 10:
                            listings.append(listing)
                    break
            except Exception as e:
                continue
        
        return listings
    
    def parse_listing_element(self, element, item_id):
        """Parse individual listing element"""
        try:
            listing = {
                'id': item_id,
                'title': '',
                'price': '',
                'location': '',
                'url': '',
                'image_url': '',
                'date_posted': '',
                'description': '',
                'scraped_at': time.strftime("%Y-%m-%d %H:%M:%S"),
                'source': 'selenium'
            }
            
            # Extract title
            title_selectors = [
                '[data-aut-id="itemTitle"]', 'h1', 'h2', 'h3', 'h4',
                '.title', '[class*="title"]', '[class*="Title"]',
                'a[title]', 'span[title]'
            ]
            
            for ts in title_selectors:
                try:
                    title_elem = element.find_element(By.CSS_SELECTOR, ts)
                    title_text = (title_elem.get_attribute('title') or 
                                 title_elem.text or 
                                 title_elem.get_attribute('alt')).strip()
                    if title_text and len(title_text) > 8:
                        listing['title'] = title_text[:200]  # Limit length
                        break
                except:
                    continue
            
            # Extract price
            price_selectors = [
                '[data-aut-id="itemPrice"]', '.price', '[class*="price"]',
                '[class*="Price"]', '.amount', '.cost'
            ]
            
            for ps in price_selectors:
                try:
                    price_elem = element.find_element(By.CSS_SELECTOR, ps)
                    price_text = price_elem.text.strip()
                    if price_text and ('₹' in price_text or 'Rs' in price_text or 
                                     price_text.replace(',', '').replace('.', '').isdigit()):
                        price_num, price_fmt = self.parse_price_fields(price_text)
                        listing['price'] = price_text[:50]
                        if price_num:
                            listing['price_numeric'] = price_num
                        if price_fmt:
                            listing['price_formatted'] = price_fmt
                        break
                except:
                    continue
            
            # Extract location
            location_selectors = [
                '[data-aut-id="itemLocation"]', '.location', '[class*="location"]',
                '[class*="Location"]', '.place', '.city'
            ]
            
            for ls in location_selectors:
                try:
                    location_elem = element.find_element(By.CSS_SELECTOR, ls)
                    location_text = location_elem.text.strip()
                    if location_text and len(location_text) > 2 and len(location_text) < 100:
                        listing['location'] = location_text
                        break
                except:
                    continue
            
            # Extract URL
            try:
                link_elem = element.find_element(By.CSS_SELECTOR, 'a[href]')
                href = link_elem.get_attribute('href')
                if href:
                    if href.startswith('http'):
                        listing['url'] = href
                    elif href.startswith('/'):
                        listing['url'] = urljoin(self.base_url, href)
            except:
                pass
            
            # Extract image
            try:
                img_elem = element.find_element(By.CSS_SELECTOR, 'img')
                src = (img_elem.get_attribute('src') or 
                      img_elem.get_attribute('data-src') or
                      img_elem.get_attribute('data-lazy-src'))
                if src and src.startswith('http'):
                    listing['image_url'] = src
            except:
                pass
            
            # Extract description from alt text or additional text
            try:
                all_text = element.text.strip()
                if all_text and len(all_text) > len(listing.get('title', '')):
                    # Take first 300 chars as description
                    listing['description'] = all_text[:300]
            except:
                pass
            
            # Only return listing if it has meaningful content
            if listing['title'] or (listing['price'] and listing['description']):
                return listing if self.filter_to_car_cover(listing) else None
            
            return None
            
        except Exception as e:
            return None
    
    def extract_with_beautifulsoup(self):
        """Enhanced BeautifulSoup extraction"""
        try:
            print("   🔄 BeautifulSoup parsing...")
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            listings = []
            
            # Save page source for debugging
            with open('debug_page_source.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            
            # Look for elements containing car cover related text
            car_cover_patterns = [
                re.compile(r'car.*cover', re.I),
                re.compile(r'cover.*car', re.I),
                re.compile(r'vehicle.*cover', re.I)
            ]
            
            # Find elements with car cover content
            for pattern in car_cover_patterns:
                elements = soup.find_all(text=pattern)
                for text_node in elements[:10]:  # Limit results
                    parent = text_node.parent
                    # Try to find the listing container
                    for _ in range(5):  # Go up max 5 levels
                        if parent and parent.name in ['div', 'article', 'li', 'section']:
                            listing_text = parent.get_text().strip()
                            if len(listing_text) > 50:  # Meaningful content
                                listing = self.parse_text_content(listing_text, len(listings) + 1)
                                if listing:
                                    listings.append(listing)
                                break
                        parent = parent.parent if parent else None
                        if not parent:
                            break
            
            return listings[:10]  # Return max 10 listings
            
        except Exception as e:
            print(f"   ❌ BeautifulSoup error: {e}")
            return []
    
    def extract_with_patterns(self):
        """Extract using regex patterns"""
        try:
            print("   🔄 Pattern matching...")
            page_source = self.driver.page_source
            listings = []
            
            # Enhanced patterns for car covers with price
            patterns = [
                r'(?i)(car\s+cover[^<>{}"]{0,300}?₹[\d,\s]+[^<>{}]{0,100})',
                r'(?i)(₹[\d,\s]+[^<>{}]{0,100}?car\s+cover[^<>{}]{0,200})',
                r'(?i)(cover\s+for\s+car[^<>{}]{0,200}?₹[\d,\s]+)',
                r'(?i)(vehicle\s+cover[^<>{}]{0,200}?₹[\d,\s]+)'
            ]
            
            for i, pattern in enumerate(patterns):
                matches = re.finditer(pattern, page_source)
                for j, match in enumerate(list(matches)[:5]):  # Max 5 per pattern
                    matched_text = match.group(1)
                    cleaned_text = re.sub(r'<[^>]+>', '', matched_text)
                    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
                    
                    if len(cleaned_text) > 30:
                        listing = self.parse_text_content(cleaned_text, f"pattern_{i}_{j}")
                        if listing:
                            listings.append(listing)
            
            return listings
            
        except Exception as e:
            print(f"   ❌ Pattern extraction error: {e}")
            return []
    
    def parse_text_content(self, text_content, item_id):
        """Parse text content to extract listing info"""
        try:
            # Extract price (strict pattern to avoid trailing digits like "₹ 7,5001")
            price_pattern = r'(₹\s*\d{1,3}(?:,\d{2,3})*|Rs\.?\s*\d{1,3}(?:,\d{2,3})*)\b'
            price_match = re.search(price_pattern, text_content)
            price = price_match.group().strip() if price_match else ''
            
            # Extract title (try to find the main product name)
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            title = ''
            for line in lines:
                if len(line) > 10 and len(line) < 150:
                    # Likely a title
                    title = line
                    break
            
            if not title and lines:
                title = lines[0][:100]  # Fallback to first line
            
            # Create listing
            listing = {
                'id': f'text_{item_id}',
                'title': title,
                'price': price,
                'location': 'Location in description',
                'url': self.driver.current_url,
                'description': text_content[:400],
                'scraped_at': time.strftime("%Y-%m-%d %H:%M:%S"),
                'source': 'text_parsing'
            }
            # Add parsed numeric price
            if price:
                num, fmt = self.parse_price_fields(price)
                if num:
                    listing['price_numeric'] = num
                if fmt:
                    listing['price_formatted'] = fmt
            
            return listing if (title or price) and self.filter_to_car_cover(listing) else None
            
        except Exception as e:
            return None

    def parse_price_fields(self, price_text):
        """Return (numeric_value, formatted_value) from a price string"""
        if not price_text:
            return (None, None)
        try:
            digits = re.sub(r'[^0-9]', '', price_text)
            if not digits:
                return (None, None)
            value = int(digits)
            return (value, f"₹{value:,}")
        except Exception:
            return (None, None)

    def filter_to_car_cover(self, listing):
        """Filter only true car body cover listings; exclude property/parking results."""
        text = ' '.join([
            str(listing.get('title') or ''),
            str(listing.get('description') or ''),
            str(listing.get('category') or '')
        ]).lower()

        # Positive phrases that indicate actual car body covers (avoid 'covered')
        include_patterns = [
            r'\bcar\s*cover\b',
            r'\bbody\s*cover\b',
            r'\bcar\s*body\s*cover\b',
            r'\bwaterproof\s*car\s*cover\b',
            r'\bcar\s*sheet\s*cover\b',
        ]
        if not any(re.search(p, text, flags=re.I) for p in include_patterns):
            return False

        # Hard excludes to remove real-estate and irrelevant matches
        exclude_patterns = [
            r'\bbhk\b', r'\bsq\.?ft\b', r'\bapartment\b', r'\bflat\b', r'\bhouse\b',
            r'\boffice\b', r'\brent\b', r'\bsale\b', r'\bparking\b', r'\bcovered\b',
            r'\bgaj\b', r'\bshop\b', r'\bcommercial\b', r'\bworkspace\b', r'\bplot\b',
        ]
        if any(re.search(p, text, flags=re.I) for p in exclude_patterns):
            return False

        return True

    def slugify_title(self, title: str) -> str:
        """Create a URL-friendly slug from a title for building fallback OLX item URLs."""
        try:
            t = (title or '').lower()
            # Replace non-alphanumeric with hyphens, collapse repeats, trim
            t = re.sub(r"[^a-z0-9]+", "-", t)
            t = re.sub(r"-+", "-", t).strip('-')
            return t or 'car-cover'
        except Exception:
            return 'car-cover'

    def normalize_api_listing(self, item):
        """Map OLX API item to our listing schema with robust fallbacks"""
        try:
            title = item.get('title') or item.get('subject') or ''
            # Price
            price_obj = item.get('price') or {}
            value_obj = price_obj.get('value') or {}
            price_display = value_obj.get('display') or price_obj.get('display') or ''
            price_raw = value_obj.get('raw') or price_obj.get('raw')
            price_num, price_fmt = (None, None)
            if price_raw is not None:
                try:
                    price_num = int(price_raw)
                    price_fmt = f"₹{price_num:,}"
                except Exception:
                    pass
            if price_num is None:
                price_num, price_fmt = self.parse_price_fields(price_display)

            # Location
            loc = item.get('locations_resolved') or item.get('locations') or {}
            location = (
                loc.get('ADMIN_LEVEL_3_name') or loc.get('ADMIN_LEVEL_2_name') or
                loc.get('CITY_name') or loc.get('COUNTRY_name') or ''
            )
            # Try to derive a more UI-like locality string (best-effort)
            locality_fields = [
                'SUBLOCALITY_level_1_name', 'SUBLOCALITY_level_2_name',
                'NEIGHBOURHOOD_name', 'NEIGHBORHOOD_name',
                'ADMIN_LEVEL_3_name', 'ADMIN_LEVEL_2_name', 'CITY_name'
            ]
            locality_parts = []
            for k in locality_fields:
                v = loc.get(k)
                if v and v not in locality_parts:
                    locality_parts.append(v)
            locality = ", ".join(locality_parts[:3]) if locality_parts else ''
            city = loc.get('CITY_name') or ''

            # ID (string) used for URL fallback
            id_str = str(item.get('id') or item.get('ad_id') or '')

            # URL
            candidate_urls = [item.get('url'), item.get('ad_link'), item.get('web_url'), item.get('share_link')]
            url = next((u for u in candidate_urls if u), '')
            if url and url.startswith('/'):
                url = urljoin(self.base_url, url)
            # Fallback: construct from slug and id when URL missing
            if not url and id_str:
                slug = self.slugify_title(title)
                url = f"{self.base_url}/item/{slug}-iid-{id_str}"

            # Image
            image_url = ''
            images = item.get('images') or []
            if isinstance(images, list) and images:
                first_img = images[0]
                image_url = (
                    first_img.get('url') or first_img.get('big') or first_img.get('medium') or ''
                )

            # Featured / promoted flag (best-effort across possible keys)
            featured = bool(
                item.get('is_featured') or item.get('is_promoted') or item.get('promoted') or item.get('premium') or item.get('is_premium')
            )

            # Posted time (epoch seconds if available)
            posted_at_ts = None
            for ts_key in ('created_time', 'created_at', 'list_time', 'last_renewed_time'):
                if ts_key in item and item.get(ts_key) is not None:
                    try:
                        ts_val = int(item.get(ts_key))
                        # Convert ms to s if needed
                        if ts_val > 10**12:
                            ts_val = ts_val // 1000
                        posted_at_ts = ts_val
                        break
                    except Exception:
                        continue
            posted_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(posted_at_ts)) if posted_at_ts else ''

            listing = {
                'id': id_str,
                'title': title,
                'price': price_display or (price_fmt or ''),
                'price_numeric': price_num,
                'price_formatted': price_fmt,
                'location': location,
                'locality': locality,
                'city': city,
                'url': url,
                'image_url': image_url,
                'description': (item.get('description') or '')[:400],
                'category': (item.get('category') or {}).get('name') if isinstance(item.get('category'), dict) else (item.get('category_name') or ''),
                'featured': featured,
                'posted_at': posted_at,
                'posted_at_ts': posted_at_ts,
                'scraped_at': time.strftime("%Y-%m-%d %H:%M:%S"),
                'source': 'olx_api'
            }

            if self.no_filter:
                return listing
            else:
                return listing if self.filter_to_car_cover(listing) else None
        except Exception:
            return None

    def fetch_via_relevance_api(self, query="car cover", size=80, location=1000001):
        """Use OLX relevance v4 search API to fetch listings (server-rendered also uses this)."""
        try:
            params = {
                'query': query,
                'facet_limit': 1000,
                'location': location,
                'location_facet_limit': 40,
                'platform': 'web-desktop',
                'pttenabled': 'true',
                'relaxedfilters': 'true',
                'size': size,
                'spellcheck': 'true',
            }
            headers = {
                'User-Agent': self.ua.random if hasattr(self, 'ua') else 'Mozilla/5.0',
                'Accept': 'application/json, text/plain, */*',
                'Referer': self.base_url,
            }
            url = urljoin(self.base_url, '/api/relevance/v4/search')
            resp = self.session.get(url, params=params, headers=headers, timeout=30)
            if resp.status_code != 200:
                print(f"   ⚠️ API HTTP {resp.status_code}")
                return []
            data = resp.json()
            items = data.get('data') or data.get('ads') or []
            results = []
            for it in items:
                norm = self.normalize_api_listing(it)
                if norm:
                    results.append(norm)
            return results
        except Exception as e:
            print(f"   ❌ API extraction error: {e}")
            return []
    
    def remove_duplicates(self, listings):
        """Remove duplicate listings based on title similarity"""
        if not listings:
            return []
        
        unique_listings = []
        seen_titles = set()
        
        for listing in listings:
            title = listing.get('title', '').lower().strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_listings.append(listing)
            elif not title and listing.get('price'):  # Keep listings with price but no title
                unique_listings.append(listing)
        
        return unique_listings
    
    def create_diagnostic_info(self):
        """Create diagnostic information when no listings found"""
        try:
            page_source = self.driver.page_source
            current_url = self.driver.current_url
            
            # Analyze page content
            car_mentions = len(re.findall(r'(?i)car', page_source))
            cover_mentions = len(re.findall(r'(?i)cover', page_source))
            price_mentions = len(re.findall(r'₹[\d,]+', page_source))
            
            diagnostic = {
                'id': 'diagnostic_info',
                'title': 'OLX Scraping Diagnostic Information',
                'price': f'{price_mentions} price elements found',
                'location': 'Diagnostic',
                'url': current_url,
                'description': f"""
Diagnostic Results:
- Current URL: {current_url}
- Page length: {len(page_source)} characters
- 'Car' mentions: {car_mentions}
- 'Cover' mentions: {cover_mentions}
- Price mentions: {price_mentions}
- Page title: {self.driver.title}
""".strip(),
                'scraped_at': time.strftime("%Y-%m-%d %H:%M:%S"),
                'source': 'diagnostic'
            }
            
            return [diagnostic]
            
        except Exception as e:
            return [{
                'id': 'error_info',
                'title': 'Scraping Error Occurred',
                'description': f'Error during diagnostic: {str(e)}',
                'scraped_at': time.strftime("%Y-%m-%d %H:%M:%S"),
                'source': 'error'
            }]
    
    def save_results(self, listings, filename_prefix="olx_car_covers_enhanced"):
        """Enhanced result saving with better formatting"""
        if not listings:
            print("❌ No listings to save")
            return
        
        timestamp = int(time.time())
        
        # Create results directory
        results_dir = "olx_scraping_results"
        os.makedirs(results_dir, exist_ok=True)
        
        # Save as JSON
        json_filename = os.path.join(results_dir, f"{filename_prefix}_{timestamp}.json")
        try:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'scrape_metadata': {
                        'search_urls': self.search_urls,
                        'successful_url': self.search_urls[self.current_url_index] if self.current_url_index < len(self.search_urls) else 'unknown',
                        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'total_listings': len(listings),
                        'search_terms': ['car cover', 'vehicle cover'],
                        'scraper_version': '2.0_enhanced'
                    },
                    'listings': listings
                }, f, indent=2, ensure_ascii=False)
            print(f"💾 Enhanced JSON saved: {json_filename}")
        except Exception as e:
            print(f"Error saving JSON: {e}")
        
        # Save as CSV
        csv_filename = os.path.join(results_dir, f"{filename_prefix}_{timestamp}.csv")
        try:
            df = pd.DataFrame(listings)
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"💾 Enhanced CSV saved: {csv_filename}")
        except Exception as e:
            print(f"Error saving CSV: {e}")
        
        # Save formatted text report
        txt_filename = os.path.join(results_dir, f"{filename_prefix}_{timestamp}_report.txt")
        try:
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("OLX CAR COVER SCRAPING REPORT\n")
                f.write("=" * 80 + "\n\n")
                
                f.write(f"Search performed on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"URLs attempted: {', '.join(self.search_urls)}\n")
                f.write(f"Total listings found: {len(listings)}\n")
                f.write(f"Scraper version: Enhanced v2.0\n\n")
                
                f.write("LISTINGS SUMMARY:\n")
                f.write("-" * 50 + "\n")
                
                for i, listing in enumerate(listings, 1):
                    f.write(f"\n[LISTING {i}]\n")
                    f.write(f"ID: {listing.get('id', 'N/A')}\n")
                    f.write(f"Title: {listing.get('title', 'No title')}\n")
                    f.write(f"Price: {listing.get('price', 'No price')}\n")
                    f.write(f"Location: {listing.get('location', 'No location')}\n")
                    if listing.get('locality'):
                        f.write(f"Locality: {listing.get('locality')}\n")
                    f.write(f"URL: {listing.get('url', 'No URL')}\n")
                    if listing.get('image_url'):
                        f.write(f"Image: {listing['image_url']}\n")
                    if listing.get('featured') is not None:
                        f.write(f"Featured: {'Yes' if listing.get('featured') else 'No'}\n")
                    if listing.get('posted_at'):
                        f.write(f"Posted: {listing.get('posted_at')}\n")
                    if listing.get('description'):
                        f.write(f"Description: {listing['description'][:200]}...\n")
                    f.write(f"Source: {listing.get('source', 'unknown')}\n")
                    f.write(f"Scraped: {listing.get('scraped_at', 'unknown')}\n")
                    f.write("-" * 40 + "\n")
                
                f.write("\n" + "=" * 80 + "\n")
                f.write("END OF REPORT\n")
                f.write("=" * 80 + "\n")
            
            print(f"💾 Enhanced report saved: {txt_filename}")
        except Exception as e:
            print(f"Error saving report: {e}")
    
    def run_enhanced_scraper(self):
        """Main enhanced scraper execution"""
        print("🚀 Enhanced OLX Car Cover Scraper v2.0")
        print("=" * 60)
        
        # API-first attempt (can skip Selenium entirely if --api-only)
        try:
            print("🔎 Trying API-first extraction...")
            api_listings = self.fetch_via_relevance_api(query=self.api_query, size=self.api_size, location=self.api_location)
            if api_listings:
                print(f"   ✅ API-first extracted {len(api_listings)} items")
                unique_listings = self.remove_duplicates(api_listings)
                enhanced_listings = self.enhance_listings(unique_listings)
                self.save_results(enhanced_listings)
                if self.api_only or len(unique_listings) >= 10:
                    print("   🛑 Skipping Selenium due to API success (api-only or sufficient results)")
                    return enhanced_listings
        except Exception as e:
            print(f"   ⚠️ API-first step failed: {e}")
        
        if not self.setup_driver():
            print("❌ Failed to setup driver")
            return []
        
        listings = []
        
        # Try multiple URLs
        for i, search_url in enumerate(self.search_urls):
            print(f"\n🌐 Attempt {i+1}/{len(self.search_urls)}")
            print(f"   URL: {search_url}")
            
            try:
                self.current_url_index = i
                self.driver.get(search_url)
                
                # Advanced protection bypass
                if not self.advanced_protection_bypass():
                    print(f"   ❌ Protection bypass failed for URL {i+1}")
                    continue
                
                # Smart content waiting
                if not self.smart_wait_for_content():
                    print(f"   ⚠️ Content loading issues for URL {i+1}")
                    # Continue anyway, might still get some data
                
                # Enhanced human simulation
                self.enhanced_human_simulation()
                
                # Comprehensive extraction
                url_listings = self.comprehensive_extraction()
                
                if url_listings and len(url_listings) > 0:
                    listings.extend(url_listings)
                    print(f"   ✅ Successfully extracted {len(url_listings)} listings from URL {i+1}")
                    
                    # If we got good results, we can stop trying other URLs
                    if len([l for l in url_listings if l.get('title') and l.get('price')]) >= 3:
                        print("   🎯 Good results obtained, stopping URL attempts")
                        break
                else:
                    print(f"   ⚠️ No listings from URL {i+1}")
                
                # Small delay between attempts
                if i < len(self.search_urls) - 1:
                    print("   ⏳ Waiting before next attempt...")
                    time.sleep(5)
                    
            except Exception as e:
                print(f"   ❌ Error with URL {i+1}: {e}")
                continue
        
        # Post-process results
        if listings:
            unique_listings = self.remove_duplicates(listings)
            print(f"\n✅ Final Results: {len(unique_listings)} unique listings")
            
            # Try to enhance listings with additional details if needed
            enhanced_listings = self.enhance_listings(unique_listings)
            
            self.save_results(enhanced_listings)
            return enhanced_listings
        else:
            print("\n⚠️ No listings extracted from any URL")
            
            # Try requests fallback as last resort
            for url in self.search_urls:
                html_content = self.try_requests_fallback(url)
                if html_content:
                    fallback_listings = self.parse_html_content(html_content, url)
                    if fallback_listings:
                        print(f"✅ Fallback extraction successful: {len(fallback_listings)} items")
                        self.save_results(fallback_listings)
                        return fallback_listings
            
            # Create diagnostic info as absolute fallback
            diagnostic_listings = self.create_diagnostic_info()
            self.save_results(diagnostic_listings)
            return diagnostic_listings
        
        # Cleanup
        if self.driver:
            try:
                self.driver.quit()
                print("\n🔒 Browser closed successfully")
            except Exception as e:
                print(f"\n⚠️ Browser cleanup error: {e}")
        
            finally:
                if self.driver:
                    try:
                        self.driver.quit()
                        print("\n🔒 Browser closed in finally block")
                    except Exception as e:
                        print(f"\n⚠️ Final cleanup error: {e}")
    
    def enhance_listings(self, listings):
        """Enhance listings with additional processing"""
        enhanced = []
        
        for listing in listings:
            # Clean and enhance title
            if listing.get('title'):
                title = listing['title'].strip()
                # Remove extra whitespace and normalize
                title = re.sub(r'\s+', ' ', title)
                listing['title'] = title
            
            # Standardize price format
            if listing.get('price'):
                price = listing['price']
                # Extract numeric value if possible
                price_match = re.search(r'[\d,]+', price.replace(' ', ''))
                if price_match:
                    numeric_price = price_match.group().replace(',', '')
                    if numeric_price.isdigit():
                        listing['price_numeric'] = int(numeric_price)
                        listing['price_formatted'] = f"₹{int(numeric_price):,}"
            
            # Add quality score based on available information
            quality_score = 0
            if listing.get('title'): quality_score += 3
            if listing.get('price'): quality_score += 3
            if listing.get('location'): quality_score += 2
            if listing.get('url'): quality_score += 1
            if listing.get('image_url'): quality_score += 1
            
            listing['quality_score'] = quality_score
            
            enhanced.append(listing)
        
        # Sorting behavior
        sort_by = getattr(self, 'sort_by', 'quality') or 'quality'
        featured_first = getattr(self, 'featured_first', False)

        def sort_key(x):
            key_parts = []
            if featured_first:
                key_parts.append(0 if x.get('featured') else 1)
            if sort_by == 'date':
                # Newest first
                ts = x.get('posted_at_ts') or 0
                key_parts.append(-int(ts))
            elif sort_by == 'price':
                # Highest price first
                key_parts.append(-(x.get('price_numeric') or 0))
            else:
                # Default to quality/relevance
                key_parts.append(-(x.get('quality_score', 0)))
            return tuple(key_parts)

        enhanced.sort(key=sort_key)
        
        return enhanced
    
    def parse_html_content(self, html_content, url):
        """Parse HTML content from requests fallback"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            listings = []
            
            # Look for car cover mentions
            text_content = soup.get_text()
            car_cover_count = len(re.findall(r'(?i)car.*cover|cover.*car', text_content))
            price_count = len(re.findall(r'₹[\d,]+', text_content))
            
            if car_cover_count > 0 or price_count > 0:
                # Find potential listing elements
                potential_elements = soup.find_all(['div', 'article', 'li'], 
                                                 string=re.compile(r'(?i)car.*cover|cover.*car'))
                
                for i, elem in enumerate(potential_elements[:5]):
                    parent = elem.parent
                    if parent:
                        text_content = parent.get_text().strip()
                        if len(text_content) > 30:
                            listing = self.parse_text_content(text_content, f"requests_{i}")
                            if listing:
                                listing['url'] = url
                                listing['source'] = 'requests_fallback'
                                listings.append(listing)
                
                # If no specific elements found, create summary
                if not listings and (car_cover_count > 0 or price_count > 0):
                    listing = {
                        'id': 'requests_summary',
                        'title': 'Car Cover Listings (Requests Method)',
                        'price': f'{price_count} prices found',
                        'location': 'Various',
                        'url': url,
                        'description': f'Found {car_cover_count} car cover mentions and {price_count} prices',
                        'scraped_at': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'source': 'requests_summary'
                    }
                    listings.append(listing)
            
            return listings
            
        except Exception as e:
            print(f"HTML content parsing error: {e}")
            return []

def main():
    """Enhanced main execution function"""
    print("🎯 Enhanced OLX Car Cover Scraper v2.0")
    print("=" * 50)
    
    # CLI arguments
    parser = argparse.ArgumentParser(description="OLX Car Cover Scraper")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--no-pause", action="store_true", help="Do not wait for Enter at the end")
    parser.add_argument("--query", type=str, default=None, help="Override API query (default: 'car cover')")
    parser.add_argument("--size", type=int, default=None, help="API size (default: 80)")
    parser.add_argument("--location", type=int, default=None, help="OLX location ID (default: 1000001)")
    parser.add_argument("--api-only", action="store_true", help="Use only API extraction and skip Selenium")
    parser.add_argument("--no-filter", action="store_true", help="Bypass car-cover filtering to mirror UI result set")
    parser.add_argument("--sort", type=str, choices=['quality','date','price','relevance'], default=None, help="Sort output: quality (default), date, price, relevance")
    parser.add_argument("--featured-first", action="store_true", help="Place featured/promoted items first (best-effort)")
    args, unknown = parser.parse_known_args()

    # User preferences (only prompt if flag not provided)
    if args.headless:
        headless = True
    else:
        print("Configuration Options:")
        try:
            headless_input = input("🖥️  Run in headless mode? (y/n, default=n): ").strip().lower()
            headless = headless_input == 'y'
        except Exception:
            headless = False
    
    # Create and run enhanced scraper
    scraper = ImprovedOLXScraper(headless=headless)
    # Apply CLI overrides for API
    if getattr(args, 'query', None):
        scraper.api_query = args.query
    if getattr(args, 'size', None):
        try:
            scraper.api_size = max(1, min(120, int(args.size)))
        except Exception:
            scraper.api_size = 80
    if getattr(args, 'location', None):
        try:
            scraper.api_location = int(args.location)
        except Exception:
            pass
    if getattr(args, 'api_only', False):
        scraper.api_only = True
    if getattr(args, 'no_filter', False):
        scraper.no_filter = True
    if getattr(args, 'sort', None):
        scraper.sort_by = args.sort
    if getattr(args, 'featured_first', False):
        scraper.featured_first = True
    
    print(f"\n🚀 Starting enhanced scraping process...")
    print(f"   Mode: {'Headless' if headless else 'Visible'}")
    print(f"   Target: Car covers on OLX India")
    print(f"   URLs to try: {len(scraper.search_urls)}")
    print(f"   Filters: {'OFF (UI-parity)' if scraper.no_filter else 'ON (car-cover only)'} | Sort: {scraper.sort_by} | Featured-first: {scraper.featured_first}")
    
    start_time = time.time()
    listings = scraper.run_enhanced_scraper()
    end_time = time.time()
    
    # Display comprehensive results
    print("\n" + "=" * 70)
    print("📊 SCRAPING RESULTS SUMMARY")
    print("=" * 70)
    
    if listings:
        print(f"✅ SUCCESS! Extracted {len(listings)} listings")
        print(f"⏱️  Total time: {end_time - start_time:.2f} seconds")
        
        # Categorize results
        quality_listings = [l for l in listings if l.get('quality_score', 0) >= 6]
        medium_listings = [l for l in listings if 3 <= l.get('quality_score', 0) < 6]
        low_listings = [l for l in listings if l.get('quality_score', 0) < 3]
        
        print(f"🎯 High quality listings: {len(quality_listings)}")
        print(f"🔶 Medium quality listings: {len(medium_listings)}")
        print(f"🔸 Low quality listings: {len(low_listings)}")
        
        print(f"\n📋 TOP RESULTS PREVIEW:")
        print("-" * 70)
        
        for i, listing in enumerate(listings[:7], 1):
            title = listing.get('title', 'No title')[:60]
            price = listing.get('price', 'No price')
            location = listing.get('location', 'No location')[:20]
            quality = listing.get('quality_score', 0)
            source = listing.get('source', 'unknown')
            
            print(f"{i:2d}. {title}")
            print(f"    💰 {price} | 📍 {location} | ⭐ Quality: {quality}/10 | 🔧 {source}")
            print()
        
        if len(listings) > 7:
            print(f"    ... and {len(listings) - 7} more listings")
        
        print(f"\n💾 Files saved in 'olx_scraping_results' directory")
        print(f"   📄 JSON, CSV, and detailed report available")
        
    else:
        print(f"❌ No listings extracted")
        print(f"⏱️  Total time: {end_time - start_time:.2f} seconds")
        
        print(f"\n🔧 Troubleshooting suggestions:")
        print(f"   • Check if OLX.in is accessible in your region")
        print(f"   • Try using a VPN")
        print(f"   • Verify the search URL works in browser")
        print(f"   • Check internet connection stability")
        print(f"   • Try running in non-headless mode for debugging")
    
    print(f"\n🎉 Scraping process completed!")
    if not args.no_pause:
        try:
            input("Press Enter to exit...")
        except Exception:
            pass

if __name__ == "__main__":
    main()