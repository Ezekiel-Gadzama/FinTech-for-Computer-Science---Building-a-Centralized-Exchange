# Centralized Cryptocurrency Exchange - Architecture Documentation

## System Overview

This is a functional prototype of a centralized cryptocurrency exchange (CEX) built using a three-tier architecture. The system enables users to trade cryptocurrencies, manage wallets, complete KYC/AML verification, and interact via REST APIs.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION TIER (Frontend)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   React UI   │  │  TradingView │  │  Admin Panel │         │
│  │  Components  │  │   Components │  │  Components  │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                  │                  │
│         └─────────────────┴──────────────────┘                  │
│                            │                                    │
│                            ▼                                    │
│                    ┌──────────────┐                            │
│                    │   Nginx      │                            │
│                    │  (Reverse    │                            │
│                    │   Proxy)     │                            │
│                    └──────┬───────┘                            │
└────────────────────────────┼────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LOGIC TIER (Backend)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Flask Application                      │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │   Auth       │  │   Trading    │  │   Wallet     │   │  │
│  │  │   Routes     │  │   Routes     │  │   Routes     │   │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │  │
│  │         │                 │                  │            │  │
│  │  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐   │  │
│  │  │   KYC/AML    │  │   Matching    │  │   Wallet     │   │  │
│  │  │   Routes     │  │   Engine      │  │   Service    │   │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │  │
│  │         │                 │                  │            │  │
│  │  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐   │  │
│  │  │   API Keys   │  │   Order Book  │  │  Hot/Cold    │   │  │
│  │  │   Routes     │  │   Manager     │  │  Wallets     │   │  │
│  │  └──────────────┘  └───────────────┘  └───────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                    │
│  ┌─────────────────────────┼─────────────────────────┐        │
│  │  Security Layer         │                         │        │
│  │  - JWT Authentication   │                         │        │
│  │  - Rate Limiting        │                         │        │
│  │  - DDoS Protection      │                         │        │
│  │  - 2FA Support          │                         │        │
│  └─────────────────────────┼─────────────────────────┘        │
│                            │                                    │
│  ┌─────────────────────────┼─────────────────────────┐        │
│  │  WebSocket Service       │                         │        │
│  │  - Real-time Updates     │                         │        │
│  │  - Order Book Streams     │                         │        │
│  │  - Trade Notifications   │                         │        │
│  └──────────────────────────┼─────────────────────────┘        │
└─────────────────────────────┼────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA TIER (Database)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    TimescaleDB                            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │   Users      │  │   Orders     │  │   Wallets    │   │  │
│  │  │   Table      │  │   Table      │  │   Table      │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │   Trades     │  │   KYC        │  │   Cold       │   │  │
│  │  │   Table      │  │   Tables     │  │   Wallets    │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  │  ┌──────────────┐  ┌──────────────┐                    │  │
│  │  │   API Keys   │  │ Transactions │                    │  │
│  │  │   Table      │  │   Table      │                    │  │
│  │  └──────────────┘  └──────────────┘                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                    │
│  ┌─────────────────────────┼─────────────────────────┐        │
│  │  Redis Cache            │                         │        │
│  │  - Rate Limiting        │                         │        │
│  │  - DDoS Protection      │                         │        │
│  │  - Session Storage       │                         │        │
│  └─────────────────────────┼─────────────────────────┘        │
└─────────────────────────────┼────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  File Storage   │
                    │  (KYC Docs)    │
                    └─────────────────┘
```

## Component Details

### 1. Presentation Tier (Frontend)

**Technology**: React.js

**Components**:
- **Dashboard**: User account overview, balances, recent trades
- **TradingView**: Real-time trading interface with order book, charts, order placement
- **Wallet**: Deposit/withdrawal interface, transaction history
- **KYC**: KYC form submission and document upload
- **Admin Panel**: KYC approval/rejection interface (admin only)
- **Security Settings**: 2FA setup, password management
- **API Keys**: API key management interface

**Features**:
- Responsive design
- Real-time updates via WebSocket
- JWT-based authentication
- Role-based access control (admin/user)

### 2. Logic Tier (Backend)

**Technology**: Python, Flask

#### Core Services

**Trading Engine** (`matching_engine.py`):
- **FIFO Algorithm**: First-In-First-Out order matching
- **Pro-Rata Algorithm**: Proportional allocation across multiple orders at same price
- Real-time order processing
- Trade execution and fee calculation
- Order book management

**Wallet Service** (`wallet_service.py`):
- Hot wallet management (user funds)
- Cold wallet management (secure offline storage)
- Automatic balance management (hot/cold transfers)
- Deposit/withdrawal processing
- Transaction history

**Order Book Manager** (`order_book.py`):
- Maintains order books for all trading pairs
- Depth management
- Real-time updates

#### API Routes

**Authentication** (`/api/auth`):
- User registration
- Login/logout
- Token refresh
- KYC submission
- Current user info

**Trading** (`/api/trading`):
- Place order (market/limit)
- Cancel order
- Get orders
- Get order book
- Get recent trades

**Wallet** (`/api/wallet`):
- Get balances
- Deposit funds
- Withdraw funds
- Get transaction history

**Market Data** (`/api/market`):
- Get prices
- Get ticker
- Get trading pairs
- Get exchange statistics

**KYC** (`/api/kyc`):
- Upload documents
- Get documents
- Admin: View pending KYC
- Admin: Approve/reject KYC

**Admin** (`/api/admin`):
- Cold wallet management
- Transfer to/from cold wallets
- View exchange wallets

**API Keys** (`/api/api-keys`):
- Create API key
- List API keys
- Update/delete API keys
- View usage statistics

**Security** (`/api/security`):
- Setup 2FA
- Verify/disable 2FA
- Get 2FA status

#### Security Layer

**Authentication**:
- JWT tokens (access + refresh)
- Password hashing (bcrypt)
- 2FA support (TOTP)

**Authorization**:
- Role-based access control (admin/user)
- KYC requirement decorator
- API key authentication

**Protection**:
- Rate limiting (per IP and per API key)
- DDoS protection (Redis-based)
- Input validation
- SQL injection prevention (SQLAlchemy ORM)

### 3. Data Tier (Database)

**Technology**: TimescaleDB (PostgreSQL extension)

**Tables**:
- `users`: User accounts, authentication info
- `wallets`: User hot wallets
- `exchange_wallets`: Exchange hot wallet balances
- `cold_wallets`: Cold wallet addresses and balances
- `cold_wallet_transfers`: Transfer records
- `orders`: Trading orders
- `trades`: Executed trades
- `transactions`: Deposit/withdrawal records
- `kyc_verifications`: KYC submission data
- `kyc_documents`: Uploaded documents
- `api_keys`: API key records
- `api_key_usage`: API usage tracking

**Features**:
- Time-series optimization for trade data
- ACID compliance
- Foreign key constraints
- Indexes for performance

**Cache**: Redis
- Rate limiting counters
- DDoS protection tracking
- Session storage

## Data Flow

### Order Placement Flow

1. User submits order via frontend
2. Request authenticated via JWT
3. Backend validates order (balance, price, quantity)
4. Order added to matching engine queue
5. Matching engine processes order:
   - Matches with opposite side orders
   - Executes trades
   - Updates wallets
   - Creates trade records
6. Order book updated
7. WebSocket broadcast to all clients
8. Frontend updates UI

### Deposit Flow

1. User initiates deposit
2. Transaction record created (pending)
3. Balance updated in hot wallet
4. If hot wallet exceeds threshold:
   - Automatic transfer to cold wallet
5. Transaction marked as completed
6. User notified

### KYC Flow

1. User submits KYC information
2. User uploads documents (passport, ID, etc.)
3. Documents stored securely
4. KYC record created (pending)
5. Admin reviews KYC
6. Admin approves/rejects
7. User status updated
8. User notified

## Security Architecture

### Authentication Flow

```
User Login
    │
    ▼
Username/Password Validation
    │
    ▼
Password Hash Verification (bcrypt)
    │
    ▼
2FA Check (if enabled)
    │
    ▼
JWT Token Generation
    │
    ▼
Token Returned to Client
```

### API Key Authentication

```
API Request
    │
    ▼
Extract API Key from Header
    │
    ▼
Hash and Lookup in Database
    │
    ▼
Verify IP Whitelist (if set)
    │
    ▼
Check Rate Limits
    │
    ▼
Process Request
```

## Scalability Considerations

### Current Implementation

- **Database**: TimescaleDB for efficient time-series queries
- **Caching**: Redis for rate limiting and session management
- **Connection Pooling**: SQLAlchemy connection pooling
- **Threading**: Matching engine runs in separate thread

### Future Improvements

- **Load Balancing**: Multiple backend instances behind load balancer
- **Database Sharding**: Shard by trading pair or user ID
- **Message Queue**: RabbitMQ/Kafka for order processing
- **Microservices**: Split into separate services (trading, wallet, KYC)
- **CDN**: Serve static assets via CDN
- **Horizontal Scaling**: Add more backend instances as needed

## Technology Stack

### Frontend
- React.js
- React Router
- Axios (HTTP client)
- Socket.io-client (WebSocket)
- React Hot Toast (notifications)

### Backend
- Python 3.8+
- Flask (web framework)
- Flask-SQLAlchemy (ORM)
- Flask-JWT-Extended (authentication)
- Flask-SocketIO (WebSocket)
- Flask-Migrate (database migrations)
- TimescaleDB (database)
- Redis (caching)
- Bcrypt (password hashing)
- PyOTP (2FA)

### Infrastructure
- Docker & Docker Compose
- Nginx (reverse proxy)
- PostgreSQL/TimescaleDB
- Redis

## Deployment Architecture

```
Internet
    │
    ▼
┌─────────┐
│  Nginx  │ (Port 80)
│ Reverse │
│  Proxy  │
└────┬────┘
     │
     ├──────────────┬──────────────┐
     │              │              │
     ▼              ▼              ▼
┌─────────┐   ┌─────────┐   ┌─────────┐
│Frontend │   │ Backend │   │ Backend │
│ (React) │   │ (Flask) │   │ (Flask) │
│ Port    │   │ Port    │   │ Port    │
│  3000   │   │  5000   │   │  5000   │
└─────────┘   └────┬────┘   └────┬────┘
                   │              │
                   └──────┬───────┘
                          │
            ┌─────────────┼─────────────┐
            │             │             │
            ▼             ▼             ▼
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │Timescale │  │  Redis   │  │  File    │
      │    DB    │  │  Cache   │  │ Storage  │
      │  Port    │  │  Port    │  │  (KYC)   │
      │  5432    │  │  6379    │  │          │
      └──────────┘  └──────────┘  └──────────┘
```

## Design Decisions

### Why TimescaleDB?

- Optimized for time-series data (trades, order book updates)
- Efficient storage and querying of historical data
- PostgreSQL compatibility (familiar tooling)
- Automatic data retention policies

### Why FIFO and Pro-Rata?

- **FIFO**: Simple, fair, easy to understand
- **Pro-Rata**: Better for large orders, distributes liquidity fairly
- Both algorithms are industry-standard

### Why Hot/Cold Wallets?

- **Hot Wallets**: Fast access for trading
- **Cold Wallets**: Secure storage for majority of funds
- Automatic balance management reduces manual intervention
- Reduces risk of theft

### Why JWT?

- Stateless authentication
- Scalable across multiple servers
- Refresh token mechanism for security
- Industry standard

## Future Enhancements

1. **Advanced Order Types**: Stop-loss, take-profit, trailing stops
2. **Margin Trading**: Leveraged trading with collateral
3. **Futures Trading**: Derivatives and contracts
4. **Staking**: Earn rewards on holdings
5. **Mobile App**: Native iOS/Android apps
6. **Advanced Charts**: TradingView integration
7. **Social Trading**: Copy trading features
8. **Multi-language Support**: Internationalization
9. **Advanced Analytics**: Trading analytics dashboard
10. **Blockchain Integration**: Direct blockchain deposits/withdrawals

