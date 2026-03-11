# Vendor Reliability MCP - Executive Summary

## What is This MCP?

The **Vendor Reliability MCP** is a Model Context Protocol server that aggregates publicly available data to assess contractor and vendor reliability. It provides a unified interface to query government databases, financial filings, and business ratings to help determine if a vendor is trustworthy for government contracts or business partnerships.

## Who is It For?

- **Government contracting officers** evaluating vendors for RFPs
- ** procurement teams** assessing supplier risk
- **Compliance officers** checking for exclusions or past performance issues
- **Business analysts** researching vendor financial health
- **MCP-powered AI assistants** needing vendor due diligence capabilities

## What Data Sources Does It Use?

| Source | Status | API Key Required | Data Retrieved |
|--------|--------|------------------|----------------|
| **USAspending.gov** | ✅ Working | No | Federal contract awards, spending amounts |
| **SAM.gov** | ✅ Working | Yes (free) | Entity registration, exclusion status |
| **SEC EDGAR** | ✅ Working | Yes (free tier) | 10-K filings, financial disclosures |
| **CPARS** | ❌ Stub | Yes (gov-only) | Performance ratings |
| **BBB** | ❌ Stub | No | Business ratings, complaints |
| **Court Records** | ⚠️ Alternative | No | Litigation alternatives provided |

## What Problems Does It Solve?

### 1. **Vendor Exclusion Checking**
Quickly determine if a vendor is debarred or suspended from federal contracting via SAM.gov exclusion database.

### 2. **Past Performance Analysis**
Pull historical contract data from USAspending.gov to see a vendor's federal contracting history, total dollars received, and award counts.

### 3. **Financial Health Assessment**
Check SEC EDGAR for 10-K annual reports (indicating public company status) and bankruptcy filings.

### 4. **Composite Reliability Scoring**
Generate a weighted reliability score (0-100) combining all available data sources into a letter grade (A-F).

### 5. **Single-Vendor Report**
Get a comprehensive report by vendor name or DUNS number that aggregates all available data sources automatically.

## Quick Start

```bash
# Install
pip install -e .

# Optional: Add API keys to .env
SEC_API_KEY=your_sec_api_key  # Free at sec-api.io
SAM_API_KEY=your_sam_key      # Free at sam.gov

# Run the server
vendor-reliability-mcp
```

## Reliability Score Breakdown

The composite score ranges from 0-100:
- **A (80-100)**: Highly reliable vendor
- **B (60-79)**: Good reliability with some concerns
- **C (40-59)**: Moderate risk
- **D (20-39)**: High risk
- **F (0-19)**: Do not use

See [API_REFERENCE.md](API_REFERENCE.md) for detailed tool documentation.
