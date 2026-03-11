"""
Vendor Reliability MCP Server
Public data sources for contractor/vendor reliability assessment
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
import argparse
from dotenv import load_dotenv

# Load .env from package directory
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)

from mcp.server import Server
from mcp.types import Tool, TextContent

# Import scrapers
from .scrapers import sam_gov, usaspending, bbb, sec_edgar


class VendorReliabilityServer:
    """MCP server for vendor reliability data"""
    
    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.server = Server("vendor-reliability-mcp")
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="lookup_duns",
                    description="Look up vendor by DUNS number",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "duns": {"type": "string", "description": "9-digit DUNS number"}
                        },
                        "required": ["duns"]
                    }
                ),
                Tool(
                    name="search_sam_entity",
                    description="Search SAM.gov entity registration",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "name": {"type": "string", "description": "Company name to search"},
                            "state": {"type": "string", "description": "US state code"}
                        }
                    }
                ),
                Tool(
                    name="get_usaspending_contracts",
                    description="Get contract history from USAspending.gov",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "recipient_name": {"type": "string"},
                            "fiscal_year": {"type": "integer"},
                            "limit": {"type": "integer", "default": 20}
                        }
                    }
                ),
                Tool(
                    name="get_cpars_rating",
                    description="Get CPARS performance rating",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "duns": {"type": "string"},
                            "agency": {"type": "string"}
                        }
                    }
                ),
                Tool(
                    name="vendor_report",
                    description="Generate vendor reliability report",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "vendor_name": {"type": "string"},
                            "duns": {"type": "string"}
                        }
                    }
                ),
                Tool(
                    name="check_bbb_rating",
                    description="Get BBB rating and complaints",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "business_name": {"type": "string"},
                            "city": {"type": "string"},
                            "state": {"type": "string"}
                        }
                    }
                ),
                Tool(
                    name="check_sec_filings",
                    description="Check SEC EDGAR filings for financial health",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "company_name": {"type": "string"},
                            "cik": {"type": "string"}
                        }
                    }
                ),
                Tool(
                    name="get_litigation",
                    description="Check court records for lawsuits",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "company_name": {"type": "string"},
                            "state": {"type": "string"}
                        }
                    }
                ),
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict) -> List[TextContent]:
            try:
                result = await self._handle_tool(name, arguments)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]
    
    async def _handle_tool(self, name: str, args: Dict) -> Any:
        if name == "lookup_duns":
            return await sam_gov.lookup_duns(args["duns"])
        elif name == "search_sam_entity":
            return await sam_gov.search_entity(args.get("name"), args.get("state"))
        elif name == "get_usaspending_contracts":
            return await usaspending.get_contracts(
                args.get("recipient_name"),
                args.get("fiscal_year"),
                args.get("limit", 20)
            )
        elif name == "get_cpars_rating":
            return await sam_gov.get_cpars(args["duns"], args.get("agency"))
        elif name == "vendor_report":
            return await self._generate_report(args)
        elif name == "check_bbb_rating":
            return await bbb.get_bbb_rating(
                args.get("business_name", ""),
                args.get("city"),
                args.get("state")
            )
        elif name == "check_sec_filings":
            if args.get("cik"):
                return await sec_edgar.get_company_filings(args["cik"])
            elif args.get("company_name"):
                return await sec_edgar.search_company(args["company_name"])
            return {"error": "Need company_name or cik"}
        elif name == "get_litigation":
            return {
                "note": "Court records require PACER (paid) or CourtListener API",
                "company": args.get("company_name"),
                "alternatives": [
                    "CourtListener (free): https://www.courtlistener.com/api/",
                    "PACER (paid): https://pacer.uscourts.gov",
                    "Justia (free): https://law.justia.com/cases"
                ]
            }
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def _generate_report(self, args: Dict) -> Dict:
        """Generate composite vendor report"""
        name = args.get("vendor_name", "")
        duns = args.get("duns", "")
        
        if not name and not duns:
            return {
                "error": "Either vendor_name or duns is required",
                "vendor": None,
                "sources": {},
                "reliability_score": None
            }
        
        report = {"vendor": name or duns, "sources": {}}
        
        sam_data = {}
        sam_search_data = {}
        
        if duns:
            sam_data = await sam_gov.lookup_duns(duns)
        
        if name:
            sam_search_data = await sam_gov.search_entity(name)
            usaspend = await usaspending.get_contracts(name)
        elif duns:
            usaspend = await usaspending.get_contracts(duns)
        else:
            usaspend = {"total_awards": 0, "total_dollars": 0, "awards": []}
        
        cpars = await sam_gov.get_cpars(duns) if duns else {"note": "No DUNS provided"}
        
        sec_data = {}
        if name:
            sec_search = await sec_edgar.search_company(name)
            if sec_search.get("matches"):
                first_match = sec_search["matches"][0]
                cik = first_match.get("cik")
                if cik:
                    sec_data = await sec_edgar.get_company_filings(cik)
        
        bbb_data = {}
        if name:
            bbb_data = await bbb.get_bbb_rating(name)
        
        report["sources"]["sam_gov"] = sam_data
        report["sources"]["sam_gov_search"] = sam_search_data
        report["sources"]["usaspending"] = usaspend
        report["sources"]["cpars"] = cpars
        report["sources"]["sec_edgar"] = sec_data
        report["sources"]["bbb"] = bbb_data
        
        score = self._calculate_score(sam_data, sam_search_data, usaspend, cpars, bbb_data, sec_data)
        report["reliability_score"] = score
        
        return report
    
    def _calculate_score(self, sam: Dict, sam_search: Dict, usa: Dict, cpars: Dict, bbb_data: Dict, sec_data: Dict = None) -> Dict:
        """Calculate composite vendor reliability score - different algorithms based on SAM availability"""
        factors = []
        
        # Check if SAM is available
        entity_list = sam_search.get("entityList", [])
        sam_available = bool(entity_list and len(entity_list) > 0)
        
        dollars = usa.get("total_dollars", 0)
        count = usa.get("total_awards", 0)
        
        # ============ SAM AVAILABLE PATH ============
        if sam_available:
            # SAM is working - use SAM as primary signal
            active_entities = [e for e in entity_list if e.get("registrationStatus") == "Active"]
            if active_entities:
                factors.append(("SAM: Active registration", 25))
            else:
                excluded = any(e.get("exclusionStatus") == "Y" for e in entity_list)
                if excluded:
                    factors.append(("SAM: EXCLUDED", -30))
                else:
                    factors.append(("SAM: Entities found", 10))
            
            # CPARS ratings
            rating = cpars.get("rating", "")
            if rating == "Exceptional":
                factors.append(("CPARS: Exceptional", 15))
            elif rating == "Very Good":
                factors.append(("CPARS: Very Good", 10))
            elif rating == "Satisfactory":
                factors.append(("CPARS: Satisfactory", 5))
            elif rating in ["Marginal", "Unsatisfactory"]:
                factors.append((f"CPARS: {rating}", -20))
            
            # Contract history
            if count > 50:
                factors.append((f"Contracts: {count} (${dollars/1e9:.1f}B)", 15))
            elif count > 10:
                factors.append((f"Contracts: {count} (${dollars/1e6:.0f}M)", 10))
            elif count > 0:
                factors.append((f"Contracts: {count}", 5))
            
            # BBB
            if bbb_data.get("found"):
                rating = bbb_data.get("rating", "")
                rating_map = {"A+": 20, "A": 18, "B+": 14, "B": 10, "C+": 6, "C": 4, "D": 2, "F": 0}
                if rating in rating_map:
                    factors.append((f"BBB: {rating}", rating_map[rating]))
            
            # SEC
            if sec_data and sec_data.get("filings"):
                k10s = [f for f in sec_data.get("filings", []) if f.get("form") == "10-K"]
                if len(k10s) >= 5:
                    factors.append((f"Public: {len(k10s)} 10-Ks", 10))
                elif len(k10s) > 0:
                    factors.append((f"Public: {len(k10s)} 10-Ks", 5))
        
        # ============ SAM NOT AVAILABLE PATH ============
        else:
            # SAM is down - weight everything else heavily to match SAM-available distribution
            # Target: $10B+ → 70-85 (A), $1B+ → 55-70 (B), $100M+ → 40-55 (C), <$100M → D/F
            
            # Contract $ (heaviest weight - determines base score)
            if dollars >= 10e9:
                base_score = 60  # $10B+ → 68-80 with bonuses (A)
                factors.append((f"Major govt contractor: ${dollars/1e9:.1f}B", base_score))
            elif dollars >= 5e9:
                base_score = 56  # $5-10B → 62-72 (A)
                factors.append((f"Major govt contractor: ${dollars/1e9:.1f}B", base_score))
            elif dollars >= 2e9:
                base_score = 52  # $2-5B → 58-68 (A/B)
                factors.append((f"Major govt contractor: ${dollars/1e9:.1f}B", base_score))
            elif dollars >= 1e9:
                base_score = 48  # $1-2B → 52-62 (B) - pushed higher
                factors.append((f"Large govt contractor: ${dollars/1e9:.1f}B", base_score))
            elif dollars >= 500e6:
                base_score = 40
                factors.append((f"Established: ${dollars/1e6:.0f}M", base_score))
            elif dollars >= 200e6:
                base_score = 34
                factors.append((f"Established: ${dollars/1e6:.0f}M", base_score))
            elif dollars >= 100e6:
                base_score = 28
                factors.append((f"Moderate: ${dollars/1e6:.0f}M", base_score))
            elif dollars >= 50e6:
                base_score = 22
                factors.append((f"Small: ${dollars/1e6:.0f}M", base_score))
            elif dollars >= 10e6:
                base_score = 14
                factors.append((f"Small: ${dollars/1e6:.0f}M", base_score))
            elif dollars >= 1e6:
                base_score = 8
                factors.append((f"Limited: ${dollars/1e6:.0f}M", base_score))
            elif dollars > 0:
                base_score = 3
                factors.append((f"Minimal: ${dollars/1e3:.0f}K", base_score))
            else:
                base_score = 0
                factors.append(("No government contracts", 0))
            
            # Add bonuses on top of base
            # Volume bonus
            if count >= 100:
                factors.append((f"High volume: {count} contracts", 10))
            elif count >= 50:
                factors.append((f"Good volume: {count} contracts", 7))
            elif count >= 20:
                factors.append((f"Volume: {count} contracts", 4))
            
            # Agency diversity bonus
            agencies = set(a.get("agency") for a in usa.get("awards", []) if a.get("agency"))
            if len(agencies) >= 5:
                factors.append((f"Very diverse: {len(agencies)} agencies", 8))
            elif len(agencies) >= 3:
                factors.append((f"Diverse: {len(agencies)} agencies", 5))
            elif len(agencies) >= 2:
                factors.append((f"Multi-agency", 2))
            
            # Recent activity bonus
            recent = [a for a in usa.get("awards", []) if a.get("start_date", "").startswith(("2024", "2025", "2026"))]
            if len(recent) >= 15:
                factors.append((f"Very active: {len(recent)} recent", 8))
            elif len(recent) >= 10:
                factors.append((f"Active: {len(recent)} recent", 6))
            elif len(recent) >= 5:
                factors.append((f"Active: {len(recent)} recent", 4))
            
            # Contract size bonus
            if count > 0:
                avg = dollars / count
                if avg >= 100e6:
                    factors.append(("Tier-1 contracts", 5))
                elif avg >= 50e6:
                    factors.append(("Large avg", 3))
            
            # SEC bonus (if available)
            if sec_data and sec_data.get("filings"):
                k10s = [f for f in sec_data.get("filings", []) if f.get("form") == "10-K"]
                if len(k10s) >= 5:
                    factors.append((f"Public company: {len(k10s)} 10-Ks", 8))
                elif len(k10s) > 0:
                    factors.append((f"Public: {len(k10s)} reports", 4))
                
                banks = sec_data.get("bankruptcy_filings", [])
                if len(banks) == 0:
                    factors.append(("No bankruptcy", 3))
        
        total = sum(v for _, v in factors)
        total = max(0, min(100, total))
        
        return {
            "score": total,
            "grade": "A" if total >= 80 else "B" if total >= 60 else "C" if total >= 40 else "D" if total >= 20 else "F",
            "factors": factors,
            "max_score": 100
        }
    
    def run(self):
        import asyncio
        import sys
        from mcp.server.stdio import stdio_server
        
        async def run_server():
            print("Running stdio server...", flush=True)
            async with stdio_server() as (read_stream, write_stream):
                print("About to run MCP server...", flush=True)
                await self.server.run(
                    read_stream, write_stream,
                    self.server.create_initialization_options()
                )
        
        print("Calling asyncio.run...", flush=True)
        asyncio.run(run_server())


def main():
    import sys
    parser = argparse.ArgumentParser(description="Vendor Reliability MCP Server")
    parser.add_argument("--cache", default="./cache")
    args = parser.parse_args()
    
    server = VendorReliabilityServer(cache_dir=args.cache)
    print("Starting Vendor Reliability MCP Server...", flush=True)
    sys.stdout.flush()
    server.run()


if __name__ == "__main__":
    main()
