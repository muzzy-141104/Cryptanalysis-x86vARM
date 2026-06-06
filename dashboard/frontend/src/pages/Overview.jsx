import { api } from '../lib/api.js'
import { useApi } from '../lib/useApi.js'
import Card from '../components/Card.jsx'
import DataTable from '../components/DataTable.jsx'
import Loader from '../components/Loader.jsx'
import ErrorBox from '../components/ErrorBox.jsx'

export default function Overview() {
  const { data, loading, error } = useApi(api.overview, [])

  if (loading) return <Loader />
  if (error) return <ErrorBox error={error} />
  if (!data) return null

  return (
    <div className="space-y-6">
      <Card title={data.project} subtitle={data.description}>
        <p className="text-slate-300 text-sm">
          This dashboard visualizes the complete x86 and ARM analysis pipeline for
          the Cryptanalysis-x86vARM project. Use the navigation above to explore
          per-architecture metrics, the cross-architecture comparison, generated
          charts, and full project reports.
        </p>
      </Card>

      <div className="grid md:grid-cols-2 gap-6">
        <Card title="Algorithms Analyzed">
          <DataTable
            rows={data.algorithms}
            columns={['name', 'description']}
          />
        </Card>

        <Card title="Architecture Targets">
          <DataTable
            rows={data.architectures.map((a) => ({
              name: a.name,
              host: a.host,
              extensions: a.extensions.join(', '),
              tools: a.tools.join(', '),
            }))}
            columns={['name', 'host', 'extensions', 'tools']}
          />
        </Card>
      </div>
    </div>
  )
}
