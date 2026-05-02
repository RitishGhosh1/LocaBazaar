from authlib.integrations.starlette_client import OAuth
from app.core.config import config

oauth = OAuth()
oauth.register(
    name='google',
    client_id=config.GOOGLE_CLIENT_ID,
    client_secret=config.GOOGLE_CLIENT_SECRET,
    server_metadata_url=config.GOOGLE_CONF_URL,
    client_kwargs={
        'scope': 'openid email profile'
    }
)
