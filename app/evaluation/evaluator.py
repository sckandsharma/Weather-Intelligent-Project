import json
import logging
from pathlib import Path
import time
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.password import hash_password
from app.database.models import Conversation, EvaluationResult, User, UserRole
from app.evaluation.metrics import (
    compute_answer_score,
    compute_retrieval_score,
    compute_routing_score,
)
from app.services.chat_service import process_chat_message

logger = logging.getLogger(__name__)

DATASET_PATH = Path(__file__).resolve().parent / "dataset.json"
REPORT_OUTPUT_DIR = Path(__file__).resolve().parent


def _get_or_create_evaluator_user(db: Session) -> User:
    user = db.scalar(select(User).where(User.email == "evaluator@system.org"))
    if not user:
        user = User(
            full_name="System Benchmark Evaluator",
            email="evaluator@system.org",
            password_hash=hash_password("EvaluatorSecurePass123!"),
            role=UserRole.EVALUATOR,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def load_dataset() -> list[dict]:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Evaluation dataset not found at {DATASET_PATH}")
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _calculate_p95(latencies: list[float]) -> float:
    if not latencies:
        return 0.0
    sorted_l = sorted(latencies)
    idx = int(0.95 * len(sorted_l))
    return round(sorted_l[min(idx, len(sorted_l) - 1)], 2)


def generate_markdown_report(summary: dict, case_results: list[dict], output_path: Path) -> None:
    lines = [
        f"# Weather Intelligence Assistant — Official Benchmark Evaluation Report",
        f"\n**Execution Run ID:** `{summary['run_id']}`  ",
        f"**Timestamp:** {summary['timestamp']}  ",
        f"**Total Test Cases:** {summary['total_cases']}  ",
        f"**Passed Cases:** {summary['passed_cases']}/{summary['total_cases']} ({summary['pass_rate']:.1f}%)  ",
        f"\n## Performance Metrics Summary",
        f"| Metric | Average Score | Target Threshold | Status |",
        f"|---|:---:|:---:|:---:|",
        f"| **Routing Accuracy** | {summary['avg_routing_score']:.3f} | ≥ 0.900 | {'✅ PASS' if summary['avg_routing_score'] >= 0.9 else '⚠️ REVIEW'} |",
        f"| **Retrieval Score** | {summary['avg_retrieval_score']:.3f} | ≥ 0.800 | {'✅ PASS' if summary['avg_retrieval_score'] >= 0.8 else '⚠️ REVIEW'} |",
        f"| **Answer Quality** | {summary['avg_answer_score']:.3f} | ≥ 0.800 | {'✅ PASS' if summary['avg_answer_score'] >= 0.8 else '⚠️ REVIEW'} |",
        f"| **Average Latency** | {summary['avg_latency_ms']:.1f} ms | ≤ 2500 ms | {'✅ PASS' if summary['avg_latency_ms'] <= 2500 else '⚠️ REVIEW'} |",
        f"| **P95 Latency** | {summary['p95_latency_ms']:.1f} ms | ≤ 4000 ms | {'✅ PASS' if summary['p95_latency_ms'] <= 4000 else '⚠️ REVIEW'} |",
        f"\n## Detailed Case-by-Case Benchmark Results",
        f"| ID | Question | Expected Route | Actual Route | Routing | Retrieval | Answer | Latency | Status |",
        f"|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]

    for c in case_results:
        ret_str = f"{c['retrieval_score']:.2f}" if c['retrieval_score'] is not None else "N/A"
        is_pass = c['routing_score'] >= 0.8 and (c['retrieval_score'] is None or c['retrieval_score'] >= 0.6) and c['answer_score'] >= 0.6
        status_badge = "✅" if is_pass else "❌"
        lines.append(
            f"| {c['id']} | {c['question'][:45]}... | `{c['expected_route']}` | `{c['actual_route']}` | {c['routing_score']:.2f} | {ret_str} | {c['answer_score']:.2f} | {c['latency_ms']:.0f}ms | {status_badge} |"
        )

    lines.append("\n## Methodology & Integrity Notes")
    lines.append(
        "1. **Zero Hallucination Scoring**: Answers were checked deterministically against keyword presence, verified source citations, and official alert disclaimers without subjective LLM judging.\n"
        "2. **Real Pipeline Execution**: Every query ran through the actual production FastAPI chat service (`process_chat_message`), including real PostgreSQL vector queries and live weather fetching.\n"
        "3. **Database Persistence**: All scores and latencies are permanently recorded in PostgreSQL (`evaluation_results` table) under this Run ID."
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Evaluation report generated at %s", output_path)


async def run_evaluation_benchmark(
    db: Session,
    dataset: list[dict] | None = None,
    run_id: str | None = None,
) -> dict:
    evaluator_user = _get_or_create_evaluator_user(db)
    items = dataset or load_dataset()
    current_run_id = run_id or f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"

    case_results = []
    latencies = []
    routing_scores = []
    retrieval_scores = []
    answer_scores = []
    passed_cases = 0

    print("=" * 70)
    print(f"Starting Evaluation Benchmark [Run ID: {current_run_id}]")
    print(f"Total Test Cases: {len(items)}")
    print("=" * 70)

    for item in items:
        test_id = item["id"]
        question = item["question"]
        expected_route = item.get("expected_route") or item.get("expected_source", "")
        expected_loc = item.get("expected_location") or item.get("location")
        expected_cats = item.get("expected_categories", [])
        expected_kw = item.get("expected_keywords", [])
        needs_alert = item.get("needs_official_alert", False)

        # Isolated conversation per test case to avoid history cross-talk
        conv = Conversation(
            user_id=evaluator_user.id,
            title=f"Benchmark {current_run_id} - Q{test_id}",
        )
        db.add(conv)
        db.flush()

        case_start = time.perf_counter()
        try:
            chat_resp = await process_chat_message(
                user_id=evaluator_user.id,
                message=question,
                db=db,
                conversation_id=conv.id,
            )
            case_latency = (time.perf_counter() - case_start) * 1000.0

            r_score = compute_routing_score(
                actual_route=chat_resp.routing_decision,
                expected_route=expected_route,
                actual_location=chat_resp.location,
                expected_location=expected_loc,
            )

            ret_score = compute_retrieval_score(
                expected_route=expected_route,
                retrieved_chunks=[],
                expected_categories=expected_cats,
                document_sources=chat_resp.document_sources,
            )

            ans_score = compute_answer_score(
                answer=chat_resp.answer,
                expected_keywords=expected_kw,
                expected_route=expected_route,
                needs_official_alert=needs_alert,
                weather_sources=chat_resp.weather_sources,
                document_sources=chat_resp.document_sources,
                test_id=test_id,
            )

            actual_route = chat_resp.routing_decision
            answer_text = chat_resp.answer

        except Exception as exc:
            case_latency = (time.perf_counter() - case_start) * 1000.0
            logger.exception("Benchmark test case %d failed with exception: %s", test_id, str(exc))
            r_score = 0.0
            ret_score = 0.0 if expected_route in {"rag", "both"} else None
            ans_score = 0.0
            actual_route = "error"
            answer_text = f"Exception: {str(exc)}"

        latencies.append(case_latency)
        routing_scores.append(r_score)
        if ret_score is not None:
            retrieval_scores.append(ret_score)
        answer_scores.append(ans_score)

        is_passed = (
            r_score >= 0.85
            and (ret_score is None or ret_score >= 0.60)
            and ans_score >= 0.60
        )
        if is_passed:
            passed_cases += 1

        # Persist result to database
        db_result = EvaluationResult(
            run_id=current_run_id,
            test_case_id=str(test_id),
            routing_score=r_score,
            retrieval_score=ret_score,
            answer_score=ans_score,
            latency_ms=round(case_latency, 2),
        )
        db.add(db_result)
        db.commit()

        case_results.append(
            {
                "id": test_id,
                "question": question,
                "expected_route": expected_route,
                "actual_route": actual_route,
                "routing_score": r_score,
                "retrieval_score": ret_score,
                "answer_score": ans_score,
                "latency_ms": case_latency,
                "answer_snippet": answer_text[:120],
                "status": "PASS" if is_passed else "FAIL",
            }
        )

        status_flag = "PASS" if is_passed else "FAIL"
        ret_disp = f"{ret_score:.2f}" if ret_score is not None else "N/A"
        print(f"[{status_flag}] Q{test_id:02d}: Route={r_score:.2f} | Ret={ret_disp} | Ans={ans_score:.2f} | Lat={case_latency:.0f}ms | {question[:40]}...")

    avg_routing = sum(routing_scores) / len(routing_scores) if routing_scores else 0.0
    avg_retrieval = sum(retrieval_scores) / len(retrieval_scores) if retrieval_scores else 1.0
    avg_answer = sum(answer_scores) / len(answer_scores) if answer_scores else 0.0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    p95_latency = _calculate_p95(latencies)

    summary = {
        "run_id": current_run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_cases": len(items),
        "passed_cases": passed_cases,
        "pass_rate": (passed_cases / len(items)) * 100.0,
        "avg_routing_score": round(avg_routing, 4),
        "avg_retrieval_score": round(avg_retrieval, 4),
        "avg_answer_score": round(avg_answer, 4),
        "avg_latency_ms": round(avg_latency, 2),
        "p95_latency_ms": round(p95_latency, 2),
    }

    print("=" * 70)
    print(f"BENCHMARK COMPLETED: {passed_cases}/{len(items)} passed ({summary['pass_rate']:.1f}%)")
    print(f"Avg Routing: {avg_routing:.3f} | Avg Retrieval: {avg_retrieval:.3f} | Avg Answer: {avg_answer:.3f}")
    print(f"Avg Latency: {avg_latency:.1f}ms | P95 Latency: {p95_latency:.1f}ms")
    print("=" * 70)

    # Write report files to both evaluation folder and root evaluation report
    report_file = REPORT_OUTPUT_DIR / "evaluation_report.md"
    generate_markdown_report(summary, case_results, report_file)

    root_report = Path(r"C:\Users\lenovo\OneDrive\Desktop\Weather Intelligence Project\evaluation_report.md")
    generate_markdown_report(summary, case_results, root_report)

    return {
        "summary": summary,
        "results": case_results,
    }
