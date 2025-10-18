#!/usr/bin/env python
"""
Check if all required environment variables are set.

This script helps validate that all necessary environment variables
are properly configured in the .env file or system environment.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv package is not installed.")
    print("Please install it with: pip install python-dotenv")
    sys.exit(1)


def check_env_variables():
    """
    Check if all required environment variables are set.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Define required variables
    required_vars = [
        ('SECRET_KEY', 'Django secret key for security'),
        ('DEBUG', 'Debug mode (True/False)'),
        ('ALLOWED_HOSTS', 'Comma-separated list of allowed hosts'),
    ]

    # Define recommended variables
    recommended_vars = [
        ('DATABASE_URL', 'Database connection URL'),
        ('EMAIL_BACKEND', 'Email backend configuration'),
        ('DEFAULT_FROM_EMAIL', 'Default sender email address'),
        ('STATIC_URL', 'URL path for static files'),
        ('MEDIA_URL', 'URL path for media files'),
    ]

    # Check required variables
    missing_required = []
    for var, desc in required_vars:
        if not os.environ.get(var):
            missing_required.append((var, desc))

    # Check recommended variables
    missing_recommended = []
    for var, desc in recommended_vars:
        if not os.environ.get(var):
            missing_recommended.append((var, desc))

    # Print results
    print("\nEnvironment Variable Check Results:")
    print("=====================================\n")

    if missing_required:
        print("CRITICAL: Missing required environment variables:")
        for var, desc in missing_required:
            print(f"  - {var}: {desc}")
        print("\nThese variables must be set for the application to function correctly.")
    else:
        print("✅ All required environment variables are set.")

    if missing_recommended:
        print("\nWARNING: Missing recommended environment variables:")
        for var, desc in missing_recommended:
            print(f"  - {var}: {desc}")
        print("\nConsider setting these variables for optimal application configuration.")
    else:
        print("✅ All recommended environment variables are set.")

    # Print current configuration (for debugging)
    if '--verbose' in sys.argv:
        print("\nCurrent Environment Configuration:")
        print("==================================\n")

        all_vars = required_vars + recommended_vars
        for var, desc in all_vars:
            value = os.environ.get(var, 'Not set')
            # Mask sensitive information
            if var in ['SECRET_KEY', 'EMAIL_HOST_PASSWORD'] and value != 'Not set':
                value = '********'
            print(f"{var}: {value}")

    return not bool(missing_required)


if __name__ == "__main__":
    # Get the project root directory
    base_dir = Path(__file__).resolve().parent.parent

    # Check if .env file exists
    env_file = base_dir / ".env"
    if not env_file.exists():
        print(f"WARNING: No .env file found at {env_file}")
        print("You should create a .env file based on .env.example")
        print("\nRun: python scripts/setup_env.py to set up your environment file.\n")

    # Check environment variables
    success = check_env_variables()

    # Exit with appropriate status code
    sys.exit(0 if success else 1)
