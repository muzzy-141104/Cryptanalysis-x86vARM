import { api } from '../lib/api.js'
import { useApi } from '../lib/useApi.js'
import Card from '../components/Card.jsx'
import Loader from '../components/Loader.jsx'
import ErrorBox from '../components/ErrorBox.jsx'

export default function Charts() {
  const { data, loading, error } = useApi(api.charts, [])

  if (loading) return <Loader />
  if (error) return <ErrorBox error={error} />
  if (!data) return null

  return (
    <div className="space-y-6">
      <Card title="Charts Gallery" subtitle={`${data.length} charts in charts/`}>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.map((chart) => (
            <figure key={chart.name} className="rounded-lg border border-slate-700/50 bg-slate-900/40 p-3">
              <img
                src={chart.url}
                alt={chart.title}
                className="w-full h-auto rounded-md bg-white/5"
                loading="lazy"
              />
              <figcaption className="mt-2 text-sm text-slate-300">{chart.title}</figcaption>
            </figure>
          ))}
        </div>
      </Card>
    </div>
  )
}
