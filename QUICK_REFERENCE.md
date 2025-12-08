# 🚀 QUICK REFERENCE - Data Collection Fixes

## ⚡ TL;DR (Too Long; Didn't Read)

**What Changed:**
- ✅ CoinGlass: 5 → 10 API keys (NO MORE ZEROS!)
- ✅ CryptoPanic: Now captures headlines for AI
- ✅ Smart rotation: Auto-manages all keys
- ✅ 5-minute interval: 864 calls/day (91% capacity)

**Deploy Now:**
```bash
cd /Users/mitulpatel/StudioProjects/Mitul/Crypto
./deploy_fixes.sh
```

---

## 📋 Quick Commands

### Start Collection
```bash
# Automatic (recommended)
./deploy_fixes.sh

# Manual
python3 run_data_factory.py

# Background mode
nohup python3 run_data_factory.py > data_factory.log 2>&1 &
```

### Monitor
```bash
# Live logs
tail -f data_factory.log

# Check for errors
tail -f data_factory.log | grep "❌"

# Watch CoinGlass
tail -f data_factory.log | grep "CoinGlass"

# Watch headlines
tail -f data_factory.log | grep "Headline"
```

### Stop
```bash
# Find process
ps aux | grep run_data_factory

# Stop it
pkill -f run_data_factory.py

# Or by PID
kill <PID>
```

### Verify Data Quality
```bash
# Run tests
python3 test_fixes_2025.py

# Check database
python3 -c "
from infrastructure.timescale_db import TimescaleDB
db = TimescaleDB()
data = db.get_latest_data('BTCUSDT', limit=10)
print('Latest 10 records:', data)
"
```

---

## 🔍 What to Look For

### ✅ Good Signs
```
✅ CoinGlassCollector initialized (10 API keys)
✅ CryptoPanicCollector (AI-Ready) initialized  
✅ CoinGlass: Liquidations = $1,234,567
✅ CryptoPanic: Headline='SEC approves...'
✅ CoinGlass: Daily reset - all keys refreshed
```

### ⚠️ Warning Signs (Normal)
```
⚠️  CoinGlass: HTTP 429  # Rate limit - will auto-rotate
⚠️  Delta Exchange: Rate limit reached, skipping...
```

### ❌ Bad Signs (Need Action)
```
❌ CoinGlass: All 10 keys exhausted  # Should auto-recover at midnight
❌ Database connection failed  # Check TimescaleDB container
❌ Syntax error  # Code issue - re-run tests
```

---

## 📊 Expected Performance

### CoinGlass Metrics
| Metric | Value | Check |
|--------|-------|-------|
| Collection Frequency | Every 5 min | `tail -f data_factory.log` |
| Liquidation Values | > $100,000 | Should NOT be zero |
| OI Change Values | Positive/Negative | Varying values |
| API Keys Active | 10 | Check startup logs |
| Daily API Calls | ~864 | 91% capacity |

### CryptoPanic Metrics
| Metric | Value | Check |
|--------|-------|-------|
| Update Frequency | Every 10 min | `grep Headline data_factory.log` |
| Headlines Captured | Top 5 | `headline_list` array |
| Sentiment Score | -1.0 to 1.0 | Numeric value varying |

---

## 🎯 API Key Status

### CoinGlass (10 Keys)
```python
# Original 5 keys
"f632594f56e74ddf995f6ffdeac6de82"
"7dbd21eb250c44a0b18607c89f07166a"
"be9776242d584b4b81bbb3cde709d4c7"
"b562b0e74fa5416fb1a754ac0a637468"
"7a4a198e1ba44d76bd7fa241d52bc075"

# New 5 keys (added Dec 2025)
"511eb0fc20344f3cb758735b4c95fdb9"
"50241cc594154776a60c3b5e6a126193"
"c5e8a3f4b79b449fa2533f9349b7cd73"
"daa45b3f5d6f4f06b94d73dcd08c7560"
"8cef566412cb4dbb8615977169ea4d80"
```

**Rotation Logic:**
- Always picks LEAST USED key
- Daily reset at midnight UTC
- 95-call limit per key (5-call safety margin)

---

## 🛠️ Troubleshooting Matrix

| Problem | Cause | Solution |
|---------|-------|----------|
| Zeros in data | Rate limit hit | ✅ Auto-fixed with 10 keys |
| Process not starting | Syntax error | Run `python3 -m py_compile *.py` |
| Database errors | TimescaleDB down | `docker ps \| grep timescale` |
| No headlines | CryptoPanic key expired | Check key validity in apikey.txt |
| High CPU usage | Too many threads | Normal for data collection |
| Log file too big | Long running time | `tail -1000 data_factory.log > temp.log` |

---

## 📁 Important Files

| File | Purpose | When to Check |
|------|---------|---------------|
| `data_layer/collectors_coinglass.py` | CoinGlass logic | If zeros still appearing |
| `data_layer/collectors_other.py` | CryptoPanic logic | If headlines missing |
| `test_fixes_2025.py` | Verification tests | Before deployment |
| `deploy_fixes.sh` | Auto deployment | For easy setup |
| `DATA_COLLECTION_FIXES_2025.md` | Full documentation | For detailed understanding |
| `IMPLEMENTATION_SUMMARY.md` | Hindi/English guide | For quick overview |
| `data_factory.log` | Runtime logs | For monitoring |

---

## 🎓 Understanding Smart Rotation

### How It Works
```
Every API Call:
  ┌─────────────────────────────────┐
  │ 1. Check: Is it a new day?      │
  │    → Yes: Reset all counters    │
  └─────────────────────────────────┘
              ↓
  ┌─────────────────────────────────┐
  │ 2. Find: Which key used least?  │
  │    calls_per_key = [10,5,15,3]  │
  │    → Select key #3 (used 3x)    │
  └─────────────────────────────────┘
              ↓
  ┌─────────────────────────────────┐
  │ 3. Check: Is it under 95 limit? │
  │    → Yes: Use this key          │
  │    → No: Try next least-used    │
  └─────────────────────────────────┘
              ↓
  ┌─────────────────────────────────┐
  │ 4. Increment: calls_per_key[3]++│
  │    New value = [10,5,15,4]      │
  └─────────────────────────────────┘
```

**Why This is Better Than Round-Robin:**
- Even distribution across all keys
- Automatically avoids exhausted keys
- Self-balancing load
- No manual intervention needed

---

## 💾 Database Schema (No Changes Needed)

Headlines are stored **in-memory only** (not in database):
```python
# In-memory (for AI agent)
collector.latest_data = {
    "top_headline": "SEC approves Bitcoin ETFs",  # TEXT
    "headline_list": ["headline1", "headline2"],  # ARRAY
    "news_sentiment": 0.73  # NUMERIC → Goes to database
}

# Database (for ML training)
feature_store table:
  - news_sentiment (DOUBLE PRECISION)  ✅ Already exists
  - No TEXT columns needed
```

**Access Headlines:**
```python
# In your AI agent code:
news = cryptopanic_collector.get_snapshot()
headline = news['top_headline']  # "SEC approves Bitcoin ETFs"
context = news['headline_list']  # ["headline1", "headline2", ...]
```

---

## 🎯 Success Checklist

### Immediate (First Hour)
- [ ] Process starts without errors
- [ ] CoinGlass shows 10 API keys initialized
- [ ] Liquidation values > 0
- [ ] Headlines appearing in logs

### Short-term (24 Hours)
- [ ] ~288 CoinGlass records in database
- [ ] ~144 CryptoPanic records
- [ ] All 10 keys used (check rotation logs)
- [ ] No rate limit errors

### Long-term (1 Week)
- [ ] 2,000+ quality training records
- [ ] Database export shows no zero columns
- [ ] Model training performance improves

---

## 🚨 Emergency Commands

### If System Hangs
```bash
# Force kill
pkill -9 -f run_data_factory.py

# Clean restart
rm data_factory.log
nohup python3 run_data_factory.py > data_factory.log 2>&1 &
```

### If Database Full
```bash
# Export data
docker exec crypto_timescaledb psql -U postgres -d crypto_data -c "\COPY (SELECT * FROM feature_store) TO '/tmp/backup.csv' WITH CSV HEADER"

# Delete old data
docker exec crypto_timescaledb psql -U postgres -d crypto_data -c "DELETE FROM feature_store WHERE timestamp < NOW() - INTERVAL '7 days'"
```

### If All Keys Exhausted
```bash
# Check usage
grep "Daily reset" data_factory.log

# Wait for midnight UTC or manually reset (in code):
# collector.calls_per_key = [0] * 10
# collector.last_reset_day = datetime.now().day
```

---

## 📞 Support Contacts

**Documentation:**
- Full Docs: `DATA_COLLECTION_FIXES_2025.md`
- Summary: `IMPLEMENTATION_SUMMARY.md`
- This Card: `QUICK_REFERENCE.md`

**Testing:**
```bash
python3 test_fixes_2025.py  # Run all tests
```

**Logs:**
```bash
tail -f data_factory.log  # Live monitoring
```

---

## 🎉 You're Ready!

Everything is implemented and tested. Just run:

```bash
./deploy_fixes.sh
```

And watch your data collection start with **no more zeros**! 🚀

---

**Last Updated:** December 8, 2025  
**Version:** 2.0 (Production Release)  
**Status:** ✅ Ready to Deploy
