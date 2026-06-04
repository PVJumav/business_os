"use client";

import { FormEvent, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowRight, Bot, Loader2, Send, Sparkles, User } from "lucide-react";
import { api } from "@/services/api";

type AssistantMetric = {
  label: string;
  value: string | number;
  detail?: string;
};

type AssistantAction = {
  label: string;
  href: string;
  description: string;
};

type AssistantRecord = {
  entity: string;
  title: string;
  subtitle: string;
  href: string;
};

type AssistantResponse = {
  answer: string;
  intent: string;
  confidence: number;
  evidence: AssistantMetric[];
  actions: AssistantAction[];
  records: AssistantRecord[];
};

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: AssistantResponse;
};

const starterPrompts = [
  "Give me a CEO summary of the whole company",
  "Show finance risks and pending approvals",
  "What is the sales pipeline position?",
  "Summarize HR workforce and payroll",
  "Which projects and SLAs need attention?",
];

function formatMetric(value: string | number) {
  if (typeof value === "number") {
    return value.toLocaleString(undefined, { maximumFractionDigits: 0 });
  }
  return value;
}

export default function AIAssistantPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "I can read Business OS data across CRM, HRM, Finance, Projects, Reports, and Analytics. Ask me about pipeline, invoices, employees, budgets, approvals, SLAs, reports, or a specific staff/customer record.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const lastIntent = useMemo(() => {
    const latest = [...messages].reverse().find((item) => item.response?.intent);
    return latest?.response?.intent ?? "company";
  }, [messages]);

  async function askAssistant(question: string) {
    const trimmed = question.trim();
    if (!trimmed || loading) return;

    setError(null);
    setInput("");
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };
    setMessages((current) => [...current, userMessage]);
    setLoading(true);

    try {
      const response = await api.post<AssistantResponse>("/api/ai/chat", { message: trimmed });
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: response.answer,
          response,
        },
      ]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "The assistant could not fetch system data.";
      setError(message);
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `I could not complete that request: ${message}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    askAssistant(input);
  }

  return (
    <div className="grid min-h-[720px] gap-4 lg:grid-cols-[280px_1fr]">
      <aside className="rounded-2xl border border-slate-200 bg-white p-4">
        <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-white">
            <Sparkles size={18} />
          </span>
          <div>
            <h2 className="text-base font-semibold text-slate-950">Business OS AI</h2>
            <p className="text-xs capitalize text-slate-500">Current focus: {lastIntent.replace("_", " ")}</p>
          </div>
        </div>

        <div className="mt-4 space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Ask Quickly</p>
          {starterPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => askAssistant(prompt)}
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-left text-sm text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
            >
              {prompt}
            </button>
          ))}
        </div>

        <div className="mt-5 rounded-xl bg-slate-50 p-3 text-sm text-slate-600">
          The assistant uses live records and returns links into the system for drill-down. Admins and managers see wider organizational context.
        </div>
      </aside>

      <section className="flex min-h-[720px] flex-col rounded-2xl border border-slate-200 bg-white">
        <div className="border-b border-slate-100 px-5 py-4">
          <h3 className="text-lg font-semibold text-slate-950">Enterprise Assistant</h3>
          <p className="text-sm text-slate-500">Ask operational questions and move directly into the relevant work area.</p>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto p-5">
          {messages.map((message) => (
            <div key={message.id} className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}>
              {message.role === "assistant" && (
                <span className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-950 text-white">
                  <Bot size={17} />
                </span>
              )}

              <div className={`max-w-[820px] ${message.role === "user" ? "order-first" : ""}`}>
                <div
                  className={`rounded-2xl px-4 py-3 text-sm leading-6 ${
                    message.role === "user"
                      ? "bg-blue-600 text-white"
                      : "border border-slate-200 bg-slate-50 text-slate-800"
                  }`}
                >
                  {message.content}
                </div>

                {message.response && (
                  <div className="mt-3 space-y-3">
                    {message.response.evidence.length > 0 && (
                      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
                        {message.response.evidence.map((item) => (
                          <div key={`${message.id}-${item.label}`} className="rounded-xl border border-slate-200 bg-white p-3">
                            <p className="text-xs text-slate-500">{item.label}</p>
                            <p className="mt-1 text-lg font-semibold text-slate-950">{formatMetric(item.value)}</p>
                            {item.detail && <p className="mt-1 text-xs text-slate-500">{item.detail}</p>}
                          </div>
                        ))}
                      </div>
                    )}

                    {message.response.records.length > 0 && (
                      <div className="rounded-xl border border-slate-200 bg-white">
                        <div className="border-b border-slate-100 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                          Related Records
                        </div>
                        <div className="divide-y divide-slate-100">
                          {message.response.records.map((record, index) => (
                            <Link
                              key={`${message.id}-${record.entity}-${index}`}
                              href={record.href}
                              className="flex items-center justify-between gap-3 px-3 py-2 text-sm transition hover:bg-slate-50"
                            >
                              <div>
                                <p className="font-medium text-slate-900">{record.title}</p>
                                <p className="text-xs text-slate-500">{record.entity} | {record.subtitle}</p>
                              </div>
                              <ArrowRight size={16} className="text-slate-400" />
                            </Link>
                          ))}
                        </div>
                      </div>
                    )}

                    {message.response.actions.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {message.response.actions.map((action) => (
                          <Link
                            key={`${message.id}-${action.href}-${action.label}`}
                            href={action.href}
                            title={action.description}
                            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
                          >
                            {action.label}
                            <ArrowRight size={15} />
                          </Link>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {message.role === "user" && (
                <span className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white">
                  <User size={17} />
                </span>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-3 text-sm text-slate-500">
              <Loader2 size={18} className="animate-spin" />
              Reading live system data...
            </div>
          )}
        </div>

        <form onSubmit={submit} className="border-t border-slate-100 p-4">
          {error && <p className="mb-2 text-sm text-red-600">{error}</p>}
          <div className="flex gap-2">
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask about revenue, unpaid invoices, staff, sales targets, projects, SLAs, reports..."
              className="min-h-12 flex-1 rounded-xl border border-slate-200 px-4 text-sm outline-none transition focus:border-slate-500"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-slate-950 text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
              title="Send"
            >
              {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
