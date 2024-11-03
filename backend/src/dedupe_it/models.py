from pydantic import BaseModel, Field
from typing import Dict, Any


class Record(BaseModel):
    id: str = Field(..., description="Unique identifier for the record")
    data: Dict[str, Any] = Field(..., description="The actual record data")

    def to_dict(self) -> Dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict) -> "Record":
        return cls(**data)
