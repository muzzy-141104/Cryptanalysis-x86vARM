const BASE = ''

async function request(path) {
  const res = await fetch(`${BASE}/api/${path}`)
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`)
  return res.json()
}

export const api = {
  overview: () => request('overview'),
  x86: () => request('x86'),
  arm: () => request('arm'),
  comparison: () => request('comparison'),
  charts: () => request('charts'),
  reports: () => request('reports'),
}
