import logging
from typing import Any, Optional

from psycopg2.extras import Json

logger = logging.getLogger(__name__)


def write_audit_log(
    cursor,
    *,
    actor_id: Optional[str],
    action: str,
    entity_type: str,
    entity_id: str,
    before: Optional[dict[str, Any]] = None,
    after: Optional[dict[str, Any]] = None,
    metadata: Optional[dict[str, Any]] = None,
):
    try:
        cursor.execute(
            """
            INSERT INTO audit_logs (actor_id, action, entity_type, entity_id, before, after, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                actor_id,
                action,
                entity_type,
                entity_id,
                Json(before or {}),
                Json(after or {}),
                Json(metadata or {}),
            ),
        )
    except Exception as exc:
        logger.warning("Failed to write audit log", extra={"error": str(exc)})
