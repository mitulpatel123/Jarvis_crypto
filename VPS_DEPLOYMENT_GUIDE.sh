#!/bin/bash
# =============================================================================
# VPS DEPLOYMENT GUIDE - Data Collection Fixes (Dec 2025)
# =============================================================================

cat << 'EOF'
═══════════════════════════════════════════════════════════════════════════════
🚀 VPS DEPLOYMENT GUIDE - Crypto Data Factory
═══════════════════════════════════════════════════════════════════════════════

This guide provides step-by-step commands to deploy the updated code to your VPS
and truncate the database to start fresh data collection.

PREREQUISITES:
  • VPS IP address and SSH credentials
  • TimescaleDB Docker container running (crypto_timescaledb)
  • Git repository or direct file transfer access

═══════════════════════════════════════════════════════════════════════════════

STEP 1: STOP RUNNING DATA COLLECTION
═══════════════════════════════════════════════════════════════════════════════
EOF

echo ""
echo "# On VPS, run these commands:"
echo ""
cat << 'EOF'
# Find and stop the data factory process
ps aux | grep run_data_factory.py

# Stop it (use one of these methods):
pkill -f run_data_factory.py           # Graceful stop
# OR if using tmux:
tmux kill-session -t crypto_factory    # Kill tmux session

# Verify it stopped
ps aux | grep run_data_factory.py
# Should show no results (except grep command)

EOF

cat << 'EOF'
═══════════════════════════════════════════════════════════════════════════════

STEP 2: BACKUP CURRENT CODE (OPTIONAL BUT RECOMMENDED)
═══════════════════════════════════════════════════════════════════════════════
EOF

echo ""
cat << 'EOF'
# On VPS:
cd ~/Crypto  # Or your project directory
cp -r data_layer data_layer.backup.$(date +%Y%m%d)
cp run_data_factory.py run_data_factory.py.backup
cp web_ui/status_server.py web_ui/status_server.py.backup

echo "✅ Backup created"

EOF

cat << 'EOF'
═══════════════════════════════════════════════════════════════════════════════

STEP 3: TRANSFER UPDATED FILES TO VPS
═══════════════════════════════════════════════════════════════════════════════
EOF

echo ""
cat << 'EOF'
# On your LOCAL machine, run:
cd /Users/mitulpatel/StudioProjects/Mitul/Crypto

# Replace YOUR_VPS_IP with actual IP (e.g., 123.45.67.89)
export VPS_IP="YOUR_VPS_IP"
export VPS_USER="root"  # Or your VPS username
export VPS_PATH="~/Crypto"

# Transfer updated collectors
scp data_layer/collectors_coinglass.py ${VPS_USER}@${VPS_IP}:${VPS_PATH}/data_layer/
scp data_layer/collectors_other.py ${VPS_USER}@${VPS_IP}:${VPS_PATH}/data_layer/

# Transfer updated UI
scp web_ui/status_server.py ${VPS_USER}@${VPS_IP}:${VPS_PATH}/web_ui/

# Transfer updated main runner
scp run_data_factory.py ${VPS_USER}@${VPS_IP}:${VPS_PATH}/

# Verify transfer
ssh ${VPS_USER}@${VPS_IP} "ls -lh ${VPS_PATH}/data_layer/collectors_*.py"

echo "✅ Files transferred successfully"

EOF

cat << 'EOF'
═══════════════════════════════════════════════════════════════════════════════

STEP 4: TRUNCATE DATABASE (START FRESH)
═══════════════════════════════════════════════════════════════════════════════
EOF

echo ""
cat << 'EOF'
# On VPS, run:

# Method 1: TRUNCATE (Fast, preserves schema) - RECOMMENDED
docker exec crypto_timescaledb psql -U postgres -d crypto_data -c "TRUNCATE TABLE feature_store;"

# Verify truncation
docker exec crypto_timescaledb psql -U postgres -d crypto_data -c "SELECT COUNT(*) FROM feature_store;"
# Should show: count | 0

echo "✅ Database truncated - ready for fresh data collection"

# Method 2: DELETE (Slower, but keeps transaction log)
# docker exec crypto_timescaledb psql -U postgres -d crypto_data -c "DELETE FROM feature_store;"

# Method 3: DROP and RECREATE (Nuclear option - only if schema changed)
# docker exec crypto_timescaledb psql -U postgres -d crypto_data -c "DROP TABLE feature_store CASCADE;"
# Then restart data factory to recreate table automatically

EOF

cat << 'EOF'
═══════════════════════════════════════════════════════════════════════════════

STEP 5: VERIFY PYTHON SYNTAX (ON VPS)
═══════════════════════════════════════════════════════════════════════════════
EOF

echo ""
cat << 'EOF'
# On VPS:
cd ~/Crypto

# Test syntax of updated files
python3 -m py_compile data_layer/collectors_coinglass.py
python3 -m py_compile data_layer/collectors_other.py
python3 -m py_compile web_ui/status_server.py
python3 -m py_compile run_data_factory.py

echo "✅ All files compile successfully"

# If any errors appear, fix them before proceeding

EOF

cat << 'EOF'
═══════════════════════════════════════════════════════════════════════════════

STEP 6: START DATA COLLECTION (PERSISTENT MODE)
═══════════════════════════════════════════════════════════════════════════════
EOF

echo ""
cat << 'EOF'
# On VPS:
cd ~/Crypto

# Option 1: Using tmux (RECOMMENDED - survives SSH disconnect)
tmux new -d -s crypto_factory 'cd ~/Crypto && python3 run_data_factory.py > factory.log 2>&1'

# Verify it's running
tmux ls
# Should show: crypto_factory: 1 windows (created ...)

# Check logs
tail -f factory.log
# Press Ctrl+C to exit tail (tmux session keeps running)

# Option 2: Using nohup (alternative)
# nohup python3 run_data_factory.py > factory.log 2>&1 &

echo "✅ Data collection started in background"

EOF

cat << 'EOF'
═══════════════════════════════════════════════════════════════════════════════

STEP 7: MONITOR & VERIFY
═══════════════════════════════════════════════════════════════════════════════
EOF

echo ""
cat << 'EOF'
# On VPS:

# 1. Check logs (first 5 minutes)
tail -f factory.log

# Look for these success messages:
# ✅ CoinGlassCollector initialized (10 API keys)
# ✅ CryptoPanicCollector (AI-Ready) initialized
# ✅ CoinGlass: Liquidations = $1,234,567 (NOT zero!)
# ✅ CryptoPanic: Headline='...'

# 2. Check database is filling
docker exec crypto_timescaledb psql -U postgres -d crypto_data -c \
  "SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM feature_store;"

# Should show increasing row count

# 3. Verify NO ZEROS in liquidation data (after 10 minutes)
docker exec crypto_timescaledb psql -U postgres -d crypto_data -c \
  "SELECT 
     AVG(liquidation_total_1h) as avg_liq,
     AVG(oi_change_4h) as avg_oi
   FROM feature_store 
   WHERE timestamp > NOW() - INTERVAL '10 minutes';"

# avg_liq should be > 100000 (NOT zero!)
# avg_oi should be non-zero (positive or negative)

# 4. Check Web UI (from your browser)
# http://YOUR_VPS_IP:8080
# Should show:
# - 10 CoinGlass API keys
# - Headlines section with real news
# - Database rows increasing

echo "✅ All systems operational"

EOF

cat << 'EOF'
═══════════════════════════════════════════════════════════════════════════════

QUICK REFERENCE COMMANDS (VPS)
═══════════════════════════════════════════════════════════════════════════════
EOF

echo ""
cat << 'EOF'
# Check if data factory is running
ps aux | grep run_data_factory.py

# View logs in real-time
tail -f ~/Crypto/factory.log

# Attach to tmux session (interactive)
tmux attach -t crypto_factory
# Press Ctrl+B then D to detach (keeps running)

# Stop data factory
pkill -f run_data_factory.py
# OR
tmux kill-session -t crypto_factory

# Restart data factory
tmux new -d -s crypto_factory 'cd ~/Crypto && python3 run_data_factory.py > factory.log 2>&1'

# Database quick stats
docker exec crypto_timescaledb psql -U postgres -d crypto_data -c \
  "SELECT COUNT(*) as rows, 
          MIN(timestamp) as first_record,
          MAX(timestamp) as last_record
   FROM feature_store;"

# Export data to CSV
docker exec crypto_timescaledb psql -U postgres -d crypto_data -c \
  "\COPY (SELECT * FROM feature_store ORDER BY timestamp DESC LIMIT 1000) TO '/tmp/latest_data.csv' WITH CSV HEADER"

docker cp crypto_timescaledb:/tmp/latest_data.csv ~/crypto/latest_data.csv

# Check CoinGlass API key rotation
grep "CoinGlass" ~/Crypto/factory.log | tail -20

# Check for errors
grep "❌" ~/Crypto/factory.log | tail -20

EOF

cat << 'EOF'
═══════════════════════════════════════════════════════════════════════════════

ALTERNATIVE: FULL DEPLOYMENT SCRIPT (ONE-COMMAND)
═══════════════════════════════════════════════════════════════════════════════
EOF

echo ""
cat << 'EOF'
# Save this as deploy_to_vps.sh on your LOCAL machine:

#!/bin/bash
VPS_IP="YOUR_VPS_IP"
VPS_USER="root"
VPS_PATH="~/Crypto"

echo "🚀 Deploying to VPS..."

# Stop running process
ssh ${VPS_USER}@${VPS_IP} "pkill -f run_data_factory.py"
sleep 2

# Transfer files
echo "📁 Transferring files..."
scp data_layer/collectors_coinglass.py ${VPS_USER}@${VPS_IP}:${VPS_PATH}/data_layer/
scp data_layer/collectors_other.py ${VPS_USER}@${VPS_IP}:${VPS_PATH}/data_layer/
scp web_ui/status_server.py ${VPS_USER}@${VPS_IP}:${VPS_PATH}/web_ui/
scp run_data_factory.py ${VPS_USER}@${VPS_IP}:${VPS_PATH}/

# Truncate database
echo "🗑️  Truncating database..."
ssh ${VPS_USER}@${VPS_IP} \
  "docker exec crypto_timescaledb psql -U postgres -d crypto_data -c 'TRUNCATE TABLE feature_store;'"

# Start data factory
echo "▶️  Starting data collection..."
ssh ${VPS_USER}@${VPS_IP} \
  "cd ${VPS_PATH} && tmux new -d -s crypto_factory 'python3 run_data_factory.py > factory.log 2>&1'"

echo "✅ Deployment complete!"
echo "Monitor: ssh ${VPS_USER}@${VPS_IP} tail -f ${VPS_PATH}/factory.log"

# Then run:
# chmod +x deploy_to_vps.sh
# ./deploy_to_vps.sh

EOF

cat << 'EOF'
═══════════════════════════════════════════════════════════════════════════════

TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════════════
EOF

echo ""
cat << 'EOF'
Problem: "No such file or directory" during scp
Solution: Verify VPS_PATH exists:
  ssh root@YOUR_VPS_IP "ls -la ~/Crypto"

Problem: Database truncation fails
Solution: Check Docker container is running:
  ssh root@YOUR_VPS_IP "docker ps | grep timescale"
  
Problem: Data factory won't start
Solution: Check Python dependencies:
  ssh root@YOUR_VPS_IP "cd ~/Crypto && python3 -m pip list | grep requests"

Problem: Still seeing zeros in data
Solution: Check API keys are valid:
  ssh root@YOUR_VPS_IP "grep 'CoinGlass' ~/Crypto/factory.log"
  Look for: "✅ CoinGlassCollector initialized (10 API keys)"

Problem: Web UI not accessible
Solution: Check port 8080 is open:
  ssh root@YOUR_VPS_IP "netstat -tuln | grep 8080"
  
Problem: tmux session not found
Solution: Create new session:
  ssh root@YOUR_VPS_IP "tmux new -d -s crypto_factory 'cd ~/Crypto && python3 run_data_factory.py > factory.log 2>&1'"

EOF

cat << 'EOF'
═══════════════════════════════════════════════════════════════════════════════

EXPECTED TIMELINE
═══════════════════════════════════════════════════════════════════════════════

T+0 min:  Deployment complete, data factory starting
T+1 min:  First database records appear
T+5 min:  CoinGlass data starts flowing (first cycle at 5 min)
T+10 min: CryptoPanic headlines captured
T+15 min: All collectors running, ~15 rows in database
T+1 hour: ~60 rows, verify NO ZEROS in liquidations
T+24 hrs: ~86,400 rows (1 per second), full 24/7 coverage

═══════════════════════════════════════════════════════════════════════════════

SUMMARY CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

Before deployment:
[ ] VPS access confirmed (ssh root@YOUR_VPS_IP)
[ ] Files ready on local machine
[ ] VPS_IP and VPS_PATH variables set

During deployment:
[ ] Old process stopped
[ ] Files transferred successfully
[ ] Database truncated (count = 0)
[ ] Python syntax verified
[ ] Data factory started in tmux

After deployment:
[ ] Logs show no errors
[ ] Database rows increasing
[ ] Liquidations NOT zero (after 10 min)
[ ] Headlines appearing in logs
[ ] Web UI accessible and showing data

═══════════════════════════════════════════════════════════════════════════════
✅ DEPLOYMENT GUIDE COMPLETE
═══════════════════════════════════════════════════════════════════════════════
EOF

echo ""
echo "For questions or issues, check:"
echo "  • IMPLEMENTATION_SUMMARY.md (Hindi/English guide)"
echo "  • DATA_COLLECTION_FIXES_2025.md (Technical details)"
echo "  • QUICK_REFERENCE.md (Commands cheatsheet)"
echo ""
