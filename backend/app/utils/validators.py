import re
from decimal import Decimal, InvalidOperation


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_username(username: str) -> bool:
    """Validate username (alphanumeric, 3-20 chars)"""
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None


def validate_password(password: str) -> tuple:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain number"
    return True, "Valid"


def validate_amount(amount: str) -> tuple:
    """Validate and convert amount"""
    try:
        decimal_amount = Decimal(amount)
        if decimal_amount <= 0:
            return False, None
        return True, decimal_amount
    except (InvalidOperation, ValueError):
        return False, None


def validate_trading_pair(pair: str) -> bool:
    """Validate trading pair format"""
    pattern = r'^[A-Z]{2,10}/[A-Z]{2,10}$'
    return re.match(pattern, pair) is not None


def validate_ethereum_address(address: str) -> bool:
    """Validate Ethereum address"""
    pattern = r'^0x[a-fA-F0-9]{40}$'
    return re.match(pattern, address) is not None
