"""
Imports the proper settings, based on the deployment environment's name (set
as an environment variable), defaulting to local settings.
"""
import os

from django.core.exceptions import ImproperlyConfigured


# Environments (these can be called anything you want)
ENV_LOCAL = 'local'
ENV_PROD = 'prod'
DEPLOYMENT_ENVS = (ENV_LOCAL, ENV_PROD)

# Get the deployment environment's name from the os environment
DEPLOYMENT_ENV = os.getenv('DJANGO_DEPLOYMENT_ENV', ENV_LOCAL)

# Ensure the deployment env's name is valid
if DEPLOYMENT_ENV not in DEPLOYMENT_ENVS:
    raise ImproperlyConfigured(
        u'Invalid `DJANGO_DEPLOYMENT_ENV`: {d}'.format(d=DEPLOYMENT_ENV)
    )

# Import env-specific settings

if DEPLOYMENT_ENV == ENV_LOCAL:
    # Local, native testing
    from .local import *

if DEPLOYMENT_ENV == ENV_PROD:
    # Production
    from .prod import *
