# Razorpay Test Script
# Run this script locally using your virtual environment to verify your Razorpay API keys:
#
#   .venv/bin/python test_razorpay.py
#

import sys
import os
from decouple import Config, RepositoryEnv

env_path = os.path.join(os.path.dirname(__file__), ".env")
if not os.path.exists(env_path):
    print(f"Error: .env not found at {env_path}")
    sys.exit(1)

env = Config(RepositoryEnv(env_path))

RAZORPAY_KEY_ID = env("RAZORPAY_KEY_ID", default="")
RAZORPAY_KEY_SECRET = env("RAZORPAY_KEY_SECRET", default="")

print("Loaded keys from .env:")
print(f"RAZORPAY_KEY_ID = {RAZORPAY_KEY_ID}")
print(f"RAZORPAY_KEY_SECRET = {'*' * len(RAZORPAY_KEY_SECRET) if RAZORPAY_KEY_SECRET else 'Empty'}")

if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    print("Error: Keys are missing or empty in .env!")
    sys.exit(1)

try:
    import razorpay
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    
    print("\nAttempting to create a test order in Razorpay...")
    order_data = {
        "amount": 100,  # 1 INR (100 paise)
        "currency": "INR",
        "receipt": "test_receipt_antigravity",
        "notes": {
            "test_key": "verification_test"
        }
    }
    
    order = client.order.create(data=order_data)
    print("\nSuccess! Test order created in Razorpay dashboard:")
    print(f"Order ID: {order.get('id')}")
    print(f"Status: {order.get('status')}")
    print(f"Amount: {order.get('amount')} {order.get('currency')}")
    
except Exception as e:
    print(f"\nError: Failed to connect to Razorpay or keys are invalid.")
    print(f"Details: {e}")
    sys.exit(1)
