from decimal import Decimal
from queue import Queue
import threading
from typing import Dict
from .. import db, socketio
from ..models.order import Order, Trade
from ..models.wallet import Wallet

class OrderMatchingEngine:
    """FIFO Order Matching Engine"""

    def __init__(self):
        self.order_queues: Dict[str, Queue] = {}
        self.order_books: Dict[str, Dict] = {}
        self.running = False
        self.lock = threading.Lock()
        self.processing_thread = None

    def start(self):
        """Start the matching engine"""
        if not self.running:
            self.running = True
            self.processing_thread = threading.Thread(target=self._process_orders, daemon=True)
            self.processing_thread.start()
            print("Matching engine started")

    def stop(self):
        """Stop the matching engine"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join()

    def add_order(self, order: Order):
        """Add order to the matching engine"""
        pair = order.trading_pair

        with self.lock:
            if pair not in self.order_queues:
                self.order_queues[pair] = Queue()
                self.order_books[pair] = {'bids': [], 'asks': []}

            self.order_queues[pair].put(order)

    def _process_orders(self):
        """Process orders from the queue"""
        while self.running:
            try:
                for pair, queue in self.order_queues.items():
                    if not queue.empty():
                        order = queue.get()
                        self._match_order(order)

                threading.Event().wait(0.01)  # Small delay to prevent CPU spinning
            except Exception as e:
                print(f"Error processing orders: {e}")

    def _match_order(self, order: Order):
        """Match an order against the order book using FIFO"""
        pair = order.trading_pair
        order_book = self.order_books[pair]

        try:
            if order.order_type == 'market':
                self._match_market_order(order, order_book)
            else:  # limit order
                self._match_limit_order(order, order_book)

            # Update order status in database
            db.session.commit()

            # Broadcast order book update
            self._broadcast_orderbook_update(pair)

        except Exception as e:
            db.session.rollback()
            print(f"Error matching order {order.order_id}: {e}")

    def _match_market_order(self, order: Order, order_book: Dict):
        """Match a market order"""
        opposite_side = 'asks' if order.side == 'buy' else 'bids'
        book_orders = order_book[opposite_side]

        remaining_qty = order.remaining_quantity

        # Match with available orders (FIFO - first in, first out)
        i = 0
        while i < len(book_orders) and remaining_qty > 0:
            book_order = book_orders[i]
            match_qty = min(remaining_qty, book_order.remaining_quantity)
            match_price = book_order.price

            # Execute trade
            self._execute_trade(order, book_order, match_qty, match_price)

            remaining_qty -= match_qty

            # Remove filled order from book
            if book_order.is_filled:
                book_orders.pop(i)
            else:
                i += 1

        # Update order status
        if remaining_qty == 0:
            order.status = 'filled'
        else:
            order.status = 'partially_filled'

    def _match_limit_order(self, order: Order, order_book: Dict):
        """Match a limit order"""
        opposite_side = 'asks' if order.side == 'buy' else 'bids'
        book_orders = order_book[opposite_side]

        remaining_qty = order.remaining_quantity

        # Match with compatible orders (FIFO)
        i = 0
        while i < len(book_orders) and remaining_qty > 0:
            book_order = book_orders[i]

            # Check price compatibility
            if order.side == 'buy':
                if order.price < book_order.price:
                    break
            else:  # sell
                if order.price > book_order.price:
                    break

            match_qty = min(remaining_qty, book_order.remaining_quantity)
            match_price = book_order.price  # Maker price takes precedence

            # Execute trade
            self._execute_trade(order, book_order, match_qty, match_price)

            remaining_qty -= match_qty

            # Remove filled order from book
            if book_order.is_filled:
                book_orders.pop(i)
            else:
                i += 1

        # If order still has remaining quantity, add to order book
        if remaining_qty > 0:
            order.status = 'open' if order.filled_quantity == 0 else 'partially_filled'
            self._add_to_orderbook(order, order_book)
        else:
            order.status = 'filled'

    def _execute_trade(self, taker_order: Order, maker_order: Order, quantity: Decimal, price: Decimal):
        """Execute a trade between two orders"""
        # Calculate fees
        fee_rate = Decimal('0.001')  # 0.1%
        maker_fee = quantity * price * fee_rate
        taker_fee = quantity * price * fee_rate

        # Update orders
        taker_order.update_fill(quantity, price)
        maker_order.update_fill(quantity, price)

        # Update fees
        taker_order.fee += taker_fee
        maker_order.fee += maker_fee

        # Create trade record
        trade = Trade(
            maker_order_id=maker_order.id,
            taker_order_id=taker_order.id,
            trading_pair=taker_order.trading_pair,
            price=price,
            quantity=quantity,
            maker_fee=maker_fee,
            taker_fee=taker_fee
        )
        db.session.add(trade)

        # Update wallets
        self._update_wallets_after_trade(taker_order, maker_order, quantity, price, taker_fee, maker_fee)

        # Broadcast trade
        self._broadcast_trade(trade)

    def _update_wallets_after_trade(self, taker_order, maker_order, quantity, price, taker_fee, maker_fee):
        """Update user wallets after trade execution"""
        base_currency, quote_currency = taker_order.trading_pair.split('/')

        if taker_order.side == 'buy':
            # Taker buys base currency with quote currency
            buyer_id, seller_id = taker_order.user_id, maker_order.user_id

            # Update buyer (taker)
            buyer_base = Wallet.query.filter_by(user_id=buyer_id, currency=base_currency).first()
            buyer_quote = Wallet.query.filter_by(user_id=buyer_id, currency=quote_currency).first()

            buyer_base.add_balance(quantity)
            buyer_quote.unlock_balance(quantity * price)
            buyer_quote.deduct_balance(quantity * price + taker_fee)

            # Update seller (maker)
            seller_base = Wallet.query.filter_by(user_id=seller_id, currency=base_currency).first()
            seller_quote = Wallet.query.filter_by(user_id=seller_id, currency=quote_currency).first()

            seller_base.unlock_balance(quantity)
            seller_base.deduct_balance(quantity)
            seller_quote.add_balance(quantity * price - maker_fee)
        else:
            # Taker sells base currency for quote currency
            seller_id, buyer_id = taker_order.user_id, maker_order.user_id

            # Update seller (taker)
            seller_base = Wallet.query.filter_by(user_id=seller_id, currency=base_currency).first()
            seller_quote = Wallet.query.filter_by(user_id=seller_id, currency=quote_currency).first()

            seller_base.unlock_balance(quantity)
            seller_base.deduct_balance(quantity)
            seller_quote.add_balance(quantity * price - taker_fee)

            # Update buyer (maker)
            buyer_base = Wallet.query.filter_by(user_id=buyer_id, currency=base_currency).first()
            buyer_quote = Wallet.query.filter_by(user_id=buyer_id, currency=quote_currency).first()

            buyer_base.add_balance(quantity)
            buyer_quote.unlock_balance(quantity * price)
            buyer_quote.deduct_balance(quantity * price + maker_fee)

    def _add_to_orderbook(self, order: Order, order_book: Dict):
        """Add order to the order book (FIFO - append at end)"""
        side = 'bids' if order.side == 'buy' else 'asks'
        order_book[side].append(order)

    def _broadcast_orderbook_update(self, pair: str):
        """Broadcast order book update via WebSocket"""
        try:
            order_book_data = self.get_orderbook(pair)
            socketio.emit('orderbook_update', {
                'pair': pair,
                'data': order_book_data
            })
        except Exception as e:
            print(f"Error broadcasting orderbook: {e}")

    def _broadcast_trade(self, trade: Trade):
        """Broadcast trade via WebSocket"""
        try:
            socketio.emit('trade', trade.to_dict())
        except Exception as e:
            print(f"Error broadcasting trade: {e}")

    def get_orderbook(self, pair: str, depth: int = 20) -> Dict:
        """Get current order book for a trading pair"""
        if pair not in self.order_books:
            return {'bids': [], 'asks': []}

        order_book = self.order_books[pair]

        # Format bids and asks
        bids = [
            {
                'price': float(order.price),
                'quantity': float(order.remaining_quantity),
                'total': float(order.price * order.remaining_quantity)
            }
            for order in order_book['bids'][:depth]
        ]

        asks = [
            {
                'price': float(order.price),
                'quantity': float(order.remaining_quantity),
                'total': float(order.price * order.remaining_quantity)
            }
            for order in order_book['asks'][:depth]
        ]

        return {'bids': bids, 'asks': asks}

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        order = Order.query.filter_by(order_id=order_id).first()
        if not order:
            return False

        if order.status not in ['open', 'partially_filled']:
            return False

        # Remove from order book
        pair = order.trading_pair
        if pair in self.order_books:
            side = 'bids' if order.side == 'buy' else 'asks'
            self.order_books[pair][side] = [
                o for o in self.order_books[pair][side] if o.order_id != order_id
            ]

        # Unlock balance
        base_currency, quote_currency = order.trading_pair.split('/')
        currency = quote_currency if order.side == 'buy' else base_currency
        amount = order.remaining_quantity * order.price if order.side == 'buy' else order.remaining_quantity

        wallet = Wallet.query.filter_by(user_id=order.user_id, currency=currency).first()
        if wallet:
            wallet.unlock_balance(amount)

        # Update order status
        order.cancel()
        db.session.commit()

        # Broadcast update
        self._broadcast_orderbook_update(pair)

        return True


# Global instance
matching_engine = OrderMatchingEngine()