# Setting Up Claude API for Nexus AI Advisor

The Nexus AI Advisor needs your Claude API key to generate trade recommendations.

## Step 1: Get Your API Key

1. Go to **https://console.anthropic.com/account/keys**
2. Click **"Create Key"**
3. Copy the API key (starts with `sk-ant-`)
4. **Save it somewhere safe** — you won't see it again!

## Step 2: Set Environment Variable (Windows)

### Option A: Temporary (for current session only)
```bash
set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Option B: Permanent (recommended)
1. Press **Windows + X**, select **System**
2. Click **Advanced system settings** → **Environment variables**
3. Click **New** (under User variables)
   - Variable name: `ANTHROPIC_API_KEY`
   - Variable value: `sk-ant-your-key-here`
4. Click **OK** → **OK** → **OK**
5. **Restart Python/terminal** for changes to take effect

### Option C: Using .env file
1. Create a file named `.env` in the project root:
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

2. Then in your code:
```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('ANTHROPIC_API_KEY')
advisor = NexusAdvisor(api_key=api_key)
```

## Step 3: Test the Setup

```bash
# Test API key is accessible
python -c "
import os
from anthropic import Anthropic

api_key = os.getenv('ANTHROPIC_API_KEY')
if api_key:
    print('API key found:', api_key[:20] + '...')
    client = Anthropic(api_key=api_key)
    print('Authentication successful!')
else:
    print('ERROR: ANTHROPIC_API_KEY not set')
"
```

## Step 4: Run Nexus Advisor

```bash
cd "C:\Antigravity\TradingBots-Aruns Project"
python nexus_advisor.py
```

Expected output:
```
Testing Nexus AI Advisor...

1. Fetching recent trades...
   Found 52 trades

2. Calculating performance metrics...
   Win rate: 15.4%
   Total trades: 52
   Profit factor: 0.03

3. Sending analysis to Claude...
   Claude analysis completed successfully

4. Fetching active recommendations...
   INFY: BUY (confidence: 82%)
   TCS: SELL (confidence: 64%)
   ...
```

## Pricing

**Claude API is affordable:**
- Sonnet: ~$3 per 1 million input tokens (~400K tokens = cost of 1 coffee)
- Typical trade analysis: 2,000 tokens input + 1,500 tokens output = ~$0.01

**Our usage:**
- Run advisor once per hour during market hours
- ~8 analyses/day * ~$0.01 = ~$0.08/day = ~$2.40/month

## API Key Security

⚠️ **NEVER commit your API key to git!**

1. Add to `.gitignore`:
```
.env
*.local
ANTHROPIC_API_KEY
```

2. The key is only needed when running the advisor
3. If you accidentally expose it, regenerate it immediately on console.anthropic.com

## Rate Limiting

Claude API has rate limits:
- Free/Trial tier: Limited
- Pro tier: Much higher limits

The Nexus advisor is designed to respect rate limits:
- Caches results for 1 hour (doesn't re-analyze same trades)
- Runs analysis only once per hour during market hours
- Handles API errors gracefully (logs and continues)

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
- Check Step 2 above
- Restart your terminal/IDE
- Verify with: `python -c "import os; print(os.getenv('ANTHROPIC_API_KEY'))"`

### "Authentication failed"
- API key might be invalid
- Get a new one from console.anthropic.com

### "Rate limit exceeded"
- Your subscription tier has run out
- Check console.anthropic.com to upgrade or wait for reset

### "Connection error"
- Check internet connection
- Verify firewall isn't blocking API calls
- Try from a different network (if possible)

## Next Steps

Once API key is set up:

1. **Test advisor**: `python nexus_advisor.py`
2. **Integrate with kickstart**: Add scheduler startup
3. **Monitor recommendations**: Check dashboard (Phase 4)
4. **Refine parameters**: Use Claude's feedback to adjust

---

**Need help?** Check the logs at `logs/nexus_advisor.log` for detailed error messages.
