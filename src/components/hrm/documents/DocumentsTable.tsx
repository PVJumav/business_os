const documents = [
  {
    title: "Employment Contract",
    employee: "Grace Wanjiku",
    type: "Contract",
    file: "grace-contract.pdf",
    access: "Confidential",
    expiry: "No Expiry",
    status: "Active",
  },
  {
    title: "National ID Copy",
    employee: "Brian Otieno",
    type: "ID Document",
    file: "brian-id.pdf",
    access: "Restricted",
    expiry: "No Expiry",
    status: "Active",
  },
  {
    title: "Fortinet NSE Certificate",
    employee: "Daniel Mwangi",
    type: "Certificate",
    file: "daniel-nse.pdf",
    access: "Internal",
    expiry: "30 Jun 2026",
    status: "Active",
  },
  {
    title: "May Payslip",
    employee: "Mercy Achieng",
    type: "Payslip",
    file: "mercy-may-payslip.pdf",
    access: "Restricted",
    expiry: "No Expiry",
    status: "Active",
  },
];

export default function DocumentsTable() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-slate-900">
          Document Records
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Employee documents, file details, access levels, and document status.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">Document</th>
              <th className="px-4 py-3 font-medium">Employee</th>
              <th className="px-4 py-3 font-medium">Type</th>
              <th className="px-4 py-3 font-medium">File</th>
              <th className="px-4 py-3 font-medium">Access</th>
              <th className="px-4 py-3 font-medium">Expiry</th>
              <th className="px-4 py-3 font-medium">Status</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200">
            {documents.map((document) => (
              <tr key={`${document.employee}-${document.title}`}>
                <td className="px-4 py-3 font-medium text-slate-900">
                  {document.title}
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {document.employee}
                </td>
                <td className="px-4 py-3 text-slate-600">{document.type}</td>
                <td className="px-4 py-3 text-slate-600">{document.file}</td>
                <td className="px-4 py-3 text-slate-600">{document.access}</td>
                <td className="px-4 py-3 text-slate-600">{document.expiry}</td>
                <td className="px-4 py-3">
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    {document.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}