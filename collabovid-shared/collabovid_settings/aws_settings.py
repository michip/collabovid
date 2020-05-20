import os

AWS_S3_OBJECT_PARAMETERS = {
    'Expires': 'Thu, 31 Dec 2099 20:00:00 GMT',
    'CacheControl': 'max-age=94608000',
}

AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', None)
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', None)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', None)
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', None)
AWS_S3_HOST = os.getenv('AWS_S3_HOST', 's3.amazonaws.com')
AWS_S3_PROTOCOL = os.getenv('AWS_S3_PROTOCOL', 'https')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.{AWS_S3_HOST}'
AWS_S3_ENDPOINT_URL = f'{AWS_S3_PROTOCOL}://{AWS_S3_HOST}'

MEDIAFILES_LOCATION = 'media'
DEFAULT_FILE_STORAGE = 'storage.custom_storage.MediaStorage'
