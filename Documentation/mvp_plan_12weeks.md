# 🎯 ARUN Bot - MVP Plan (12 Weeks to Launch)

**Philosophy:** "Prove Value First, Scale Later"  
**Core Promise:** Help Indian retail investors make BETTER decisions using institutional-grade intelligence  
**Success Metric:** 10 paying beta users + 70% retention after Month 1

---

## 🚨 The MVP Mindset

### What is MVP?

**NOT:** Build everything we discussed  
**YES:** Build the MINIMUM to prove the core value proposition

**Our Core Value:**
> *"Give me a Confluence Score (0-100) for any stock so I know if it's a good buy RIGHT NOW."*

That's it. Everything else is nice-to-have.

---

## 📋 What's IN the MVP (The Essentials)

### ✅ MUST HAVE (Weeks 1-8)

**1. Confluence Engine (4-Layer Scoring)**
- Technical (RSI, MA, Volume) - 30 points
- Fundamentals (ROE, Debt, Growth) - 30 points
- Macro (NIFTY trend, FII flows) - 20 points
- Sentiment (Earnings, Analyst ratings) - 20 points
- **Total:** 0-100 score with visual breakdown

**2. Web Dashboard (Streamlit)**
- Login (password protection)
- Stock search (enter symbol → get score)
- Score breakdown (show all 4 layers)
- Top 10 recommendations (auto-screened daily)
- Watchlist (save stocks to track)

**3. 2 Core Strategies**
- **RSI Mean Reversion** (you have this!)
- **QGLP Filter** (Raamdeo Agrawal style)

**4. Safety Features**
- Circuit breaker (stop if NIFTY crashes >3%)
- Regime detector (Bull/Bear/Crisis)
- Stop-loss automation (existing)

**5. Paper Trading Mode**
- Users test strategies risk-free
- Track hypothetical P&L
- Build confidence before live

---

## ❌ What's NOT in MVP (Build Later)

**Save These for v2.0:**
- ❌ Mobile app (web-first!)
- ❌ Advanced charts/visualizations (numbers are enough)
- ❌ Multiple brokers (start with Zerodha only)
- ❌ Community features (forums, copy trading)
- ❌ AI/ML (manual logic is fine)
- ❌ IPO waiting room (too niche for MVP)
- ❌ Magic Formula + High Growth strategies (focus on 2)
- ❌ Telegram integration (email alerts enough)
- ❌ Tax reports (not essential day 1)

**Why?**
These are all great ideas, but they don't prove the core value. If users don't care about the Confluence Score, fancy features won't save us.

---

## 🗓️ The 12-Week Build Plan

### **Phase 1: Foundation (Weeks 1-4)**

**Goal:** Get Confluence Engine working

#### Week 1-2: Data Pipeline
**Build:**
- Connect to Yahoo Finance (OHLCV data)
- Integrate Screener.in API (fundamentals)
- Fetch NIFTY data + FII/DII flows (NSE website)
- Cache system (don't re-fetch every time)

**Test:**
```python
# Test script: test_data_pipeline.py
def test_can_fetch_stock_data():
    data = fetch_ohlcv('TCS')
    assert len(data) > 0
    assert 'close' in data.columns

def test_can_fetch_fundamentals():
    fund = get_fundamentals('TCS')
    assert fund['roe'] > 0
    assert 'promoter_holding' in fund

def test_fii_data_fresh():
    fii = get_fii_flows()
    assert fii['date'] == today()
```

**Success Criteria:**
- ✅ Can fetch data for 50 NIFTY stocks
- ✅ Data refreshes daily automatically
- ✅ No errors for 3 consecutive days

---

#### Week 3: Confluence Scoring Algorithm
**Build:**
- `calculate_technical_score()` - 0-30 points
- `calculate_fundamental_score()` - 0-30 points
- `calculate_macro_score()` - 0-20 points
- `calculate_sentiment_score()` - 0-20 points
- `get_confluence_score()` - combines all 4

**Test:**
```python
# Manual validation against known good stocks
def test_confluence_makes_sense():
    # TCS (known quality stock)
    tcs_score = get_confluence_score('TCS')
    assert tcs_score > 70, "TCS should score high"
    
    # Recent IPO that crashed
    bad_ipo_score = get_confluence_score('PAYTM')
    assert bad_ipo_score < 50, "Bad stock should score low"
```

**Success Criteria:**
- ✅ Scores match intuition (good stocks = high, bad stocks = low)
- ✅ All 4 layers contributing properly
- ✅ Backtested on 10 historical examples

---

#### Week 4: Basic Dashboard
**Build:**
- Streamlit app with login
- Stock search bar
- Display Confluence Score with breakdown
- Show recommendation (BUY/WAIT/SELL)

**Test:**
```bash
# User Acceptance Test
1. Open http://localhost:8501
2. Login with password
3. Search "TCS"
4. See score 78/100 with green BUY signal
5. See breakdown: Technical 24, Fund 26, Macro 16, Sentiment 12
6. Click "Why this score?" → Tooltip explains each layer
```

**Success Criteria:**
- ✅ 5 non-techie friends can use it without help
- ✅ Takes <10 seconds to get a score
- ✅ Interface is clear (no confusion)

**MILESTONE 1:** 🎉 **End of Week 4 - Have a working demo!**

---

### **Phase 2: Strategies (Weeks 5-6)**

**Goal:** Implement 2 trading strategies

#### Week 5: RSI Strategy Enhancement
**Build:**
- Add Confluence filter to existing RSI bot
- Only trade if Confluence > 65
- Visual backtesting results in dashboard

**Test:**
```python
# Backtest on 3 months of data
def test_rsi_with_confluence_improves_win_rate():
    results_without = backtest_rsi_only(start='2023-10-01', end='2024-01-01')
    results_with = backtest_rsi_with_confluence(start='2023-10-01', end='2024-01-01')
    
    assert results_with['win_rate'] > results_without['win_rate']
    assert results_with['sharpe_ratio'] > results_without['sharpe_ratio']
```

**Success Criteria:**
- ✅ Win rate improves by 5-10%
- ✅ Sharpe ratio > 1.0
- ✅ Max drawdown < 15%

---

#### Week 6: QGLP Strategy
**Build:**
- Screen all NIFTY 500 stocks for QGLP criteria
- Auto-generate "Top 10 Quality Stocks" list
- Update weekly

**Test:**
```python
# Compare vs. known QGLP stocks from Motilal Oswal
def test_qglp_finds_quality():
    our_list = run_qglp_screener()
    known_quality = ['TCS', 'INFY', 'HDFCBANK', 'ASIANPAINT', 'TITAN']
    
    overlap = set(our_list[:20]) & set(known_quality)
    assert len(overlap) >= 3, "Should identify at least 3 known quality stocks"
```

**Success Criteria:**
- ✅ Finds 15-20 stocks meeting QGLP
- ✅ At least 30% overlap with institutional favorites
- ✅ Manual review: "Yes, these look good"

**MILESTONE 2:** 🎉 **End of Week 6 - Have 2 working strategies!**

---

### **Phase 3: Safety & Polish (Weeks 7-8)**

**Goal:** Make it safe and user-friendly

#### Week 7: Safety Systems
**Build:**
- Circuit breakers (NIFTY crash detection)
- Regime detector (Bull/Bear/Crisis)
- Auto-adjust strategy based on regime

**Test:**
```python
# Simulate crash scenario
def test_circuit_breaker_blocks_trades():
    simulate_nifty_crash(percent=-5)
    
    signal = check_if_should_trade('TCS')
    assert signal == False, "Should block trades during crash"
    assert "Circuit breaker active" in get_veto_reason()
```

**Success Criteria:**
- ✅ Detected 2008 crash (historical test)
- ✅ Detected March 2020 COVID crash
- ✅ Resumes trading after market stabilizes

---

#### Week 8: User Experience
**Build:**
- Onboarding tutorial (5 slides)
- Tooltips explaining every metric
- "Example walkthrough" (pre-loaded with TCS)
- Export watchlist to Excel

**Test:**
```bash
# 10-Minute New User Test
Give dashboard to someone who has NEVER seen it.
Start timer. Can they:
1. Login? (✅/❌)
2. Search a stock? (✅/❌)
3. Understand the score? (✅/❌)
4. Know what to do next? (✅/❌)

Success = All ✅ in < 10 minutes with ZERO guidance
```

**Success Criteria:**
- ✅ 8/10 test users complete successfully
- ✅ Average time < 7 minutes
- ✅ Post-test survey: "Would recommend" > 80%

**MILESTONE 3:** 🎉 **End of Week 8 - MVP is READY!**

---

### **Phase 4: Beta Launch (Weeks 9-12)**

**Goal:** Get real users and validate

#### Week 9: Closed Beta (10 Users)
**Who:**
- 5 friends/family who trade stocks
- 5 from Reddit r/IndianStockMarket (recruit via post)

**What They Do:**
- Use dashboard daily for 2 weeks
- Paper trade using recommendations
- Fill weekly feedback form

**Test:**
```bash
# Weekly Check-in Questions
1. How many times did you use it this week? _____
2. Did you take any action based on recommendations? (Yes/No)
3. What was confusing? ________________________________
4. What feature do you wish existed? __________________
5. Would you pay ₹999/month for this? (Yes/Maybe/No)
```

**Success Criteria:**
- ✅ 7/10 users login at least 3x per week
- ✅ 5/10 users take at least 1 trading action
- ✅ 6/10 would pay (or say "maybe")

---

#### Week 10: Iterate Based on Feedback
**Build:**
- Fix top 3 pain points from beta
- Add 1-2 most-requested features (if quick)
- Polish UI based on confusion points

**Test:**
```bash
# Re-test with same 10 users
"We fixed X, Y, Z based on your feedback. Try again."

New satisfaction score > Previous score?
```

**Success Criteria:**
- ✅ Satisfaction increases by 20%
- ✅ Confusion points reduced by 50%
- ✅ At least 5 users say "this is much better"

---

#### Week 11: Monetization Test
**Build:**
- Payment integration (Razorpay)
- Pricing tiers:
  - **Free:** 3 stocks/day limit
  - **Pro (₹999/month):** Unlimited + Alerts
  - **Elite (₹2,999/month):** + Auto-trading

**Test:**
```bash
# Conversion Test
Ask beta users: "If we launched paid version tomorrow, would you subscribe?"

Track:
- How many say YES immediately?
- How many want free trial first?
- What objections do they have?
```

**Success Criteria:**
- ✅ 3/10 beta users willing to pay
- ✅ No major objections (if there are, fix them!)
- ✅ Price anchoring works (Pro preferred over Elite)

---

#### Week 12: Soft Launch
**Build:**
- Landing page (one-pager explaining value)
- Sign-up form
- Onboarding email sequence

**Launch:**
- Post on Reddit r/IndianStockMarket
- Share on LinkedIn
- Friends/family referrals

**Target:** 50 sign-ups, 10 paid conversions

**Test:**
```bash
# Launch Metrics (Day 1-7)
- Sign-ups: _____/50
- Activations (used it): _____/50
- Paid conversions: _____/10
- Churn (quit within week): _____/50

Success = 10+ activations, 2+ paid, <20% churn
```

**MILESTONE 4:** 🎉 **End of Week 12 - LAUNCHED WITH PAYING CUSTOMERS!**

---

## 🧪 Testing Strategy (How to Validate At Each Step)

### 1. **Unit Tests (Developer)**
Every function has a test:
```python
# tests/test_confluence.py
def test_technical_score_range():
    score = calculate_technical_score('TCS', get_mock_data())
    assert 0 <= score <= 30
```

**Run:** After every code change  
**Tool:** pytest  
**Goal:** Catch bugs immediately

---

### 2. **Integration Tests (System)**
Test that pieces work together:
```python
# tests/test_end_to_end.py
def test_full_flow():
    # User searches stock → Gets score → Sees breakdown
    result = process_user_search('TCS')
    assert 'confluence_score' in result
    assert 'breakdown' in result
    assert result['recommendation'] in ['BUY', 'WAIT', 'SELL']
```

**Run:** Daily (automated)  
**Tool:** pytest + GitHub Actions  
**Goal:** Ensure system stability

---

### 3. **Backtests (Strategy Validation)**
Prove strategies work historically:
```python
# tests/backtest_rsi.py
def test_rsi_strategy_2023():
    results = backtest_strategy(
        strategy='RSI',
        symbols=['NIFTY50_stocks'],
        start='2023-01-01',
        end='2023-12-31'
    )
    
    assert results['total_return'] > 0
    assert results['win_rate'] > 55
    assert results['sharpe_ratio'] > 1.0
```

**Run:** Weekly + before major changes  
**Tool:** Custom backtesting framework  
**Goal:** Ensure strategies are profitable

---

### 4. **User Acceptance Tests (Real People)**
Give it to non-techies:
```bash
# tests/uat_script.md
🧪 USER TEST: New User Onboarding

Recruit: Friend who trades stocks but isn't technical

Tasks:
1. Go to website, create account (Time: ____ sec)
2. Search for "RELIANCE" (Time: ____ sec)
3. Explain what the score means (Correct? Yes/No)
4. Find the Top 10 recommendations (Time: ____ sec)
5. Add a stock to watchlist (Time: ____ sec)

Pass Criteria: All tasks < 2 min, no help needed
```

**Run:** Before each milestone  
**Participants:** 3-5 people each time  
**Goal:** Catch UX issues early

---

### 5. **A/B Tests (Optimize)**
Test variations in production:
```python
# Experiment: Does showing "Used by 500+ traders" increase sign-ups?

Group A: Landing page WITHOUT social proof
Group B: Landing page WITH social proof

Track: Sign-up conversion rate

if B_conversion > A_conversion * 1.2:
    make_B_permanent()
```

**Run:** During Week 11-12 (beta launch)  
**Tool:** Google Optimize or manual  
**Goal:** Improve conversion

---

## 📊 Success Metrics (How to Know If It's Working)

### **Week 4 (Demo Ready)**
- ✅ Can show working demo to 5 people
- ✅ They understand it without explanation
- ✅ At least 3 say "I'd use this"

**Decision Gate:** If NO → Pivot UX. If YES → Proceed.

---

### **Week 6 (Strategies Ready)**
- ✅ Backtest shows positive returns
- ✅ Win rate > 55%
- ✅ Strategies complement each other (low correlation)

**Decision Gate:** If NO → Fix strategies. If YES → Proceed.

---

### **Week 8 (MVP Complete)**
- ✅ 10 beta users can use without bugs
- ✅ Uptime > 95% (no crashes)
- ✅ Data accuracy = 100% (verified against sources)

**Decision Gate:** If NO → Bug fixing sprint. If YES → Launch beta.

---

### **Week 12 (Launch)**
- ✅ 50+ sign-ups
- ✅ 10+ active users (login 3x/week)
- ✅ 3+ paying customers
- ✅ 70%+ retention (still using after Month 1)

**Decision Gates:**
- **If ALL ✅:** Scale! (Hire, marketing, v2.0 features)
- **If 2-3 ✅:** Iterate! (Ask users what's missing)
- **If 0-1 ✅:** Pivot or Kill! (Re-think value prop)

---

## 🎯 Why This Plan Works

### 1. **Focused Scope**
- We're building 1 thing well (Confluence Score)
- Not 10 things poorly
- Clear what's in/out

### 2. **Continuous Validation**
- Test at EVERY milestone
- Real users involved early (Week 9)
- Data-driven decisions (not gut feel)

### 3. **Fast Feedback Loops**
- 4-week cycles (not 6 months to first user)
- Beta in Week 9 (not after "finishing")
- Can pivot quickly if wrong

### 4. **Risk Mitigation**
- Paper trading first (no real money lost)
- Small beta (10 users, not 1,000)
- Paid test early (Week 11, not after launch)

### 5. **Built-in Learning**
- Each phase teaches us something
- Backtests → Do strategies work?
- Beta → Do users care?
- Monetization test → Will they pay?

---

## 🚨 What Could Go Wrong (& How to Handle)

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Data sources unreliable** | Medium | High | Have 2 backup sources for each layer |
| **Users don't understand scores** | High | High | Extensive UX testing (Week 4, 8) |
| **Strategies don't backtest well** | Medium | High | Start with proven ones (RSI, QGLP) |
| **No one signs up** | Medium | Critical | Reddit marketing + referrals |
| **No one pays** | High | Critical | Free tier to prove value first |
| **SEBI regulation issues** | Low | Critical | Legal review in Week 11 |

**Contingency:** If we hit a blocker, we have decision gates to pivot (not blindly continue).

---

## ✅ The Ultimate Success Criteria

**By Week 12, we need:**

1. **Proof of Value**
   - Users log in 3x+ per week
   - They take actions based on recommendations
   - Testimonial: "This helped me make better decisions"

2. **Proof of Willingness to Pay**
   - 3-5 paying customers @ ₹999+/month
   - LTV > CAC (customer pays more than we spent acquiring them)

3. **Proof of Scalability**
   - System handles 50 users without breaking
   - Can add 10 users/week sustainably
   - Code is maintainable (not spaghetti)

**If we have all 3:** This is a BUSINESS. Scale it.  
**If we have 1-2:** This is a PRODUCT. Iterate.  
**If we have 0:** This is a LEARNING. Pivot or kill.

---

## 🎓 Final Thoughts

**This MVP is about LEARNING, not LAUNCHING.**

We're testing 3 hypotheses:
1. **Do users want intelligent stock recommendations?** (Product-market fit)
2. **Does Confluence scoring actually help?** (Technical validation)
3. **Will they pay for it?** (Business model validation)

**12 weeks to answer these questions** is aggressive but doable.

**The alternative?**  
Build for 6 months in isolation, launch to crickets, realize we built the wrong thing.

**This plan?**  
Build for 8 weeks, test with real users in Week 9, iterate based on feedback, launch with paying customers in Week 12.

**Which sounds smarter?** 🎯

---

**Next Steps:**
1. Review this plan
2. Commit to the 12-week timeline
3. Start Week 1 (Data Pipeline setup)

**Let's build! 🚀**
