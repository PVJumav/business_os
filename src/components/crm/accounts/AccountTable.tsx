const accounts = [
  {
    name: "KCB Bank",
    industry: "Banking",
    owner: "Paul Juma",
    value: "$240,000",
    status: "Active",
  },
  {
    name: "Britam",
    industry: "Insurance",
    owner: "Vivian",
    value: "$120,000",
    status: "Prospect",
  },
  {
    name: "Safaricom",
    industry: "Telecommunications",
    owner: "Albanus",
    value: "$410,000",
    status: "Active",
  },
];

export default function AccountTable() {
  return (
    <div className="rounded-2xl border bg-background p-6 shadow-sm">
      <h2 className="mb-6 text-xl font-semibold">
        Accounts
      </h2>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="pb-3">Account</th>
              <th className="pb-3">Industry</th>
              <th className="pb-3">Owner</th>
              <th className="pb-3">Value</th>
              <th className="pb-3">Status</th>
            </tr>
          </thead>

          <tbody>
            {accounts.map((account) => (
              <tr
                key={account.name}
                className="border-b"
              >
                <td className="py-4 font-medium">
                  {account.name}
                </td>

                <td>{account.industry}</td>

                <td>{account.owner}</td>

                <td>{account.value}</td>

                <td>
                  <span className="rounded-full bg-green-100 px-3 py-1 text-xs text-green-700">
                    {account.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}