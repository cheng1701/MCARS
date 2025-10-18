from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.core.cache import cache
import re

# Email functions
def send_registration_email(member):
    """Send email to new member when they register"""
    subject = 'Your Membership Application is Being Reviewed'
    context = {
        'member': member,
        'user': member.user,
    }
    html_message = render_to_string('emails/registration_email.html', context)
    plain_message = render_to_string('emails/registration_email_plain.txt', context)

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [member.user.email],
        html_message=html_message,
        fail_silently=False,
    )

def send_approval_email(member):
    """Send email to member when their membership is approved"""
    subject = 'Your Membership Has Been Approved'
    context = {
        'member': member,
        'user': member.user,
    }
    html_message = render_to_string('emails/approval_email.html', context)
    plain_message = render_to_string('emails/approval_email_plain.txt', context)

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [member.user.email],
        html_message=html_message,
        fail_silently=False,
    )

# Security functions
def is_email_blocked(email):
    """Check if email is in blocklist"""
    # Check cache first
    cache_key = f"blocked_email:{email}"
    if cache.get(cache_key):
        return True

    # Check for common disposable email domains
    disposable_domains = [
        'tempmail.com', 'throwawaymail.com', 'mailinator.com',
        'temp-mail.org', 'guerrillamail.com', 'yopmail.com',
        'sharklasers.com', 'trashmail.com', 'fakeinbox.com'
    ]

    domain = email.split('@')[-1]
    if domain.lower() in disposable_domains:
        # Add to cache
        cache.set(cache_key, True, settings.BLOCKED_EMAILS_CACHE_TTL)
        return True
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.core.cache import cache
import re

# Email functions
def send_registration_email(member):
    """Send email to new member when they register"""
    subject = 'Your Membership Application is Being Reviewed'
    context = {
        'member': member,
        'user': member.user,
    }
    html_message = render_to_string('emails/registration_email.html', context)
    plain_message = render_to_string('emails/registration_email_plain.txt', context)

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [member.user.email],
        html_message=html_message,
        fail_silently=False,
    )

def send_approval_email(member):
    """Send email to member when their membership is approved"""
    subject = 'Your Membership Has Been Approved'
    context = {
        'member': member,
        'user': member.user,
    }
    html_message = render_to_string('emails/approval_email.html', context)
    plain_message = render_to_string('emails/approval_email_plain.txt', context)

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [member.user.email],
        html_message=html_message,
        fail_silently=False,
    )

# Security functions
def is_email_blocked(email):
    """Check if email is in blocklist"""
    # Check cache first
    cache_key = f"blocked_email:{email}"
    if cache.get(cache_key):
        return True

    # Check for common disposable email domains
    disposable_domains = [
        'tempmail.com', 'throwawaymail.com', 'mailinator.com',
        'temp-mail.org', 'guerrillamail.com', 'yopmail.com',
        'sharklasers.com', 'trashmail.com', 'fakeinbox.com'
    ]

    domain = email.split('@')[-1]
    if domain.lower() in disposable_domains:
        # Add to cache
        cache.set(cache_key, True, 86400)  # 24 hours
        return True

    return False

def is_ip_blocked(ip_address):
    """Check if IP is in blocklist"""
    cache_key = f"blocked_ip:{ip_address}"
    return cache.get(cache_key, False)

def block_ip(ip_address):
    """Add IP to blocklist"""
    cache_key = f"blocked_ip:{ip_address}"
    cache.set(cache_key, True, 86400)  # 24 hours

def block_email(email):
    """Add email to blocklist"""
    cache_key = f"blocked_email:{email}"
    cache.set(cache_key, True, 86400)  # 24 hours

def increment_failed_attempts(ip_address):
    """Increment failed login/registration attempts"""
    cache_key = f"failed_attempts:{ip_address}"
    attempts = cache.get(cache_key, 0) + 1
    cache.set(cache_key, attempts, 3600)  # 1 hour expiry

    # Block IP if too many attempts
    if attempts >= 5:  # Default threshold
        block_ip(ip_address)

    return attempts

def reset_failed_attempts(ip_address):
    """Reset failed attempts counter"""
    cache_key = f"failed_attempts:{ip_address}"
    cache.delete(cache_key)
    return False

def is_ip_blocked(ip_address):
    """Check if IP is in blocklist"""
    cache_key = f"blocked_ip:{ip_address}"
    return cache.get(cache_key, False)

def block_ip(ip_address):
    """Add IP to blocklist"""
    cache_key = f"blocked_ip:{ip_address}"
    cache.set(cache_key, True, settings.BLOCKED_IPS_CACHE_TTL)

def block_email(email):
    """Add email to blocklist"""
    cache_key = f"blocked_email:{email}"
    cache.set(cache_key, True, settings.BLOCKED_EMAILS_CACHE_TTL)

def increment_failed_attempts(ip_address):
    """Increment failed login/registration attempts"""
    cache_key = f"failed_attempts:{ip_address}"
    attempts = cache.get(cache_key, 0) + 1
    cache.set(cache_key, attempts, 3600)  # 1 hour expiry

    # Block IP if too many attempts
    if attempts >= settings.FAILED_LOGIN_ATTEMPTS_ALLOWED:
        block_ip(ip_address)

    return attempts
def create_member_if_needed(user):
    """
    Create a Member profile for a user if one doesn't exist yet
    Returns the Member object
    """
    from .models import Member, Address, MembershipType
    import uuid

    try:
        return user.member
    except Member.DoesNotExist:
        # Create a default address
        address = Address.objects.create(
            street='',
            city='',
            state='',
            zip_code='',
            country='USA'
        )

        # Get the default/free membership type
        try:
            membership_type = MembershipType.objects.filter(billing_frequency='free').first()
            if not membership_type:
                membership_type = MembershipType.objects.first()
        except:
            membership_type = None

        # Create a new member profile
        return Member.objects.create(
            user=user,
            phone_number='',
            address=address,
            status='pending',
            membership_type=membership_type,
            membership_id=str(uuid.uuid4())[:8].upper()
        )
def reset_failed_attempts(ip_address):
    """Reset failed attempts counter"""
    cache_key = f"failed_attempts:{ip_address}"
    cache.delete(cache_key)
