from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class User:
    id: str
    display_name: str
    email: str
    role: str  # e.g., "user", "admin", "viewer"


@dataclass
class Record:
    """
    A high-level entity like an AI Use Case.
    'content' details live in the latest RecordVersion.
    """
    id: str
    title: str
    record_type: str       # e.g., "ai_use_case"
    current_version_id: Optional[str]
    created_by: str        # user.id
    created_at: datetime
    status: str            # e.g., "draft", "submitted"


@dataclass
class RecordVersion:
    """
    A specific snapshot of a Record at a point in time.
    Stores the full content as a JSON-like dict.
    """
    id: str
    record_id: str
    version_number: int
    content: Dict[str, Any]         # later this holds problem, metadata, etc.
    created_by: str
    created_by_name: str
    created_at: datetime
    version_type: str               # e.g., "draft", "submit", "override"
    parent_version_id: Optional[str] = None


@dataclass
class OverrideEvent:
    id: str
    record_id: str
    version_id: str
    field_path: str          # e.g., "ai_metadata.framework_tags"
    original_value: Any
    new_value: Any
    overridden_by: str       # user id
    overridden_by_name: str
    overridden_at: datetime

@dataclass
class Comment:
    id: str
    record_id: str
    version_id: Optional[str]  # can be None or point to a specific version
    author_id: str
    author_name: str
    role: str                   # e.g., "user", "admin"
    text: str
    created_at: datetime