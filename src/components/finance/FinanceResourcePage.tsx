"use client";

import { useParams } from "next/navigation";
import ResourcePage from "@/components/data/ResourcePage";

export default function FinanceResourcePage() {
  const params = useParams<{ resource: string }>();
  return <ResourcePage resourceKey={`finance.${params.resource}`} />;
}
