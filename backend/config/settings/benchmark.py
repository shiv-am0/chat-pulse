"""Settings for repeatable local performance benchmarks.

This module deliberately refuses to start unless the selected database name
contains ``benchmark``. That guard keeps data-generation commands and load tests
away from development and production databases.
"""

from django.core.exceptions import ImproperlyConfigured
from decouple import config

from .local import *  # noqa: F403


DEBUG = False
BENCHMARK_MODE = True
BENCHMARK_USER_PASSWORD = config("BENCHMARK_USER_PASSWORD", default="")

database_name = str(DATABASES["default"]["NAME"])  # noqa: F405
if "benchmark" not in database_name.lower():
    raise ImproperlyConfigured(
        "Benchmark settings require a database whose name contains 'benchmark'."
    )

if config("BENCHMARK_DISABLE_THROTTLING", default=False, cast=bool):
    REST_FRAMEWORK = {  # noqa: F405
        **REST_FRAMEWORK,  # noqa: F405
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }
