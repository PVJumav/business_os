"use client";

import { createContext, useContext, useMemo, useState } from "react";

interface SearchContextValue {
  query: string;
  setQuery: (query: string) => void;
}

const SearchContext = createContext<SearchContextValue | null>(null);

export function SearchProvider({ children }: { children: React.ReactNode }) {
  const [query, setQuery] = useState("");
  const value = useMemo(() => ({ query, setQuery }), [query]);

  return <SearchContext.Provider value={value}>{children}</SearchContext.Provider>;
}

export function useGlobalSearch() {
  const context = useContext(SearchContext);
  if (!context) {
    return { query: "", setQuery: () => undefined };
  }
  return context;
}
