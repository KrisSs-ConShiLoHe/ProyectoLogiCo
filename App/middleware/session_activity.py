from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class SessionActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.session['ultima_actividad'] = timezone.now().isoformat()
        return self.get_response(request)