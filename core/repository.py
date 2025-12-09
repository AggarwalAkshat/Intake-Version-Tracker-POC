import os
import sqlite3
import json
from datetime import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo

from .models import Record, RecordVersion, User, Comment, OverrideEvent
from . import roles

TORONTO_TZ = ZoneInfo("America/Toronto")


def now_toronto_iso() -> str:
    """
    Return current date/time in Toronto as ISO string with timezone info.
    """
    return datetime.now(TORONTO_TZ).isoformat()


# Path to the SQLite DB file (inside the 'data' folder)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "change_tracker.db")


def get_connection():
    """
    Get a connection to the SQLite database.
    'check_same_thread=False' allows Streamlit to reuse the connection.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Create tables if they don't already exist.
    Safe to call on every app run.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()

    # Records table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            record_type TEXT NOT NULL,
            current_version_id TEXT,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL
        )
        """
    )

    # Record versions table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS record_versions (
            id TEXT PRIMARY KEY,
            record_id TEXT NOT NULL,
            version_number INTEGER NOT NULL,
            content TEXT NOT NULL,  -- JSON as string
            created_by TEXT NOT NULL,
            created_by_name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            version_type TEXT NOT NULL,
            parent_version_id TEXT
        )
        """
    )

    # Comments table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS comments (
            id TEXT PRIMARY KEY,
            record_id TEXT NOT NULL,
            version_id TEXT,
            author_id TEXT NOT NULL,
            author_name TEXT NOT NULL,
            role TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    # Override events table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS override_events (
            id TEXT PRIMARY KEY,
            record_id TEXT NOT NULL,
            version_id TEXT NOT NULL,
            field_path TEXT NOT NULL,
            original_value TEXT,
            new_value TEXT,
            overridden_by TEXT NOT NULL,
            overridden_by_name TEXT NOT NULL,
            overridden_at TEXT NOT NULL
        )
        """
    )


    conn.commit()
    conn.close()


def _row_to_record(row: sqlite3.Row) -> Record:
    return Record(
        id=row["id"],
        title=row["title"],
        record_type=row["record_type"],
        current_version_id=row["current_version_id"],
        created_by=row["created_by"],
        created_at=datetime.fromisoformat(row["created_at"]),
        status=row["status"],
    )


def _row_to_record_version(row: sqlite3.Row) -> RecordVersion:
    return RecordVersion(
        id=row["id"],
        record_id=row["record_id"],
        version_number=row["version_number"],
        content=json.loads(row["content"]),
        created_by=row["created_by"],
        created_by_name=row["created_by_name"],
        created_at=datetime.fromisoformat(row["created_at"]),
        version_type=row["version_type"],
        parent_version_id=row["parent_version_id"],
    )

def _row_to_comment(row: sqlite3.Row) -> Comment:
    return Comment(
        id=row["id"],
        record_id=row["record_id"],
        version_id=row["version_id"],
        author_id=row["author_id"],
        author_name=row["author_name"],
        role=row["role"],
        text=row["text"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )

def _row_to_override_event(row: sqlite3.Row) -> OverrideEvent:
    return OverrideEvent(
        id=row["id"],
        record_id=row["record_id"],
        version_id=row["version_id"],
        field_path=row["field_path"],
        original_value=json.loads(row["original_value"]) if row["original_value"] else None,
        new_value=json.loads(row["new_value"]) if row["new_value"] else None,
        overridden_by=row["overridden_by"],
        overridden_by_name=row["overridden_by_name"],
        overridden_at=datetime.fromisoformat(row["overridden_at"]),
    )


def create_record_with_initial_version(
    title: str,
    record_type: str,
    content: dict,
    user: User,
    status: str = "draft",
) -> Record:
    """
    Create a new record with an initial version (version_number = 1).
    """
    import uuid

    conn = get_connection()
    cur = conn.cursor()

    now = now_toronto_iso()
    record_id = str(uuid.uuid4())
    version_id = str(uuid.uuid4())

    # Insert record
    cur.execute(
        """
        INSERT INTO records (id, title, record_type, current_version_id, created_by, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (record_id, title, record_type, version_id, user.id, now, status),
    )

    # Insert initial version
    cur.execute(
        """
        INSERT INTO record_versions (
            id, record_id, version_number, content,
            created_by, created_by_name, created_at,
            version_type, parent_version_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            version_id,
            record_id,
            1,
            json.dumps(content),
            user.id,
            user.display_name,
            now,
            "draft",
            None,
        ),
    )

    conn.commit()
    conn.close()

    return Record(
        id=record_id,
        title=title,
        record_type=record_type,
        current_version_id=version_id,
        created_by=user.id,
        created_at=datetime.fromisoformat(now),
        status=status,
    )


def list_records_for_user(user: User) -> List[Record]:
    """
    List records visible to the given user.

    For now:
    - Admins see all records.
    - Normal users see only records they created.
    - Viewers see all submitted records (status != 'draft').
    """
    conn = get_connection()
    cur = conn.cursor()

    if roles.is_admin(user):
        cur.execute("SELECT * FROM records ORDER BY created_at DESC")
    elif roles.is_user(user):
        cur.execute(
            "SELECT * FROM records WHERE created_by = ? ORDER BY created_at DESC",
            (user.id,),
        )
    else:
        # viewer: can see only non-draft records
        cur.execute(
            "SELECT * FROM records WHERE status != 'draft' ORDER BY created_at DESC"
        )

    rows = cur.fetchall()
    conn.close()

    return [_row_to_record(r) for r in rows]


def count_records() -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM records")
    row = cur.fetchone()
    conn.close()
    return row["c"] if row else 0


def ensure_demo_data(user_for_demo: User):
    """
    Seed some demo records if the DB is empty.
    This makes the UI feel alive immediately.
    """
    if count_records() > 0:
        return  # already seeded

    # Simple example content; later this will include real fields + ai_metadata
    demo_content_1 = {
        "business_problem": "Detect suspicious benefit claims using AI.",
        "description": "Use classification models to flag high-risk claims for review.",
        "ai_metadata": {
            "framework_tags": ["Risk & Governance"],
            "capability_groups": ["Fraud Detection"],
        },
    }

    demo_content_2 = {
        "business_problem": "Automate document summarization for policy briefs.",
        "description": "Use NLP to create short summaries for long policy documents.",
        "ai_metadata": {
            "framework_tags": ["Knowledge Management"],
            "capability_groups": ["NLP"],
        },
    }

    # Create two demo records:
    create_record_with_initial_version(
        title="Fraud Detection in Benefit Claims",
        record_type="ai_use_case",
        content=demo_content_1,
        user=user_for_demo,
        status="draft",
    )

    admin_like = User(
        id="admin-seed",
        display_name="Seeded Admin Record Owner",
        email="seeded-admin@example.com",
        role="admin",
    )

    create_record_with_initial_version(
        title="Policy Document Summarization",
        record_type="ai_use_case",
        content=demo_content_2,
        user=admin_like,
        status="submitted",
    )


def get_record_by_id(record_id: str) -> Optional[Record]:
    """
    Fetch a single Record by ID.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM records WHERE id = ?", (record_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return _row_to_record(row)


def get_current_version(record_id: str) -> Optional[RecordVersion]:
    """
    Fetch the current RecordVersion for a given record_id,
    based on records.current_version_id.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Get the current_version_id from the records table
    cur.execute(
        "SELECT current_version_id FROM records WHERE id = ?",
        (record_id,),
    )
    row = cur.fetchone()
    if not row or row["current_version_id"] is None:
        conn.close()
        return None

    version_id = row["current_version_id"]

    # Fetch that version
    cur.execute("SELECT * FROM record_versions WHERE id = ?", (version_id,))
    vrow = cur.fetchone()
    conn.close()

    if not vrow:
        return None

    return _row_to_record_version(vrow)


def list_versions_for_record(record_id: str) -> List[RecordVersion]:
    """
    List all versions for a given record, newest last (by version_number).
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM record_versions WHERE record_id = ? ORDER BY version_number ASC",
        (record_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [_row_to_record_version(r) for r in rows]


def create_new_version(
    record_id: str,
    new_title: str,
    content: dict,
    user: User,
    version_type: str = "edit",
    new_status: Optional[str] = None,
) -> RecordVersion:
    """
    Create a new RecordVersion for an existing record and update the record's
    current_version_id, title, and status.

    - record_id: which record we're updating
    - new_title: updated title for the record
    - content: full content snapshot for this version
    - user: the user performing the edit
    - version_type: e.g. 'edit', 'submit', 'override'
    - new_status: if None, keep the existing status
    """
    import uuid

    conn = get_connection()
    cur = conn.cursor()

    # Get current record info
    cur.execute(
        "SELECT current_version_id, status FROM records WHERE id = ?",
        (record_id,),
    )
    rec_row = cur.fetchone()
    if not rec_row:
        conn.close()
        raise ValueError(f"Record with id {record_id} not found")

    parent_version_id = rec_row["current_version_id"]
    existing_status = rec_row["status"]

    # Determine next version number
    cur.execute(
        "SELECT COALESCE(MAX(version_number), 0) AS max_v FROM record_versions WHERE record_id = ?",
        (record_id,),
    )
    row = cur.fetchone()
    next_version_number = (row["max_v"] or 0) + 1

    now = now_toronto_iso()
    version_id = str(uuid.uuid4())

    # Insert new version
    cur.execute(
        """
        INSERT INTO record_versions (
            id, record_id, version_number, content,
            created_by, created_by_name, created_at,
            version_type, parent_version_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            version_id,
            record_id,
            next_version_number,
            json.dumps(content),
            user.id,
            user.display_name,
            now,
            version_type,
            parent_version_id,
        ),
    )

    # Update the record with new current_version_id, status, and title
    final_status = new_status if new_status is not None else existing_status
    cur.execute(
        """
        UPDATE records
        SET current_version_id = ?, status = ?, title = ?
        WHERE id = ?
        """,
        (version_id, final_status, new_title, record_id),
    )

    conn.commit()
    conn.close()

    return RecordVersion(
        id=version_id,
        record_id=record_id,
        version_number=next_version_number,
        content=content,
        created_by=user.id,
        created_by_name=user.display_name,
        created_at=datetime.fromisoformat(now),
        version_type=version_type,
        parent_version_id=parent_version_id,
    )

def add_comment(
    record_id: str,
    version_id: Optional[str],
    text: str,
    user: User,
) -> Comment:
    """
    Add a new comment to a record (optionally tied to a specific version).
    """
    import uuid

    conn = get_connection()
    cur = conn.cursor()

    now = datetime.utcnow().isoformat()
    comment_id = str(uuid.uuid4())

    cur.execute(
        """
        INSERT INTO comments (
            id, record_id, version_id,
            author_id, author_name, role, text, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            comment_id,
            record_id,
            version_id,
            user.id,
            user.display_name,
            user.role,
            text,
            now,
        ),
    )

    conn.commit()
    conn.close()

    return Comment(
        id=comment_id,
        record_id=record_id,
        version_id=version_id,
        author_id=user.id,
        author_name=user.display_name,
        role=user.role,
        text=text,
        created_at=datetime.fromisoformat(now),
    )


def list_comments_for_record(record_id: str) -> List[Comment]:
    """
    List all comments for a record, oldest first.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM comments
        WHERE record_id = ?
        ORDER BY created_at ASC
        """,
        (record_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [_row_to_comment(r) for r in rows]


def update_comment(comment_id: str, new_text: str) -> None:
    """
    Update the text (and timestamp) of an existing comment.
    """
    conn = get_connection()
    cur = conn.cursor()
    now = now_toronto_iso()

    cur.execute(
        """
        UPDATE comments
        SET text = ?, created_at = ?
        WHERE id = ?
        """,
        (new_text, now, comment_id),
    )

    conn.commit()
    conn.close()


def delete_comment(comment_id: str) -> None:
    """
    Permanently delete a comment.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM comments WHERE id = ?", (comment_id,))

    conn.commit()
    conn.close()


def log_override_events(
    record_id: str,
    version_id: str,
    overrides: list,
    user: User,
) -> None:
    """
    Store one or more override events for a given record & version.

    overrides is a list of (field_path, original_value, new_value).
    """
    import uuid

    if not overrides:
        return

    conn = get_connection()
    cur = conn.cursor()
    now = now_toronto_iso()

    for field_path, original_value, new_value in overrides:
        event_id = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO override_events (
                id, record_id, version_id,
                field_path, original_value, new_value,
                overridden_by, overridden_by_name, overridden_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                record_id,
                version_id,
                field_path,
                json.dumps(original_value),
                json.dumps(new_value),
                user.id,
                user.display_name,
                now,
            ),
        )

    conn.commit()
    conn.close()


def list_overrides_for_record(record_id: str) -> List[OverrideEvent]:
    """
    List all override events for a record, oldest first.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM override_events
        WHERE record_id = ?
        ORDER BY overridden_at ASC
        """,
        (record_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [_row_to_override_event(r) for r in rows]
