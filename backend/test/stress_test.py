import requests
import concurrent.futures
import time

API_URL = "http://localhost:5000/api"
TEST_USER = {
    "username": "testuser",
    "email": "test@test.com",
    "password": "password123"
}


def register_user():
    response = requests.post(f"{API_URL}/auth/register", json=TEST_USER)
    return response.json()


def login_user():
    response = requests.post(f"{API_URL}/auth/login", json={
        "username": TEST_USER["username"],
        "password": TEST_USER["password"]
    })
    return response.json()


def place_order(token, side="buy"):
    headers = {"Authorization": f"Bearer {token}"}
    order = {
        "trading_pair": "BTC/USDT",
        "side": side,
        "order_type": "limit",
        "price": 45000 if side == "buy" else 46000,
        "quantity": 0.01
    }
    response = requests.post(f"{API_URL}/trading/order", json=order, headers=headers)
    return response


def stress_test_orders(num_orders=100):
    # Login
    auth_data = login_user()
    token = auth_data.get("access_token")

    start_time = time.time()

    # Place orders concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for i in range(num_orders):
            side = "buy" if i % 2 == 0 else "sell"
            future = executor.submit(place_order, token, side)
            futures.append(future)

        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    end_time = time.time()

    success_count = sum(1 for r in results if r.status_code == 201)

    print(f"Total Orders: {num_orders}")
    print(f"Successful: {success_count}")
    print(f"Failed: {num_orders - success_count}")
    print(f"Time Taken: {end_time - start_time:.2f} seconds")
    print(f"Orders per second: {num_orders / (end_time - start_time):.2f}")


if __name__ == "__main__":
    print("Starting stress test...")

    # Register user
    register_result = register_user()
    print("User registered")

    # Deposit funds
    auth_data = login_user()
    token = auth_data.get("access_token")

    headers = {"Authorization": f"Bearer {token}"}
    requests.post(f"{API_URL}/wallet/deposit",
                  json={"currency": "USDT", "amount": 1000000},
                  headers=headers)
    requests.post(f"{API_URL}/wallet/deposit",
                  json={"currency": "BTC", "amount": 10},
                  headers=headers)
    print("Funds deposited")

    # Run stress test
    stress_test_orders(100)