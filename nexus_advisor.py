"""
Nexus AI Advisor - Phase 3
Claude-powered AI that learns from trades and provides recommendations.

This module uses Claude Sonnet to:
1. Analyze trade patterns and win/loss rates
2. Identify which parameters work best
3. Recommend parameter adjustments
4. Suggest stocks to focus on or avoid
5. Detect anomalies and red flags
6. Provide confluence-scored recommendations
"""

import anthropic
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database.analytics_migration import AnalyticsDatabase

logger = logging.getLogger("nexus_advisor")


class NexusAdvisor:
    """
    AI advisor that analyzes trading performance and generates recommendations.
    Uses Claude Sonnet for deep analysis.
    """

    def __init__(self, analytics_db: Optional[AnalyticsDatabase] = None,
                 api_key: Optional[str] = None):
        """
        Initialize Nexus Advisor.

        Args:
            analytics_db: AnalyticsDatabase instance
            api_key: Anthropic API key (from env if not provided)
        """
        self.analytics_db = analytics_db or AnalyticsDatabase()

        # Initialize Claude client
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"  # Most capable for analysis

        self.last_analysis_time = None
        self.analysis_cache = None
        self.cache_duration = 3600  # 1 hour cache

    def get_recent_trades(self, days: int = 7) -> List[Dict]:
        """
        Get recent trades with their analysis and market context.

        Args:
            days: Number of days of history to analyze

        Returns:
            List of trade analysis records
        """
        try:
            conn = self.analytics_db.conn
            cursor = conn.cursor()

            # Query trades from the last N days with market context
            cursor.execute("""
                SELECT
                    ta.id,
                    ta.symbol,
                    ta.timestamp,
                    ta.action,
                    ta.rsi_value,
                    ta.reason,
                    ta.entry_price,
                    ta.exit_price,
                    ta.pnl,
                    ta.pnl_pct,
                    ta.strategy,
                    ta.parameters_used,
                    ta.nifty_50_change_pct,
                    ta.market_volatility,
                    ta.market_regime,
                    ta.sector_performance
                FROM trade_analysis ta
                WHERE datetime(ta.created_at) >= datetime('now', ?)
                ORDER BY ta.created_at DESC
            """, (f"-{days} days",))

            rows = cursor.fetchall()
            trades = []

            for row in rows:
                trade_dict = {
                    'id': row[0],
                    'symbol': row[1],
                    'timestamp': row[2],
                    'action': row[3],
                    'rsi_value': row[4],
                    'reason': row[5],
                    'entry_price': row[6],
                    'exit_price': row[7],
                    'pnl': row[8],
                    'pnl_pct': row[9],
                    'strategy': row[10],
                    'parameters_used': json.loads(row[11]) if row[11] else {},
                    'nifty_50_change_pct': row[12],
                    'market_volatility': row[13],
                    'market_regime': row[14],
                    'sector_performance': json.loads(row[15]) if row[15] else {}
                }
                trades.append(trade_dict)

            return trades

        except Exception as e:
            logger.error(f"Error fetching recent trades: {e}")
            return []

    def calculate_performance_metrics(self, trades: List[Dict]) -> Dict:
        """
        Calculate performance metrics from trade list.

        Returns:
            {
                'total_trades': int,
                'winning_trades': int,
                'losing_trades': int,
                'neutral_trades': int,
                'win_rate': float (0-100),
                'avg_profit': float,
                'avg_loss': float,
                'profit_factor': float,
                'by_symbol': {symbol: metrics},
                'by_regime': {regime: metrics},
                'by_rsi': {range: metrics}
            }
        """
        if not trades:
            return {}

        total = len(trades)
        winning = sum(1 for t in trades if t.get('pnl') and t['pnl'] > 0)
        losing = sum(1 for t in trades if t.get('pnl') and t['pnl'] < 0)
        neutral = sum(1 for t in trades if t.get('pnl') is None or t['pnl'] == 0)

        win_rate = (winning / total * 100) if total > 0 else 0

        # Calculate profit/loss
        profits = [t['pnl'] for t in trades if t.get('pnl') and t['pnl'] > 0]
        losses = [abs(t['pnl']) for t in trades if t.get('pnl') and t['pnl'] < 0]

        avg_profit = sum(profits) / len(profits) if profits else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        total_profit = sum(profits) if profits else 0
        total_loss = sum(losses) if losses else 0

        profit_factor = total_profit / total_loss if total_loss > 0 else (1 if total_profit > 0 else 0)

        # Analyze by symbol
        by_symbol = {}
        for symbol in set(t['symbol'] for t in trades):
            symbol_trades = [t for t in trades if t['symbol'] == symbol]
            symbol_wins = sum(1 for t in symbol_trades if t.get('pnl') and t['pnl'] > 0)
            total_pnl = sum((t.get('pnl') or 0) for t in symbol_trades)
            by_symbol[symbol] = {
                'trades': len(symbol_trades),
                'wins': symbol_wins,
                'win_rate': (symbol_wins / len(symbol_trades) * 100) if symbol_trades else 0,
                'total_pnl': total_pnl
            }

        # Analyze by market regime
        by_regime = {}
        for regime in set(t.get('market_regime', 'UNKNOWN') for t in trades if t.get('market_regime')):
            regime_trades = [t for t in trades if t.get('market_regime') == regime]
            regime_wins = sum(1 for t in regime_trades if t.get('pnl') and t['pnl'] > 0)
            regime_pnls = [t.get('pnl') for t in regime_trades if t.get('pnl') is not None]
            by_regime[regime] = {
                'trades': len(regime_trades),
                'wins': regime_wins,
                'win_rate': (regime_wins / len(regime_trades) * 100) if regime_trades else 0,
                'avg_pnl': sum(regime_pnls) / len(regime_pnls) if regime_pnls else 0
            }

        return {
            'total_trades': total,
            'winning_trades': winning,
            'losing_trades': losing,
            'neutral_trades': neutral,
            'win_rate': round(win_rate, 2),
            'avg_profit': round(avg_profit, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'by_symbol': by_symbol,
            'by_regime': by_regime
        }

    def analyze_with_claude(self, trades: List[Dict], metrics: Dict) -> Optional[str]:
        """
        Send trades and metrics to Claude for analysis.

        Returns:
            Claude's analysis as a string
        """
        if not trades:
            logger.warning("No trades to analyze")
            return None

        # Build analysis prompt
        prompt = f"""
You are an expert trading advisor analyzing a trader's recent performance.
The trader uses RSI Mean Reversion strategy on Indian stocks (NSE).

TRADING PERFORMANCE (Last 7 Days):
{json.dumps(metrics, indent=2)}

RECENT TRADES (with market context):
{json.dumps(trades[:10], indent=2)}

Provide a concise analysis covering:

1. **Win/Loss Patterns**: What do winning trades have in common? What about losing trades?

2. **Market Regime Impact**: How does the strategy perform in different market conditions?
   - UPTREND: Win rate and performance
   - DOWNTREND: Win rate and performance
   - SIDEWAYS: Win rate and performance
   - OVERBOUGHT/OVERSOLD: Performance

3. **Stock-Specific Performance**: Which stocks should we focus on? Which to avoid?

4. **Parameter Recommendations**: Based on the data, should we adjust:
   - Buy RSI threshold (currently 35)?
   - Sell RSI threshold (currently 65)?
   - Position size?
   - Holding period?

5. **Market Condition Alerts**: When should we NOT trade or reduce size?

6. **Confidence Scores**: For each recommendation, how confident are you (0-100)?

7. **Red Flags**: Any anomalies or concerning patterns?

Format your response with clear sections. Be specific with numbers and data references.
"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis = message.content[0].text
            logger.info("Claude analysis completed successfully")
            return analysis

        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return None

    def extract_recommendations(self, claude_analysis: str) -> List[Dict]:
        """
        Extract structured recommendations from Claude's analysis.
        Parses Claude's response and creates recommendation records.

        Returns:
            List of recommendation dictionaries
        """
        if not claude_analysis:
            return []

        try:
            # Build extraction prompt
            extraction_prompt = f"""
From this trading analysis, extract specific recommendations in JSON format.
For each recommendation, provide:
- symbol: Stock symbol (or "GENERAL" for non-stock-specific)
- signal: BUY, SELL, HOLD, AVOID, or TWEAK_PARAMS
- reason: Brief explanation
- confluence_score: 0-100 (how many signals align)
- confidence: 0-1
- recommended_action: What specific action to take
- stop_loss_pct: Suggested stop loss (optional)
- profit_target_pct: Suggested profit target (optional)

ANALYSIS TO EXTRACT FROM:
{claude_analysis}

Respond ONLY with valid JSON array. Example:
[
  {{
    "symbol": "INFY",
    "signal": "BUY",
    "reason": "Strong RSI reversal + sector strength",
    "confluence_score": 85,
    "confidence": 0.82,
    "recommended_action": "Increase position size by 20%",
    "stop_loss_pct": 2.5,
    "profit_target_pct": 5.0
  }}
]
"""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": extraction_prompt}]
            )

            response_text = message.content[0].text

            # Parse JSON from response
            try:
                recommendations = json.loads(response_text)
                logger.info(f"Extracted {len(recommendations)} recommendations")
                return recommendations if isinstance(recommendations, list) else []
            except json.JSONDecodeError:
                logger.warning("Could not parse JSON from Claude response")
                return []

        except Exception as e:
            logger.error(f"Error extracting recommendations: {e}")
            return []

    def store_recommendations(self, recommendations: List[Dict]) -> List[int]:
        """
        Store recommendations in the database.

        Returns:
            List of recommendation IDs
        """
        stored_ids = []

        for rec in recommendations:
            try:
                rec_id = self.analytics_db.insert_recommendation(
                    symbol=rec.get('symbol', 'GENERAL'),
                    signal=rec.get('signal', 'HOLD'),
                    reason=rec.get('reason', ''),
                    confluence_score=rec.get('confluence_score', 50),
                    confidence=rec.get('confidence', 0.5),
                    recommended_action=rec.get('recommended_action'),
                    stop_loss_pct=rec.get('stop_loss_pct'),
                    profit_target_pct=rec.get('profit_target_pct'),
                    why_we_like_it=rec.get('why_we_like_it'),
                    expires_at=(datetime.now() + timedelta(days=7)).isoformat()  # Valid for 7 days
                )

                if rec_id > 0:
                    stored_ids.append(rec_id)
                    logger.info(f"Stored recommendation ID {rec_id}: {rec.get('symbol')} {rec.get('signal')}")

            except Exception as e:
                logger.error(f"Error storing recommendation: {e}")

        return stored_ids

    def run_analysis(self, days: int = 7) -> Dict:
        """
        Run complete analysis: fetch trades → analyze with Claude → store recommendations.

        Returns:
            {
                'status': 'success' | 'error',
                'trades_analyzed': int,
                'recommendations_generated': int,
                'recommendation_ids': [int],
                'analysis_summary': str,
                'error': str (if any)
            }
        """
        result = {
            'status': 'success',
            'trades_analyzed': 0,
            'recommendations_generated': 0,
            'recommendation_ids': [],
            'analysis_summary': '',
            'error': None
        }

        try:
            # Step 1: Get recent trades
            trades = self.get_recent_trades(days=days)
            result['trades_analyzed'] = len(trades)

            if not trades:
                logger.warning(f"No trades found in last {days} days")
                result['status'] = 'warning'
                result['error'] = "No trades to analyze"
                return result

            logger.info(f"Analyzing {len(trades)} trades from last {days} days")

            # Step 2: Calculate metrics
            metrics = self.calculate_performance_metrics(trades)
            logger.info(f"Performance: {metrics['total_trades']} trades, "
                       f"Win rate: {metrics.get('win_rate', 0):.1f}%")

            # Step 3: Send to Claude for analysis
            analysis = self.analyze_with_claude(trades, metrics)
            if not analysis:
                result['status'] = 'error'
                result['error'] = "Claude API call failed"
                return result

            result['analysis_summary'] = analysis[:500]  # First 500 chars as summary

            # Step 4: Extract structured recommendations
            recommendations = self.extract_recommendations(analysis)
            result['recommendations_generated'] = len(recommendations)

            # Step 5: Store in database
            stored_ids = self.store_recommendations(recommendations)
            result['recommendation_ids'] = stored_ids

            logger.info(f"Analysis complete: {len(recommendations)} recommendations generated")
            return result

        except Exception as e:
            logger.error(f"Error in analysis pipeline: {e}")
            result['status'] = 'error'
            result['error'] = str(e)
            return result

    def get_active_recommendations(self, symbol: Optional[str] = None,
                                   min_confidence: float = 0.6,
                                   limit: int = 20) -> List[Dict]:
        """
        Get active recommendations from database.

        Args:
            symbol: Filter by stock (or None for all)
            min_confidence: Minimum confidence threshold
            limit: Max recommendations to return

        Returns:
            List of recommendation records
        """
        return self.analytics_db.get_recommendations(
            symbol=symbol,
            min_confidence=min_confidence,
            limit=limit
        )


if __name__ == "__main__":
    """Test Nexus Advisor"""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(message)s'
    )

    print("Testing Nexus AI Advisor...\n")

    advisor = NexusAdvisor()

    print("1. Fetching recent trades...")
    trades = advisor.get_recent_trades(days=7)
    print(f"   Found {len(trades)} trades")

    if len(trades) > 0:
        print("\n2. Calculating performance metrics...")
        metrics = advisor.calculate_performance_metrics(trades)
        print(f"   Win rate: {metrics.get('win_rate', 0):.1f}%")
        print(f"   Total trades: {metrics.get('total_trades', 0)}")
        print(f"   Profit factor: {metrics.get('profit_factor', 0):.2f}")

        print("\n3. Sending analysis to Claude...")
        result = advisor.run_analysis(days=7)

        if result['status'] == 'success':
            print(f"   Status: {result['status']}")
            print(f"   Trades analyzed: {result['trades_analyzed']}")
            print(f"   Recommendations generated: {result['recommendations_generated']}")
            print(f"   Recommendation IDs: {result['recommendation_ids']}")
            print(f"\n   Analysis Summary:")
            print(f"   {result['analysis_summary']}\n")

            print("4. Fetching active recommendations...")
            recs = advisor.get_active_recommendations(min_confidence=0.6)
            for rec in recs:
                print(f"   {rec['symbol']}: {rec['signal']} (confidence: {rec['confidence']:.0%})")

            print("\nSUCCESS: Nexus Advisor is working!")
        else:
            print(f"   Error: {result['error']}")
    else:
        print("   WARNING: No trades to analyze. Run the bot first to generate trade data.")
