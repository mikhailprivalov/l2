from .celery import app as celery_app

__all__ = ('celery_app',)

__version__ = (2022, 1, 12, 'c3149530')
VERSION = ".".join(map(str, __version__))
