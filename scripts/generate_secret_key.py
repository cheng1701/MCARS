#!/usr/bin/env python
"""
Generate a secure random Django secret key.
Run this script to generate a new secret key for your .env file.
"""

import secrets
import string


def generate_secret_key(length=50):
    """
    Generate a secure random string suitable for use as a Django secret key.
    """
    chars = string.ascii_letters + string.digits + '!@#$%^&*()_-+='
    return ''.join(secrets.choice(chars) for _ in range(length))


if __name__ == "__main__":
    # Generate a new secret key
    secret_key = generate_secret_key()

    print("\nGenerated Django SECRET_KEY:\n")
    print(secret_key)
    print("\nAdd this to your .env file as:\n")
    print(f"SECRET_KEY={secret_key}")
    print("\nKeep this value secret and never commit it to version control!\n")
