import { Routes, Route, NavLink, Link } from 'react-router-dom'
import Overview from './pages/Overview.jsx'
import X86 from './pages/X86.jsx'
import Arm from './pages/Arm.jsx'
import Comparison from './pages/Comparison.jsx'
import Charts from './pages/Charts.jsx'
import Report from './pages/Report.jsx'

const NAV = [
  { to: '/', label: 'Overview' },
  { to: '/x86', label: 'x86 Analysis' },
  { to: '/arm', label: 'ARM Analysis' },
  { to: '/comparison', label: 'Comparison' },
  { to: '/charts', label: 'Charts' },
  { to: '/report', label: 'Reports' },
]

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-700/60 bg-slate-900/70 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="text-xl font-semibold">
            <span className="text-accent">Cryptanalysis</span> x86 <span className="opacity-60">vs</span> ARM
          </Link>
          <nav className="flex gap-1 flex-wrap">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded-md text-sm transition ${
                    isActive
                      ? 'bg-accent/20 text-accent'
                      : 'text-slate-300 hover:bg-slate-800'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/x86" element={<X86 />} />
          <Route path="/arm" element={<Arm />} />
          <Route path="/comparison" element={<Comparison />} />
          <Route path="/charts" element={<Charts />} />
          <Route path="/report" element={<Report />} />
          <Route path="/report/:slug" element={<Report />} />
        </Routes>
      </main>

      <footer className="border-t border-slate-700/60 text-slate-400 text-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between">
          <span>Cryptanalysis-x86vARM Dashboard</span>
          <span>Data: results/ + charts/</span>
        </div>
      </footer>
    </div>
  )
}
