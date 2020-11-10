import os

AWS_S3_OBJECT_PARAMETERS = {
    'Expires': 'Thu, 31 Dec 2099 20:00:00 GMT',
    'CacheControl': 'max-age=94608000',
}
AWS_DEFAULT_ACL = None
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', None)
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', None)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', None)
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', None)
AWS_S3_HOST = os.getenv('AWS_S3_HOST', 's3.amazonaws.com')
AWS_S3_PROTOCOL = os.getenv('AWS_S3_PROTOCOL', 'https')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.{AWS_S3_HOST}'
AWS_S3_ENDPOINT_URL = f'{AWS_S3_PROTOCOL}://{AWS_S3_HOST}'
AWS_S3_BUCKET_URL = f'{AWS_S3_PROTOCOL}://{AWS_S3_CUSTOM_DOMAIN}'

MEDIAFILES_LOCATION = 'media'
DEFAULT_FILE_STORAGE = 'storage.custom_storage.MediaStorage'
S3_DB_EXPORT_LOCATION = 'export'

AWS_EMBEDDINGS_FILE_PATH = 'embeddings/embeddings_3d.json'
EMBEDDINGS_FILE_URL = AWS_S3_BUCKET_URL + f'/{AWS_EMBEDDINGS_FILE_PATH}'
PAPER_ATLAS_IMAGES_FILE_URL = AWS_S3_BUCKET_URL + '/embeddings/atlas.jpg'

AWS_SES_ACCESS_KEY_ID = os.getenv('AWS_SES_ACCESS_KEY_ID', None)
AWS_SES_SECRET_ACCESS_KEY = os.getenv('AWS_SES_SECRET_ACCESS_KEY', None)
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_REGION_NAME = 'eu-central-1'
AWS_SES_REGION_ENDPOINT = 'email.eu-central-1.amazonaws.com'
