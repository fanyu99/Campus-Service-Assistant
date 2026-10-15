from pydantic import BaseModel


class ServiceItemResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str