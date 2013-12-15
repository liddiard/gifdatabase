from .base import *

# email settings
EMAIL_HOST = 'smtp.mandrill.com'
EMAIL_PORT = 465
EMAIL_HOST_USER = os.environ['MANDRILL_USERNAME']
EMAIL_HOST_PASSWORD = os.environ['MANDRILL_APIKEY']
EMAIL_USE_SSL = True
