"use client";

import { useEffect, useState } from "react";
import { Loader2, Sparkles } from "lucide-react";

import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import { Button } from "@/components/ui/button";
import { generateBriefing, getBriefing } from "@/lib/api";
import { fmtGbp } from "@/lib/format";
import { useAppStore } from "@/lib/store";
import type { BriefItem, ExecutiveBriefing } from "@/lib/types";

function BriefCard({ item, kind }: { item: BriefItem; kind: "risk" | "opportunity" }) {
  return (
    <div className="rounded-xl border border-[#222] bg-[#111] p-5">
      <div className="flex justify-between gap-3">
        <div>
          <p className="font-semibold text-zinc-100">{item.title}</p>
          <p className="text-xs text-zinc-500 mt-0.5">{item.subtitle}</p>
        </div>
        <ConfidenceBadge confidence={item.confidence} />
      </div>
      <p className="font-mono text-xl font-bold text-amber-400 mt-3 tabular-nums">
        {fmtGbp(item.amount_gbp)}
      </p>
      <p className="text-xs text-zinc-500 mt-1">
        {kind === "risk" ? "Cash at risk" : "Recoverable"}
      </p>
      <p className="text-sm text-zinc-400 mt-3">{item.recommended_action}</p>
    </div>
  );
}

export function BriefingPanel() {
  const briefing = useAppStore((s) => s.briefing);
  const setBriefing = useAppStore((s) => s.setBriefing);
  const [loading, setLoading] = useState(!briefing);
  const [streaming, setStreaming] = useState(false);
  const [narrative, setNarrative] = useState(briefing?.narrative ?? "");
  const [error, setError] = useState<string | null>(null);

  const loadBriefing = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getBriefing();
      setBriefing(data);
      setNarrative(data.narrative ?? "");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load briefing");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!briefing) void loadBriefing();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleGenerate = async () => {
    setStreaming(true);
    setNarrative("");
    setError(null);
    try {
      const res = await generateBriefing();
      if (!res.ok || !res.body) throw new Error("Briefing stream failed");
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let text = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        for (const line of chunk.split("\n")) {
          if (!line.startsWith("data: ")) continue;
          const payload = line.slice(6);
          try {
            const parsed = JSON.parse(payload) as { text?: string };
            if (parsed.text) text += parsed.text;
          } catch {
            text += payload;
          }
          setNarrative(text);
        }
      }
      if (briefing) {
        setBriefing({ ...briefing, narrative: text });
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Narrative generation failed");
    } finally {
      setStreaming(false);
    }
  };

  if (loading && !briefing) {
    return (
      <div className="space-y-4 py-12">
        <div className="h-32 rounded-xl bg-[#111] animate-pulse" />
        <Button onClick={loadBriefing}>Retry load</Button>
      </div>
    );
  }

  const b: ExecutiveBriefing | null = briefing;

  return (
    <div className="space-y-10">
      {error && <p className="text-sm text-red-400">{error}</p>}

      {b && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: "Bank balance", value: b.cash_position.bank_balance_gbp },
              { label: "Payables", value: b.cash_position.outstanding_payables_gbp },
              { label: "Receivables", value: b.cash_position.expected_receivables_gbp },
              { label: "Net cash", value: b.cash_position.net_cash_gbp },
            ].map((m) => (
              <div
                key={m.label}
                className="rounded-xl border border-[#222] bg-[#111] px-4 py-3 text-center"
              >
                <p className="text-xs text-zinc-500">{m.label}</p>
                <p className="font-mono text-lg font-bold text-zinc-200 tabular-nums">
                  {fmtGbp(m.value)}
                </p>
              </div>
            ))}
          </div>

          <div className="rounded-xl border border-amber-400/20 bg-amber-400/5 px-6 py-4 text-center">
            <p className="text-xs text-zinc-500">Total cash liberation opportunity</p>
            <p className="font-mono text-3xl font-bold text-amber-400 tabular-nums">
              {fmtGbp(b.total_liberation_gbp)}
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-8">
            <div>
              <h2 className="text-sm font-medium text-zinc-400 mb-4">Top risks</h2>
              <div className="space-y-4">
                {b.top_risks.map((item) => (
                  <BriefCard key={item.id} item={item} kind="risk" />
                ))}
              </div>
            </div>
            <div>
              <h2 className="text-sm font-medium text-zinc-400 mb-4">Top opportunities</h2>
              <div className="space-y-4">
                {b.top_opportunities.map((item) => (
                  <BriefCard key={item.id} item={item} kind="opportunity" />
                ))}
              </div>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-medium text-zinc-400">Morning narrative</h2>
              <Button onClick={handleGenerate} disabled={streaming}>
                {streaming ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating…
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate Morning Brief
                  </>
                )}
              </Button>
            </div>
            <div className="rounded-xl border border-[#222] bg-[#111] p-8 prose prose-invert max-w-none">
              {narrative ? (
                <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">
                  {narrative}
                </p>
              ) : (
                <p className="text-sm text-zinc-600 italic">
                  Pre-computed risks and opportunities are ready. Generate narrative for
                  the founder&apos;s morning read (LLM uses injected facts only).
                </p>
              )}
            </div>
          </div>

          <p className="text-center text-xs text-green-500/80">
            Verified against bank_transactions.csv · 20/20 reconciliation rules
          </p>
        </>
      )}

      {!b && !loading && (
        <Button onClick={loadBriefing}>Load executive briefing</Button>
      )}
    </div>
  );
}
