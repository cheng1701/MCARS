#!/usr/bin/env python

"""
Standalone script to initialize data in the database.
This script can be run directly to seed the database with initial data.

Usage:
    python scripts/initialize_data.py
"""

import os
import sys
import django

# Add the project path to the sys.path list
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MCARS.settings')
django.setup()

from Members.models import MembershipType


def initialize_membership_types():
    print('Starting IFT-MCARS types initialization...')

    # Define the membership types
    membership_types = [
        {
            'name': 'Free Trial',
            'description': 'Basic membership with limited features for a year. Perfect for trying out our services.',
            'price': 0.00,
            'duration_months': 12,
            'is_family': False,
            'billing_frequency': 'free'
        },
        {
            'name': 'Basic',
            'description': 'Standard membership with all core features and benefits. Renews monthly.',
            'price': 5.99,
            'duration_months': 1,
            'is_family': False,
            'billing_frequency': 'monthly'
        },
        {
            'name': 'Premium',
            'description': 'Enhanced membership with premium features and priority support. Best value for individuals.',
            'price': 9.99,
            'duration_months': 1,
            'is_family': False,
            'billing_frequency': 'monthly'
        },
        {
            'name': 'Family',
            'description': 'Full membership for the whole family. Add multiple children and enjoy family-oriented events and services.',
            'price': 14.99,
            'duration_months': 1,
            'is_family': True,
            'billing_frequency': 'monthly'
        },
        {
            'name': 'Annual Standard',
            'description': 'Save over monthly billing with our annual plan. All standard features included.',
            'price': 59.99,
            'duration_months': 12,
            'is_family': False,
            'billing_frequency': 'yearly'
        },
        {
            'name': 'Annual Family',
            'description': 'Annual plan for families. Best value for families who want to commit for a year.',
            'price': 149.99,
            'duration_months': 12,
            'is_family': True,
            'billing_frequency': 'yearly'
        },
        {
            'name': 'Lifetime',
            'description': 'One-time payment for lifetime access to all our services. Never worry about renewals again.',
            'price': 299.99,
            'duration_months': 0,  # 0 indicates lifetime
            'is_family': False,
            'billing_frequency': 'lifetime'
        },
        {
            'name': 'Lifetime Family',
            'description': 'Lifetime membership for the whole family. The ultimate package with all premium features included.',
            'price': 499.99,
            'duration_months': 0,  # 0 indicates lifetime
            'is_family': True,
            'billing_frequency': 'lifetime'
        },
    ]

    # Create or update membership types
    created_count = 0
    updated_count = 0

    for mt_data in membership_types:
        membership_type, created = MembershipType.objects.update_or_create(
            name=mt_data['name'],
            defaults={
                'description': mt_data['description'],
                'price': mt_data['price'],
                'duration_months': mt_data['duration_months'],
                'is_family': mt_data['is_family'],
                'billing_frequency': mt_data['billing_frequency']
            }
        )

        if created:
            created_count += 1
            print(f'Created: {membership_type.name}')
        else:
            updated_count += 1
            print(f'Updated: {membership_type.name}')

    print(f'Membership types initialization complete. Created: {created_count}, Updated: {updated_count}')


def main():
    initialize_membership_types()
    print('All data initialized successfully.')


if __name__ == '__main__':
    main()
