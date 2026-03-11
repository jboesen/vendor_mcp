# Vendor Reliability MCP - Testing Guide

Ask me to run a vendor report: "vendor report for [company name]"

---

## Scoring Algorithm

### When SAM is available:
- SAM registration (primary): +25 max
- CPARS rating: +15 max
- Contract history: +15 max
- BBB rating: +20 max
- SEC filings: +10 max

### When SAM is NOT available:
- Contract dollars (primary differentiator): +25 max
- Contract volume: +8 max
- Agency diversity: +6 max
- Recent activity: +6 max
- Average contract size: +4 max
- SEC filings: +10 max
- BBB rating: +15 max

**Grade:** A (80+), B (60-79), C (40-59), D (20-39), F (<20)

---

## Current Status

| Source | Status |
|--------|--------|
| USAspending | ✅ Working |
| SAM.gov | ⚠️ Rate limited |
| SEC | ⚠️ Rate limited |
| BBB | ❌ Blocked |

---

## Example Results (SAM unavailable)

| Vendor | Score | Grade | Primary Factor |
|--------|-------|-------|---------------|
| Bechtel | 33 | D | $17.6B (25pts) |
| Lockheed | 18 | F | $134M (12pts) |
| Target | 16 | F | $108M (12pts) |
| Microsoft | 14 | F | $28M (8pts) |
| Google | 11 | F | $6M (5pts) |
| Apple | 8 | F | $630K (2pts) |

---

## Try It

Message me: "vendor report for [company]"
