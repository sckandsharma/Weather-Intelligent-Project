from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import require_evaluator
from app.database.models import EvaluationResult, User
from app.database.session import get_db
from app.evaluation.evaluator import run_evaluation_benchmark
from app.services.logging_service import log_audit_event

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


class EvaluationResultItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: str | None
    test_case_id: str
    routing_score: float
    retrieval_score: float | None
    answer_score: float
    latency_ms: float
    created_at: datetime


class PaginatedEvaluationResults(BaseModel):
    items: list[EvaluationResultItem]
    total: int
    limit: int
    offset: int
    run_id_filter: str | None = None


@router.post("/run", status_code=status.HTTP_200_OK)
async def trigger_evaluation_run(
    db: Session = Depends(get_db),
    evaluator_user: User = Depends(require_evaluator),
) -> dict[str, Any]:
    benchmark_output = await run_evaluation_benchmark(db=db)
    summary = benchmark_output["summary"]

    log_audit_event(
        db=db,
        action="evaluation_run",
        resource=f"run:{summary['run_id']}",
        user_id=evaluator_user.id,
    )

    return benchmark_output


@router.get("/results", response_model=PaginatedEvaluationResults, status_code=status.HTTP_200_OK)
def get_evaluation_results(
    run_id: str | None = Query(default=None, description="Filter by evaluation run ID"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    evaluator_user: User = Depends(require_evaluator),
    db: Session = Depends(get_db),
) -> PaginatedEvaluationResults:
    query = select(EvaluationResult)
    count_query = select(func.count(EvaluationResult.id))

    if run_id:
        query = query.where(EvaluationResult.run_id == run_id)
        count_query = count_query.where(EvaluationResult.run_id == run_id)

    total_count = db.scalar(count_query) or 0

    query = query.order_by(EvaluationResult.created_at.desc(), EvaluationResult.id.desc()).limit(limit).offset(offset)
    results = db.execute(query).scalars().all()

    items = [
        EvaluationResultItem(
            id=r.id,
            run_id=r.run_id,
            test_case_id=r.test_case_id,
            routing_score=r.routing_score,
            retrieval_score=r.retrieval_score,
            answer_score=r.answer_score,
            latency_ms=r.latency_ms,
            created_at=r.created_at,
        )
        for r in results
    ]

    return PaginatedEvaluationResults(
        items=items,
        total=total_count,
        limit=limit,
        offset=offset,
        run_id_filter=run_id,
    )
