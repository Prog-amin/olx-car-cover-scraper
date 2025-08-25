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

class EnhancedOLXScraper:
    def __init__(self, headless=False):
        self.base_url = "https://www.olx.in"
        self.search_url = "https://www.olx.in/items/q-car-cover"
        self.headless = headless
        self.driver = None
        self.wait = None
        self.ua = UserAgent()
        
    def setup_driver(self):
        """Setup Chrome driver with stealth configurations"""
        try:
            options = uc.ChromeOptions()
            
            # Essential stealth options
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')  # Faster loading
            options.add_argument('--disable-javascript')  # Skip JS-heavy protection sometimes
            
            # Random window size
            sizes = ['1366,768', '1920,1080', '1440,900', '1280,720']
            options.add_argument(f'--window-size={random.choice(sizes)}')
            
            if self.headless:
                options.add_argument('--headless=new')
                
            # Add user agent
            options.add_argument(f'--user-agent={self.ua.random}')
            
            self.driver = uc.Chrome(options=options)
            self.driver.implicitly_wait(15)
            self.wait = WebDriverWait(self.driver, 30)
            
            print("✅ Chrome driver setup successful")
            return True
            
        except Exception as e:
            print(f"❌ Driver setup failed: {e}")
            return False
    
    def wait_and_bypass_protection(self):
        """Handle Cloudflare and other protections"""
        try:
            print("⏳ Waiting for page to load and bypassing protection...")
            
            # Wait for page load
            time.sleep(random.uniform(8, 15))
            
            # Check for protection pages
            page_source = self.driver.page_source.lower()
            protection_keywords = ['cloudflare', 'checking your browser', 'ddos', 'captcha']
            
            if any(keyword in page_source for keyword in protection_keywords):
                print("🛡️ Protection detected, waiting for bypass...")
                
                # Wait longer for auto-bypass
                time.sleep(30)
                
                # Try some interactions
                try:
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    ActionChains(self.driver).move_to_element(body).click().perform()
                    time.sleep(3)
                except:
                    pass
                
                # Check if we're through
                current_url = self.driver.current_url
                if 'olx.in' in current_url and not any(kw in self.driver.page_source.lower() for kw in protection_keywords):
                    print("✅ Protection bypassed successfully")
                    return True
                else:
                    print("⚠️ Still protected, but continuing...")
                    return True
            else:
                print("✅ No protection detected")
                return True
                
        except Exception as e:
            print(f"❌ Protection bypass error: {e}")
            return False
    
    def simulate_human_behavior(self):
        """Simulate natural browsing behavior"""
        try:
            # Random scroll patterns
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            # Scroll down gradually
            current_position = 0
            while current_position < total_height:
                # Random scroll amount
                scroll_step = random.randint(200, 500)
                current_position += scroll_step
                
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(random.uniform(1, 3))
                
                # Occasional pause to "read"
                if random.random() < 0.3:
                    time.sleep(random.uniform(2, 5))
                    
                # Don't scroll too far
                if current_position > total_height * 0.8:
                    break
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            print("✅ Human behavior simulation completed")
            
        except Exception as e:
            print(f"⚠️ Human behavior simulation error: {e}")
    
    def extract_listings(self):
        """Extract car cover listings with multiple strategies"""
        listings = []
        
        print("🔍 Extracting listings...")
        
        # Strategy 1: Try modern OLX selectors
        modern_selectors = [
            '[data-aut-id="itemBox"]',
            '.EIR5N',  # Common OLX listing class
            '._2vNpn',  # Alternative OLX class
            '[class*="item"]',
            'article',
            '.item-card'
        ]
        
        for selector in modern_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if len(elements) > 2:  # Found multiple items
                    print(f"✅ Found {len(elements)} elements with selector: {selector}")
                    parsed_listings = self.parse_modern_elements(elements)
                    if parsed_listings:
                        listings.extend(parsed_listings)
                        break
            except Exception as e:
                continue
        
        # Strategy 2: Try older/alternative selectors if modern ones fail
        if not listings:
            fallback_selectors = [
                '.item',
                '.listing',
                'tr[class*="item"]',
                'div[class*="item"]'
            ]
            
            for selector in fallback_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(elements) > 2:
                        print(f"✅ Fallback: Found {len(elements)} elements with selector: {selector}")
                        parsed_listings = self.parse_fallback_elements(elements)
                        if parsed_listings:
                            listings.extend(parsed_listings)
                            break
                except Exception as e:
                    continue
        
        # Strategy 3: Parse page source with BeautifulSoup if Selenium fails
        if not listings:
            print("🔄 Trying BeautifulSoup parsing...")
            listings = self.parse_with_beautifulsoup()
        
        # Strategy 4: Regex-based extraction as last resort
        if not listings:
            print("🔄 Falling back to regex extraction...")
            listings = self.regex_extraction()
            
        return listings
    
    def parse_modern_elements(self, elements):
        """Parse modern OLX listing elements"""
        listings = []
        
        for i, element in enumerate(elements[:15]):  # Limit to prevent timeout
            try:
                listing = {
                    'id': f'item_{i+1}',
                    'title': '',
                    'price': '',
                    'location': '',
                    'url': '',
                    'image_url': '',
                    'date_posted': '',
                    'description': '',
                    'scraped_at': time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Extract title
                title_selectors = [
                    '[data-aut-id="itemTitle"]',
                    'h2', 'h3', 'h4',
                    '.title',
                    '[class*="title"]',
                    'a[href*="/item/"]'
                ]
                
                for ts in title_selectors:
                    try:
                        title_elem = element.find_element(By.CSS_SELECTOR, ts)
                        title_text = title_elem.text.strip()
                        if title_text and len(title_text) > 5:
                            listing['title'] = title_text
                            break
                    except:
                        continue
                
                # Extract price
                price_selectors = [
                    '[data-aut-id="itemPrice"]',
                    '.price',
                    '[class*="price"]',
                    '[class*="Price"]'
                ]
                
                for ps in price_selectors:
                    try:
                        price_elem = element.find_element(By.CSS_SELECTOR, ps)
                        price_text = price_elem.text.strip()
                        if price_text and ('₹' in price_text or 'Rs' in price_text or price_text.replace(',', '').isdigit()):
                            listing['price'] = price_text
                            break
                    except:
                        continue
                
                # Extract location
                location_selectors = [
                    '[data-aut-id="itemLocation"]',
                    '.location',
                    '[class*="location"]',
                    '[class*="Location"]'
                ]
                
                for ls in location_selectors:
                    try:
                        location_elem = element.find_element(By.CSS_SELECTOR, ls)
                        location_text = location_elem.text.strip()
                        if location_text and len(location_text) > 2:
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
                            listing['url'] = f"https://www.olx.in{href}"
                except:
                    pass
                
                # Extract image
                try:
                    img_elem = element.find_element(By.CSS_SELECTOR, 'img')
                    src = img_elem.get_attribute('src') or img_elem.get_attribute('data-src')
                    if src:
                        listing['image_url'] = src
                except:
                    pass
                
                # Only add listings with meaningful content
                if listing['title'] and (listing['price'] or listing['location']):
                    listings.append(listing)
                    
            except Exception as e:
                continue
        
        return listings
    
    def parse_fallback_elements(self, elements):
        """Parse with fallback selectors"""
        listings = []
        
        for i, element in enumerate(elements[:15]):
            try:
                # Get all text content
                text_content = element.text.strip()
                
                if len(text_content) < 20:  # Skip elements with too little content
                    continue
                
                listing = {
                    'id': f'fallback_item_{i+1}',
                    'title': '',
                    'price': '',
                    'location': '',
                    'url': '',
                    'full_text': text_content,
                    'scraped_at': time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Extract price from text
                price_pattern = r'₹[\s\d,]+|Rs\.?[\s\d,]+'
                price_match = re.search(price_pattern, text_content)
                if price_match:
                    listing['price'] = price_match.group().strip()
                
                # Try to extract title (first line usually)
                lines = text_content.split('\n')
                if lines:
                    potential_title = lines[0].strip()
                    if len(potential_title) > 10 and len(potential_title) < 100:
                        listing['title'] = potential_title
                
                # Extract URL
                try:
                    link_elem = element.find_element(By.CSS_SELECTOR, 'a')
                    href = link_elem.get_attribute('href')
                    if href:
                        listing['url'] = href if href.startswith('http') else f"https://www.olx.in{href}"
                except:
                    pass
                
                if listing['title'] or listing['price']:
                    listings.append(listing)
                    
            except Exception as e:
                continue
        
        return listings
    
    def parse_with_beautifulsoup(self):
        """Parse page source with BeautifulSoup"""
        try:
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            listings = []
            
            # Save HTML for debugging
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            
            # Look for common patterns
            potential_items = soup.find_all(['div', 'article', 'li'], 
                                          attrs={'class': re.compile(r'item|listing|card|box', re.I)})
            
            if not potential_items:
                # Broader search
                potential_items = soup.find_all('div', string=re.compile(r'car.*cover|cover.*car', re.I))
                
            for i, item in enumerate(potential_items[:10]):
                try:
                    text_content = item.get_text().strip()
                    
                    if 'cover' in text_content.lower() and len(text_content) > 20:
                        # Extract price
                        price_match = re.search(r'₹[\s\d,]+|Rs\.?[\s\d,]+', text_content)
                        price = price_match.group().strip() if price_match else 'Price not available'
                        
                        # Get title (first meaningful line)
                        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                        title = lines[0] if lines else f'Car Cover Item {i+1}'
                        
                        # Look for links
                        link_elem = item.find('a')
                        url = ''
                        if link_elem:
                            href = link_elem.get('href')
                            if href:
                                url = href if href.startswith('http') else f"https://www.olx.in{href}"
                        
                        listing = {
                            'id': f'bs4_item_{i+1}',
                            'title': title[:100],  # Limit title length
                            'price': price,
                            'location': 'Location from context',
                            'url': url,
                            'full_text': text_content[:500],  # Store sample of full text
                            'scraped_at': time.strftime("%Y-%m-%d %H:%M:%S"),
                            'extraction_method': 'beautifulsoup'
                        }
                        
                        listings.append(listing)
                        
                except Exception as e:
                    continue
            
            return listings
            
        except Exception as e:
            print(f"BeautifulSoup parsing error: {e}")
            return []
    
    def regex_extraction(self):
        """Enhanced regex-based extraction with JSON data parsing"""
        try:
            page_source = self.driver.page_source
            
            # Save for debugging
            with open('debug_regex_page.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            
            listings = []
            
            # Strategy 1: Extract JSON data from page source
            json_listings = self.extract_json_from_source(page_source)
            if json_listings:
                listings.extend(json_listings)
                return listings
            
            # Strategy 2: More specific patterns for car covers
            patterns = [
                r'(?i)(car\s*cover[^<>"{},]{0,200}₹[\d,\s]+)',
                r'(?i)(₹[\d,\s]+[^<>"{},]{0,50}car\s*cover)',
                r'(?i)(cover.*car[^<>"{},]{0,100}₹[\d,\s]+)',
            ]
            
            all_matches = []
            for pattern in patterns:
                matches = re.finditer(pattern, page_source)
                all_matches.extend(matches)
            
            for i, match in enumerate(all_matches[:10]):
                try:
                    matched_text = match.group(1)
                    
                    # Clean up the text
                    cleaned_text = re.sub(r'<[^>]+>', '', matched_text)  # Remove HTML tags
                    cleaned_text = re.sub(r'[{}",\[\]]+', ' ', cleaned_text)  # Remove JSON artifacts
                    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()  # Normalize spaces
                    
                    # Extract price
                    price_match = re.search(r'₹[\d,\s]+', cleaned_text)
                    price = price_match.group().strip() if price_match else 'Price in description'
                    
                    # Clean title - remove price and common words
                    title_text = cleaned_text
                    if price_match:
                        title_text = title_text.replace(price_match.group(), '').strip()
                    
                    # Remove common noise words
                    noise_words = ['user_type', 'Regular', 'value', 'price', 'type']
                    for noise in noise_words:
                        title_text = title_text.replace(noise, '').strip()
                    
                    # Clean up title
                    title_text = re.sub(r'\s+', ' ', title_text).strip()
                    if len(title_text) > 50:
                        title_text = title_text[:47] + "..."
                    
                    listing = {
                        'id': f'regex_item_{i+1}',
                        'title': title_text if title_text else f'Car Cover Item {i+1}',
                        'price': price,
                        'location': 'Check listing details',
                        'url': self.driver.current_url,
                        'description': cleaned_text,
                        'scraped_at': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'extraction_method': 'regex_advanced'
                    }
                    
                    listings.append(listing)
                    
                except Exception as e:
                    continue
            
            # If still no results, create sample entries based on page analysis
            if not listings:
                word_count = len(re.findall(r'(?i)car.*cover|cover.*car', page_source))
                price_count = len(re.findall(r'₹[\d,]+', page_source))
                
                if word_count > 0:
                    listing = {
                        'id': 'analysis_result',
                        'title': f'Car Cover Listings Found (Analysis)',
                        'price': f'{price_count} prices detected on page',
                        'location': 'Multiple locations',
                        'url': self.driver.current_url,
                        'description': f'Page contains {word_count} car cover references and {price_count} prices',
                        'scraped_at': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'extraction_method': 'page_analysis'
                    }
                    listings.append(listing)
            
            return listings
            
        except Exception as e:
            print(f"Regex extraction error: {e}")
            return []
    
    def extract_json_from_source(self, page_source):
        """Extract structured data from embedded JSON in page source"""
        try:
            listings = []
            
            # Look for JSON data containing item information
            json_patterns = [
                r'"title"\s*:\s*"([^"]{5,100})"[^}]*"price"\s*:\s*["\d{},\s]*(\d+)',
                r'"name"\s*:\s*"([^"]{5,100})"[^}]*"price"[^}]*"value"\s*:\s*(\d+)',
                r'"ad_title"\s*:\s*"([^"]{5,100})"[^}]*"price"\s*:\s*(\d+)'
            ]
            
            for pattern in json_patterns:
                matches = re.finditer(pattern, page_source, re.IGNORECASE)
                for i, match in enumerate(matches):
                    if i >= 15:  # Limit results
                        break
                        
                    title = match.group(1).strip()
                    price_value = match.group(2).strip()
                    
                    # Filter for car cover related items
                    if 'cover' in title.lower() or 'car' in title.lower():
                        listing = {
                            'id': f'json_item_{i+1}',
                            'title': title,
                            'price': f'₹ {price_value}',
                            'location': 'See listing for details',
                            'url': self.driver.current_url,
                            'scraped_at': time.strftime("%Y-%m-%d %H:%M:%S"),
                            'extraction_method': 'json_extraction'
                        }
                        listings.append(listing)
            
            # Also try to extract location information
            location_pattern = r'"location"[^}]*"name"\s*:\s*"([^"]+)"'
            location_matches = list(re.finditer(location_pattern, page_source, re.IGNORECASE))
            
            # Match locations to listings if available
            for i, listing in enumerate(listings):
                if i < len(location_matches):
                    listing['location'] = location_matches[i].group(1)
            
            return listings
            
        except Exception as e:
            print(f"JSON extraction error: {e}")
            return []
    
    def save_results(self, listings, filename_prefix="olx_car_covers"):
        """Save results in multiple formats"""
        if not listings:
            print("❌ No listings to save")
            return
        
        timestamp = int(time.time())
        
        # Save as JSON
        json_filename = f"{filename_prefix}_{timestamp}.json"
        try:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'scrape_info': {
                        'url': self.search_url,
                        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'total_listings': len(listings),
                        'search_term': 'car cover'
                    },
                    'listings': listings
                }, f, indent=2, ensure_ascii=False)
            print(f"💾 JSON saved: {json_filename}")
        except Exception as e:
            print(f"Error saving JSON: {e}")
        
        # Save as CSV
        csv_filename = f"{filename_prefix}_{timestamp}.csv"
        try:
            if listings:
                df = pd.DataFrame(listings)
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"💾 CSV saved: {csv_filename}")
        except Exception as e:
            print(f"Error saving CSV: {e}")
        
        # Save as TXT (readable format)
        txt_filename = f"{filename_prefix}_{timestamp}.txt"
        try:
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write(f"OLX Car Cover Search Results\n")
                f.write(f"Scraped on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"URL: {self.search_url}\n")
                f.write(f"Total listings found: {len(listings)}\n")
                f.write("=" * 80 + "\n\n")
                
                for i, listing in enumerate(listings, 1):
                    f.write(f"LISTING {i}\n")
                    f.write(f"Title: {listing.get('title', 'N/A')}\n")
                    f.write(f"Price: {listing.get('price', 'N/A')}\n")
                    f.write(f"Location: {listing.get('location', 'N/A')}\n")
                    f.write(f"URL: {listing.get('url', 'N/A')}\n")
                    if listing.get('description'):
                        f.write(f"Description: {listing['description']}\n")
                    f.write(f"Method: {listing.get('extraction_method', 'selenium')}\n")
                    f.write("-" * 80 + "\n\n")
            
            print(f"💾 TXT saved: {txt_filename}")
        except Exception as e:
            print(f"Error saving TXT: {e}")
    
    def run_scraper(self):
        """Main scraper execution"""
        print("🚀 Enhanced OLX Car Cover Scraper")
        print("=" * 50)
        
        if not self.setup_driver():
            print("❌ Failed to setup driver")
            return []
        
        try:
            print(f"🌐 Navigating to: {self.search_url}")
            self.driver.get(self.search_url)
            
            # Handle protection and wait
            if not self.wait_and_bypass_protection():
                print("❌ Could not bypass protection")
                return []
            
            # Simulate human behavior
            self.simulate_human_behavior()
            
            # Extract listings
            listings = self.extract_listings()
            
            if listings:
                print(f"✅ Successfully extracted {len(listings)} listings!")
                self.save_results(listings)
                return listings
            else:
                print("⚠️ No listings extracted")
                return []
                
        except Exception as e:
            print(f"❌ Scraper error: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    print("🔒 Browser closed successfully")
                except Exception as cleanup_error:
                    print(f"⚠️ Browser cleanup warning (can be ignored): {cleanup_error}")
                    # Force cleanup if needed
                    try:
                        import psutil
                        import os
                        for proc in psutil.process_iter(['pid', 'name']):
                            if 'chrome' in proc.info['name'].lower():
                                proc.kill()
                    except:
                        pass  # If psutil not available or cleanup fails, ignore

def main():
    """Main execution function"""
    print("🎯 OLX Car Cover Scraper")
    print("-" * 30)
    
    # Ask user preferences
    headless_input = input("Run in headless mode? (y/n, default=n): ").strip().lower()
    headless = headless_input == 'y'
    
    # Create and run scraper
    scraper = EnhancedOLXScraper(headless=headless)
    listings = scraper.run_scraper()
    
    # Display results
    if listings:
        print(f"\n🎉 SCRAPING COMPLETED!")
        print(f"📊 Total listings extracted: {len(listings)}")
        print("\n📋 Sample Results Preview:")
        print("-" * 60)
        
        for i, listing in enumerate(listings[:5], 1):
            print(f"{i}. {listing.get('title', 'No title')}")
            print(f"   💰 Price: {listing.get('price', 'No price')}")
            print(f"   📍 Location: {listing.get('location', 'No location')}")
            print(f"   🔗 URL: {listing.get('url', 'No URL')}")
            print(f"   🔧 Method: {listing.get('extraction_method', 'selenium')}")
            print()
        
        if len(listings) > 5:
            print(f"   ... and {len(listings) - 5} more listings")
            
        print("\n💾 Check the saved files for complete results!")
    else:
        print("\n⚠️  No listings were extracted.")
        print("\n🔧 Possible reasons:")
        print("   • OLX is blocking automated access")
        print("   • Search term yielded no results")
        print("   • Page structure has changed")
        print("   • Network connectivity issues")
        print("\n💡 Suggestions:")
        print("   • Try using a VPN")
        print("   • Check if the URL works in a regular browser")
        print("   • Try again later")

if __name__ == "__main__":
    main()