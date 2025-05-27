from pydantic import BaseModel
from typing import Optional

class InputQueryDto(BaseModel):
    query_text: str
    source: Optional[str] = "text" 
    email: Optional[str] = None     
