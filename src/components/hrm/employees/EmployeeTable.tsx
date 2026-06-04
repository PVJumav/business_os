const employees = [
  {
    code: "EMP-001",
    name: "Grace Wanjiku",
    email: "grace@company.com",
    role: "HR Manager",
    department: "Human Resources",
    type: "Full-time",
    status: "Active",
  },
  {
    code: "EMP-002",
    name: "Brian Otieno",
    email: "brian@company.com",
    role: "Finance Officer",
    department: "Finance",
    type: "Full-time",
    status: "Active",
  },
  {
    code: "EMP-003",
    name: "Mercy Achieng",
    email: "mercy@company.com",
    role: "Sales Executive",
    department: "Sales",
    type: "Full-time",
    status: "On Leave",
  },
  {
    code: "EMP-004",
    name: "Daniel Mwangi",
    email: "daniel@company.com",
    role: "Systems Engineer",
    department: "Technical",
    type: "Contract",
    status: "Active",
  },
  {
    code: "EMP-005",
    name: "Sarah Njeri",
    email: "sarah@company.com",
    role: "Operations Lead",
    department: "Operations",
    type: "Full-time",
    status: "Probation",
  },
];

export default function EmployeeTable() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            Employee Directory
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            View and manage employee records.
          </p>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">Code</th>
              <th className="px-4 py-3 font-medium">Employee</th>
              <th className="px-4 py-3 font-medium">Role</th>
              <th className="px-4 py-3 font-medium">Department</th>
              <th className="px-4 py-3 font-medium">Type</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Action</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200">
            {employees.map((employee) => (
              <tr key={employee.code}>
                <td className="px-4 py-3 font-medium text-slate-900">
                  {employee.code}
                </td>

                <td className="px-4 py-3">
                  <p className="font-medium text-slate-900">{employee.name}</p>
                  <p className="text-xs text-slate-500">{employee.email}</p>
                </td>

                <td className="px-4 py-3 text-slate-600">{employee.role}</td>
                <td className="px-4 py-3 text-slate-600">
                  {employee.department}
                </td>
                <td className="px-4 py-3 text-slate-600">{employee.type}</td>

                <td className="px-4 py-3">
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    {employee.status}
                  </span>
                </td>

                <td className="px-4 py-3">
                  <button className="text-sm font-medium text-slate-900 hover:underline">
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}