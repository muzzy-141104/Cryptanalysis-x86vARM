export default function Card({ title, subtitle, children, className = '' }) {
  return (
    <section className={`rounded-xl border border-slate-700/50 bg-slate-900/40 p-5 ${className}`}>
      <header className="mb-3">
        <h2 className="text-lg font-semibold text-slate-100">{title}</h2>
        {subtitle && <p className="text-sm text-slate-400">{subtitle}</p>}
      </header>
      {children}
    </section>
  )
}
