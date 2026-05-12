from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Store(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    line_user_id: str
    gbp_location_id: str = ""
    gbp_access_token: str = ""
    gbp_refresh_token: str = ""
    store_name: str = "サンプル店舗"
    store_category: str = "飲食店"
    notification_enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Conversation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    store_id: str
    channel: str = "line"  # 'line' | 'slack' | 'web'
    role: str  # 'user' | 'assistant'
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Review(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    store_id: str
    gbp_review_id: str
    reviewer_name: str
    star_rating: int
    comment: str
    reply_text: str = ""
    reply_status: str = "pending"  # 'pending' | 'replied' | 'flagged'
    created_at: datetime = Field(default_factory=datetime.utcnow)
    replied_at: datetime | None = None


class MonitoringJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    store_id: str
    job_type: str  # 'review_check' | 'post_reminder' | 'photo_audit'
    result: dict[str, Any] = Field(default_factory=dict)
    notified_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# LINE Webhookリクエスト用
class LineWebhookEvent(BaseModel):
    type: str
    replyToken: str = ""
    source: dict[str, Any] = Field(default_factory=dict)
    message: dict[str, Any] = Field(default_factory=dict)
    timestamp: int = 0


class LineWebhookBody(BaseModel):
    destination: str = ""
    events: list[LineWebhookEvent] = Field(default_factory=list)


# モックチャット用
class MockChatRequest(BaseModel):
    user_id: str = "mock_user_001"
    message: str


class MockChatResponse(BaseModel):
    user_id: str
    reply: str
    tool_calls: list[str] = Field(default_factory=list)
