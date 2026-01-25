# ARUN Trading Bot - Architecture Overview

**Version**: 4.0 (Proposed)
**Date**: January 25, 2026
**Status**: Architecture Modernization Plan

---

## Table of Contents

1. [Current Architecture (v3.0)](#current-architecture-v30)
2. [Problems with Current Design](#problems-with-current-design)
3. [Proposed Architecture (v4.0)](#proposed-architecture-v40)
4. [Service Layer Design](#service-layer-design)
5. [Data Flow Diagrams](#data-flow-diagrams)
6. [Technology Stack](#technology-stack)
7. [Design Patterns](#design-patterns)
8. [Scalability Considerations](#scalability-considerations)
9. [Migration Strategy](#migration-strategy)
10. [API Specifications](#api-specifications)

---

## Current Architecture (v3.0)

### System Overview

```
┌───────────────────────────────────────────────────────────┐
│                    Desktop Application                    │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────┐     │
│  │     CustomTkinter GUI (dashboard_v2.py)         │     │
│  │  - Position Table                               │     │
│  │  - Settings Management                          │     │
│  │  - Start/Stop Controls                          │     │
│  │                                                  │     │
│  │  Direct Access to Global Variables ↓            │     │
│  └─────────────────────────────────────────────────┘     │
│                                                           │
│  ┌─────────────────────────────────────────────────┐     │
│  │  Monolithic Trading Engine (kickstart.py)       │     │
│  │                                                  │     │
│  │  Global State (20+ variables):                  │     │
│  │    - STOP_REQUESTED                             │     │
│  │    - OFFLINE                                    │     │
│  │    - CYCLE_QUOTES                               │     │
│  │    - portfolio_state                            │     │
│  │    - CANDLE_CACHE                               │     │
│  │                                                  │     │
│  │  Mixed Responsibilities:                        │     │
│  │    ├─ Trading Logic                             │     │
│  │    ├─ Market Data Fetching                      │     │
│  │    ├─ Risk Management                           │     │
│  │    ├─ Order Execution                           │     │
│  │    ├─ Position Management                       │     │
│  │    └─ Notification Sending                      │     │
│  └─────────────────────────────────────────────────┘     │
│                                                           │
│  ┌─────────────────────────────────────────────────┐     │
│  │         Supporting Modules                       │     │
│  │  ┌──────────────┐  ┌──────────────┐             │     │
│  │  │ risk_manager │  │ notifications │             │     │
│  │  └──────────────┘  └──────────────┘             │     │
│  │  ┌──────────────┐  ┌──────────────┐             │     │
│  │  │ state_manager│  │ getRSI        │             │     │
│  │  └──────────────┘  └──────────────┘             │     │
│  └─────────────────────────────────────────────────┘     │
│                                                           │
└───────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────┐
│                    External Dependencies                  │
├───────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐                  │
│  │ SQLite DB      │  │ mStock API     │                  │
│  │ (trades.db)    │  │ (hardcoded)    │                  │
│  └────────────────┘  └────────────────┘                  │
│  ┌────────────────┐  ┌────────────────┐                  │
│  │ Telegram API   │  │ Local Files    │                  │
│  │                │  │ (settings.json)│                  │
│  └────────────────┘  └────────────────┘                  │
└───────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### 1. User Interface Layer
- **File**: `dashboard_v2.py`
- **Technology**: CustomTkinter (Python GUI framework)
- **Responsibilities**:
  - Display positions, P&L, trading activity
  - Settings management (7 tabs)
  - Start/Stop bot controls
  - Real-time updates via polling

**Issues**:
- Directly accesses global variables (tight coupling)
- Polling-based updates (inefficient)
- Desktop-only (no web/mobile access)

#### 2. Business Logic Layer
- **File**: `kickstart.py` (2,463 lines)
- **Technology**: Python synchronous programming
- **Responsibilities**: Everything (God Object anti-pattern)

**Issues**:
- No separation of concerns
- Impossible to test individual components
- Cannot scale horizontally
- Difficult to maintain

#### 3. Data Layer
- **File**: `database/trades_db.py`
- **Technology**: SQLite with pandas
- **Responsibilities**: Trade logging, P&L tracking

**Issues**:
- Thread safety violations
- Limited concurrency support
- No connection pooling
- Cannot scale to multiple users

---

## Problems with Current Design

### 1. Monolithic Architecture

**Problem**: All logic in single 2,463-line file

**Consequences**:
- **Maintenance Nightmare**: Finding relevant code is difficult
- **Testing Impossible**: Cannot test components in isolation
- **Tight Coupling**: Changing one part breaks others
- **Knowledge Silos**: Only original developer understands flow

**Example**:
```python
# kickstart.py - Everything mixed together
def run_cycle():
    # 300 lines doing:
    # - Fetch market data
    # - Calculate RSI
    # - Check risk limits
    # - Place orders
    # - Update portfolio
    # - Send notifications
    # - Log trades
    # All in one function!
```

---

### 2. Global State Overload

**Problem**: 20+ global variables managing state

**Consequences**:
- **Race Conditions**: Multiple threads access without locks
- **Hidden Dependencies**: Functions rely on globals not in signature
- **Testing Difficult**: Must manipulate global state
- **Debugging Hard**: State changes happen anywhere

**Example**:
```python
# Global variables scattered throughout
STOP_REQUESTED = False
OFFLINE = False
CYCLE_QUOTES = {}
portfolio_state = {}
CANDLE_CACHE = {}
INSUFFICIENT_HISTORY_TS = {}
LAST_CYCLE_TIME = None
# ... 13 more

# Functions with hidden dependencies
def place_order(symbol, qty):
    # Relies on globals not in signature
    if STOP_REQUESTED:  # Hidden dependency
        return
    if OFFLINE:  # Hidden dependency
        return
    # ...
```

---

### 3. Synchronous Blocking Operations

**Problem**: API calls block entire trading cycle

**Consequences**:
- **Poor Performance**: 5-8 seconds per cycle
- **Limited Scalability**: Cannot handle 100+ symbols
- **Timeout Issues**: One slow API call blocks everything
- **Missed Opportunities**: Cannot process signals in parallel

**Example**:
```python
# Current: Blocks for every symbol
for symbol in symbols:
    quote = fetch_quote(symbol)  # Blocks 200ms
    candles = fetch_candles(symbol)  # Blocks 300ms
    # Total: 500ms × 10 symbols = 5 seconds wasted!

# Could be: All in parallel (500ms total for 10 symbols)
async def run_cycle_async():
    tasks = [process_symbol(symbol) for symbol in symbols]
    await asyncio.gather(*tasks)
```

---

### 4. Single Broker Lock-in

**Problem**: mStock API calls hardcoded throughout

**Consequences**:
- **No Portability**: Cannot switch to Zerodha, Interactive Brokers
- **Vendor Risk**: Dependent on single broker's API stability
- **Limited Market**: Can only serve mStock users
- **Difficult Migration**: Broker logic scattered across files

**Example**:
```python
# Hardcoded mStock API calls everywhere
resp = mstock_api.get_positions()
resp = mstock_api.place_order(...)
resp = mstock_api.get_quote(...)

# Should be: Abstracted behind interface
resp = broker.get_positions()  # Works with any broker
```

---

### 5. No Service Boundaries

**Problem**: Business logic, data access, and presentation mixed

**Consequences**:
- **Cannot Reuse**: Logic tied to specific UI
- **Cannot Test**: No way to test without running entire app
- **Cannot Scale**: All or nothing deployment
- **Cannot Evolve**: Changes ripple across entire codebase

---

## Proposed Architecture (v4.0)

### Service-Oriented Architecture (SOA)

```
┌─────────────────────────────────────────────────────────────┐
│                      Presentation Layer                     │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │   Web UI         │  │  Desktop UI      │                │
│  │   (React)        │  │  (CustomTkinter) │                │
│  └────────┬─────────┘  └────────┬─────────┘                │
│           │                     │                           │
│           └──────────┬──────────┘                           │
└──────────────────────┼──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  API Gateway Layer                          │
│              (FastAPI - REST + WebSocket)                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Endpoints:                                        │    │
│  │    GET  /api/positions                            │    │
│  │    POST /api/orders                               │    │
│  │    WS   /ws/live-quotes                           │    │
│  │    GET  /api/analytics/performance                │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Service Layer (Async)                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Trading Engine   │  │ Market Data Svc  │                │
│  │ Service          │  │                  │                │
│  │ ┌──────────────┐ │  │ ┌──────────────┐ │                │
│  │ │ Signal Gen   │ │  │ │ Quote Feed   │ │                │
│  │ │ Entry/Exit   │ │  │ │ Candle Cache │ │                │
│  │ │ Position Mgmt│ │  │ │ WS Handler   │ │                │
│  │ └──────────────┘ │  │ └──────────────┘ │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Risk Management  │  │ Order Management │                │
│  │ Service          │  │ Service          │                │
│  │ ┌──────────────┐ │  │ ┌──────────────┐ │                │
│  │ │ Position Lmt │ │  │ │ Order Queue  │ │                │
│  │ │ Drawdown Mon │ │  │ │ Retry Logic  │ │                │
│  │ │ Circuit Break│ │  │ │ Status Track │ │                │
│  │ └──────────────┘ │  │ └──────────────┘ │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Portfolio        │  │ Notification     │                │
│  │ Service          │  │ Service          │                │
│  │ ┌──────────────┐ │  │ ┌──────────────┐ │                │
│  │ │ P&L Tracking │ │  │ │ Telegram Bot │ │                │
│  │ │ Holdings     │ │  │ │ Email/SMS    │ │                │
│  │ │ Analytics    │ │  │ │ Push Notifs  │ │                │
│  │ └──────────────┘ │  │ └──────────────┘ │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  Data Access Layer                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Trade Repository │  │ Position Repo    │                │
│  │                  │  │                  │                │
│  └────────┬─────────┘  └────────┬─────────┘                │
│           │                     │                           │
│           └──────────┬──────────┘                           │
└──────────────────────┼──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    Data Storage Layer                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ PostgreSQL   │  │ Redis Cache  │  │ TimescaleDB      │  │
│  │              │  │              │  │ (Market Data     │  │
│  │ - Trades     │  │ - Quotes     │  │  Timeseries)     │  │
│  │ - Positions  │  │ - Sessions   │  │                  │  │
│  │ - Users      │  │ - Locks      │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│               Broker Adapter Layer (Plugin)                 │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ mStock       │  │ Zerodha      │  │ Interactive      │  │
│  │ Adapter      │  │ Adapter      │  │ Brokers Adapter  │  │
│  │              │  │              │  │                  │  │
│  │ - Auth       │  │ - Auth       │  │ - Auth           │  │
│  │ - Orders     │  │ - Orders     │  │ - Orders         │  │
│  │ - Quotes     │  │ - Quotes     │  │ - Quotes         │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Service Layer Design

### 1. Trading Engine Service

**Responsibility**: Core trading logic and signal generation

**Interface**:
```python
class TradingEngineService:
    def __init__(self,
                 market_data: MarketDataService,
                 order_service: OrderManagementService,
                 risk_service: RiskManagementService,
                 portfolio_service: PortfolioService):
        self.market_data = market_data
        self.orders = order_service
        self.risk = risk_service
        self.portfolio = portfolio_service

    async def run_trading_cycle(self) -> CycleResult:
        """Execute one trading cycle for all active symbols"""
        pass

    async def evaluate_buy_conditions(self, symbol: str) -> Optional[BuySignal]:
        """Check if symbol meets buy criteria"""
        pass

    async def evaluate_sell_conditions(self, position: Position) -> Optional[SellSignal]:
        """Check if position should be exited"""
        pass

    async def execute_entry(self, signal: BuySignal) -> OrderResult:
        """Place entry order for buy signal"""
        pass

    async def execute_exit(self, signal: SellSignal) -> OrderResult:
        """Place exit order for sell signal"""
        pass
```

**Key Features**:
- Async/await for non-blocking operations
- Dependency injection for testability
- Clear separation of concerns
- Event-driven architecture

---

### 2. Market Data Service

**Responsibility**: Real-time quotes, candle data, WebSocket feeds

**Interface**:
```python
class MarketDataService:
    def __init__(self, broker_adapter: BrokerAdapter, cache: RedisCache):
        self.broker = broker_adapter
        self.cache = cache

    async def get_quote(self, symbol: str) -> Quote:
        """Get latest quote with caching"""
        # Check cache first
        cached = await self.cache.get(f"quote:{symbol}")
        if cached and not self._is_stale(cached):
            return cached

        # Fetch from broker
        quote = await self.broker.get_quote(symbol)
        await self.cache.set(f"quote:{symbol}", quote, ttl=5)
        return quote

    async def get_candles(self, symbol: str, timeframe: str, limit: int) -> List[Candle]:
        """Get historical candle data with smart caching"""
        pass

    async def subscribe_live_quotes(self, symbols: List[str], callback: Callable):
        """Subscribe to WebSocket live quote feed"""
        pass

    async def calculate_rsi(self, symbol: str, period: int = 14) -> float:
        """Calculate RSI indicator"""
        pass
```

**Key Features**:
- Multi-level caching (Redis + in-memory)
- WebSocket support for real-time data
- Smart cache invalidation
- Parallel data fetching

---

### 3. Risk Management Service

**Responsibility**: Position limits, drawdown monitoring, circuit breakers

**Interface**:
```python
class RiskManagementService:
    def __init__(self, config: RiskConfig, portfolio: PortfolioService):
        self.config = config
        self.portfolio = portfolio

    async def check_entry_allowed(self, symbol: str, quantity: int, price: float) -> RiskCheckResult:
        """Verify if new position passes risk checks"""
        # Check position size limits
        if not self._check_position_limit(symbol, quantity, price):
            return RiskCheckResult(allowed=False, reason="Position limit exceeded")

        # Check portfolio concentration
        if not self._check_concentration(symbol, quantity, price):
            return RiskCheckResult(allowed=False, reason="Concentration limit exceeded")

        # Check available capital
        if not await self._check_capital(quantity, price):
            return RiskCheckResult(allowed=False, reason="Insufficient capital")

        return RiskCheckResult(allowed=True)

    async def monitor_drawdown(self) -> Optional[CircuitBreakerEvent]:
        """Monitor for drawdown threshold breach"""
        pass

    async def check_exit_conditions(self, position: Position) -> ExitRecommendation:
        """Check if position should be force-closed for risk"""
        pass
```

**Key Features**:
- Pre-trade risk validation
- Real-time drawdown monitoring
- Automatic circuit breakers
- Portfolio-level risk aggregation

---

### 4. Order Management Service

**Responsibility**: Order placement, retry logic, status tracking

**Interface**:
```python
class OrderManagementService:
    def __init__(self, broker_adapter: BrokerAdapter, trade_repo: TradeRepository):
        self.broker = broker_adapter
        self.trades = trade_repo
        self.order_queue = asyncio.Queue()

    async def place_order(self, order: Order) -> OrderResult:
        """Place order with automatic retry logic"""
        for attempt in range(3):  # Retry up to 3 times
            try:
                result = await self.broker.place_order(order)
                if result.success:
                    await self.trades.save_trade(result.trade)
                    return result
            except BrokerAPIError as e:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise

    async def get_order_status(self, order_id: str) -> OrderStatus:
        """Check status of placed order"""
        pass

    async def cancel_order(self, order_id: str) -> bool:
        """Attempt to cancel pending order"""
        pass
```

**Key Features**:
- Automatic retry with exponential backoff
- Order queue for rate limiting
- Comprehensive logging
- Status tracking

---

### 5. Portfolio Service

**Responsibility**: Position tracking, P&L calculation, analytics

**Interface**:
```python
class PortfolioService:
    def __init__(self, position_repo: PositionRepository, market_data: MarketDataService):
        self.positions = position_repo
        self.market_data = market_data

    async def get_open_positions(self) -> List[Position]:
        """Get all open positions with live P&L"""
        positions = await self.positions.get_open()
        for pos in positions:
            quote = await self.market_data.get_quote(pos.symbol)
            pos.current_price = quote.ltp
            pos.unrealized_pnl = self._calculate_pnl(pos)
        return positions

    async def get_portfolio_summary(self) -> PortfolioSummary:
        """Get overall portfolio metrics"""
        pass

    async def update_position(self, position: Position):
        """Update position details"""
        pass

    def _calculate_pnl(self, position: Position) -> float:
        """Calculate P&L for position"""
        return (position.current_price - position.entry_price) * position.quantity
```

**Key Features**:
- Real-time P&L calculation
- Historical performance tracking
- Position aggregation
- Analytics generation

---

### 6. Notification Service

**Responsibility**: Multi-channel alerts (Telegram, Email, SMS, Push)

**Interface**:
```python
class NotificationService:
    def __init__(self, config: NotificationConfig):
        self.telegram = TelegramClient(config.telegram_token)
        self.email = EmailClient(config.smtp_settings)
        self.sms = SMSClient(config.sms_provider)

    async def send_notification(self, event: NotificationEvent):
        """Send notification via configured channels"""
        tasks = []
        if self.config.telegram_enabled:
            tasks.append(self.telegram.send(event.message))
        if self.config.email_enabled:
            tasks.append(self.email.send(event.message))
        if self.config.sms_enabled:
            tasks.append(self.sms.send(event.message))

        await asyncio.gather(*tasks, return_exceptions=True)

    async def send_trade_alert(self, trade: Trade):
        """Specialized alert for trade execution"""
        pass

    async def send_risk_alert(self, risk_event: RiskEvent):
        """Specialized alert for risk events"""
        pass
```

---

## Data Flow Diagrams

### Trading Cycle Flow

```
┌─────────────────┐
│ Trading Engine  │
│ Service         │
└────────┬────────┘
         │ 1. Start cycle
         ▼
┌─────────────────┐
│ Market Data Svc │◄───────┐
│                 │        │
│ Fetch quotes    │        │ 3. Return quotes
│ and candles     │        │
└────────┬────────┘        │
         │ 2. Request data │
         ▼                 │
┌─────────────────┐        │
│ Broker Adapter  │────────┘
│ (mStock/Zerodha)│
└─────────────────┘

         │
         │ 4. Quotes received
         ▼
┌─────────────────┐
│ Trading Engine  │
│                 │
│ Evaluate signals│
└────────┬────────┘
         │ 5. BuySignal generated
         ▼
┌─────────────────┐
│ Risk Mgmt Svc   │
│                 │
│ Check limits    │
└────────┬────────┘
         │ 6. Risk check passed
         ▼
┌─────────────────┐
│ Order Mgmt Svc  │
│                 │
│ Place order     │
└────────┬────────┘
         │ 7. Order placed
         ▼
┌─────────────────┐
│ Portfolio Svc   │
│                 │
│ Update position │
└────────┬────────┘
         │ 8. Position updated
         ▼
┌─────────────────┐
│ Notification Svc│
│                 │
│ Send alert      │
└─────────────────┘
```

---

### User Request Flow (Web UI)

```
┌─────────────────┐
│  React Web UI   │
│                 │
│ User clicks     │
│ "Close Position"│
└────────┬────────┘
         │ HTTP POST /api/orders/close
         ▼
┌─────────────────┐
│  API Gateway    │
│  (FastAPI)      │
│                 │
│  - Authenticate │
│  - Validate     │
└────────┬────────┘
         │ Call service method
         ▼
┌─────────────────┐
│ Trading Engine  │
│ Service         │
│                 │
│ close_position()│
└────────┬────────┘
         │ Delegate to order service
         ▼
┌─────────────────┐
│ Order Mgmt Svc  │
│                 │
│ place_order()   │
└────────┬────────┘
         │ Execute via broker
         ▼
┌─────────────────┐
│ Broker Adapter  │
│                 │
│ API call        │
└────────┬────────┘
         │ Order confirmed
         ▼
┌─────────────────┐
│ Portfolio Svc   │
│                 │
│ Update holdings │
└────────┬────────┘
         │ WebSocket event
         ▼
┌─────────────────┐
│  API Gateway    │
│  (WebSocket)    │
│                 │
│ Push update     │
└────────┬────────┘
         │ Live update
         ▼
┌─────────────────┐
│  React Web UI   │
│                 │
│ Position removed│
│ from table      │
└─────────────────┘
```

---

## Technology Stack

### Backend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API Framework** | FastAPI | REST + WebSocket endpoints |
| **Async Runtime** | asyncio + uvloop | High-performance async I/O |
| **Database** | PostgreSQL 15 | Primary data store |
| **Cache** | Redis 7 | Hot data, sessions, locks |
| **Time-series DB** | TimescaleDB | Market data storage |
| **Message Queue** | RabbitMQ / Redis Pub/Sub | Event-driven communication |
| **Authentication** | JWT + OAuth2 | Secure auth with refresh tokens |
| **ORM** | SQLAlchemy 2.0 (async) | Database abstraction |
| **Testing** | pytest + pytest-asyncio | Unit and integration tests |
| **Monitoring** | Prometheus + Grafana | Metrics and dashboards |
| **Logging** | structlog + ELK Stack | Centralized logging |

### Frontend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | React 18 | UI library |
| **Language** | TypeScript | Type safety |
| **State** | Redux Toolkit + RTK Query | State management |
| **UI Library** | Material-UI (MUI) | Component library |
| **Charts** | TradingView Lightweight | Trading charts |
| **Real-time** | Socket.IO | WebSocket client |
| **Build Tool** | Vite | Fast builds |
| **Styling** | Tailwind CSS | Utility-first CSS |

### Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Containerization** | Docker + Docker Compose | Container packaging |
| **Orchestration** | Kubernetes (k8s) | Container orchestration |
| **CI/CD** | GitHub Actions | Automated testing/deployment |
| **Cloud** | AWS / GCP / DigitalOcean | Hosting |
| **CDN** | Cloudflare | Static asset delivery |
| **Monitoring** | DataDog / New Relic | APM and alerting |

---

## Design Patterns

### 1. Dependency Injection

**Pattern**: Constructor injection for all dependencies

**Example**:
```python
class TradingEngineService:
    def __init__(self,
                 market_data: MarketDataService,
                 order_service: OrderManagementService,
                 risk_service: RiskManagementService):
        self.market_data = market_data
        self.orders = order_service
        self.risk = risk_service

# Usage with DI container
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    broker_adapter = providers.Singleton(
        MStockAdapter,
        api_key=config.broker.api_key
    )

    market_data = providers.Singleton(
        MarketDataService,
        broker_adapter=broker_adapter
    )

    order_service = providers.Singleton(
        OrderManagementService,
        broker_adapter=broker_adapter
    )

    trading_engine = providers.Singleton(
        TradingEngineService,
        market_data=market_data,
        order_service=order_service
    )
```

**Benefits**:
- Easy to test (inject mocks)
- Clear dependencies
- Loose coupling

---

### 2. Repository Pattern

**Pattern**: Abstract data access behind interfaces

**Example**:
```python
from abc import ABC, abstractmethod

class TradeRepository(ABC):
    @abstractmethod
    async def save_trade(self, trade: Trade) -> int:
        pass

    @abstractmethod
    async def get_today_trades(self) -> List[Trade]:
        pass

    @abstractmethod
    async def get_pnl_summary(self, start_date, end_date) -> PnLSummary:
        pass

class PostgresTradeRepository(TradeRepository):
    def __init__(self, db_session: AsyncSession):
        self.session = db_session

    async def save_trade(self, trade: Trade) -> int:
        self.session.add(trade)
        await self.session.commit()
        return trade.id

# Easy to swap implementations
class InMemoryTradeRepository(TradeRepository):
    def __init__(self):
        self.trades = []

    async def save_trade(self, trade: Trade) -> int:
        trade.id = len(self.trades) + 1
        self.trades.append(trade)
        return trade.id
```

**Benefits**:
- Database agnostic
- Easy to test (use in-memory)
- Centralized query logic

---

### 3. Strategy Pattern

**Pattern**: Pluggable trading strategies

**Example**:
```python
class TradingStrategy(ABC):
    @abstractmethod
    async def evaluate_entry(self, symbol: str, market_data: MarketData) -> Optional[BuySignal]:
        pass

    @abstractmethod
    async def evaluate_exit(self, position: Position, market_data: MarketData) -> Optional[SellSignal]:
        pass

class RSIStrategy(TradingStrategy):
    async def evaluate_entry(self, symbol: str, market_data: MarketData) -> Optional[BuySignal]:
        rsi = await market_data.calculate_rsi(symbol)
        if rsi < 30:  # Oversold
            return BuySignal(symbol=symbol, reason="RSI oversold")
        return None

class MACDStrategy(TradingStrategy):
    async def evaluate_entry(self, symbol: str, market_data: MarketData) -> Optional[BuySignal]:
        macd = await market_data.calculate_macd(symbol)
        if macd.signal == "bullish_crossover":
            return BuySignal(symbol=symbol, reason="MACD bullish crossover")
        return None

# Trading engine uses strategy
class TradingEngineService:
    def __init__(self, strategy: TradingStrategy):
        self.strategy = strategy

    async def run_cycle(self):
        signal = await self.strategy.evaluate_entry(symbol, market_data)
```

**Benefits**:
- Easy to add new strategies
- Strategies can be tested independently
- Users can switch strategies dynamically

---

### 4. Observer Pattern (Event-Driven)

**Pattern**: Event bus for loose coupling

**Example**:
```python
class EventBus:
    def __init__(self):
        self.subscribers = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable):
        self.subscribers[event_type].append(handler)

    async def publish(self, event_type: str, data: dict):
        for handler in self.subscribers[event_type]:
            await handler(data)

# Usage
event_bus = EventBus()

# Subscribe to events
event_bus.subscribe("order.placed", notification_service.send_trade_alert)
event_bus.subscribe("order.placed", analytics_service.track_trade)
event_bus.subscribe("risk.threshold_breached", risk_service.trigger_circuit_breaker)

# Publish events
await event_bus.publish("order.placed", {
    "symbol": "GOLDBEES",
    "quantity": 5,
    "price": 927
})
```

**Benefits**:
- Services don't need to know about each other
- Easy to add new features (just subscribe)
- Audit trail automatically built

---

### 5. Circuit Breaker Pattern

**Pattern**: Prevent cascading failures

**Example**:
```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state = "closed"  # closed, open, half_open
        self.last_failure_time = None

    async def call(self, func: Callable, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half_open"
            else:
                raise CircuitBreakerOpenError("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            raise

# Usage
broker_circuit_breaker = CircuitBreaker()

async def place_order_with_circuit_breaker(order):
    return await broker_circuit_breaker.call(broker.place_order, order)
```

**Benefits**:
- Prevents overwhelming failing services
- Automatic recovery
- Protects against cascading failures

---

## Scalability Considerations

### Horizontal Scaling

**Current Limitation**: Single-process desktop app

**Proposed**: Stateless services that can scale horizontally

```yaml
# Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trading-engine
spec:
  replicas: 5  # Scale to 5 instances
  template:
    spec:
      containers:
      - name: engine
        image: arun-trading-engine:latest
        resources:
          limits:
            cpu: "1"
            memory: "512Mi"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: trading-engine-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: trading-engine
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

### Database Scaling

**Read Replicas**:
```python
# Master for writes
write_db = create_engine(MASTER_DB_URL)

# Replicas for reads
read_db = create_engine(REPLICA_DB_URL)

# Use appropriate connection
async def get_positions():
    return await read_db.execute("SELECT * FROM positions")

async def save_trade(trade):
    return await write_db.execute("INSERT INTO trades ...")
```

**Sharding** (for multi-tenancy):
```python
# Shard by user_id
def get_shard_for_user(user_id: int) -> str:
    shard_num = user_id % NUM_SHARDS
    return f"shard_{shard_num}"

user_db = get_database(get_shard_for_user(user_id))
```

---

### Caching Strategy

**Multi-Level Cache**:
```
┌─────────────────────────────────────┐
│  Application (L1 Cache)             │
│  - In-memory LRU cache              │
│  - TTL: 5 seconds                   │
│  - Size: 1000 items                 │
└──────────────┬──────────────────────┘
               │ Cache miss
               ▼
┌─────────────────────────────────────┐
│  Redis (L2 Cache)                   │
│  - Distributed cache                │
│  - TTL: 60 seconds                  │
│  - Shared across instances          │
└──────────────┬──────────────────────┘
               │ Cache miss
               ▼
┌─────────────────────────────────────┐
│  Database (Source of Truth)         │
│  - PostgreSQL / TimescaleDB         │
└─────────────────────────────────────┘
```

---

### Load Balancing

```
┌─────────────────────────────────────┐
│         NGINX Load Balancer         │
│      (Round-robin / Least conn)     │
└──────────────┬──────────────────────┘
               │
      ┌────────┴────────┬────────┐
      ▼                 ▼        ▼
┌──────────┐      ┌──────────┐  ┌──────────┐
│ API      │      │ API      │  │ API      │
│ Instance │      │ Instance │  │ Instance │
│ 1        │      │ 2        │  │ 3        │
└──────────┘      └──────────┘  └──────────┘
```

---

## Migration Strategy

### Phase 1: Extract Services (Weeks 3-6)

**Goal**: Refactor monolith into service classes (still in same process)

**Steps**:
1. Create service classes with dependency injection
2. Move logic from `kickstart.py` into services
3. Add unit tests for each service
4. Keep existing UI working

**Example**:
```python
# Old: Everything in kickstart.py
def run_cycle():
    # 300 lines of mixed logic

# New: Extracted services
trading_engine = TradingEngineService(
    market_data=MarketDataService(...),
    orders=OrderManagementService(...),
    risk=RiskManagementService(...)
)
trading_engine.run_cycle()
```

---

### Phase 2: Add API Layer (Weeks 7-10)

**Goal**: Expose services via REST API

**Steps**:
1. Create FastAPI application
2. Add endpoints for each service method
3. Desktop UI calls API instead of direct service access
4. Add authentication and rate limiting

**Example**:
```python
# api/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/positions")
async def get_positions():
    return await portfolio_service.get_open_positions()

@app.post("/api/orders")
async def place_order(order: OrderRequest):
    return await order_service.place_order(order)
```

---

### Phase 3: Build Web UI (Weeks 11-16)

**Goal**: Replace desktop UI with web interface

**Steps**:
1. Build React app consuming API
2. Implement real-time updates via WebSocket
3. Feature parity with desktop UI
4. Deploy to cloud

---

### Phase 4: Multi-Tenancy (Weeks 17-24)

**Goal**: Support multiple users

**Steps**:
1. Add user management and authentication
2. Shard database by user
3. Isolate user data and state
4. Deploy on Kubernetes for scalability

---

## API Specifications

### REST Endpoints

#### Authentication

```
POST /api/auth/login
Request:
{
  "username": "user@example.com",
  "password": "secret"
}

Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 3600
}
```

#### Positions

```
GET /api/positions
Headers:
  Authorization: Bearer <token>

Response:
{
  "positions": [
    {
      "symbol": "GOLDBEES",
      "quantity": 5,
      "entry_price": 927.0,
      "current_price": 930.0,
      "unrealized_pnl": 15.0,
      "unrealized_pnl_pct": 0.32
    }
  ]
}
```

#### Orders

```
POST /api/orders
Headers:
  Authorization: Bearer <token>

Request:
{
  "symbol": "TATASTEEL",
  "action": "BUY",
  "quantity": 3,
  "order_type": "MARKET"
}

Response:
{
  "order_id": "20260125123456",
  "status": "PENDING",
  "message": "Order placed successfully"
}
```

### WebSocket Events

#### Subscribe to Live Quotes

```
WS /ws/quotes
Send:
{
  "action": "subscribe",
  "symbols": ["GOLDBEES", "TATASTEEL"]
}

Receive:
{
  "event": "quote_update",
  "data": {
    "symbol": "GOLDBEES",
    "ltp": 930.0,
    "change": 3.0,
    "change_pct": 0.32,
    "timestamp": "2026-01-25T14:32:00Z"
  }
}
```

#### Trade Notifications

```
WS /ws/notifications
Receive:
{
  "event": "trade_executed",
  "data": {
    "symbol": "GOLDBEES",
    "action": "BUY",
    "quantity": 5,
    "price": 927.0,
    "timestamp": "2026-01-25T14:30:00Z"
  }
}
```

---

## Conclusion

This architecture transformation will:
- **Improve Maintainability**: Clear separation of concerns
- **Enable Testing**: Each service testable independently
- **Support Scaling**: Horizontal scaling via stateless services
- **Future-Proof**: Easy to add features and integrations
- **SaaS-Ready**: Multi-tenancy and cloud deployment built-in

**Next Steps**: Begin Phase 1 refactoring to extract services from monolith.
