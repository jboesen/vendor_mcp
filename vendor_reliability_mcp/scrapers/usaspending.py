"""USAspending.gov scrapers for contract data"""

import aiohttp
import json
from typing import Dict, Any, List

USASPENDING_API = "https://api.usaspending.gov/api/v2"

# Required fields for the API
CONTRACT_FIELDS = [
    "Award ID",
    "Recipient Name",
    "Start Date",
    "End Date", 
    "Award Amount",
    "Awarding Agency",
    "Awarding Sub Agency",
    "Contract Award Type",
    "Description",
    "Total Outlays"
]


async def get_contracts(
    recipient_name: str = None,
    fiscal_year: int = None,
    limit: int = 20
) -> Dict[str, Any]:
    """Get contract awards for a recipient using POST request"""
    
    # Build filters
    filters = {
        "award_type_codes": ["A", "B", "C", "D"],  # Contract award types
    }
    
    # Add keyword search for recipient name
    if recipient_name:
        filters["keywords"] = [recipient_name]
    
    # Add time period filter
    if fiscal_year:
        filters["time_period"] = [
            {
                "start_date": f"{fiscal_year}-10-01",
                "end_date": f"{fiscal_year + 1}-09-30"
            }
        ]
    else:
        # Default to last 5 years if no fiscal year specified
        filters["time_period"] = [
            {"start_date": "2020-10-01", "end_date": "2025-09-30"}
        ]
    
    payload = {
        "filters": filters,
        "fields": CONTRACT_FIELDS,
        "limit": limit
    }
    
    url = f"{USASPENDING_API}/search/spending_by_award"
    
    headers = {
        "User-Agent": "VendorReliabilityMCP/0.1 (research@localhost)",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                return _parse_awards(data)
            elif resp.status == 429:
                return {"error": "Rate limited - try again later"}
            text = await resp.text()
            return {"error": f"Status {resp.status}", "detail": text[:500]}


def _parse_awards(data: Dict) -> Dict[str, Any]:
    """Parse USAspending award results"""
    results = data.get("results", [])
    awards = []
    total_dollars = 0
    for award in results:
        amount = award.get("Award Amount") or award.get("award_amount")
        if amount:
            try:
                total_dollars += float(amount)
            except (ValueError, TypeError):
                pass
        awards.append({
            "id": award.get("Award ID"),
            "amount": amount,
            "start_date": award.get("Start Date"),
            "end_date": award.get("End Date"),
            "agency": award.get("Awarding Agency"),
            "sub_agency": award.get("Awarding Sub Agency"),
            "contract_type": award.get("Contract Award Type"),
            "description": award.get("Description"),
        })
    return {
        "total_awards": len(awards),
        "total_dollars": total_dollars,
        "awards": awards
    }
