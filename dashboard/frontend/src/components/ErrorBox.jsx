export default function ErrorBox({ error }) {
  if (!error) return null
  return (
    <div className="rounded-md border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200">
      {error}
    </div>
  )
}
