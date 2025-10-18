from django.http import HttpResponseForbidden
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages
from .utils import is_ip_blocked

class SecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get IP address
        ip_address = self._get_client_ip(request)

        # Check if IP is blocked
        if is_ip_blocked(ip_address):
            # Allow access to certain paths like 'contact'
            if request.path == reverse('members:contact'):
                return self.get_response(request)
class ThemeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set theme context variable for templates
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                # Try to get the member's theme preference
                request.theme = request.user.member.theme_preference
            except:
                # Default to light theme if there's an error
                request.theme = 'light'
        else:
            # Default theme for non-authenticated users
            request.theme = request.session.get('theme', 'light')

        response = self.get_response(request)
        return response

        # Block access to all other paths
        messages.error(request, "Access denied. Please contact support if you believe this is an error.")
        return HttpResponseForbidden("Access denied. Your IP has been blocked due to suspicious activity.")

        return self.get_response(request)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages
from .utils import is_ip_blocked

class SecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get IP address
        ip_address = self._get_client_ip(request)

        # Check if IP is blocked
        if is_ip_blocked(ip_address):
            # Allow access to certain paths like 'contact'
            if request.path == reverse('members:contact'):
                return self.get_response(request)

            # Block access to all other paths
            messages.error(request, "Access denied. Please contact support if you believe this is an error.")
            return HttpResponseForbidden("Access denied. Your IP has been blocked due to suspicious activity.")

        return self.get_response(request)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip