export default function DataTable({ rows, columns }) {
  if (!rows || rows.length === 0) {
    return <p className="text-slate-400 italic">No data available.</p>
  }
  const cols = columns && columns.length ? columns : Object.keys(rows[0])
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-700/50">
      <table className="text-sm">
        <thead className="bg-slate-800/60">
          <tr>
            {cols.map((c) => (
              <th key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="odd:bg-slate-900/40 even:bg-slate-900/10">
              {cols.map((c) => (
                <td key={c}>{formatCell(row[c])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function formatCell(value) {
  if (value === null || value === undefined) return 'N/A'
  if (typeof value === 'number') {
    if (Number.isInteger(value)) return value.toLocaleString()
    return value.toLocaleString(undefined, { maximumFractionDigits: 4 })
  }
  return String(value)
}
