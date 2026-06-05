"""FlyOS FastAPI server — pandas computes, Claude explains."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse

from action_center import build_action_list, build_briefing_items, simulate_action
from cash_engine import (
    DATASET_TODAY,
    compute_cash_liberation_total,
    compute_cash_position,
    find_ad_waste,
    find_best_backtest_date,
    find_dead_inventory,
    find_late_pos,
    find_reorder_candidates,
    run_backtest,
)
from config import BACKTEST_HORIZON_DAYS, DEFAULT_DATA_DIR, TOP_LEAKS_LIMIT
from data_loader import DataLoader
from leak_mapper import build_leak_list
from llm_service import (
    explain_leak_for_api,
    generate_briefing_narrative,
    generate_email_campaign,
)
from models import (
    ActionsResponse,
    BacktestResult,
    BestBacktestDate,
    BriefItem,
    CashLeaksResponse,
    CashPosition,
    ExecutiveBriefing,
    GenerateEmailRequest,
    HealthResponse,
    LoadDataRequest,
    LoadDataResponse,
    ReorderSuggestion,
    SimulateActionRequest,
    SimulateActionResponse,
    ValidationFailure,
    utc_now_iso,
)
from segment_export import export_dead_stock_segment

load_dotenv()


def _map_validation_failures(raw: list) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    for i, item in enumerate(raw, start=1):
        if isinstance(item, dict):
            if "rule_number" in item:
                failures.append(ValidationFailure(**item))
            else:
                failures.append(
                    ValidationFailure(
                        rule_number=i,
                        description=str(item.get("rule", "reconciliation")),
                        status="FAIL",
                        message=str(item.get("message", "")),
                    )
                )
    return failures


def _brief_item(data: dict) -> BriefItem:
    return BriefItem(
        id=data["id"],
        title=data["title"],
        subtitle=data["subtitle"],
        amount_gbp=float(data["amount_gbp"]),
        category=data["category"],
        recommended_action=data["recommended_action"],
        confidence=data["confidence"],
    )


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date '{value}'. Use YYYY-MM-DD.",
        ) from exc


def _require_data(request: Request) -> None:
    if not getattr(request.app.state, "validated", False):
        raise HTTPException(
            status_code=400,
            detail="Data not loaded or validation failed. Call POST /api/load-data first.",
        )


def _resolve_data_path(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = (Path(__file__).resolve().parent / path).resolve()
    return path


def _leak_by_id(request: Request, leak_id: str, as_of: date):
    dfs = request.app.state.dfs
    suppliers = dfs.get("suppliers")
    dead = find_dead_inventory(dfs, as_of)
    late = find_late_pos(dfs["purchase_orders"], as_of, suppliers)
    ad = find_ad_waste(
        dfs["google_ads_daily"],
        dfs["meta_ads_daily"],
        dfs["orders"],
        as_of,
        window_days=14,
    )
    leaks = build_leak_list(dead, late, ad, limit=None)
    return next((l for l in leaks if l.id == leak_id), None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.dfs: dict = {}
    app.state.validated = False
    app.state.validation_output = ""
    if DEFAULT_DATA_DIR.is_dir():
        try:
            loader = DataLoader(DEFAULT_DATA_DIR)
            result = loader.load()
            app.state.dfs = result["dfs"]
            app.state.validated = bool(result["validation"].get("passed"))
            app.state.validation_output = result["validation"].get("output", "")
        except (FileNotFoundError, OSError):
            pass
    yield


app = FastAPI(title="FlyOS API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        {"error": exc.detail, "type": "HTTPException"},
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        {"error": str(exc), "type": type(exc).__name__},
        status_code=500,
    )


@app.post("/api/load-data", response_model=LoadDataResponse)
async def load_data(body: LoadDataRequest, request: Request) -> LoadDataResponse:
    data_path = _resolve_data_path(body.data_path or str(DEFAULT_DATA_DIR))
    try:
        loader = DataLoader(data_path)
        result = loader.load()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    validation = result["validation"]
    request.app.state.dfs = result["dfs"]
    request.app.state.validated = bool(validation.get("passed"))
    request.app.state.validation_output = validation.get("output", "")

    files = sorted(result["dfs"].keys())
    passed = request.app.state.validated
    failures_raw = validation.get("failures", [])
    failures = [
        ValidationFailure(
            rule_number=int(f.get("rule_number", 0)),
            description=str(f.get("description", "")),
            status=f.get("status", "FAIL"),  # type: ignore[arg-type]
            message=f.get("message"),
        )
        for f in failures_raw
        if f.get("status") == "FAIL"
    ]

    return LoadDataResponse(
        success=True,
        validation_passed=passed,
        validation_output=request.app.state.validation_output,
        validation_failures=failures,
        files_loaded=files,
        message=(
            "Data loaded and reconciliation passed."
            if passed
            else "Data loaded but reconciliation failed — fix before using other endpoints."
        ),
    )


@app.get("/api/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    dfs = getattr(request.app.state, "dfs", {})
    return HealthResponse(
        status="ok",
        validated=bool(getattr(request.app.state, "validated", False)),
        files_loaded=len(dfs),
    )


@app.get("/api/cash-position", response_model=CashPosition)
async def cash_position(
    request: Request,
    as_of_date: str = Query(default=DATASET_TODAY.isoformat()),
) -> CashPosition:
    _require_data(request)
    as_of = _parse_date(as_of_date)
    pos = compute_cash_position(request.app.state.dfs, as_of)
    return CashPosition(as_of_date=as_of.isoformat(), **pos)


@app.get("/api/cash-leaks", response_model=CashLeaksResponse)
async def cash_leaks(
    request: Request,
    as_of_date: str = Query(default=DATASET_TODAY.isoformat()),
) -> CashLeaksResponse:
    _require_data(request)
    as_of = _parse_date(as_of_date)
    dfs = request.app.state.dfs
    suppliers = dfs.get("suppliers")

    dead = find_dead_inventory(dfs, as_of)
    late = find_late_pos(dfs["purchase_orders"], as_of, suppliers)
    ad = find_ad_waste(
        dfs["google_ads_daily"],
        dfs["meta_ads_daily"],
        dfs["orders"],
        as_of,
        window_days=14,
    )
    totals = compute_cash_liberation_total(dead, late, ad)
    leaks = build_leak_list(dead, late, ad, limit=TOP_LEAKS_LIMIT)

    return CashLeaksResponse(
        total_recoverable_gbp=float(totals["total_gbp"]),
        leaks=leaks,
        validation_status="passed" if request.app.state.validated else "failed",
        computed_at=utc_now_iso(),
        breakdown={
            "inventory_gbp": totals["inventory_gbp"],
            "supplier_gbp": totals["supplier_gbp"],
            "ads_gbp": totals["ads_gbp"],
            "full_total_gbp": totals["total_gbp"],
            "item_count": float(totals["item_count"]),
        },
    )


@app.get("/api/actions", response_model=ActionsResponse)
async def get_actions(
    request: Request,
    as_of_date: str = Query(default=DATASET_TODAY.isoformat()),
    limit: int = Query(default=5, ge=1, le=50),
) -> ActionsResponse:
    _require_data(request)
    as_of = _parse_date(as_of_date)
    actions, totals = build_action_list(request.app.state.dfs, as_of, limit=limit)
    all_leaks = build_leak_list(
        find_dead_inventory(request.app.state.dfs, as_of),
        find_late_pos(
            request.app.state.dfs["purchase_orders"],
            as_of,
            request.app.state.dfs.get("suppliers"),
        ),
        find_ad_waste(
            request.app.state.dfs["google_ads_daily"],
            request.app.state.dfs["meta_ads_daily"],
            request.app.state.dfs["orders"],
            as_of,
            window_days=14,
        ),
        limit=None,
    )
    return ActionsResponse(
        total_liberation_gbp=float(totals["total_gbp"]),
        action_count=len(all_leaks),
        actions=actions,
        breakdown={
            "inventory_gbp": float(totals["inventory_gbp"]),
            "supplier_gbp": float(totals["supplier_gbp"]),
            "ads_gbp": float(totals["ads_gbp"]),
            "item_count": float(totals["item_count"]),
        },
        computed_at=utc_now_iso(),
    )


@app.get("/api/briefing", response_model=ExecutiveBriefing)
async def get_briefing(
    request: Request,
    as_of_date: str = Query(default=DATASET_TODAY.isoformat()),
) -> ExecutiveBriefing:
    _require_data(request)
    as_of = _parse_date(as_of_date)
    dfs = request.app.state.dfs
    pos = compute_cash_position(dfs, as_of)
    suppliers = dfs.get("suppliers")
    dead = find_dead_inventory(dfs, as_of)
    late = find_late_pos(dfs["purchase_orders"], as_of, suppliers)
    ad = find_ad_waste(
        dfs["google_ads_daily"],
        dfs["meta_ads_daily"],
        dfs["orders"],
        as_of,
        window_days=14,
    )
    totals = compute_cash_liberation_total(dead, late, ad)
    risks_raw, opps_raw = build_briefing_items(dfs, as_of)

    return ExecutiveBriefing(
        as_of_date=as_of.isoformat(),
        cash_position=CashPosition(as_of_date=as_of.isoformat(), **pos),
        total_liberation_gbp=float(totals["total_gbp"]),
        top_risks=[BriefItem(**r) for r in risks_raw],
        top_opportunities=[BriefItem(**o) for o in opps_raw],
        narrative=None,
    )


@app.post("/api/briefing/generate")
async def generate_briefing(request: Request) -> StreamingResponse:
    _require_data(request)
    as_of = DATASET_TODAY
    briefing = await get_briefing(request, as_of_date=as_of.isoformat())
    facts = {
        "as_of_date": briefing.as_of_date,
        "net_cash_gbp": briefing.cash_position.net_cash_gbp,
        "bank_balance_gbp": briefing.cash_position.bank_balance_gbp,
        "total_liberation_gbp": briefing.total_liberation_gbp,
        "top_risks": [r.model_dump() for r in briefing.top_risks],
        "top_opportunities": [o.model_dump() for o in briefing.top_opportunities],
    }
    stream = generate_briefing_narrative(facts)
    return StreamingResponse(stream, media_type="text/event-stream")


@app.get("/api/explain-leak")
async def explain_leak(
    request: Request,
    id: str = Query(..., description="Leak id"),
    as_of_date: str = Query(default=DATASET_TODAY.isoformat()),
) -> JSONResponse:
    _require_data(request)
    as_of = _parse_date(as_of_date)
    leak = _leak_by_id(request, id, as_of)
    if leak is None:
        raise HTTPException(status_code=404, detail=f"Leak not found: {id}")
    explanation = await explain_leak_for_api(leak.model_dump())
    return JSONResponse({"id": id, "explanation": explanation})


@app.get("/api/export-segment")
async def export_segment(
    request: Request,
    leak_id: str = Query(...),
    as_of_date: str = Query(default=DATASET_TODAY.isoformat()),
) -> PlainTextResponse:
    _require_data(request)
    as_of = _parse_date(as_of_date)
    try:
        csv_text, count = export_dead_stock_segment(
            request.app.state.dfs, leak_id, as_of
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return PlainTextResponse(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="segment-{leak_id}.csv"',
            "X-Segment-Count": str(count),
        },
    )


@app.get("/api/reorder-suggestions", response_model=list[ReorderSuggestion])
async def reorder_suggestions(
    request: Request,
    as_of_date: str = Query(default=DATASET_TODAY.isoformat()),
) -> list[ReorderSuggestion]:
    _require_data(request)
    as_of = _parse_date(as_of_date)
    df = find_reorder_candidates(request.app.state.dfs, as_of)
    if df.empty:
        return []
    return [
        ReorderSuggestion(
            variant_id=str(row["variant_id"]),
            sku=str(row["sku"]),
            product_title=str(row["product_title"]),
            supplier_name=str(row["supplier_name"]),
            suggested_qty=int(row["suggested_qty"]),
            unit_cost_gbp=float(row["unit_cost_gbp"]),
            po_value_gbp=float(row["po_value_gbp"]),
            days_of_stock=float(row["days_of_stock"]),
            units_sold_30d=float(row["units_sold_30d"]),
        )
        for _, row in df.iterrows()
    ]


@app.post("/api/simulate-action", response_model=SimulateActionResponse)
async def simulate_action_endpoint(
    body: SimulateActionRequest,
    request: Request,
    as_of_date: str = Query(default=DATASET_TODAY.isoformat()),
) -> SimulateActionResponse:
    _require_data(request)
    as_of = _parse_date(as_of_date)
    result = simulate_action(body.leak_id, request.app.state.dfs, as_of)
    return SimulateActionResponse(**result)


@app.get("/api/backtest/best-date", response_model=BestBacktestDate)
async def best_backtest_date(request: Request) -> BestBacktestDate:
    _require_data(request)
    result = find_best_backtest_date(
        request.app.state.dfs,
        horizon_days=BACKTEST_HORIZON_DAYS,
    )
    return BestBacktestDate(**result)


@app.get("/api/backtest", response_model=BacktestResult)
async def backtest(
    request: Request,
    date: str = Query(..., description="Historical as-of date YYYY-MM-DD"),
) -> BacktestResult:
    _require_data(request)
    as_of = _parse_date(date)
    result = run_backtest(
        request.app.state.dfs,
        as_of,
        horizon_days=BACKTEST_HORIZON_DAYS,
    )
    recommendations = build_leak_list(
        result["dead_inv"],
        result["late_pos"],
        result["ad_waste"],
        limit=TOP_LEAKS_LIMIT,
    )
    return BacktestResult(
        as_of_date=as_of.isoformat(),
        recommendations=recommendations,
        actual_outcome_summary=result["actual_outcome_summary"],
        estimated_cash_recovered_gbp=result["estimated_cash_recovered_gbp"],
        inventory_recovered_gbp=result.get("inventory_recovered_gbp", 0.0),
        po_recovered_gbp=result.get("po_recovered_gbp", 0.0),
        ad_saved_gbp=result.get("ad_saved_gbp", 0.0),
    )


@app.post("/api/generate-email")
async def generate_email(body: GenerateEmailRequest) -> StreamingResponse:
    stream = generate_email_campaign(
        variant_title=body.variant_title,
        units=body.units,
        cash_tied=body.cash_tied,
        sku=body.sku,
    )
    return StreamingResponse(stream, media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    port = int(__import__("os").getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
