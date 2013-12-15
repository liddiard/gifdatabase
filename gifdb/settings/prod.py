from .base import *
import dj_database_url

DEBUG = False

THUMB_DIR = "thumb"

DATABASES = {
    'default': dj_database_url.config()
}


REGISTRATION_OPEN = True

# email settings
EMAIL_HOST = 'smtp.mandrill.com'
EMAIL_PORT = 465
EMAIL_HOST_USER = get_env_variable('MANDRILL_USERNAME')
EMAIL_HOST_PASSWORD = get_env_variable('MANDRILL_APIKEY')
EMAIL_USE_SSL = True
