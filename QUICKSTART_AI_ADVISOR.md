# Quick Start: Activate Your AI Advisor

**Goal**: Get your Claude AI Advisor working in 5 minutes  
**Difficulty**: Easy | **Time**: 5 minutes

---

## Step 1: Get Claude API Key (2 minutes)

1. Go to: **https://console.anthropic.com/account/keys**
2. Click **"Create Key"**
3. Copy the key (looks like: `sk-ant-...`)
4. **Save it!** (You won't see it again)

---

## Step 2: Set Environment Variable (2 minutes)

**Windows - Permanent Setup (Recommended)**:

1. Press **Windows Key + X**
2. Select **"System"**
3. Click **"Advanced system settings"** (on the left)
4. Click **"Environment Variables"** button
5. Click **"New"** (under User variables)
6. Enter:
   - Variable name: `ANTHROPIC_API_KEY`
   - Variable value: `sk-ant-your-key-here`
7. Click **OK** three times
8. **Close and reopen your terminal** for changes to take effect

**Or Windows - Temporary (Current session only)**:
```bash
set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

---

## Step 3: Test It Works (1 minute)

```bash
cd "C:\Antigravity\TradingBots-Aruns Project"

python -c "
import os
print('Testing API key...')
key = os.getenv('ANTHROPIC_API_KEY')
if key:
    print(f'API key found: {key[:20]}...')
    print('SUCCESS! Ready to run advisor.')
else:
    print('ERROR: ANTHROPIC_API_KEY not set')
    print('Did you set the environment variable and restart?')
"
```

Expected output:
```
Testing API key...
API key found: sk-ant-...
SUCCESS! Ready to run advisor.
```

---

## Step 4: Generate Your First Recommendations (1 minute)

```bash
python nexus_advisor.py
```

Expected output:
```
2026-06-21 12:35:15 [nexus_advisor] Market context fetcher started
2026-06-21 12:35:16 [nexus_advisor] Fetching recent trades...
2026-06-21 12:35:17 [nexus_advisor] Found 52 trades
2026-06-21 12:35:18 [nexus_advisor] Calculating performance metrics...
   Win rate: 15.4%
   Total trades: 52
   Profit factor: 0.03
2026-06-21 12:35:22 [nexus_advisor] Sending analysis to Claude...
2026-06-21 12:35:27 [nexus_advisor] Claude analysis completed successfully
2026-06-21 12:35:28 [nexus_advisor] Extracted 3 recommendations
2026-06-21 12:35:28 [nexus_advisor] Stored recommendation ID 1: INFY BUY
2026-06-21 12:35:28 [nexus_advisor] Stored recommendation ID 2: WIPRO AVOID
2026-06-21 12:35:28 [nexus_advisor] Stored recommendation ID 3: GENERAL TWEAK_PARAMS
```

**Success!** Your AI advisor just analyzed 52 trades and generated 3 recommendations.

---

## What Did It Generate?

The AI advisor analyzed your trades and likely recommended:

```
1. INFY - BUY
   "Strong RSI reversal pattern + sector strength"
   Confidence: 82%
   Reason: Win rate analysis shows INFY has better performance
   Action: Increase position size by 20%

2. WIPRO - AVOID  
   "Win rate only 8%, pattern inconsistent"
   Confidence: 71%
   Reason: Consistent losses - not aligned with parameters
   Action: Skip trading until parameters adjusted

3. Parameter Adjustment
   "Increase buy RSI from 35 → 40"
   Confidence: 68%
   Reason: Too many false signals with current threshold
   Action: Update settings.json
```

---

## View Recommendations in Database

```bash
python -c "
from nexus_advisor import NexusAdvisor
advisor = NexusAdvisor()
recs = advisor.get_active_recommendations(min_confidence=0.6, limit=10)
print(f'Found {len(recs)} recommendations:\n')
for rec in recs:
    print(f'{rec[\"symbol\"]:10} - {rec[\"signal\"]:12} (Confidence: {rec[\"confidence\"]:.0%})')
    print(f'  Reason: {rec[\"reason\"]}')
    print()
"
```

---

## Integrate with Kickstart (Optional)

To make the AI advisor run automatically:

**In kickstart.py, around line 50 (after imports), add:**

```python
# AI Advisor (Phase 3)
from nexus_advisor import NexusAdvisor

# Initialize advisor
advisor = NexusAdvisor()

# Run analysis every hour (during market hours)
def run_ai_analysis():
    """Run AI advisor analysis"""
    import datetime
    now = datetime.datetime.now()
    
    # Only during market hours (9:30 AM - 3:30 PM)
    if 9 <= now.hour <= 15:
        result = advisor.run_analysis(days=7)
        
        if result['status'] == 'success':
            recs = advisor.get_active_recommendations(min_confidence=0.7)
            print(f"AI generated {len(recs)} recommendations")

# Call this once per hour
# (or add to your trading cycle)
run_ai_analysis()
```

---

## Now What?

### Immediate:
- ✅ AI advisor is running
- ✅ Generating recommendations
- ✅ Storing in database

### Next Week:
- Build Phase 4: Dashboard UI to view recommendations
- Add "Track to Stocks" button to act on recommendations
- Show recommendation confidence & explanations

### Ongoing:
- Run advisor every hour (recommendations automatically refresh)
- Monitor recommendation quality
- Adjust Claude prompt based on results
- Collect feedback (accept/reject recommendations)

---

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
- Did you restart your terminal after setting environment variable?
- Try closing and reopening Command Prompt/PowerShell completely
- Verify: Open new terminal, run: `echo %ANTHROPIC_API_KEY%`
- Should see your API key printed (or empty = not set)

### "Connection error" or "API error"
- Check internet connection
- Verify API key is correct (starts with `sk-ant-`)
- Check console.anthropic.com that key is active
- Retry in a few seconds (might be temporary API issue)

### "No recommendations generated"
- Check: `python -c "from nexus_advisor import NexusAdvisor; a = NexusAdvisor(); print(len(a.get_recent_trades()))"` trades
- If 0 trades: Run your trading bot first to generate data
- If >0 trades: Try running again (Claude analysis takes 5 seconds)

### "Rate limited"
- Your API tier has hit limits
- Check console.anthropic.com for usage
- Upgrade to Pro tier if needed
- Or wait for next billing cycle

---

## Cost Check

```
Claude API Usage:
- Per run: ~2,000 input tokens + 1,500 output = ~$0.01
- Once per hour: 8 × $0.01 = $0.08/day
- Per month (20 trading days): ~$1.60/month
- Total annual: ~$20-25

→ Less than cost of coffee, huge value
```

---

## What's Happening Behind the Scenes?

```
Your Bot's Trades (52 total)
    ↓
    ↓ Market context captured (every 5 minutes)
    ↓
    ↓ Stored in analytics database
    ↓
Claude AI Advisor (Claude 3.5 Sonnet)
    ├─ Analyzes: Which trades won/lost?
    ├─ Analyzes: What market conditions were present?
    ├─ Analyzes: Which parameters work best?
    ├─ Analyzes: Which stocks to focus on?
    └─ Generates: Structured recommendations
    ↓
Recommendations Stored
    ├─ Symbol to trade
    ├─ Signal (BUY/SELL/AVOID/TWEAK)
    ├─ Confidence level
    ├─ Detailed reasoning
    └─ Expires in 7 days
    ↓
Dashboard (Phase 4)
    ├─ View recommendations
    ├─ See confidence scores
    ├─ Accept/reject recommendations
    └─ Feedback loop (AI learns)
```

---

## Summary

You now have:

✅ **AI Advisor** - Claude analyzes your trades  
✅ **Market Context** - Bot sees market conditions  
✅ **Recommendations** - AI suggests stocks & parameter adjustments  
✅ **Learning Loop** - AI improves as it learns  

**All for ~$0.01 per run.**

---

## Next Reading

- See `PHASE_SUMMARY.md` for complete overview
- See `PHASE3_NEXUS_AI.md` for technical details
- See `SETUP_CLAUDE_API.md` for API troubleshooting

---

**Congratulations! You've activated the Nexus AI Advisor! 🤖**

Your trading bot is now learning and improving with every trade. 

📈 Let's make your win rate better than 15.4%! 🚀
