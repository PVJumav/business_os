import ResourceManager from "@/components/data/ResourceManager";
import { resourceConfigs } from "@/lib/resourceConfigs";

export default function ResourcePage({ resourceKey }: { resourceKey: string }) {
  const config = resourceConfigs[resourceKey];

  if (!config) {
    return <div className="rounded-xl border bg-white p-6">Unknown resource.</div>;
  }

  return <ResourceManager config={config} />;
}
