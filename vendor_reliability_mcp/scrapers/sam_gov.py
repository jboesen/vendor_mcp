"""SAM.gov scrapers for entity lookup and CPARS data"""

import aiohttp
import json
import os
import asyncio
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load API key from .env
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(_env_path)

SAM_API_KEY = os.environ.get("SAM_API_KEY", "")

# Use v4 API with API key in query string
SAM_API_BASE = "https://api.sam.gov/entity-information/v4"

# Simple in-memory cache for SAM.gov responses (handles rate limits)
# Format: {cache_key: (timestamp, response)}
_sam_cache: Dict[str, tuple[float, Dict[str, Any]]] = {}
_CACHE_TTL = 3600  # 1 hour cache

def _get_cache(key: str) -> Optional[Dict[str, Any]]:
    """Get cached response if still valid"""
    if key in _sam_cache:
        timestamp, data = _sam_cache[key]
        if time.time() - timestamp < _CACHE_TTL:
            return data
        del _sam_cache[key]
    return None

def _set_cache(key: str, data: Dict[str, Any]) -> None:
    """Cache a response"""
    _sam_cache[key] = (time.time(), data)


async def _make_request_with_retry(url: str, params: Dict = None, method: str = "GET", 
                                    data: Dict = None, max_retries: int = 3) -> Dict[str, Any]:
    """Make request with exponential backoff retry for rate limits"""
    for attempt in range(max_retries):
        async with aiohttp.ClientSession() as session:
            try:
                if method == "GET":
                    async with session.get(url, params=params) as resp:
                        if resp.status == 200:
                            return await resp.json()
                        elif resp.status == 429:
                            # Rate limited - wait and retry
                            wait_time = (2 ** attempt) * 2  # 2, 4, 6 seconds
                            if attempt < max_retries - 1:
                                await asyncio.sleep(wait_time)
                                continue
                            text = await resp.text()
                            return {"error": "Rate limited", "status": 429, "detail": text[:300], "retry_attempted": True}
                        text = await resp.text()
                        return {"error": f"Status {resp.status}", "detail": text[:200]}
                elif method == "POST":
                    async with session.post(url, json=data, params=params) as resp:
                        if resp.status == 200:
                            return await resp.json()
                        elif resp.status == 429:
                            wait_time = (2 ** attempt) * 2
                            if attempt < max_retries - 1:
                                await asyncio.sleep(wait_time)
                                continue
                            text = await resp.text()
                            return {"error": "Rate limited", "status": 429, "detail": text[:300], "retry_attempted": True}
                        text = await resp.text()
                        return {"error": f"Status {resp.status}", "detail": text[:200]}
            except aiohttp.ClientError as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return {"error": f"Client error: {str(e)}"}
    return {"error": "Max retries exceeded"}


async def lookup_duns(duns: str) -> Dict[str, Any]:
    """Look up entity by DUNS/UEI number"""
    if not SAM_API_KEY:
        return {"error": "SAM_API_KEY not set"}
    
    # SAM.gov v4 API - use correct parameter: ueiSAM for UEI lookup
    # DUNS numbers can be converted to UEI or used directly
    # Clean the input - remove any dashes, keep only alphanumeric
    uei = duns.upper().replace("-", "").replace(" ", "")
    
    # Check cache first
    cache_key = f"lookup:{uei}"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    url = f"{SAM_API_BASE}/entities"
    # Correct parameter for UEI lookup is ueiSAM
    params = {
        "api_key": SAM_API_KEY, 
        "ueiSAM": uei  # 12-character UEI or DUNS converted to UEI format
    }
    
    result = await _make_request_with_retry(url, params=params)
    
    # Cache the result (even errors to avoid hammering rate limited API)
    _set_cache(cache_key, result)
    
    # Extract the entity data if found
    if result.get("entityData") and len(result["entityData"]) > 0:
        # Return the first matching entity (most relevant)
        entity = result["entityData"][0]
        entity_reg = entity.get("entityRegistration", {})
        core_data = entity.get("coreData", {})
        
        return {
            "found": True,
            "ueiSAM": entity_reg.get("ueiSAM"),
            "legalEntityName": entity_reg.get("legalBusinessName"),
            "dbaName": entity_reg.get("dbaName"),
            "cageCode": entity_reg.get("cageCode"),
            "registrationStatus": entity_reg.get("registrationStatus"),
            "exclusionStatus": entity_reg.get("exclusionStatusFlag"),
            "physicalAddress": core_data.get("physicalAddress"),
            "mailingAddress": core_data.get("mailingAddress"),
            "entityType": core_data.get("generalInformation", {}).get("entityTypeDesc"),
            "stateOfIncorporation": core_data.get("generalInformation", {}).get("stateOfIncorporationDesc"),
            "countryOfIncorporation": core_data.get("generalInformation", {}).get("countryOfIncorporationDesc"),
            "registrationDate": entity_reg.get("registrationDate"),
            "expirationDate": entity_reg.get("registrationExpirationDate"),
        }
    
    # If error in response, return it
    if result.get("error"):
        return result
    
    return {
        "found": False,
        "duns": duns,
        "note": "Entity not found in SAM.gov"
    }


async def search_entity(name: str = None, state: str = None) -> Dict[str, Any]:
    """Search SAM.gov entity registration - with improved filtering"""
    if not SAM_API_KEY:
        return {"error": "SAM_API_KEY not set"}
    
    # Use 'q' parameter for general search (works better than specific fields)
    params = {"api_key": SAM_API_KEY}
    if name:
        params["q"] = name
    
    # Filter by state if provided - use correct parameter
    if state:
        params["physicalAddressStateOrProvince"] = state.upper()
    
    # Check cache first
    cache_key = f"search:{name}:{state}"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    url = f"{SAM_API_BASE}/entities"
    result = await _make_request_with_retry(url, params=params)
    
    # Cache the result
    _set_cache(cache_key, result)
    
    # Post-process to filter out false positives and format results
    if result.get("entityData") and name:
        original_count = len(result["entityData"])
        
        # Format the results nicely
        formatted_entities = []
        search_term = name.lower()
        
        for entity in result["entityData"]:
            entity_reg = entity.get("entityRegistration", {})
            core_data = entity.get("coreData", {})
            legal_name = entity_reg.get("legalBusinessName", "").lower()
            
            # Only include if entity name contains our search term (not just address)
            if search_term in legal_name:
                formatted_entities.append({
                    "ueiSAM": entity_reg.get("ueiSAM"),
                    "legalEntityName": entity_reg.get("legalBusinessName"),
                    "dbaName": entity_reg.get("dbaName"),
                    "cageCode": entity_reg.get("cageCode"),
                    "registrationStatus": entity_reg.get("registrationStatus"),
                    "exclusionStatus": entity_reg.get("exclusionStatusFlag"),
                    "state": core_data.get("physicalAddress", {}).get("stateOrProvinceCode"),
                    "city": core_data.get("physicalAddress", {}).get("city"),
                })
        
        return {
            "entityList": formatted_entities,
            "filtered": {
                "original_count": original_count,
                "filtered_count": len(formatted_entities),
                "note": "Filtered to only include entities where name contains search term"
            }
        }
    
    # If no results, return empty list with info
    if result.get("entityData") is None or len(result.get("entityData", [])) == 0:
        return {
            "entityList": [],
            "note": "No entities found matching criteria"
        }
    
    return result


async def get_cpars(duns: str, agency: str = None) -> Dict[str, Any]:
    """Get CPARS rating - requires separate access"""
    return {
        "note": "CPARS requires access at https://cparsers.gov",
        "duns": duns,
        "instructions": [
            "1. Register at cpars.gov",
            "2. Request agency-specific access",
            "3. Search by DUNS",
            "Ratings: Exceptional, Very Good, Satisfactory, Marginal, Unsatisfactory"
        ]
    }


async def check_exclusions(uei: str = None, name: str = None) -> Dict[str, Any]:
    """Check exclusion status (debarment, suspension)"""
    if not SAM_API_KEY:
        return {"error": "SAM_API_KEY not set"}
    
    params = {"api_key": SAM_API_KEY}
    if uei:
        params["ueiSAM"] = uei  # Correct param for exclusions API
    if name:
        params["exclusionName"] = name  # Correct param for exclusions API
    
    url = f"{SAM_API_BASE}/exclusions"
    
    return await _make_request_with_retry(url, params=params)
