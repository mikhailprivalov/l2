import redis

from laboratory import settings

redis_client = None


def get_redis_client():
    global redis_client
    if not redis_client:
        cache_settings = settings.CACHES['default']
        if 'redis' in cache_settings['BACKEND'].lower():
            location = cache_settings['LOCATION']
            if isinstance(location, str):
                redis_client = redis.Redis.from_url(location)

    return redis_client
