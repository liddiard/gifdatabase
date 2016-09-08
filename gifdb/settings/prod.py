from .base import *
import dj_database_url

DEBUG = False

THUMB_DIR = "thumb"

DATABASES = {
    'default': dj_database_url.config()
}


REGISTRATION_OPEN = os.environ.get('REGISTRATION_OPEN', False)

# email settings
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_HOST_USER = get_env_variable('SENDGRID_USERNAME')
EMAIL_HOST_PASSWORD = get_env_variable('SENDGRID_PASSWORD')
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = "kikl.co <no-reply@kikl.co>"