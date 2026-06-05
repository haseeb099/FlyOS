import type {
  ActionsResponse,
  BacktestResult,
  BestBacktestDate,
  CashLeaksResponse,
  CashPosition,
  EmailParams,
  ExecutiveBriefing,
  HealthResponse,
  LoadDataResponse,
  SimulateActionResponse,
} from "./types";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function parseError(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as {
      detail?: string | { msg: string }[];
      error?: string;
    };
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail.map((d) => d.msg).join("; ");
    }
    return body.error ?? res.statusText;
  } catch {
    return res.statusText;
  }
}

export async function loadData(dataPath: string): Promise<LoadDataResponse> {
  const res = await fetch(`${API}/api/load-data`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ data_path: dataPath }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API}/api/health`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function getCashPosition(asOfDate?: string): Promise<CashPosition> {
  const url = asOfDate
    ? `${API}/api/cash-position?as_of_date=${asOfDate}`
    : `${API}/api/cash-position`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function getCashLeaks(asOfDate?: string): Promise<CashLeaksResponse> {
  const url = asOfDate
    ? `${API}/api/cash-leaks?as_of_date=${asOfDate}`
    : `${API}/api/cash-leaks`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function getActions(limit = 5): Promise<ActionsResponse> {
  const res = await fetch(`${API}/api/actions?limit=${limit}`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function getBriefing(): Promise<ExecutiveBriefing> {
  const res = await fetch(`${API}/api/briefing`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export function generateBriefing(): Promise<Response> {
  return fetch(`${API}/api/briefing/generate`, { method: "POST" });
}

export async function explainLeak(id: string): Promise<string> {
  const res = await fetch(`${API}/api/explain-leak?id=${encodeURIComponent(id)}`);
  if (!res.ok) throw new Error(await parseError(res));
  const body = (await res.json()) as { explanation: string };
  return body.explanation;
}

export async function exportSegment(leakId: string): Promise<{ csv: string; count: number }> {
  const res = await fetch(`${API}/api/export-segment?leak_id=${encodeURIComponent(leakId)}`);
  if (!res.ok) throw new Error(await parseError(res));
  const csv = await res.text();
  const count = parseInt(res.headers.get("X-Segment-Count") ?? "0", 10);
  return { csv, count };
}

export async function simulateAction(leakId: string): Promise<SimulateActionResponse> {
  const res = await fetch(`${API}/api/simulate-action`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ leak_id: leakId }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function runBacktest(date: string): Promise<BacktestResult> {
  const res = await fetch(`${API}/api/backtest?date=${date}`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function getBestBacktestDate(): Promise<BestBacktestDate> {
  const res = await fetch(`${API}/api/backtest/best-date`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export function generateEmail(params: EmailParams): Promise<Response> {
  return fetch(`${API}/api/generate-email`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
}
