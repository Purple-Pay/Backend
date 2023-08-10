import secrets
import hashlib
import hmac


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


def generate_signature(payload, secret_key):
    return hmac.new(
        bytes(secret_key, "utf-8"),
        msg=bytes(payload, "utf-8"),
        digestmod=hashlib.sha512
    ).hexdigest().upper()


def verify_signature(payload, secret_key, received_signature):
    expected_signature = generate_signature(payload, secret_key)
    print("*" * 100)
    print("Recevied Signature: ", received_signature)
    print("*" * 100)
    print("Expected Signature: ", expected_signature)
    print('Payload:', payload)
    print('Secret key:', secret_key)
    print("*" * 100)
    return expected_signature == received_signature








