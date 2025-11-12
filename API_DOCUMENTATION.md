# API Documentation

Complete REST API reference for the Centralized Cryptocurrency Exchange.

## Base URL

- Development: `http://localhost/api`
- Production: `https://your-domain.com/api`

## Authentication

Most endpoints require authentication via JWT tokens.

### Getting a Token

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "your_username",
    "email": "user@example.com"
  }
}
```

### Using the Token

Include the token in the Authorization header:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## Endpoints

### Authentication

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "password": "secure_password"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "username",
  "password": "password"
}
```

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <token>
```

#### Refresh Token
```http
POST /api/auth/refresh
Authorization: Bearer <refresh_token>
```

### Trading

#### Place Order
```http
POST /api/trading/order
Authorization: Bearer <token>
Content-Type: application/json

{
  "trading_pair": "BTC/USDT",
  "side": "buy",
  "order_type": "limit",
  "quantity": "0.1",
  "price": "50000"
}
```

**Order Types:**
- `market` - Market order (no price required)
- `limit` - Limit order (price required)

**Sides:**
- `buy` - Buy order
- `sell` - Sell order

#### Get Orders
```http
GET /api/trading/orders?status=open&pair=BTC/USDT&limit=50
Authorization: Bearer <token>
```

**Query Parameters:**
- `status` - Filter by status (open, filled, cancelled, etc.)
- `pair` - Filter by trading pair
- `limit` - Number of results (default: 50)

#### Get Order Book
```http
GET /api/trading/orderbook?pair=BTC/USDT&depth=20
```

**Query Parameters:**
- `pair` - Trading pair (required)
- `depth` - Number of price levels (default: 20)

**Response:**
```json
{
  "bids": [
    {"price": 50000, "quantity": 0.5, "total": 25000},
    {"price": 49999, "quantity": 1.0, "total": 49999}
  ],
  "asks": [
    {"price": 50001, "quantity": 0.3, "total": 15000.3},
    {"price": 50002, "quantity": 0.8, "total": 40001.6}
  ]
}
```

#### Get Recent Trades
```http
GET /api/trading/trades?pair=BTC/USDT&limit=50
```

**Query Parameters:**
- `pair` - Trading pair (required)
- `limit` - Number of results (default: 50)

#### Cancel Order
```http
DELETE /api/trading/order/<order_id>
Authorization: Bearer <token>
```

### Wallet

#### Get Balances
```http
GET /api/wallet/balances
Authorization: Bearer <token>
```

**Response:**
```json
{
  "balances": [
    {
      "currency": "USDT",
      "balance": "10000.00",
      "locked_balance": "500.00",
      "available_balance": "9500.00"
    },
    {
      "currency": "BTC",
      "balance": "1.5",
      "locked_balance": "0.1",
      "available_balance": "1.4"
    }
  ]
}
```

#### Deposit
```http
POST /api/wallet/deposit
Authorization: Bearer <token>
Content-Type: application/json

{
  "currency": "USDT",
  "amount": "1000",
  "description": "Deposit from bank"
}
```

#### Withdraw
```http
POST /api/wallet/withdraw
Authorization: Bearer <token>
Content-Type: application/json

{
  "currency": "USDT",
  "amount": "500",
  "address": "0x1234567890abcdef",
  "description": "Withdrawal to wallet"
}
```

#### Get Transactions
```http
GET /api/wallet/transactions?currency=USDT&type=deposit&limit=50
Authorization: Bearer <token>
```

**Query Parameters:**
- `currency` - Filter by currency
- `type` - Filter by type (deposit, withdrawal)
- `limit` - Number of results (default: 50)

### Market Data

#### Get Prices
```http
GET /api/market/prices
```

**Response:**
```json
{
  "BTC/USDT": 50000,
  "ETH/USDT": 3000,
  "BNB/USDT": 400
}
```

#### Get Ticker
```http
GET /api/market/ticker?pair=BTC/USDT
```

**Query Parameters:**
- `pair` - Trading pair (required)

#### Get Trading Pairs
```http
GET /api/market/pairs
```

**Response:**
```json
{
  "pairs": [
    "BTC/USDT",
    "ETH/USDT",
    "BNB/USDT",
    "ADA/USDT",
    "SOL/USDT"
  ]
}
```

#### Get Exchange Statistics
```http
GET /api/market/stats
```

### KYC

#### Submit KYC Information
```http
POST /api/auth/kyc
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "John Doe",
  "date_of_birth": "1990-01-01",
  "country": "USA",
  "nationality": "American",
  "phone": "+1234567890",
  "address": "123 Main St",
  "city": "New York",
  "postal_code": "10001"
}
```

#### Upload KYC Document
```http
POST /api/kyc/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <file>
document_type: passport
```

**Document Types:**
- `passport`
- `id_card`
- `driver_license`
- `proof_of_address`

#### Get KYC Documents
```http
GET /api/kyc/documents
Authorization: Bearer <token>
```

#### Get KYC Status
```http
GET /api/auth/kyc/status
Authorization: Bearer <token>
```

#### Get Pending KYC (Admin Only)
```http
GET /api/kyc/pending
Authorization: Bearer <admin_token>
```

#### Approve KYC (Admin Only)
```http
POST /api/kyc/verify/<user_id>
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "notes": "KYC approved",
  "aml_status": "cleared",
  "risk_score": 10
}
```

#### Reject KYC (Admin Only)
```http
POST /api/kyc/reject/<user_id>
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "reason": "Document quality insufficient"
}
```

### Admin

#### Get Cold Wallets
```http
GET /api/admin/cold-wallets
Authorization: Bearer <admin_token>
```

#### Get Cold Wallet by Currency
```http
GET /api/admin/cold-wallet/<currency>
Authorization: Bearer <admin_token>
```

#### Transfer to Cold Wallet
```http
POST /api/admin/transfer/to-cold
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "currency": "USDT",
  "amount": "10000"
}
```

#### Transfer from Cold Wallet
```http
POST /api/admin/transfer/from-cold
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "currency": "USDT",
  "amount": "5000"
}
```

#### Approve Cold Wallet Transfer
```http
POST /api/admin/transfer/approve/<transfer_id>
Authorization: Bearer <admin_token>
```

#### Get Exchange Wallets
```http
GET /api/admin/exchange-wallets
Authorization: Bearer <admin_token>
```

### API Keys

#### Create API Key
```http
POST /api/api-keys
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "My Trading Bot",
  "permissions": ["read", "trade"],
  "ip_whitelist": "192.168.1.1,10.0.0.1"
}
```

**Permissions:**
- `read` - Read-only access
- `trade` - Trading access
- `withdraw` - Withdrawal access (requires 2FA)

#### Get API Keys
```http
GET /api/api-keys
Authorization: Bearer <token>
```

#### Get API Key Details
```http
GET /api/api-keys/<key_id>
Authorization: Bearer <token>
```

#### Update API Key
```http
PUT /api/api-keys/<key_id>
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Updated Name",
  "is_active": true
}
```

#### Delete API Key
```http
DELETE /api/api-keys/<key_id>
Authorization: Bearer <token>
```

#### Get API Key Usage
```http
GET /api/api-keys/<key_id>/usage
Authorization: Bearer <token>
```

### Security

#### Setup 2FA
```http
POST /api/security/2fa/setup
Authorization: Bearer <token>
```

**Response:**
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,..."
}
```

#### Verify 2FA
```http
POST /api/security/2fa/verify
Authorization: Bearer <token>
Content-Type: application/json

{
  "token": "123456"
}
```

#### Disable 2FA
```http
POST /api/security/2fa/disable
Authorization: Bearer <token>
Content-Type: application/json

{
  "token": "123456"
}
```

#### Get 2FA Status
```http
GET /api/security/2fa/status
Authorization: Bearer <token>
```

## WebSocket API

### Connection

```javascript
import io from 'socket.io-client';

const socket = io('http://localhost', {
  auth: {
    token: 'your_jwt_token'
  }
});
```

### Events

#### Subscribe to Order Book Updates
```javascript
socket.emit('subscribe', { channel: 'orderbook', pair: 'BTC/USDT' });
socket.on('orderbook_update', (data) => {
  console.log('Order book updated:', data);
});
```

#### Subscribe to Trades
```javascript
socket.emit('subscribe', { channel: 'trades', pair: 'BTC/USDT' });
socket.on('trade', (data) => {
  console.log('New trade:', data);
});
```

#### Subscribe to User Orders
```javascript
socket.emit('subscribe', { channel: 'orders' });
socket.on('order_update', (data) => {
  console.log('Order updated:', data);
});
```

## Error Responses

All errors follow this format:

```json
{
  "error": "Error message description"
}
```

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Too Many Requests (Rate Limited)
- `500` - Internal Server Error

### Common Errors

**401 Unauthorized:**
```json
{
  "error": "Invalid or expired token"
}
```

**403 Forbidden:**
```json
{
  "error": "Admin access required"
}
```

**429 Too Many Requests:**
```json
{
  "error": "Rate limit exceeded",
  "limit": 100,
  "window": 3600
}
```

## Rate Limits

- **Unauthenticated**: 10 requests/minute
- **Authenticated**: 100 requests/minute
- **API Keys**: Varies by key tier
- **Admin**: 200 requests/minute

## API Key Authentication

For API key authentication, include headers:

```http
X-API-Key: your_api_key
X-API-Secret: your_api_secret  # Optional, for enhanced security
```

## Examples

### Python Example

```python
import requests

# Login
response = requests.post('http://localhost/api/auth/login', json={
    'username': 'user',
    'password': 'pass'
})
token = response.json()['access_token']

# Place order
headers = {'Authorization': f'Bearer {token}'}
response = requests.post('http://localhost/api/trading/order', 
    headers=headers,
    json={
        'trading_pair': 'BTC/USDT',
        'side': 'buy',
        'order_type': 'limit',
        'quantity': '0.1',
        'price': '50000'
    })
```

### JavaScript Example

```javascript
// Login
const loginResponse = await fetch('http://localhost/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'user',
    password: 'pass'
  })
});
const { access_token } = await loginResponse.json();

// Place order
const orderResponse = await fetch('http://localhost/api/trading/order', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    trading_pair: 'BTC/USDT',
    side: 'buy',
    order_type: 'limit',
    quantity: '0.1',
    price: '50000'
  })
});
```

## Testing

Use the test suite to verify API functionality:

```bash
cd backend
pytest test/test_api_endpoints.py -v
```

