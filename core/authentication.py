from rest_framework import authentication, exceptions
from config.settings import settings


class APIKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        api_key = request.headers.get('X-Api-Key')
        
        if not api_key:
            raise exceptions.AuthenticationFailed('API key is required')
        
        if api_key != settings.API_KEY:
            raise exceptions.AuthenticationFailed('Invalid API key')
        
        return (None, None)
