#!/usr/bin/env python
"""
Setup environment file for Django project.

This script helps create a .env file based on .env.example,
and generates a new secret key for the project.
"""

import os
import secrets
import string
import shutil
from pathlib import Path


def generate_secret_key(length=50):
    """
    Generate a secure random string suitable for use as a Django secret key.
    """
    chars = string.ascii_letters + string.digits + '!@#$%^&*()_-+='
    return ''.join(secrets.choice(chars) for _ in range(length))


def setup_env_file():
    """
    Set up the .env file based on .env.example.
    """
    # Get the project root directory
    base_dir = Path(__file__).resolve().parent.parent

    # Check if .env file already exists
    env_file = base_dir / ".env"
    env_example_file = base_dir / ".env.example"

    if env_file.exists():
        overwrite = input(".env file already exists. Overwrite? (y/n): ").lower() == 'y'
        if not overwrite:
            print("Setup cancelled. Existing .env file was not modified.")
            return False

    # Check if .env.example exists
    if not env_example_file.exists():
        print("Error: .env.example file not found.")
        return False

    # Generate a new secret key
    secret_key = generate_secret_key()

    # Copy .env.example to .env
    shutil.copy(env_example_file, env_file)

    # Read the .env file
    with open(env_file, 'r') as f:
        env_content = f.read()

    # Replace the secret key placeholder
    env_content = env_content.replace(
        "SECRET_KEY=your-secret-key-here",
        f"SECRET_KEY={secret_key}"
    )

    # Write the updated content back to .env
    with open(env_file, 'w') as f:
        f.write(env_content)

    print("\nEnvironment setup complete!")
    print(f"A new .env file has been created at: {env_file}")
    print("A new SECRET_KEY has been generated and added to the .env file.")
    print("\nMake sure to review and update other settings in the .env file as needed.")
    return True


if __name__ == "__main__":
    setup_env_file()
