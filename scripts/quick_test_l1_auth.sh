#!/bin/bash
# Quick L1 Auth Test Script
# Run this after connecting your wallet to Extended web UI

echo "======================================================================"
echo "🧪 Quick L1 Authentication Test"
echo "======================================================================"
echo ""
echo "This will test if your Ethereum wallet is now registered with Extended."
echo ""
echo "BEFORE RUNNING THIS:"
echo "  1. Go to https://app.extended.exchange"
echo "  2. Connect your wallet"
echo "  3. Verify you can see your dashboard"
echo ""
echo "Then run this test."
echo ""
echo "======================================================================"
echo ""

# Run the Python debug script
cd /Users/tdl321/hummingbot
python3 scripts/debug_l1_auth.py
