#!/bin/bash
# Vendor Reliability MCP Server runner
cd /root/.openclaw/workspace/vendor_reliability_mcp
source venv/bin/activate
exec ./venv/bin/vendor-reliability-mcp
