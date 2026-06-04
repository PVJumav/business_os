"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { Search } from "lucide-react";
import { api } from "@/services/api";
import { useGlobalSearch } from "@/store/searchStore";

interface SearchResult {
  entity: string;
  title: string;
  subtitle: string;
  href: string;
  id: string;
}

function contextLabel(pathname: string) {
  if (pathname.startsWith("/hrm")) return "HRM";
  if (pathname.startsWith("/crm")) return "CRM";
  if (pathname.startsWith("/finance")) return "Finance";
  if (pathname.startsWith("/projects")) return "Projects";
  return "Company";
}

export default function GlobalSearchBox({ className = "w-[500px]" }: { className?: string }) {
  const pathname = usePathname();
  const { query, setQuery } = useGlobalSearch();
  const [results, setResults] = useState<SearchResult[]>([]);
  const scope = contextLabel(pathname);

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    const term = query.trim();
    if (term.length < 2) {
      setResults([]);
      return;
    }

    const timer = window.setTimeout(() => {
      api
        .get<SearchResult[]>("/api/search", { params: { query: term, scope } })
        .then(setResults)
        .catch(() => setResults([]));
    }, 250);

    return () => window.clearTimeout(timer);
  }, [query, scope]);
  /* eslint-enable react-hooks/set-state-in-effect */

  return (
    <div className={`relative ${className}`}>
      <div className="focus-ring flex h-11 items-center rounded-lg border border-slate-200 bg-white/82 px-4 shadow-sm backdrop-blur">
        <Search size={18} className="text-slate-500" />
        <input
          type="text"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={`Search ${scope.toLowerCase()} records...`}
          className="w-full bg-transparent px-3 text-sm text-slate-800 outline-none placeholder:text-slate-400"
        />
      </div>

      {results.length > 0 && (
        <div className="glass-panel absolute left-0 right-0 top-12 z-50 max-h-96 overflow-y-auto rounded-lg">
          {results.map((result) => (
            <Link
              key={`${result.entity}-${result.id}`}
              href={result.href}
              onClick={() => {
                setQuery("");
                setResults([]);
              }}
              className="block border-b border-slate-200/70 px-4 py-3 text-sm transition hover:bg-blue-50/60"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="font-semibold text-slate-900">{result.title}</p>
                <span className="status-pill px-2 py-1 text-xs text-slate-600">{result.entity}</span>
              </div>
              <p className="mt-1 text-xs text-slate-500">{result.subtitle}</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
