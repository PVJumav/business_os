interface Column<T> {
  key: keyof T;
  header: string;
  render?: (value: T[keyof T], row: T) => React.ReactNode;
}

interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  emptyMessage?: string;
}

export default function Table<T extends { id?: string | number }>({
  columns,
  data,
  emptyMessage = "No data found.",
}: TableProps<T>) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200/80 bg-white/80 shadow-sm">
      <div className="overflow-x-auto">
      <table className="w-full text-sm text-left">
        <thead className="bg-slate-50/90">
          <tr className="border-b border-slate-200/80">
            {columns.map((col) => (
              <th key={String(col.key)} className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-slate-400">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, i) => (
                <tr key={row.id ?? i} className="border-b border-slate-100/80 transition hover:bg-blue-50/45">
                  {columns.map((col) => (
                    <td key={String(col.key)} className="px-4 py-3 text-slate-700">
                    {col.render ? col.render(row[col.key], row) : String(row[col.key] ?? "")}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
      </div>
    </div>
  );
}
