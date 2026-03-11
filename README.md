# Vendor Reliability MCP

MCP server for vendor reliability data from public sources.

## Data Sources

| Source | URL | Data | Score Impact |
|--------|-----|------|--------------|
| SAM.gov | sam.gov | Entity registration, exclusions, CPARS | ±50 |
| USAspending.gov | usaspending.gov | Contract awards, spending | +15 |
| BBB | bbb.org | Complaints, ratings, accreditation | +30 |
| SEC EDGAR | sec.gov | 10-K filings, bankruptcy | ±40 |

## Tools

| Tool | Description |
|------|-------------|
| `lookup_duns` | Get SAM.gov entity registration by DUNS |
| `search_sam_entity` | Search SAM.gov entities by name/state |
| `get_usaspending_contracts` | Contract history from USAspending |
| `check_bbb_rating` | BBB rating and complaints |
| `check_sec_filings` | SEC EDGAR filings for financial health |
| `get_litigation` | Court record alternatives |
| `vendor_report` | Generate composite reliability report |

## Scoring Model

**SAM.gov (max 35)**
- Not excluded: +20
- Exceptional CPARS: +15
- Very Good CPARS: +10
- Satisfactory CPARS: +5
- Marginal/Unsatisfactory: -20
- Excluded: -50

**USAspending (max 15)**
- 50+ contracts: +15
- 10-50 contracts: +10
- <10 contracts: +5

**BBB (max 30)**
- Rating (0-5 scale ×5): up to +25
- Accredited: +5
- Complaints resolved >10: +5

**SEC EDGAR (max 20)**
- Annual reports (10-K): +10
- No bankruptcy: +10
- Bankruptcy filings: -30

**Grade Scale**: A (80+), B (60-79), C (40-59), D (20-39), F (<20)

## Usage

```bash
# Optional: SEC API key (free tier: 100 calls/month)
# Sign up at https://sec-api.io/signup/free
export SEC_API_KEY=your_key

# SAM.gov API key (free registration at sam.gov)
export SAM_API_KEY=your_key

pip install -e .
vendor-reliability-mcp
```

## Status

| Source | Status | API Key | Notes |
|--------|--------|---------|-------|
| USAspending | ✅ Working | No | No key needed, works out of box |
| SEC EDGAR | ✅ Working | Yes | Free tier at sec-api.io (100 calls/mo) |
| SAM.gov | ❌ Stub | Yes | Needs SAM_API_KEY from sam.gov |
| CPARS | ❌ Stub | Yes | Requires cpars.gov access |
| BBB | ❌ Stub | No | BBB blocks scraping; no free API |

## Running Tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

## Configuration

```bash
# Required for SEC EDGAR (free): https://sec-api.io/signup/free
SEC_API_KEY=your_key

# Required for SAM.gov (free): https://sam.gov
SAM_API_KEY=your_key

# Optional: put in .env file in package root
```

## Example Report

```json
{
  "vendor": "Bechtel Corporation",
  "reliability_score": {
    "score": 85,
    "grade": "A",
    "factors": [
      ["SAM: Not excluded", 20],
      ["CPARS: Exceptional", 15],
      ["Contracts: 234 ($12.5B)", 15],
      ["BBB: A+", 25],
      ["SEC: 15 annual reports", 10]
    ]
  }
}
```
