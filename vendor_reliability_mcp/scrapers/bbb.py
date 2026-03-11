"""BBB complaints scraper - scraped data"""

import aiohttp
from typing import Dict, Any, List
from bs4 import BeautifulSoup
import asyncio

BBB_API_KEY = ""  # Set via environment


async def get_bbb_rating(business_name: str, city: str = None, state: str = None) -> Dict[str, Any]:
    """Get BBB rating - tries multiple approaches"""
    
    # Try scraping BBB search first
    try:
        result = await scrape_bbb_search(business_name, city, state)
        if result.get("found") or result.get("rating"):
            return result
    except Exception as e:
        error_msg = str(e)[:200]
    
    # Fallback with alternatives - BBB scraping is often blocked
    return {
        "source": "bbb.org",
        "business": business_name,
        "found": False,
        "note": "BBB scraping is blocked (common anti-bot measures). Using alternative sources recommended.",
        "alternatives": [
            {"name": "Google Business Profile", "url": f"https://www.google.com/search?q={business_name.replace(' ', '+')}+reviews"},
            {"name": "Trustpilot", "url": f"https://www.trustpilot.com/search?query={business_name.replace(' ', '%20')}"},
            {"name": "Yelp", "url": f"https://www.yelp.com/search?find_desc={business_name.replace(' ', '%20')}"},
            {"name": "G2 (for B2B)", "url": f"https://www.g2.com/search?query={business_name.replace(' ', '%20')}"},
            {"name": "Capterra (for B2B software)", "url": f"https://www.capterra.com/search/?q={business_name.replace(' ', '%20')}"}
        ]
    }


async def scrape_bbb_search(business_name: str, city: str = None, state: str = None) -> Dict[str, Any]:
    """Scrape BBB page - with improved anti-bot handling"""
    
    # Add delay to appear more human-like
    await asyncio.sleep(0.5)
    
    # Try the BBB.org search format
    search_url = f"https://www.bbb.org/search"
    
    if state:
        search_url += f"?state={state}"
        if city:
            search_url += f"&find_text={business_name}"
        else:
            search_url += f"&find_text={business_name}"
    else:
        search_url += f"?find_text={business_name}"
    search_url += "&type=name"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(search_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                return {"error": f"Status {resp.status}", "source": "bbb.org"}
            
            html = await resp.text()
            
            # Check if blocked
            if "captcha" in html.lower() or "blocked" in html.lower() or "access denied" in html.lower():
                return {"error": "BBB blocked automated access", "source": "bbb.org", "blocked": True}
            
            soup = BeautifulSoup(html, "html.parser")
            
            # Try multiple selectors for the BBB site
            selectors = [
                ".results-card",
                ".business-search-result",
                "[data-testid='business-card']",
                "article.business-card",
                ".MuiCard-root",
                ".ag-root-wrapper",
                ".search-results",
                ".business-listing"
            ]
            
            results = []
            for sel in selectors:
                results = soup.select(sel)
                if results:
                    break
            
            if results:
                # Extract from first result
                first = results[0]
                name_elem = first.select_one("h2, h3, .business-name, [class*='name']")
                name = name_elem.get_text(strip=True) if name_elem else first.get_text(strip=True)[:100]
                
                # Look for rating - multiple possible locations
                rating = None
                rating_patterns = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"]
                text = first.get_text()
                for pattern in rating_patterns:
                    if pattern in text:
                        rating = pattern
                        break
                
                # Extract complaints info if available
                complaints = None
                if "complaint" in text.lower():
                    import re
                    comp_match = re.search(r'(\d+)\s*complaint', text, re.IGNORECASE)
                    if comp_match:
                        complaints = int(comp_match.group(1))
                
                return {
                    "source": "bbb.org",
                    "business": name[:50] if name else business_name,
                    "rating": rating,
                    "complaints": complaints,
                    "found": True,
                    "note": "Extracted from BBB search results"
                }
            
            # Check for no results
            if "no results" in html.lower() or "0 results" in html.lower() or "we couldn't find" in html.lower():
                return {
                    "source": "bbb.org", 
                    "business": business_name,
                    "found": False,
                    "note": "No BBB listing found - business may not be accredited"
                }
            
            # Check if redirected to specific business page
            if "business/" in html.lower():
                return {
                    "source": "bbb.org",
                    "business": business_name,
                    "found": "maybe",
                    "note": "Results page changed - manual check recommended",
                    "url": search_url
                }
            
            return {
                "source": "bbb.org",
                "business": business_name,
                "found": False,
                "note": "Could not parse BBB results - website may have changed",
                "url": search_url
            }
