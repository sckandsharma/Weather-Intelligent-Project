from typing import Any
from sqlalchemy.orm import Session

from app.database.models import AuditLog, WeatherAPILog


def log_weather_api_call(
    db: Session,
    city: str,
    request_params: dict[str, Any],
    response_json: dict[str, Any] | None,
    status_code: int | None,
    latency_ms: float,
) -> WeatherAPILog | None:
    try:
        log_entry = WeatherAPILog(
            city=city,
            request_params=request_params,
            response_json=response_json,
            status_code=status_code,
            latency_ms=round(latency_ms, 2),
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry
    except Exception:
        db.rollback()
        return None


def log_audit_event(
    db: Session,
    action: str,
    resource: str,
    user_id: int | None = None,
) -> AuditLog | None:
    try:
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry
    except Exception:
        db.rollback()
        return None