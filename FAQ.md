# Frequently Asked Questions - Vendor Reliability MCP

## General Questions

### What is the Vendor Reliability MCP?

The Vendor Reliability MCP is a Model Context Protocol server that aggregates public data from government databases (SAM.gov, USAspending.gov, SEC EDGAR) and business ratings (BBB) to assess contractor and vendor reliability. It provides a unified interface for AI assistants to perform vendor due diligence.

### Who should use this MCP?

- Government contracting officers evaluating vendors
- Procurement teams assessing supplier risk
- Compliance officers checking for exclusions or past performance issues
- Business analysts researching vendor financial health

---

## API Keys

### Do I need API keys?

**USAspending.gov**: No API key required - works out of the box.

**SAM.gov**: Yes, a free API key is required. Register at [sam.gov](https://sam.gov).

**SEC EDGAR**: Yes, a free API key is recommended. Register at [sec-api.io](https://sec-api.io/signup/free) (free tier: 100 calls/month).

**BBB**: No API key, but scraping is blocked by Cloudflare protection.

### How do I get a SAM.gov API key?

1. Go to [sam.gov](https://sam.gov)
2. Click "Sign In" → Create an account (or use existing login)
3. Once logged in, go to "My SAM" → "API Key Management"
4. Request an API key (free for public data access)
5. Copy the key and add to your `.env` file as `SAM_API_KEY=your_key`

### How do I get an SEC API key?

1. Go to [sec-api.io](https://sec-api.io/signup/free)
2. Create a free account
3. Navigate to your dashboard to find your API key
4. Copy the key and add to your `.env` file as `SEC_API_KEY=your_key`

The free tier provides 100 API calls per month, which is sufficient for most use cases.

### Where do I store the API keys?

Create a `.env` file in the `vendor_reliability_mcp` directory:

```
SAM_API_KEY=your_sam_key_here
SEC_API_KEY=your_sec_key_here
```

The server automatically loads these from the `.env` file on startup.

---

## Rate Limits

### What's the rate limit?

| Source | Rate Limit |
|--------|------------|
| USAspending.gov | Varies; returns 429 if exceeded |
| SAM.gov | Based on your API key tier |
| SEC EDGAR (sec-api.io) | 100 calls/month (free tier) |
| BBB | N/A (scraping blocked) |

If you hit a rate limit, wait a minute and try again.

---

## Reliability Score

### What does the reliability score mean?

The reliability score is a composite metric (0-100) combining data from all available sources:

| Grade | Score Range | Interpretation |
|-------|-------------|----------------|
| A | 80-100 | Highly reliable vendor |
| B | 60-79 | Good reliability with minor concerns |
| C | 40-59 | Moderate risk |
| D | 20-39 | High risk |
| F | 0-19 | Do not use |

### How is the score calculated?

**SAM.gov (max 35 points)**
- Not excluded from federal contracts: +20
- Excluded (debarred/suspended): -50
- Exceptional CPARS rating: +15
- Very Good CPARS: +10
- Satisfactory CPARS: +5
- Marginal/Unsatisfactory CPARS: -20

**USAspending.gov (max 15 points)**
- 50+ contracts: +15
- 10-50 contracts: +10
- 1-9 contracts: +5

**BBB (max 30 points)**
- Rating (0-5 × 5): up to +25
- BBB Accredited: +5
- 10+ complaints resolved in 12 months: +5

**SEC EDGAR (max 20 points)**
- Has 10-K annual reports: +10
- No bankruptcy filings: +10
- Any bankruptcy filings: -30

---

## Data Sources

### Why is BBB not working?

BBB (Better Business Bureau) blocks automated scraping with Cloudflare protection. There is no free public API available. The tool returns alternative review sources (Trustpilot, Google Reviews, Yelp, G2) instead.

### Why is CPARS not returning data?

CPARS (Contractor Performance Assessment Reporting System) is a government-only system that requires:
1. A government email address
2. Registration at [cpars.gov](https://cparsers.gov)
3. Agency-specific access permissions

The tool provides instructions on how to access CPARS manually.

### What does "Exclusions" status mean?

Exclusion status from SAM.gov indicates whether a vendor is:
- **Not excluded**: Allowed to receive federal contracts (positive indicator)
- **Excluded/Debarred**: Prohibited from receiving federal contracts (major red flag)

### What do SEC filings tell me?

SEC EDGAR filings provide financial health indicators:
- **10-K (Annual Report)**: Company is publicly traded, requires audited financials
- **10-Q (Quarterly Report)**: Regular public company reporting
- **8-K (Current Report)**: Material events
- **Bankruptcy filings**: Major financial distress indicator

---

## Troubleshooting

### Why does the tool return "SAM_API_KEY not set"?

You need to:
1. Get a free API key from [sam.gov](https://sam.gov)
2. Add it to your `.env` file as `SAM_API_KEY=your_key`
3. Restart the MCP server

### Why does SEC search return no results?

Possible causes:
1. **No SEC_API_KEY**: Set up your key from [sec-api.io](https://sec-api.io)
2. **Company is private**: Private companies don't file with SEC
3. **Name mismatch**: Try alternative spellings or use CIK directly
4. **Rate limit hit**: Wait and try again

### Why am I getting empty results for USAspending?

- Check the spelling of the vendor name
- Try searching by DUNS number instead
- Some vendors may not have federal contracts

### Why does the vendor report show partial data?

The report only includes data from sources that are working:
- If you don't have SAM_API_KEY, SAM.gov data won't appear
- If you don't have SEC_API_KEY, SEC filings won't appear
- BBB and CPARS are stubs and always return alternatives

---

## Technical Questions

### What is a DUNS number?

DUNS (Data Universal Numbering System) is a 9-digit identifier assigned by Dun & Bradstreet. It's commonly used to identify businesses in government contracting. SAM.gov now uses UEI (Unique Entity Identifier) instead, but DUNS is still widely used.

### What is a CIK?

CIK (Central Index Key) is a 10-digit number assigned by the SEC to identify companies in EDGAR filings. CIKs must be zero-padded to 10 digits when querying (e.g., `0000320193` for Apple).

### How do I find a company's CIK?

Use the `check_sec_filings` tool with the company name, or search manually at [sec.gov/cgi-bin/browse-edgar?action=getcompany](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany).

### Can I use this for state-level vendors?

This MCP focuses on federal data sources. For state-level vendor checks:
- State-specific SAM.gov data may be available
- State court records vary by state
- State business registrations vary by state

---

## Alternatives & Complementary Tools

### What are alternatives to BBB for business reviews?

- **Trustpilot** (https://www.trustpilot.com) - Consumer reviews
- **G2** (https://www.g2.com) - B2B software reviews
- **Yelp** (https://www.yelp.com) - Local business reviews
- **Google Business Reviews** (https://business.google.com) - Local reviews

### How do I check court records for litigation?

- **CourtListener API** (free): https://www.courtlistener.com/api/
- **PACER** (paid): https://pacer.uscourts.gov
- **Justia** (free): https://law.justia.com/cases

### Are there other vendor reliability data sources?

- **FPDS** (Federal Procurement Data System) - Government contracts
- **System for Award Management (SAM)** - Entity registration
- **USAspending.gov** - Award spending data
- **Dun & Bradstreet** - Credit ratings (commercial, not free)
