from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


def verify_token(token: str):
    # stub: add actual validation
    if not token:
        raise ValueError('Missing token')
    return True
