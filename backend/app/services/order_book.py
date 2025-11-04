from typing import Dict, List
from decimal import Decimal
from datetime import datetime
from ..models.order import Order


class OrderBookManager:
    """Manages order books for all trading pairs"""

    def __init__(self):
        self.order_books: Dict[str, Dict] = {}

    def get_order_book(self, pair: str, depth: int = 20) -> Dict:
        """Get order book with specified depth"""
        if pair not in self.order_books:
            self.order_books[pair] = {'bids': [], 'asks': []}

        book = self.order_books[pair]

        # Sort and limit depth
        bids = sorted(book['bids'], key=lambda x: x['price'], reverse=True)[:depth]
        asks = sorted(book['asks'], key=lambda x: x['price'])[:depth]

        return {
            'bids': bids,
            'asks': asks,
            'timestamp': datetime.utcnow().isoformat()
        }

    def add_order(self, order: Order):
        """Add order to order book"""
        pair = order.trading_pair
        if pair not in self.order_books:
            self.order_books[pair] = {'bids': [], 'asks': []}

        order_data = {
            'order_id': order.order_id,
            'price': float(order.price),
            'quantity': float(order.remaining_quantity),
            'total': float(order.price * order.remaining_quantity)
        }

        side = 'bids' if order.side == 'buy' else 'asks'
        self.order_books[pair][side].append(order_data)

    def remove_order(self, order_id: str, pair: str):
        """Remove order from order book"""
        if pair in self.order_books:
            for side in ['bids', 'asks']:
                self.order_books[pair][side] = [
                    o for o in self.order_books[pair][side]
                    if o['order_id'] != order_id
                ]

    def update_order(self, order: Order):
        """Update order quantity in order book"""
        pair = order.trading_pair
        side = 'bids' if order.side == 'buy' else 'asks'

        if pair in self.order_books:
            for order_data in self.order_books[pair][side]:
                if order_data['order_id'] == order.order_id:
                    order_data['quantity'] = float(order.remaining_quantity)
                    order_data['total'] = float(order.price * order.remaining_quantity)
                    break


order_book_manager = OrderBookManager()