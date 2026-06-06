import { api } from '../lib/api.js'
import { useApi } from '../lib/useApi.js'
import Card from '../components/Card.jsx'
import DataTable from '../components/DataTable.jsx'
import Loader from '../components/Loader.jsx'
import ErrorBox from '../components/ErrorBox.jsx'

export default function Comparison() {
  const { data, loading, error } = useApi(api.comparison, [])

  if (loading) return <Loader />
  if (error) return <ErrorBox error={error} />
  if (!data) return null

  return (
    <div className="space-y-6">
      <Card title="x86 vs ARM" subtitle="Cross-architecture comparison">
        <DataTable rows={data.x86_vs_arm} />
      </Card>

      <Card title="Unified Comparison" subtitle="Detailed metric-by-metric table">
        <DataTable rows={data.unified} />
      </Card>

      <Card title="Pin vs DynamoRIO (x86)">
        <DataTable rows={data.pin_vs_dynamorio} />
      </Card>
    </div>
  )
}
