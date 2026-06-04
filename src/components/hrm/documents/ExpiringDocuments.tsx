const expiringDocuments = [
  {
    title: "Fortinet NSE Certificate",
    employee: "Daniel Mwangi",
    expiry: "30 Jun 2026",
  },
  {
    title: "Work Permit",
    employee: "John Kamau",
    expiry: "15 Jul 2026",
  },
  {
    title: "Professional Membership",
    employee: "Grace Wanjiku",
    expiry: "28 Jul 2026",
  },
];

export default function ExpiringDocuments() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">
        Expiring Soon
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Documents requiring renewal.
      </p>

      <div className="mt-5 space-y-3">
        {expiringDocuments.map((document) => (
          <div
            key={`${document.employee}-${document.title}`}
            className="rounded-xl border border-slate-200 p-4"
          >
            <p className="text-sm font-semibold text-slate-900">
              {document.title}
            </p>
            <p className="mt-1 text-xs text-slate-500">{document.employee}</p>
            <p className="mt-2 text-xs font-medium text-slate-700">
              Expires: {document.expiry}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}