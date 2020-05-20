from .settings_base import *
from collabovid_settings.service_settings import *
from collabovid_settings.postgres_settings import *
from collabovid_settings.tasks_settings import *
from collabovid_settings.aws_settings import *

DEBUG = False

ALLOWED_HOSTS += [SEARCH_SERVICE_HOST]

POD_IP = os.getenv('POD_IP', None)
if POD_IP:
    ALLOWED_HOSTS += [POD_IP]


SECRET_KEY = os.getenv('SECRET_KEY', '7_%)-$#43s2hk6e6)ip)4+*3d6vz&73%zqos7un9qkz$2pt@h*')