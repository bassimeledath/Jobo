from pydantic import BaseModel, Field
from typing import List, Optional

class TextInput(BaseModel):
    name: Optional[str] = None

class TextResponse(BaseModel):
    identifier: str
    value: str

class RadioOption(BaseModel):
    value: str
    checked: bool

class RadioButtonGroup(BaseModel):
    name: str
    options: List[RadioOption]
    labelOrText: str

class RadioResponse(BaseModel):
    name: str
    selectedValue: str

class TextareaInput(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    placeholder: Optional[str] = None

class TextareaResponse(BaseModel):
    identifier: str
    value: str
