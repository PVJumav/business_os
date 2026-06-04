const contacts = [
  {
    name: "Anthony Mwangi",
    organization: "Niwa Sacco",
    type: "Customer",
    role: "ICT Manager",
    email: "anthony@niwasacco.co.ke",
    phone: "+254 7XX XXX XXX",
    status: "Active",
  },
  {
    name: "Vivian Njeri",
    organization: "Exclusive Networks",
    type: "Distributor",
    role: "Partner Manager",
    email: "vivian@example.com",
    phone: "+254 7XX XXX XXX",
    status: "Active",
  },
  {
    name: "Patrick Otieno",
    organization: "Security Integrator Partner",
    type: "Third-Party Integrator",
    role: "Solutions Engineer",
    email: "patrick@example.com",
    phone: "+254 7XX XXX XXX",
    status: "Pending Follow-up",
  },
];

export default function ContactTable() {
  return (
    <div className="rounded-2xl border bg-background p-6 shadow-sm">
      <h2 className="mb-6 text-xl font-semibold">Contact Directory</h2>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="pb-3">Name</th>
              <th className="pb-3">Organization</th>
              <th className="pb-3">Type</th>
              <th className="pb-3">Role</th>
              <th className="pb-3">Email</th>
              <th className="pb-3">Phone</th>
              <th className="pb-3">Status</th>
            </tr>
          </thead>

          <tbody>
            {contacts.map((contact) => (
              <tr key={contact.email} className="border-b">
                <td className="py-4 font-medium">{contact.name}</td>
                <td>{contact.organization}</td>
                <td>{contact.type}</td>
                <td>{contact.role}</td>
                <td>{contact.email}</td>
                <td>{contact.phone}</td>
                <td>
                  <span className="rounded-full bg-muted px-3 py-1 text-xs">
                    {contact.status}
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