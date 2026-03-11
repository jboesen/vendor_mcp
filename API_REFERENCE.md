# API Reference - Vendor Reliability MCP

## Table of Contents

1. [lookup_duns](#lookup_duns) - Look up vendor by DUNS number
2. [search_sam_entity](#search_sam_entity) - Search SAM.gov entity registration
3. [get_usaspending_contracts](#get_usaspending_contracts) - Get contract history
4. [get_cpars_rating](#get_cpars_rating) - Get CPARS performance rating
5. [vendor_report](#vendor_report) - Generate composite reliability report
6. [check_bbb_rating](#check_bbb_rating) - Get BBB rating and complaints
7. [check_sec_filings](#check_sec_filings) - Check SEC EDGAR filings
8. [get_litigation](#get_litigation) - Court records alternatives

---

## lookup_duns

Look up a vendor's SAM.gov entity registration using their 9-digit DUNS number.

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `duns` | string | Yes | 9-digit DUNS (Data Universal Numbering System) number |

### Example Call

```json
{
  "name": "lookup_duns",
  "arguments": {
    "duns": "079235148"
  }
}
```

### Response Format

```json
{
  "samUniqueEntityId": "079235148",
  "legalBusinessName": "BECHTEL CORPORATION",
  "entityStatus": "Active",
  "cageCode": "19539",
  "address": {
    "addressLine1": "12011 SUNSET HILLS RD",
    "city": "RESTON",
    "state": "VA",
    "zipCode": "20190"
  },
  "exclusion": {
    "recordStatus": "Active"
  }
}
```

---

## search_sam_entity

Search SAM.gov entity registration database by company name and/or US state.

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | No | Company name to search (partial match supported) |
| `state` | string | No | US state code (e.g., "VA", "CA", "TX") |

### Example Call

```json
{
  "name": "search_sam_entity",
  "arguments": {
    "name": "Bechtel",
    "state": "VA"
  }
}
```

### Response Format

```json
{
  "total": 5,
  "entities": [
    {
      "samUniqueEntityId": "079235148",
      "legalBusinessName": "BECHTEL CORPORATION",
      "entityStatus": "Active",
      "state": "VA"
    }
  ]
}
```

---

## get_usaspending_contracts

Get federal contract award history from USAspending.gov. Returns contract count, total dollars, and individual awards.

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `recipient_name` | string | No | Vendor name to search |
| `fiscal_year` | integer | No | Filter by specific fiscal year (e.g., 2024) |
| `limit` | integer | No | Maximum number of awards to return (default: 20) |

### Example Call

```json
{
  "name": "get_usaspending_contracts",
  "arguments": {
    "recipient_name": "Bechtel Corporation",
    "limit": 10
  }
}
```

### Response Format

```json
{
  "total_awards": 234,
  "total_dollars": 12500000000,
  "awards": [
    {
      "id": "FA865021C0001",
      "amount": "15000000",
      "start_date": "2021-10-01",
      "end_date": "2026-09-30",
      "agency": "Department of Defense",
      "sub_agency": "Air Force",
      "contract_type": "C",
      "description": "Architect-Engineer Services"
    }
  ]
}
```

---

## get_cpars_rating

Get CPARS (Contractor Performance Assessment Reporting System) performance rating. **Note: CPARS data requires separate government access and is not available via public API.**

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `duns` | string | Yes | 9-digit DUNS number |
| `agency` | string | No | Specific agency to filter by |

### Example Call

```json
{
  "name": "get_cpars_rating",
  "arguments": {
    "duns": "079235148"
  }
}
```

### Response Format

```json
{
  "note": "CPARS requires access at https://cparsers.gov",
  "duns": "079235148",
  "instructions": [
    "1. Register at cpars.gov",
    "2. Request agency-specific access",
    "3. Search by DUNS",
    "Ratings: Exceptional, Very Good, Satisfactory, Marginal, Unsatisfactory"
  ]
}
```

---

## vendor_report

Generate a comprehensive vendor reliability report combining all available data sources. This is the main tool for getting a complete picture of a vendor.

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vendor_name` | string | No | Company name |
| `duns` | string | No | 9-digit DUNS number |

**Note**: At least one of `vendor_name` or `duns` must be provided.

### Example Call

```json
{
  "name": "vendor_report",
  "arguments": {
    "vendor_name": "Bechtel Corporation",
    "duns": "079235148"
  }
}
```

### Response Format

```json
{
  "vendor": "Bechtel Corporation",
  "sources": {
    "sam_gov": {
      "samUniqueEntityId": "079235148",
      "legalBusinessName": "BECHTEL CORPORATION",
      "entityStatus": "Active"
    },
    "usaspending": {
      "total_awards": 234,
      "total_dollars": 12500000000
    },
    "cpars": {
      "note": "CPARS requires access..."
    }
  },
  "reliability_score": {
    "score": 85,
    "grade": "A",
    "factors": [
      ["SAM: Not excluded", 20],
      ["CPARS: Exceptional", 15],
      ["Contracts: 234 ($12.5M)", 15],
      ["BBB: A+", 25],
      ["SEC: 15 annual reports", 10]
    ],
    "max_score": 100
  }
}
```

---

## check_bbb_rating

Get Better Business Bureau rating and complaint data. **Note: BBB scraping is currently blocked by Cloudflare. The tool returns alternative review sources.**

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `business_name` | string | Yes | Name of the business |
| `city` | string | No | Business city |
| `state` | string | No | US state code |

### Example Call

```json
{
  "name": "check_bbb_rating",
  "arguments": {
    "business_name": "Bechtel Corporation",
    "city": "Reston",
    "state": "VA"
  }
}
```

### Response Format

```json
{
  "note": "BBB scraping failed, using alternatives",
  "error": "403 Forbidden",
  "business": "Bechtel Corporation",
  "alternatives": [
    {"name": "Trustpilot", "url": "https://www.trustpilot.com"},
    {"name": "Google Business Reviews", "url": "https://business.google.com"},
    {"name": "Yelp", "url": "https://www.yelp.com"},
    {"name": "G2", "url": "https://www.g2.com"}
  ]
}
```

---

## check_sec_filings

Check SEC EDGAR filings for financial health indicators. Requires SEC_API_KEY from sec-api.io (free tier available).

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `company_name` | string | No | Company name to search |
| `cik` | string | No | SEC Central Index Key (10-digit, zero-padded) |

**Note**: Provide either `company_name` OR `cik`, not both.

### Example Call (by company name)

```json
{
  "name": "check_sec_filings",
  "arguments": {
    "company_name": "Bechtel"
  }
}
```

### Example Call (by CIK)

```json
{
  "name": "check_sec_filings",
  "arguments": {
    "cik": "0000013772"
  }
}
```

### Response Format

```json
{
  "found": true,
  "vendor": "Bechtel",
  "matches": [
    {
      "cik": "0000013772",
      "name": "BECHTEL GROUP INC",
      "ticker": "BCH"
    }
  ],
  "count": 1
}
```

Or when querying filings directly:

```json
{
  "found": true,
  "cik": "0000320193",
  "ticker": "AAPL",
  "filings": [
    {
      "form": "10-K",
      "date": "2024-10-30",
      "description": "Annual report"
    },
    {
      "form": "8-K",
      "date": "2024-09-27",
      "description": "Current report"
    }
  ]
}
```

---

## get_litigation

Get information about court records for litigation history. **Note: Court records require PACER (paid) or CourtListener API access. This tool returns alternatives.**

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `company_name` | string | Yes | Company name to search |
| `state` | string | No | Specific state to limit search |

### Example Call

```json
{
  "name": "get_litigation",
  "arguments": {
    "company_name": "Bechtel Corporation"
  }
}
```

### Response Format

```json
{
  "note": "Court records require PACER (paid) or CourtListener API",
  "company": "Bechtel Corporation",
  "alternatives": [
    "CourtListener (free): https://www.courtlistener.com/api/",
    "PACER (paid): https://pacer.uscourts.gov",
    "Justia (free): https://law.justia.com/cases"
  ]
}
```

---

## Error Responses

All tools may return errors in the following format:

```json
{
  "error": "Error description",
  "detail": "Additional error details if available"
}
```

Common errors:
- `"SAM_API_KEY not set"` - Missing SAM.gov API key
- `"SEC_API_KEY not set and SEC.gov is blocked"` - Missing SEC API key
- `"Rate limited - try again later"` - API rate limit exceeded
- `"Status 403"` - Access forbidden (BBB Cloudflare blocking)
