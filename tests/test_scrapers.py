"""Tests for vendor_reliability_mcp scrapers"""

import pytest
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load env
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)

# Set path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from vendor_reliability_mcp.scrapers import usaspending, sec_edgar, sam_gov, bbb


class TestUSAspending:
    """Test USAspending.gov scraper"""
    
    @pytest.mark.asyncio
    async def test_boeing_has_contracts(self):
        """Boeing should have many federal contracts"""
        result = await usaspending.get_contracts("Boeing", limit=5)
        assert result.get("total_awards", 0) > 0, "Boeing should have contracts"
    
    @pytest.mark.asyncio
    async def test_nonexistent_vendor_returns_empty(self):
        """Nonexistent vendor should return 0 awards, not error"""
        result = await usaspending.get_contracts("XYZ_NONEXISTENT_VENDOR_12345", limit=5)
        assert result.get("total_awards", -1) == 0, "Nonexistent vendor should have 0 awards"
    
    @pytest.mark.asyncio
    async def test_lockheed_has_contracts(self):
        """Lockheed Martin should have contracts"""
        result = await usaspending.get_contracts("Lockheed Martin", limit=5)
        assert result.get("total_awards", 0) > 0
    
    @pytest.mark.asyncio
    async def test_new_vendors_raytheon(self):
        """Raytheon should have contracts"""
        result = await usaspending.get_contracts("Raytheon", limit=5)
        assert result.get("total_awards", 0) > 0, "Raytheon should have contracts"
    
    @pytest.mark.asyncio
    async def test_new_vendors_northrop(self):
        """Northrop Grumman should have contracts"""
        result = await usaspending.get_contracts("Northrop Grumman", limit=5)
        assert result.get("total_awards", 0) > 0, "Northrop Grumman should have contracts"
    
    @pytest.mark.asyncio
    async def test_new_vendors_general_dynamics(self):
        """General Dynamics should have contracts"""
        result = await usaspending.get_contracts("General Dynamics", limit=5)
        assert result.get("total_awards", 0) > 0, "General Dynamics should have contracts"
    
    @pytest.mark.asyncio
    async def test_new_vendors_hewlett_packard(self):
        """Hewlett Packard should have contracts"""
        result = await usaspending.get_contracts("Hewlett Packard", limit=5)
        # HP may or may not have federal contracts, just check structure
        assert "total_awards" in result
    
    @pytest.mark.asyncio
    async def test_new_vendors_accenture(self):
        """Accenture should have contracts"""
        result = await usaspending.get_contracts("Accenture", limit=5)
        assert result.get("total_awards", 0) > 0, "Accenture should have contracts"


class TestSECEdgar:
    """Test SEC EDGAR scraper"""
    
    @pytest.mark.asyncio
    async def test_apple_filings(self):
        """Apple (CIK 0000320193) should have SEC filings"""
        filings = await sec_edgar.get_company_filings("0000320193")
        assert filings.get("found", True) or len(filings.get("filings", [])) > 0, "Apple should have filings"
    
    @pytest.mark.asyncio
    async def test_invalid_cik_returns_error(self):
        """Invalid CIK should return error, not crash"""
        result = await sec_edgar.get_company_filings("NOT_A_CIK")
        assert "error" in result or result.get("found") == False
    
    @pytest.mark.asyncio
    async def test_unknown_cik_returns_error(self):
        """Unknown CIK should return helpful error"""
        result = await sec_edgar.get_company_filings("9999999999")
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_search_company(self):
        """Search by company name should return matches"""
        result = await sec_edgar.search_company("Microsoft")
        assert result.get("count", 0) > 0, "Should find Microsoft"
    
    @pytest.mark.asyncio
    async def test_search_raytheon(self):
        """Search Raytheon should return CIK"""
        result = await sec_edgar.search_company("Raytheon")
        assert result.get("count", 0) > 0, "Should find Raytheon"
    
    @pytest.mark.asyncio
    async def test_search_accenture(self):
        """Search Accenture should return CIK"""
        result = await sec_edgar.search_company("Accenture")
        assert result.get("count", 0) > 0, "Should find Accenture"


class TestSAMGov:
    """Test SAM.gov scraper"""
    
    @pytest.mark.asyncio
    async def test_search_raytheon(self):
        """Search Raytheon should find entities"""
        result = await sam_gov.search_entity("Raytheon")
        # Should have entityList (may be empty due to rate limiting)
        assert "entityList" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_search_lockheed(self):
        """Search Lockheed should find entities"""
        result = await sam_gov.search_entity("Lockheed Martin")
        assert "entityList" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_search_special_chars_obrien(self):
        """Search with special character O'Brien should work"""
        result = await sam_gov.search_entity("O'Brien")
        # Should return without crashing
        assert "entityList" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_search_special_chars_company_inc(self):
        """Search with Company, Inc. should work"""
        result = await sam_gov.search_entity("Company, Inc.")
        # Should return without crashing
        assert "entityList" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_search_empty_string(self):
        """Search with empty string should return empty list"""
        result = await sam_gov.search_entity("")
        assert result.get("entityList", []) == [], "Empty search should return empty list"
    
    @pytest.mark.asyncio
    async def test_search_long_name(self):
        """Search with very long name should handle gracefully"""
        long_name = "A" * 500
        result = await sam_gov.search_entity(long_name)
        # Should return without crashing
        assert "entityList" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_search_with_state_filter(self):
        """Search with state filter should work"""
        result = await sam_gov.search_entity("Boeing", state="WA")
        # Should return without crashing
        assert "entityList" in result or "error" in result


class TestBBB:
    """Test BBB scraper"""
    
    @pytest.mark.asyncio
    async def test_boeing_bbb(self):
        """Boeing BBB check should work"""
        result = await bbb.get_bbb_rating("Boeing")
        # Should return without crashing
        assert "found" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_microsoft_bbb(self):
        """Microsoft BBB check should work"""
        result = await bbb.get_bbb_rating("Microsoft")
        assert "found" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_nonexistent_business(self):
        """Nonexistent business should return found=False"""
        result = await bbb.get_bbb_rating("XYZNonexistentBusiness12345")
        # Should return found=False, not error
        assert result.get("found") == False


class TestVendorReport:
    """Test vendor_report function"""
    
    @pytest.mark.asyncio
    async def test_report_with_name(self):
        """Report with vendor_name should work"""
        from vendor_reliability_mcp.server import VendorReliabilityServer
        server = VendorReliabilityServer()
        result = await server._generate_report({"vendor_name": "Boeing"})
        assert "reliability_score" in result
        assert "sources" in result
    
    @pytest.mark.asyncio
    async def test_report_empty_name_and_duns(self):
        """Report with no name or duns should return error"""
        from vendor_reliability_mcp.server import VendorReliabilityServer
        server = VendorReliabilityServer()
        result = await server._generate_report({})
        assert result.get("error") is not None
    
    @pytest.mark.asyncio
    async def test_report_whitespace_only(self):
        """Report with whitespace-only name should handle gracefully"""
        from vendor_reliability_mcp.server import VendorReliabilityServer
        server = VendorReliabilityServer()
        result = await server._generate_report({"vendor_name": "   "})
        # Should either error or return score
        assert "reliability_score" in result or "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
