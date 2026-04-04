import redis
from django.conf import settings


_redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=20,
    decode_responses=True,
)


def get_redis_client():
    return redis.Redis(connection_pool=_redis_pool)