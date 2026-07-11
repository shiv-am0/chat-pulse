import logging
from django.http import JsonResponse
from django.db import connection
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)


def health_check(request):
    db_ok = True
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except OperationalError:
        db_ok = False
        logger.error("Health check: database unreachable")

    status_code = 200 if db_ok else 503
    return JsonResponse(
        {
            'status': 'ok' if db_ok else 'degraded',
            'database': 'ok' if db_ok else 'error',
        },
        status=status_code,
    )
