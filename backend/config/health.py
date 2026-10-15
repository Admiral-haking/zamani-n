from django.db import connection
from django.http import JsonResponse


def health(request):
    """Small public readiness probe without exposing database credentials."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return JsonResponse({"status": "ok", "database": "connected"})
    except Exception:
        return JsonResponse({"status": "error", "database": "unavailable"}, status=503)
