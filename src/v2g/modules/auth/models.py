from v2g.core.models import BaseSchema


class Token(BaseSchema):
    access_token: str
    token_type: str = 'bearer'
