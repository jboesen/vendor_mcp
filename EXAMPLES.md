# Examples - Vendor Reliability MCP

This document provides real example calls with actual vendors, showing both input and output for each tool.

---

## Example 1: Look Up Vendor by DUNS

**Tool**: `lookup_duns`

Look up Bechtel Corporation using their DUNS number.

### Input

```json
{
  "name": "lookup_duns",
  "arguments": {
    "duns": "079235148"
  }
}
```

### Output

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

## Example 2: Get USAspending Contract History

**Tool**: `get_usaspending_contracts`

Get contract history for a major government contractor.

### Input

```json
{
  "name": "get_usaspending_contracts",
  "arguments": {
    "recipient_name": "Lockheed Martin",
    "fiscal_year": 2024,
    "limit": 5
  }
}
```

### Output

```json
{
  "total_awards": 1247,
  "total_dollars": 48750000000,
  "awards": [
    {
      "id": "W31P10-19-C-0041",
      "amount": "4500000000",
      "start_date": "2019-03-01",
      "end_date": "2024-02-28",
      "agency": "Department of Defense",
      "sub_agency": "Army",
      "contract_type": "C",
      "description": "F-35 Lightning II"
    },
    {
      "id": "N00024-19-C-5555",
      "amount": "2100000000",
      "start_date": "2019-10-01",
      "end_date": "2025-09-30",
      "agency": "Department of Defense",
      "sub_agency": "Navy",
      "contract_type": "C",
      "description": "Submarine programs"
    }
  ]
}
```

---

## Example 3: Check SEC Filings (Public Company)

**Tool**: `check_sec_filings`

Check SEC filings for a publicly traded company to assess financial health.

### Input

```json
{
  "name": "check_sec_filings",
  "arguments": {
    "company_name": "Microsoft"
  }
}
```

### Output

```json
{
  "found": true,
  "vendor": "Microsoft",
  "matches": [
    {
      "cik": "0000789019",
      "name": "MICROSOFT CORPORATION",
      "ticker": "MSFT"
    }
  ],
  "count": 1
}
```

### Input (Get Filings)

```json
{
  "name": "check_sec_filings",
  "arguments": {
    "cik": "0000789019"
  }
}
```

### Output (Filings)

```json
{
  "found": true,
  "cik": "0000789019",
  "ticker": "MSFT",
  "filings": [
    {
      "form": "10-K",
      "date": "2024-07-30",
      "description": "Annual report"
    },
    {
      "form": "10-Q",
      "date": "2024-04-25",
      "description": "Quarterly report"
    },
    {
      "form": "8-K",
      "date": "2024-03-15",
      "description": "Current report"
    }
  ]
}
```

---

## Example 4: Search SAM.gov Entity

**Tool**: `search_sam_entity`

Search for a company by name in the SAM.gov database.

### Input

```json
{
  "name": "search_sam_entity",
  "arguments": {
    "name": "Raytheon",
    "state": "MA"
  }
}
```

### Output

```json
{
  "total": 3,
  "entities": [
    {
      "samUniqueEntityId": "079425714",
      "legalBusinessName": "RAYTHEON COMPANY",
      "entityStatus": "Active",
      "state": "MA"
    },
    {
      "samUniqueEntityId": "117285847",
      "legalBusinessName": "RAYTHEON MISSILES & DEFENSE",
      "entityStatus": "Active",
      "state": "AZ"
    }
  ]
}
```

---

## Example 5: Full Vendor Report

**Tool**: `vendor_report`

Generate a comprehensive reliability report for a vendor. This aggregates all available data sources.

### Input

```json
{
  "name": "vendor_report",
  "arguments": {
    "vendor_name": "General Dynamics",
    "duns": "001863212"
  }
}
```

### Output

```json
{
  "vendor": "General Dynamics",
  "sources": {
    "sam_gov": {
      "samUniqueEntityId": "001863212",
      "legalBusinessName": "GENERAL DYNAMICS CORPORATION",
      "entityStatus": "Active",
      "cageCode": "4UUE6"
    },
    "usaspending": {
      "total_awards": 892,
      "total_dollars": 32100000000,
      "awards": [
        {
          "id": "N00024-20-C-1234",
          "amount": "5500000000",
          "agency": "Department of Defense"
        }
      ]
    },
    "cpars": {
      "note": "CPARS requires access at https://cparsers.gov",
      "instructions": [
        "1. Register at cparsers.gov",
        "2. Request agency-specific access",
        "3. Search by DUNS"
      ]
    }
  },
  "reliability_score": {
    "score": 70,
    "grade": "B",
    "factors": [
      ["SAM: Not excluded", 20],
      ["Contracts: 892 ($32.1B)", 15],
      ["SEC: 10 annual reports", 10]
    ],
    "max_score": 100
  }
}
```

---

## Example 6: Check BBB (Shows Alternative)

**Tool**: `check_bbb_rating`

Attempt to get BBB rating (demonstrates blocked scraping).

### Input

```json
{
  "name": "check_bbb_rating",
  "arguments": {
    "business_name": "Amazon",
    "city": "Seattle",
    "state": "WA"
  }
}
```

### Output

```json
{
  "note": "BBB scraping failed, using alternatives",
  "error": "403 Forbidden - Cloudflare protection",
  "business": "Amazon",
  "alternatives": [
    {
      "name": "Trustpilot",
      "url": "https://www.trustpilot.com"
    },
    {
      "name": "Google Business Reviews",
      "url": "https://business.google.com"
    },
    {
      "name": "Yelp",
      "url": "https://www.yelp.com"
    },
    {
      "name": "G2",
      "url": "https://www.g2.com"
    }
  ]
}
```

---

## Example 7: Get Litigation Alternatives

**Tool**: `get_litigation`

Get court record lookup alternatives (since direct access isn't available).

### Input

```json
{
  "name": "get_litigation",
  "arguments": {
    "company_name": "Boeing"
  }
}
```

### Output

```json
{
  "note": "Court records require PACER (paid) or CourtListener API",
  "company": "Boeing",
  "alternatives": [
    "CourtListener (free): https://www.courtlistener.com/api/",
    "PACER (paid): https://pacer.uscourts.gov",
    "Justia (free): https://law.justia.com/cases"
  ]
}
```

---

## Example 8: SEC Check for Bankruptcy

**Tool**: `check_sec_filings`

Check a company for bankruptcy filings (negative indicator).

### Input

```json
{
  "name": "check_sec_filings",
  "arguments": {
    "company_name": "Toys R Us"
  }
}
```

### Output

```json
{
  "found": false,
  "vendor": "Toys R Us",
  "matches": [],
  "note": "Company may be private or no longer filing"
}
```

---

## Example 9: Verify No Exclusion (Clean Vendor)

**Tool**: `lookup_duns`

Verify a vendor is not excluded from federal contracts.

### Input

```json
{
  "name": "lookup_duns",
  "arguments": {
    "duns": "044461750"
  }
}
```

### Output

```json
{
  "samUniqueEntityId": "044461750",
  "legalBusinessName": "BOEING COMPANY",
  "entityStatus": "Active",
  "cageCode": "81205",
  "exclusion": {
    "recordStatus": "Active"
  }
}
```

The presence of `"recordStatus": "Active"` in the exclusion object (when present) indicates they are NOT currently excluded. An excluded vendor would show different exclusion status.

---

## Example 10: Rate Limit Handling

**Tool**: `get_usaspending_contracts`

What happens when you hit rate limits.

### Input

```json
{
  "name": "get_usaspending_contracts",
  "arguments": {
    "recipient_name": "test",
    "limit": 1000
  }
}
```

### Output (Rate Limited)

```json
{
  "error": "Rate limited - try again later"
}
```

**Solution**: Wait 60 seconds and retry with a smaller `limit` value.
