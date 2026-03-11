"""SEC EDGAR scraper for financial disclosures"""

import aiohttp
import os
import json
from typing import Dict, Any, List
import time
import asyncio
from dotenv import load_dotenv

# Try to load .env if available (in production, server.py loads it first)
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(_env_path)

SEC_API_KEY = os.environ.get("SEC_API_KEY", "")

SEC_BASE = "https://www.sec.gov"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# Rate limiting for SEC (when not using sec-api.io)
_last_request_time = 0
REQUEST_DELAY = 0.5  # seconds between requests


async def search_company(name: str) -> Dict[str, Any]:
    """Search SEC company database - uses sec-api.io if key provided, else falls back to SEC.gov"""
    
    # Validate input
    if not name or len(name.strip()) < 2:
        return {"found": False, "vendor": name, "error": "Name too short", "matches": []}
    
    # Use sec-api.io if key is available
    if SEC_API_KEY:
        result = await _search_via_sec_api(name)
        if result.get("count", 0) == 0:
            return {"found": False, "vendor": name, "matches": []}
        return {"found": True, "vendor": name, **result}
    
    # Fallback to SEC.gov (likely blocked)
    return {"found": False, "vendor": name, "error": "SEC_API_KEY not set and SEC.gov is blocked", "matches": []}


async def _search_via_sec_api(name: str) -> Dict[str, Any]:
    """Search using sec-api.io"""
    url = "https://api.sec-api.io"
    payload = {
        "query": f"companyName:{name}",
        "from": "0",
        "size": "10",
        "sort": [{"filedAt": {"order": "desc"}}]
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": SEC_API_KEY
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                filings = data.get("filings", [])
                matches = []
                seen_companies = set()
                for f in filings:
                    cik = f.get("cik")
                    company = f.get("companyName", "")
                    if cik and cik not in seen_companies:
                        seen_companies.add(cik)
                        matches.append({
                            "cik": cik,
                            "name": company,
                            "ticker": f.get("ticker", "")
                        })
                        if len(matches) >= 10:
                            break
                return {"matches": matches, "query": name, "count": len(matches)}
            elif resp.status == 403:
                text = await resp.text()
                if "invalid" in text.lower():
                    return {"error": "SEC API key is invalid. Get a valid key from sec-api.io", "status": 403}
            text = await resp.text()
            return {"error": f"Status {resp.status}: {text[:200]}"}


async def get_company_filings(cik: str, count: int = 20) -> Dict[str, Any]:
    """Get recent SEC filings for a CIK or company name - uses sec-api.io if key provided"""
    
    # Validate input
    if not cik:
        return {"found": False, "error": "CIK is required", "filings": []}
    
    # If it looks like a company name (not a valid CIK), try to look up CIK first
    cik_str = str(cik).strip()
    # CIK can be 5-10 digits (it's the padded or unpadded version)
    if not cik_str.isdigit() or len(cik_str) > 10:
        # Treat as company name, look up CIK
        lookup_result = await search_company(cik_str)
        if lookup_result.get("matches"):
            cik = lookup_result["matches"][0]["cik"]
            cik_str = str(cik).zfill(10)
        else:
            return {"found": False, "error": f"Could not find CIK for: {cik}", "suggestion": "Try using the stock ticker (e.g., AAPL, MSFT)", "filings": []}
    
    # Validate CIK format (should be 10 digits)
    cik_clean = cik_str.zfill(10)  # Pad to 10 digits
    if not cik_clean.isdigit():
        return {"found": False, "error": f"Invalid CIK format: {cik}", "cik": cik, "filings": []}
    
    if SEC_API_KEY:
        result = await _get_filings_via_sec_api(cik_clean, count)
        if result.get("filings"):
            return {"found": True, **result}
        return {"found": False, "vendor": cik, **result, "filings": result.get("filings", [])}
    
    # Fallback to SEC.gov (likely blocked)
    return {"found": False, "error": "SEC_API_KEY not set and SEC.gov is blocked", "filings": []}


async def _get_filings_via_sec_api(cik: str, count: int = 20) -> Dict[str, Any]:
    """Get filings via sec-api.io - query by company name derived from CIK"""
    url = "https://api.sec-api.io"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": SEC_API_KEY,
        "User-Agent": "VendorReliabilityMCP/0.1"
    }
    
    # Known CIK→ticker mappings for common companies (fallback when SEC.gov blocked)
    CIK_TO_TICKER = {
        "0000320193": "AAPL",  # Apple
        "0001018724": "AMZN",  # Amazon
        "0000789019": "MSFT",  # Microsoft
        "0000732717": "NVDA",  # NVIDIA
        "0001652044": "GOOGL", # Alphabet
        "0001326801": "META",  # Meta
        "0001045810": "XOM",   # Exxon
        "0000093410": "KO",    # Coca-Cola
        "0000086524": "INTC",  # Intel
        "0000732717": "AMD",   # AMD
        "0000012927": "BA",    # Boeing
        "0001420142": "TSLA", # Tesla
        "0000001800": "IBM",      # IBM
        "0000812994": "INTC",  # Intel again
    }
    
    ticker = CIK_TO_TICKER.get(cik) or CIK_TO_TICKER.get(str(cik).zfill(10))
    if not ticker:
        # Try to look up via SEC.gov 
        try:
            cik_for_lookup = str(cik).zfill(10)
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://data.sec.gov/submissions/CIK{cik_for_lookup}.json",
                    headers={"User-Agent": "VendorReliabilityMCP/0.1", "Accept": "application/json"}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        name = data.get("name", "")
                        # Extract ticker from name or SIC code - try to get from company name
                        ticker = None  # Can't easily get ticker from SEC.gov
        except Exception as e:
            pass
        
        if not ticker:
            return {"error": f"Could not find ticker for CIK {cik}. Try using the stock ticker directly (e.g., BA for Boeing).", "cik": str(cik).zfill(10)}
    
    # Query by ticker - filter client-side (API filters may not work with free tier)
    payload = {
        "query": f"ticker:{ticker}",
        "from": "0",
        "size": str(count),
        "sort": [{"filedAt": {"order": "desc"}}]
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                all_filings = data.get("filings", [])
                
                matching_filings = []
                for f in all_filings:
                    form = f.get("formType", "")
                    if form in ["10-K", "10-Q", "8-K", "4", "S-1", "S-3"]:
                        matching_filings.append({
                            "form": form,
                            "date": f.get("filedAt"),
                            "description": f.get("description", "")[:100] if f.get("description") else ""
                        })
                
                return {
                    "cik": cik,
                    "ticker": ticker,
                    "filings": matching_filings[:count]
                }
            text = await resp.text()
            return {"error": f"Status {resp.status}: {text[:200]}", "cik": cik}


def _parse_filings(data: Dict, limit: int) -> Dict[str, Any]:
    """Parse SEC submissions response (for direct SEC.gov access)"""
    recent = data.get("filings", {}).get("recent", {})
    filings = []
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    for i in range(min(limit, len(forms))):
        filings.append({
            "form": forms[i],
            "date": dates[i],
        })
    return {
        "cik": data.get("cik"),
        "name": data.get("name"),
        "filings": filings,
    }
