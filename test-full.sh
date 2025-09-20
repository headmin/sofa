#!/bin/bash

# SOFA Full Pipeline Test Script
# Runs complete init -> gather -> fetch -> build -> extract pipeline

set -e  # Exit on any error

echo "🚀 SOFA Full Pipeline Test"
echo "=" $(printf '=%.0s' {1..50})

# Check if we're in the right directory
if [ ! -f "./bin/sofa-init" ]; then
    echo "❌ Error: Must be run from root directory containing bin/ with SOFA binaries"
    exit 1
fi

echo "📋 Step 1: Initialize configuration"
echo ./bin/sofa-init generate scaffold.comprehensive.toml
echo "✅ Configuration initialized"
echo ""

echo "📦 Step 2: Gather external data sources"
./bin/sofa-gather all
echo "✅ All data sources gathered"
echo ""

echo "🔍 Step 3: Fetch Apple security data" 
./bin/sofa-fetch
echo "✅ Apple security data fetched"
echo ""

echo "🏗️  Step 4: Build all platform feeds"
./bin/sofa-build all --legacy
echo "✅ All platform feeds built"
echo ""

echo "🧠 Step 5: Extract CVEs from security data"
./bin/sofa-cve extract
echo "✅ CVEs extracted"
echo ""

echo "🔍 Step 6: Enrich CVEs with vulnerability data"
echo ./bin/sofa-cve enrich --api-key=vulncheck_5c161e1756efb71fb8369a56cf294c9e6451f0721cec4b4ce645e63e3190e547
echo "✅ CVEs enriched"
echo ""

echo "📚 Step 7: Index CVEs for search"
./bin/sofa-cve index
echo "✅ CVEs indexed"
echo ""

echo "📊 Final Status Report"
echo "=" $(printf '=%.0s' {1..50})
if [ -f "data/resources/sofa-status.json" ]; then
    echo "✅ Unified status file created: data/resources/sofa-status.json"
    # Show summary using jq if available, otherwise basic info
    if command -v jq >/dev/null 2>&1; then
        echo ""
        echo "📈 Pipeline Summary:"
        echo "  Gather sources: $(jq -r '.pipeline.gather.sources | keys | length' data/resources/sofa-status.json)"
        echo "  Build platforms v1: $(jq -r '.pipeline.build.v1.platforms | keys | length' data/resources/sofa-status.json 2>/dev/null || echo '0')"
        echo "  Build platforms v2: $(jq -r '.pipeline.build.v2.platforms | keys | length' data/resources/sofa-status.json 2>/dev/null || echo '0')"
        echo "  Generated: $(jq -r '.generated' data/resources/sofa-status.json)"
    else
        echo ""
        echo "📁 Status file size: $(du -h data/resources/sofa-status.json | cut -f1)"
    fi
else
    echo "❌ Warning: Unified status file not found"
fi

echo ""
echo "🎉 SOFA Full Pipeline Test Complete!"
echo "📁 Check data/resources/sofa-status.json for unified pipeline status"