from decimal import Decimal
from queue import Queue
import threading
from typing import Dict, Literal
from .. import db, socketio
from ..models.order import Order, Trade
from ..models.wallet import Wallet

class OrderMatchingEngine:
    """Order Matching Engine with FIFO and Pro-Rata algorithms"""

    def __init__(self, matching_algorithm: Literal['FIFO', 'PRO_RATA'] = 'FIFO'):
        self.order_queues: Dict[str, Queue] = {}
        self.order_books: Dict[str, Dict] = {}
        self.running = False
        self.lock = threading.Lock()
        self.processing_thread = None
        self.matching_algorithm = matching_algorithm  # 'FIFO' or 'PRO_RATA'

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
        """Match a limit order using selected algorithm"""
        if self.matching_algorithm == 'PRO_RATA':
            self._match_limit_order_pro_rata(order, order_book)
        else:
            self._match_limit_order_fifo(order, order_book)

    def _match_limit_order_fifo(self, order: Order, order_book: Dict):
        """Match a limit order using FIFO algorithm"""
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

    def _match_limit_order_pro_rata(self, order: Order, order_book: Dict):
        """Match a limit order using Pro-Rata algorithm"""
        opposite_side = 'asks' if order.side == 'buy' else 'bids'
        book_orders = order_book[opposite_side]

        remaining_qty = order.remaining_quantity

        # Find all compatible orders at the best price level
        compatible_orders = []
        best_price = None

        for book_order in book_orders:
            # Check price compatibility
            if order.side == 'buy':
                if order.price < book_order.price:
                    break
            else:  # sell
                if order.price > book_order.price:
                    break

            if best_price is None:
                best_price = book_order.price

            # Collect orders at the best price level
            if book_order.price == best_price:
                compatible_orders.append(book_order)
            else:
                break  # We've moved to a worse price level

        if not compatible_orders:
            # No compatible orders, add to order book
            order.status = 'open'
            self._add_to_orderbook(order, order_book)
            return

        # Calculate total quantity available at best price
        total_available = sum(o.remaining_quantity for o in compatible_orders)

        # Pro-Rata allocation: distribute order quantity proportionally
        if remaining_qty >= total_available:
            # Fill all compatible orders
            for book_order in compatible_orders:
                match_qty = book_order.remaining_quantity
                self._execute_trade(order, book_order, match_qty, best_price)
                remaining_qty -= match_qty
                # Remove filled orders from book
                if book_order.is_filled:
                    book_orders.remove(book_order)
        else:
            # Allocate proportionally
            allocations = []
            for book_order in compatible_orders:
                proportion = book_order.remaining_quantity / total_available
                allocated_qty = remaining_qty * proportion
                allocations.append((book_order, allocated_qty))

            # Execute trades
            for book_order, allocated_qty in allocations:
                if allocated_qty > 0 and remaining_qty > 0:
                    match_qty = min(allocated_qty, remaining_qty, book_order.remaining_quantity)
                    if match_qty > 0:
                        self._execute_trade(order, book_order, match_qty, best_price)
                        remaining_qty -= match_qty
                        # Remove filled orders from book
                        if book_order.is_filled:
                            book_orders.remove(book_order)

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
        """Add order to the order book"""
        side = 'bids' if order.side == 'buy' else 'asks'
        
        if self.matching_algorithm == 'FIFO':
            # FIFO: append at end (first in, first out)
            order_book[side].append(order)
        else:
            # Pro-Rata: maintain price-time priority
            # Insert at appropriate position based on price and time
            inserted = False
            for i, existing_order in enumerate(order_book[side]):
                if order.side == 'buy':
                    # For bids: higher price first, then earlier time
                    if order.price > existing_order.price or \
                       (order.price == existing_order.price and order.created_at < existing_order.created_at):
                        order_book[side].insert(i, order)
                        inserted = True
                        break
                else:
                    # For asks: lower price first, then earlier time
                    if order.price < existing_order.price or \
                       (order.price == existing_order.price and order.created_at < existing_order.created_at):
                        order_book[side].insert(i, order)
                        inserted = True
                        break
            
            if not inserted:
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