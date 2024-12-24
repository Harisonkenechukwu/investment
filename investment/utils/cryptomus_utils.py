### utils/cryptomus_utils.py
import requests
import hmac
import hashlib

CRYPTOMUS_API_URL = "https://api.cryptomus.com/v1/"
API_KEY = "c0b898ec737ed2b849ef9fa9541b2f250fd68957"
MERCHANT_ID = "1468d624-10ed-4fe3-baee-83ea70624a92"


def create_cryptomus_invoice(amount, user_id, callback_url, success_url):
    headers = {
        "Content-Type": "application/json",
        "apikey": API_KEY,
    }

    data = {
        "merchant": MERCHANT_ID,
        "amount": str(amount),
        "order_id": f"user-{user_id}",
        "currency": "USDT",
        "callback_url": callback_url,
        "success_url": success_url,
    }

    response = requests.post(f"{CRYPTOMUS_API_URL}invoice", json=data, headers=headers)

    if response.status_code == 200:
        result = response.json()
        if 'result' in result and 'url' in result['result']:
            return result
        else:
            print("Invalid Cryptomus response:", result)
    else:
        print("Cryptomus request failed:", response.status_code, response.text)

    return None


def verify_signature(secret_key, data, signature):
    sorted_data = ''.join(f"{key}:{value}" for key, value in sorted(data.items()))
    calculated_signature = hmac.new(secret_key.encode(), sorted_data.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(calculated_signature, signature)