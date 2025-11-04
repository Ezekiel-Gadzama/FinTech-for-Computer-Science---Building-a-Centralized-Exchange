export const TRADING_PAIRS = [
  'BTC/USDT',
  'ETH/USDT',
  'BNB/USDT',
  'ADA/USDT',
  'SOL/USDT'
];

export const ORDER_TYPES = {
  LIMIT: 'limit',
  MARKET: 'market'
};

export const ORDER_SIDES = {
  BUY: 'buy',
  SELL: 'sell'
};

export const ORDER_STATUS = {
  PENDING: 'pending',
  OPEN: 'open',
  PARTIALLY_FILLED: 'partially_filled',
  FILLED: 'filled',
  CANCELLED: 'cancelled',
  REJECTED: 'rejected'
};

export const TRANSACTION_TYPES = {
  DEPOSIT: 'deposit',
  WITHDRAW: 'withdraw',
  TRADE: 'trade',
  FEE: 'fee'
};

export const CURRENCIES = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'USDT'];

export const TRADING_FEE = 0.001; // 0.1%

export const MIN_ORDER_SIZE = 10; // USDT