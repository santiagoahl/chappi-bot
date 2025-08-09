from pydantic import BaseModel


# N: [SOLID] The responsability is to Represent the structure of the client's input 
class ClientModel(BaseModel):
    prompt: str
    file: bytes