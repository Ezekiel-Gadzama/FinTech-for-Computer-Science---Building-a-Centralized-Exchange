# Centralized Cryptocurrency Exchange

A functional prototype of a centralized cryptocurrency exchange (CEX) built with a three-tier architecture. This platform enables users to trade cryptocurrencies, manage wallets, complete KYC/AML verification, and interact via REST APIs.

## Features

### Trading Engine
- ✅ **Order Matching**: FIFO and Pro-Rata algorithms
- ✅ **Order Types**: Market and Limit orders
- ✅ **Real-time Order Book**: Live updates via WebSocket
- ✅ **Trade Execution**: Automatic matching and execution
- ✅ **Fee Calculation**: Maker/taker fee structure

### Wallet System
- ✅ **Hot Wallets**: Fast access for trading
- ✅ **Cold Wallets**: Secure offline storage
- ✅ **Automatic Balance Management**: Auto-transfer between hot/cold
- ✅ **Deposit/Withdrawal**: Fund management
- ✅ **Transaction History**: Complete audit trail

### User Interface
- ✅ **Dashboard**: Account overview and balances
- ✅ **Trading Interface**: Real-time trading with charts
- ✅ **Wallet Management**: Deposit/withdrawal interface
- ✅ **KYC/AML**: Compliance verification
- ✅ **Admin Panel**: KYC approval interface
- ✅ **Security Settings**: 2FA, password management
- ✅ **API Key Management**: Create and manage API keys

### Security
- ✅ **JWT Authentication**: Secure token-based auth
- ✅ **2FA Support**: TOTP-based two-factor authentication
- ✅ **Rate Limiting**: DDoS protection and rate limits
- ✅ **Password Hashing**: Bcrypt encryption
- ✅ **API Key Authentication**: Secure API access
- ✅ **KYC Requirement**: Enforced for sensitive operations

### API Gateway
- ✅ **RESTful API**: Complete REST API
- ✅ **WebSocket Support**: Real-time updates
- ✅ **API Key Management**: Third-party integration
- ✅ **Rate Limiting**: Per-key and per-IP limits
- ✅ **Documentation**: Comprehensive API docs

## Technology Stack

### Frontend
- React.js
- React Router
- Axios
- Socket.io-client
- React Hot Toast

### Backend
- Python 3.8+
- Flask
- Flask-SQLAlchemy
- Flask-JWT-Extended
- Flask-SocketIO
- TimescaleDB (PostgreSQL)
- Redis

### Infrastructure
- Docker & Docker Compose
- Nginx
- PostgreSQL/TimescaleDB
- Redis

## Prerequisites

- Docker and Docker Compose
- Python 3.8+ (for local development)
- Node.js 16+ (for frontend development)

## Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd crypto-exchange
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   ```

3. **Initialize database**
   ```bash
   docker exec -it crypto-exchange-backend-1 python migrate_db.py
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost/api
   - Admin Panel: http://localhost:3000/admin (admin access required)

### Local Development

#### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**
   Create a `.env` file:
   ```env
   DATABASE_URL=postgresql://crypto_user:crypto_pass@localhost:5432/crypto_exchange
   REDIS_URL=redis://localhost:6379/0
   SECRET_KEY=your-secret-key-here
   JWT_SECRET_KEY=your-jwt-secret-key-here
   FLASK_ENV=development
   ```

5. **Run migrations**
   ```bash
   flask db upgrade
   # Or
   python migrate_db.py
   ```

6. **Start the backend**
   ```bash
   python run.py
   ```

#### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set environment variables**
   Create a `.env` file:
   ```env
   REACT_APP_API_URL=http://localhost
   REACT_APP_WS_URL=http://localhost
   ```

4. **Start the frontend**
   ```bash
   npm start
   ```

## Creating an Admin User

### Using the Script (Recommended)

```bash
# Inside Docker
docker exec -it crypto-exchange-backend-1 python make_admin.py <username_or_email>

# Local development
cd backend
python make_admin.py <username_or_email>
```

### Using the API (Development Only)

```bash
curl -X POST http://localhost/api/auth/create-admin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "username": "admin",
    "password": "secure_password"
  }'
```

**Note**: This endpoint only works when `FLASK_ENV=development`.

## Running Tests

### Backend Tests

```bash
cd backend
pytest test/ -v

# Run specific test file
pytest test/test_trading_engine_comprehensive.py -v

# Run with coverage
pytest test/ --cov=app --cov-report=html

# Run all tests using the test runner
python test/run_tests.py

docker-compose exec backend python -m pytest test/test_trading_engine_comprehensive.py -v --tb=short -p no:warnings
docker-compose exec backend python -m pytest test/test_wallet_system.py -v --tb=short -p no:warnings
docker-compose exec backend python -m pytest test/test_kyc_aml.py -v --tb=short -p no:warnings
docker-compose exec backend python -m pytest test/test_api_endpoints.py -v --tb=short -p no:warnings
docker-compose exec backend python -m pytest test/test_security.py -v --tb=short -p no:warnings
docker-compose exec backend python -m pytest test/test_matching_engine.py -v --tb=short -p no:warnings
docker-compose exec backend pytest test/ -v --tb=short -p no:warnings --cov=app --cov-report=html
docker-compose exec backend python test/stress_test.py

```

### Fixing Web3 Dependency Issue

If you encounter an `ImportError: cannot import name 'ContractName' from 'eth_typing'` error:

1. **Update dependencies in Docker:**
   ```bash
   docker-compose exec backend pip install eth-typing==3.5.2
   ```

2. **Or rebuild the Docker container:**
   ```bash
   docker-compose down
   docker-compose build --no-cache backend
   docker-compose up -d
   ```

3. **The `pytest.ini` file should automatically disable the problematic web3 plugin**, but if issues persist, run tests with:
   ```bash
   pytest test/ -p no:web3.tools.pytest_ethereum -v
   ```

### Test Coverage

- ✅ Trading Engine (FIFO and Pro-Rata)
- ✅ Wallet System (Hot/Cold)
- ✅ KYC/AML Functionality
- ✅ API Endpoints
- ✅ Security Measures
- ✅ Authentication/Authorization

## Project Structure

```
crypto-exchange/
├── backend/
│   ├── app/
│   │   ├── models/          # Database models
│   │   ├── routes/          # API routes
│   │   ├── services/        # Business logic
│   │   ├── utils/           # Utilities
│   │   ├── middleware/      # Security middleware
│   │   └── websocket/       # WebSocket handlers
│   ├── test/               # Test suite
│   ├── migrations/         # Database migrations
│   ├── make_admin.py        # Admin user creation script
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/        # API services
│   │   ├── contexts/        # React contexts
│   │   └── styles/          # CSS styles
│   └── package.json        # Node dependencies
├── nginx/                   # Nginx configuration
├── docker-compose.yml       # Docker setup
├── ARCHITECTURE.md          # Architecture documentation
├── API_DOCUMENTATION.md     # API documentation
└── README.md                # This file
```

## API Documentation

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

## Key Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

### Trading
- `POST /api/trading/order` - Place order
- `GET /api/trading/orders` - Get user orders
- `GET /api/trading/orderbook` - Get order book
- `DELETE /api/trading/order/<id>` - Cancel order

### Wallet
- `GET /api/wallet/balances` - Get balances
- `POST /api/wallet/deposit` - Deposit funds
- `POST /api/wallet/withdraw` - Withdraw funds
- `GET /api/wallet/transactions` - Get transaction history

### KYC
- `POST /api/auth/kyc` - Submit KYC information
- `POST /api/kyc/upload` - Upload KYC document
- `GET /api/kyc/documents` - Get user documents
- `GET /api/kyc/pending` - Get pending KYC (admin)
- `POST /api/kyc/verify/<user_id>` - Approve KYC (admin)
- `POST /api/kyc/reject/<user_id>` - Reject KYC (admin)

### Admin
- `GET /api/admin/cold-wallets` - Get cold wallets
- `POST /api/admin/transfer/to-cold` - Transfer to cold
- `POST /api/admin/transfer/from-cold` - Transfer from cold

## Configuration

### Environment Variables

**Backend**:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - Flask secret key
- `JWT_SECRET_KEY` - JWT signing key
- `FLASK_ENV` - Environment (development/production)
- `MATCHING_ALGORITHM` - FIFO or PRO_RATA

**Frontend**:
- `REACT_APP_API_URL` - Backend API URL
- `REACT_APP_WS_URL` - WebSocket URL

## Security Considerations

### Production Deployment

1. **Change default secrets**: Update `SECRET_KEY` and `JWT_SECRET_KEY`
2. **Use HTTPS**: Configure SSL/TLS certificates
3. **Database security**: Use strong passwords, restrict access
4. **Redis security**: Enable authentication
5. **Rate limiting**: Adjust limits for production
6. **CORS**: Configure allowed origins
7. **File uploads**: Validate and sanitize uploaded files
8. **Environment variables**: Use secrets management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is for educational purposes.

## Support

For issues and questions, please open an issue on GitHub.

## Acknowledgments

- Built as a functional prototype for educational purposes
- Implements industry-standard practices for cryptocurrency exchanges
- Uses modern web technologies and best practices

