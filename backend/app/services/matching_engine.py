from decimal import Decimal
from typing import Dict, Literal
import threading

from flask import current_app

from .. import db, socketio
from ..models.order import Order, Trade
from ..models.wallet import Wallet


class OrderMatchingEngine:
    """
    Simple FIFO order matching engine.

    - In-memory order books:
        self.order_books[pair] = {"bids": [Order], "asks": [Order]}
    - Matching is done synchronously when add_order() is called.
    - No background thread, no Queue.
    """

    def __init__(self, matching_algorithm: Literal["FIFO"] = "FIFO"):
        self.order_books: Dict[str, Dict] = {}
        self.lock = threading.Lock()
        self.matching_algorithm = matching_algorithm  # kept for config compatibility

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
    def start(self):
        """Kept for compatibility – nothing to start in synchronous mode."""
        print("Matching engine running in synchronous FIFO mode")

    def stop(self):
        """Kept for compatibility – nothing to stop."""
        pass

    def add_order(self, order: Order):
        """
        Entry point from your route.

        Called from /api/trading/order after the order is saved to DB.
        Matching is performed immediately in the same request.
        """
        pair = order.trading_pair

        with self.lock:
            # Ensure order book exists
            if pair not in self.order_books:
                self.order_books[pair] = {"bids": [], "asks": []}

            try:
                # Load fresh order from DB (ensure we have attached instance)
                if getattr(order, "order_id", None):
                    db_order = Order.query.filter_by(order_id=order.order_id).first()
                else:
                    db_order = Order.query.get(order.id)

                if not db_order:
                    print(f"[MatchingEngine] Order not found in DB: {order}")
                    return

                # Ensure remaining_quantity is set
                if db_order.remaining_quantity is None:
                    db_order.remaining_quantity = db_order.quantity - db_order.filled_quantity

                if db_order.remaining_quantity <= 0:
                    return

                # Decide matching path
                if db_order.order_type == "market":
                    self._match_market_order(db_order)
                else:
                    self._match_limit_order(db_order)

                # Persist changes
                db.session.commit()

                # Broadcast updated book
                self._broadcast_orderbook_update(pair)

            except Exception as e:
                db.session.rollback()
                print(f"[MatchingEngine] Error matching order {order}: {e}")
                import traceback
                traceback.print_exc()

    def get_orderbook(self, pair: str, depth: int = 20) -> Dict:
        """Return current order book snapshot for REST & WebSocket."""
        if pair not in self.order_books:
            return {"bids": [], "asks": []}

        book = self.order_books[pair]

        bids = [
            {
                "price": float(o.price),
                "quantity": float(o.remaining_quantity),
                "total": float(o.price * o.remaining_quantity),
            }
            for o in book["bids"][:depth]
            if o.remaining_quantity > 0
        ]

        asks = [
            {
                "price": float(o.price),
                "quantity": float(o.remaining_quantity),
                "total": float(o.price * o.remaining_quantity),
            }
            for o in book["asks"][:depth]
            if o.remaining_quantity > 0
        ]

        return {"bids": bids, "asks": asks}

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order and clean from book + wallets."""
        try:
            with current_app.app_context(), self.lock:
                order = Order.query.filter_by(order_id=order_id).first()
                if not order:
                    return False

                if order.status not in ["open", "partially_filled"]:
                    return False

                pair = order.trading_pair

                # Remove from in-memory book
                if pair in self.order_books:
                    side = "bids" if order.side == "buy" else "asks"
                    self.order_books[pair][side] = [
                        o for o in self.order_books[pair][side] if o.order_id != order_id
                    ]

                # Unlock remaining locked balance
                base_currency, quote_currency = pair.split("/")
                if order.side == "buy":
                    currency = quote_currency
                    amount = order.remaining_quantity * order.price
                else:
                    currency = base_currency
                    amount = order.remaining_quantity

                wallet = Wallet.query.filter_by(user_id=order.user_id, currency=currency).first()
                if wallet:
                    wallet.unlock_balance(amount)

                order.cancel()
                db.session.commit()

                self._broadcast_orderbook_update(pair)
                return True

        except Exception as e:
            db.session.rollback()
            print(f"[MatchingEngine] Error canceling order {order_id}: {e}")
            return False

    # -------------------------------------------------------------------------
    # Core matching logic
    # -------------------------------------------------------------------------
    def _match_market_order(self, order: Order):
        """Match a market order against the best prices on the opposite side."""
        pair = order.trading_pair
        book = self.order_books[pair]

        remaining = order.remaining_quantity
        if remaining <= 0:
            return

        if order.side == "buy":
            # Buy market → match against best asks (lowest price first)
            opposite_list = book["asks"]
        else:
            # Sell market → match against best bids (highest price first)
            opposite_list = book["bids"]

        i = 0
        while remaining > 0 and i < len(opposite_list):
            maker = opposite_list[i]

            # Skip empty / fully filled orders
            if maker.remaining_quantity <= 0 or maker.status == "filled":
                opposite_list.pop(i)
                continue

            # Market order takes whatever price is available
            match_qty = min(remaining, maker.remaining_quantity)
            match_price = maker.price

            self._execute_trade(taker_order=order, maker_order=maker,
                                quantity=match_qty, price=match_price)

            remaining = order.remaining_quantity  # update from Order.update_fill

            # Remove maker if fully filled
            if maker.remaining_quantity <= 0 or maker.status == "filled":
                opposite_list.pop(i)
            else:
                i += 1

        # Set final status
        if order.remaining_quantity <= 0:
            order.status = "filled"
        else:
            # For pure market, if nothing left to trade, mark as partially_filled or open
            order.status = "partially_filled" if order.filled_quantity > 0 else "open"

    def _match_limit_order(self, order: Order):
        """Match a limit order and add any remainder to the book."""
        pair = order.trading_pair
        book = self.order_books[pair]

        remaining = order.remaining_quantity
        if remaining <= 0:
            return

        if order.side == "buy":
            # Buy limit: match against asks with ask.price <= order.price
            opposite_list = book["asks"]
            price_ok = lambda maker_price: maker_price <= order.price
        else:
            # Sell limit: match against bids with bid.price >= order.price
            opposite_list = book["bids"]
            price_ok = lambda maker_price: maker_price >= order.price

        i = 0
        while remaining > 0 and i < len(opposite_list):
            maker = opposite_list[i]

            # Skip empty / fully filled
            if maker.remaining_quantity <= 0 or maker.status == "filled":
                opposite_list.pop(i)
                continue

            # Check price compatibility
            if not price_ok(maker.price):
                # Since list is sorted by best price first, we can stop here
                break

            match_qty = min(remaining, maker.remaining_quantity)
            match_price = maker.price  # maker's price wins

            self._execute_trade(taker_order=order, maker_order=maker,
                                quantity=match_qty, price=match_price)

            remaining = order.remaining_quantity

            if maker.remaining_quantity <= 0 or maker.status == "filled":
                opposite_list.pop(i)
            else:
                i += 1

        # After trying to match, if still quantity left → add to book
        if order.remaining_quantity > 0:
            order.status = "open" if order.filled_quantity == 0 else "partially_filled"
            self._add_to_orderbook(order)
        else:
            order.status = "filled"

    # -------------------------------------------------------------------------
    # Wallets, trades, book maintenance
    # -------------------------------------------------------------------------
    def _execute_trade(self, taker_order: Order, maker_order: Order,
                       quantity: Decimal, price: Decimal):
        """Execute a trade and update orders, wallets and broadcast."""
        if quantity <= 0:
            return

        # Fees
        fee_rate = Decimal("0.001")  # 0.1%
        maker_fee = quantity * price * fee_rate
        taker_fee = quantity * price * fee_rate

        # Update orders via model helpers
        taker_order.update_fill(quantity, price)
        maker_order.update_fill(quantity, price)

        taker_order.fee += taker_fee
        maker_order.fee += maker_fee

        # Trade record
        trade = Trade(
            maker_order_id=maker_order.id,
            taker_order_id=taker_order.id,
            trading_pair=taker_order.trading_pair,
            price=price,
            quantity=quantity,
            maker_fee=maker_fee,
            taker_fee=taker_fee,
        )
        db.session.add(trade)

        # Wallet updates
        self._update_wallets_after_trade(
            taker_order, maker_order, quantity, price, taker_fee, maker_fee
        )

        # Broadcast trade over WebSocket
        self._broadcast_trade(trade)

    def _update_wallets_after_trade(self, taker_order, maker_order,
                                    quantity, price, taker_fee, maker_fee):
        """Exactly your previous wallet logic, unchanged."""
        base_currency, quote_currency = taker_order.trading_pair.split("/")

        if taker_order.side == "buy":
            # Taker buys base with quote
            buyer_id, seller_id = taker_order.user_id, maker_order.user_id

            buyer_base = Wallet.query.filter_by(user_id=buyer_id, currency=base_currency).first()
            buyer_quote = Wallet.query.filter_by(user_id=buyer_id, currency=quote_currency).first()

            if buyer_base and buyer_quote:
                buyer_base.add_balance(quantity)
                buyer_quote.unlock_balance(quantity * price)
                buyer_quote.deduct_balance(quantity * price + taker_fee)

            seller_base = Wallet.query.filter_by(user_id=seller_id, currency=base_currency).first()
            seller_quote = Wallet.query.filter_by(user_id=seller_id, currency=quote_currency).first()

            if seller_base and seller_quote:
                seller_base.unlock_balance(quantity)
                seller_base.deduct_balance(quantity)
                seller_quote.add_balance(quantity * price - maker_fee)
        else:
            # Taker sells base for quote
            seller_id, buyer_id = taker_order.user_id, maker_order.user_id

            seller_base = Wallet.query.filter_by(user_id=seller_id, currency=base_currency).first()
            seller_quote = Wallet.query.filter_by(user_id=seller_id, currency=quote_currency).first()

            if seller_base and seller_quote:
                seller_base.unlock_balance(quantity)
                seller_base.deduct_balance(quantity)
                seller_quote.add_balance(quantity * price - taker_fee)

            buyer_base = Wallet.query.filter_by(user_id=buyer_id, currency=base_currency).first()
            buyer_quote = Wallet.query.filter_by(user_id=buyer_id, currency=quote_currency).first()

            if buyer_base and buyer_quote:
                buyer_base.add_balance(quantity)
                buyer_quote.unlock_balance(quantity * price)
                buyer_quote.deduct_balance(quantity * price + maker_fee)

    def _add_to_orderbook(self, order: Order):
        """Insert order into in-memory book with price-time priority."""
        pair = order.trading_pair
        if pair not in self.order_books:
            self.order_books[pair] = {"bids": [], "asks": []}

        book = self.order_books[pair]
        side_key = "bids" if order.side == "buy" else "asks"
        side_list = book[side_key]

        # Insert with best price first, then earlier time
        inserted = False
        for i, existing in enumerate(side_list):
            if order.side == "buy":
                # Higher price first; if equal price, older first
                if order.price > existing.price or (
                    order.price == existing.price and order.created_at < existing.created_at
                ):
                    side_list.insert(i, order)
                    inserted = True
                    break
            else:
                # Sell: lower price first; if equal, older first
                if order.price < existing.price or (
                    order.price == existing.price and order.created_at < existing.created_at
                ):
                    side_list.insert(i, order)
                    inserted = True
                    break

        if not inserted:
            side_list.append(order)

    # -------------------------------------------------------------------------
    # WebSocket broadcasting
    # -------------------------------------------------------------------------
    def _broadcast_orderbook_update(self, pair: str):
        try:
            data = self.get_orderbook(pair)
            socketio.emit(
                "orderbook_update",
                {"pair": pair, "data": data},
            )
        except Exception as e:
            print(f"[MatchingEngine] Error broadcasting orderbook: {e}")

    def _broadcast_trade(self, trade: Trade):
        try:
            socketio.emit("trade", trade.to_dict())
        except Exception as e:
            print(f"[MatchingEngine] Error broadcasting trade: {e}")


# Global instance
matching_engine = OrderMatchingEngine()
