#!/bin/bash
# =============================================================================
# DEPLOYMENT SCRIPT - Data Collection Fixes (Dec 2025)
# =============================================================================

echo "================================================================================"
echo "🚀 CRYPTO DATA COLLECTION - DEPLOYMENT SCRIPT"
echo "================================================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "run_data_factory.py" ]; then
    echo "❌ Error: Must run from Crypto project directory"
    exit 1
fi

echo "📋 Pre-Deployment Checklist"
echo "================================================================================"
echo ""

# 1. Verify files exist
echo "1️⃣  Verifying modified files..."
files=(
    "data_layer/collectors_coinglass.py"
    "data_layer/collectors_other.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ MISSING: $file"
        exit 1
    fi
done
echo ""

# 2. Run syntax check
echo "2️⃣  Running Python syntax validation..."
python3 -m py_compile data_layer/collectors_coinglass.py data_layer/collectors_other.py
if [ $? -eq 0 ]; then
    echo "   ✅ All files compile successfully"
else
    echo "   ❌ Syntax errors detected!"
    exit 1
fi
echo ""

# 3. Run verification tests
echo "3️⃣  Running verification tests..."
python3 test_fixes_2025.py
if [ $? -eq 0 ]; then
    echo "   ✅ All tests passed"
else
    echo "   ❌ Tests failed! Review errors above."
    exit 1
fi
echo ""

# 4. Check for running processes
echo "4️⃣  Checking for running data collection..."
if pgrep -f "run_data_factory.py" > /dev/null; then
    echo "   ⚠️  Data factory is currently running!"
    read -p "   Stop current process and restart? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "   🛑 Stopping current process..."
        pkill -f "run_data_factory.py"
        sleep 2
        echo "   ✅ Process stopped"
    else
        echo "   ℹ️  Deployment aborted by user"
        exit 0
    fi
else
    echo "   ✅ No running process detected"
fi
echo ""

# 5. Summary of changes
echo "================================================================================"
echo "📊 DEPLOYMENT SUMMARY"
echo "================================================================================"
echo ""
echo "CoinGlass API Improvements:"
echo "  • API Keys: 5 → 10 (100% increase)"
echo "  • Capacity: 500 → 950 calls/day"
echo "  • Collection: Every 5 minutes (864 calls/day, 91% utilization)"
echo "  • Rotation: Smart min-usage algorithm"
echo "  • Safety: 9.1% margin per key"
echo ""
echo "CryptoPanic AI Enhancements:"
echo "  • Added: top_headline (for LLM/AI)"
echo "  • Added: headline_list (top 5 headlines)"
echo "  • Preserved: news_sentiment (for ML training)"
echo ""

# 6. Start the data factory
echo "================================================================================"
echo "🚀 STARTING DATA COLLECTION"
echo "================================================================================"
echo ""

read -p "Start data collection now? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 Starting run_data_factory.py..."
    echo ""
    
    # Option 1: Run in foreground (for testing)
    # python3 run_data_factory.py
    
    # Option 2: Run in background with nohup
    nohup python3 run_data_factory.py > data_factory.log 2>&1 &
    PID=$!
    
    echo "✅ Data factory started!"
    echo "   Process ID: $PID"
    echo "   Log file: data_factory.log"
    echo ""
    
    # Wait a few seconds and check if process is running
    sleep 3
    if ps -p $PID > /dev/null; then
        echo "✅ Process is running successfully"
        echo ""
        echo "📊 Monitor with:"
        echo "   tail -f data_factory.log"
        echo ""
        echo "🛑 Stop with:"
        echo "   kill $PID"
        echo "   OR: pkill -f run_data_factory.py"
    else
        echo "❌ Process failed to start! Check data_factory.log for errors."
        exit 1
    fi
else
    echo "ℹ️  Deployment complete. Start manually with:"
    echo "   python3 run_data_factory.py"
fi

echo ""
echo "================================================================================"
echo "✅ DEPLOYMENT COMPLETE"
echo "================================================================================"
echo ""
echo "Expected behavior:"
echo "  ✅ CoinGlass: Data every 5 minutes (no zeros)"
echo "  ✅ CryptoPanic: Headlines captured every 10 minutes"
echo "  ✅ All 10 API keys rotating smartly"
echo "  ✅ Database filling with quality training data"
echo ""
echo "Next steps:"
echo "  1. Monitor logs for first 30 minutes"
echo "  2. Verify no rate limit errors"
echo "  3. Check database for non-zero liquidation data"
echo "  4. Confirm headline fields populated"
echo ""
echo "Happy data collecting! 🚀"
