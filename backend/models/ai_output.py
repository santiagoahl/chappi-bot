from pydantic import BaseModel, Field, StrictStr
from typing import Annotated, Optional

payment_reference_pattern = "^M(\d{7}|\d{8})"  # Get invoice reference number


class ResponseModel(BaseModel):
    pass


class StandardModel(ResponseModel):
    ai_reponse: StrictStr


class PaymentModel(ResponseModel):
    ai_reponse: Annotated[str, Field(pattern=payment_reference_pattern)]
