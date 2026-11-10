"""Only configured DNS names and literal IP addresses may reach Django.

Django ALLOWED_HOSTS='*' is required to support unknown server IPs before
deployment; this middleware replaces that wildcard with strict validation.
It MUST remain first in MIDDLEWARE, before SecurityMiddleware and CsrfViewMiddleware.
"""
import ipaddress

from django.conf import settings
from django.core.exceptions import DisallowedHost
from django.http import JsonResponse
from django.http.request import split_domain_port, validate_host


class HostValidationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        raw = request.META.get("HTTP_HOST") or request.META.get("SERVER_NAME", "")
        domain, _port = split_domain_port(raw)
        allowed = bool(domain) and validate_host(domain, settings.QUIZ_STATIC_ALLOWED_HOSTS)
        if not allowed and domain and settings.QUIZ_ALLOW_IP_HOSTS:
            try:
                ipaddress.ip_address(domain.strip("[]"))
                allowed = True
            except ValueError:
                pass
        if not allowed:
            if request.path.startswith("/api/"):
                return JsonResponse(
                    {"error": "Unrecognized hostname. Use the server IP or add your DNS name to DJANGO_ALLOWED_HOSTS."},
                    status=400,
                )
            raise DisallowedHost("Host is not permitted.")
        return self.get_response(request)
