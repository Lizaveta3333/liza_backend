from pydantic import BaseModel


class ResponseTokensSchema(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


# class ResponseTokensSchema(BaseModel):
#     access_token: str
#     refresh_token: str
