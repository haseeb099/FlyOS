"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toaster";
import { exportSegment, generateEmail } from "@/lib/api";
import type { EmailParams } from "@/lib/types";

interface EmailPreviewProps {
  params: EmailParams | null;
}

function parseStreamedEmail(raw: string): {
  subject: string;
  preview: string;
  body: string;
  cta: string;
} {
  try {
    const jsonMatch = raw.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]) as Record<string, string>;
      return {
        subject: parsed.subject ?? "",
        preview: parsed.preview_text ?? "",
        body: parsed.body ?? "",
        cta: parsed.cta ?? "",
      };
    }
  } catch {
    /* use raw as body */
  }
  return { subject: "", preview: "", body: raw, cta: "" };
}

export function EmailPreview({ params }: EmailPreviewProps) {
  const { toast } = useToast();
  const [subject, setSubject] = useState("");
  const [preview, setPreview] = useState("");
  const [body, setBody] = useState("");
  const [cta, setCta] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const handleGenerate = async () => {
    if (!params) return;
    setStreaming(true);
    setSubject("");
    setPreview("");
    setBody("");
    setCta("");

    try {
      const res = await generateEmail(params);
      if (!res.ok || !res.body) {
        throw new Error("Email generation failed");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let accumulated = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        for (const line of chunk.split("\n")) {
          const payload = line.startsWith("data: ")
            ? line.slice(6)
            : line.trim()
              ? line
              : "";
          if (!payload) continue;
          accumulated += payload;
          const parsed = parseStreamedEmail(accumulated);
          setSubject(parsed.subject);
          setPreview(parsed.preview);
          setBody(parsed.body);
          setCta(parsed.cta);
        }
      }
    } catch (e) {
      setBody(e instanceof Error ? e.message : "Could not generate email");
    } finally {
      setStreaming(false);
    }
  };

  const copyAll = async () => {
    const text = `Subject: ${subject}\n\n${preview}\n\n${body}\n\nCTA: ${cta}`;
    await navigator.clipboard.writeText(text);
    toast("Copied to clipboard", "success");
  };

  const downloadCsv = async () => {
    if (!params?.leak_id) return;
    setDownloading(true);
    try {
      const { csv, count } = await exportSegment(params.leak_id);
      const blob = new Blob([csv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `segment-${params.leak_id}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      toast(`Downloaded segment (${count} customers)`, "success");
    } catch (e) {
      toast(e instanceof Error ? e.message : "Export failed", "error");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="space-y-4">
      <Button disabled={!params || streaming} onClick={handleGenerate}>
        {streaming ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Writing copy…
          </>
        ) : (
          "Generate Email"
        )}
      </Button>

      <div className="rounded-xl border border-[#222] bg-[#0a0a0a] p-4">
        <div className="rounded-lg bg-[#1a1a1a] border border-[#222] p-6 space-y-4 font-sans">
          <div>
            <label className="text-xs text-zinc-500">To</label>
            <p className="text-sm text-zinc-300">Dead-stock segment · Klaviyo</p>
          </div>
          <div>
            <label className="text-xs text-zinc-500">Subject</label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full mt-1 rounded border border-[#333] bg-[#0a0a0a] px-2 py-1 text-sm text-zinc-100"
              placeholder={streaming ? "…" : "—"}
            />
          </div>
          <div>
            <label className="text-xs text-zinc-500">Preview</label>
            <input
              type="text"
              value={preview}
              onChange={(e) => setPreview(e.target.value)}
              className="w-full mt-1 rounded border border-[#333] bg-[#0a0a0a] px-2 py-1 text-sm text-zinc-400"
            />
          </div>
          <div>
            <label className="text-xs text-zinc-500">Body</label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={6}
              className="w-full mt-1 rounded border border-[#333] bg-[#0a0a0a] px-2 py-1 text-sm text-zinc-300"
              placeholder={streaming ? "Generating…" : "—"}
            />
          </div>
          {cta && (
            <div>
              <label className="text-xs text-zinc-500">CTA</label>
              <p className="text-sm font-medium text-amber-400">{cta}</p>
            </div>
          )}
        </div>
      </div>

      <div className="flex gap-3">
        <Button variant="outline" onClick={copyAll} disabled={!body}>
          Copy All
        </Button>
        <Button variant="outline" onClick={downloadCsv} disabled={!params || downloading}>
          {downloading ? "Exporting…" : "Download CSV"}
        </Button>
      </div>
    </div>
  );
}
