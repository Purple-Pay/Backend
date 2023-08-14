import secrets
import hashlib
import hmac
import uuid
import time
from datetime import datetime


def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes
            # this call is needed for request permissions
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)
        return decorated_func
    return decorator


def generate_secret_for_api_key():
    # Specify the desired key length in bytes
    key_length_bytes = 16      # 256 bits (recommended for higher security)

    # Generate a random secret key
    secret_key = secrets.token_hex(key_length_bytes)

    print("Generated Secret Key:", secret_key)
    return secret_key


def generate_secret_for_webhook():
    # Specify the desired key length in bytes
    key_length_bytes = 16      # 256 bits (recommended for higher security)

    # Generate a random secret key
    secret_key = secrets.token_hex(key_length_bytes)

    print("Generated Secret Key:", secret_key)
    return secret_key


def generate_signature(payload, secret_key):
    return hmac.new(
        bytes(secret_key, "utf-8"),
        msg=bytes(payload, "utf-8"),
        digestmod=hashlib.sha512
    ).hexdigest().upper()


def verify_signature(payload, secret_key, received_signature):
    expected_signature = generate_signature(payload, secret_key)
    print("*" * 100)
    print("Received Signature: ", received_signature)
    print("*" * 100)
    print("Expected Signature: ", expected_signature)
    print('Payload:', payload)
    print('Secret key:', secret_key)
    print("*" * 100)
    return expected_signature == received_signature


def generate_checkout_id():
    # Search merchant

    timestamp = int(time.time() * 1000)
    random_chars = str(uuid.uuid4().hex)[:6]
    checkout_id = f"{timestamp}_{random_chars}"

    return checkout_id


# # Generate a unique checkout ID
# checkout_id = generate_checkout_id()
# print("Generated Checkout ID:", checkout_id)


def generate_timestamp():
    timestamp = datetime.now()
    unix_timestamp_ms = int(timestamp.timestamp() * 1000)
    return unix_timestamp_ms


def generate_nonce():
    nonce_length_bytes = 16  # Adjust the length as needed

    # Generate a random nonce as a hexadecimal string
    random_nonce = secrets.token_hex(nonce_length_bytes)
    return random_nonce


def generate_webhook_signature(request_payload, secret_key):
    timestamp = generate_timestamp()
    nonce = generate_nonce()
    signature_payload = f"{timestamp}\n{nonce}\n{request_payload}\n"
    signature = generate_signature(signature_payload, secret_key)
    print(signature)
    result = dict(signature=signature, timestamp=timestamp, signature_payload=signature_payload, nonce=nonce)
    return result


