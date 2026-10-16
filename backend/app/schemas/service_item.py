from pydantic import BaseModel


class ServiceItemResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    # 契约 §3.1 的「选返」字段：补齐后前端可直接消费（此前只有 4 个必返字段）
    icon: str | None = None
    tone: str | None = None
    prompt: str | None = None