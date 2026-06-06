import { api } from '../lib/api.js'
import { useApi } from '../lib/useApi.js'
import Card from '../components/Card.jsx'
import DataTable from '../components/DataTable.jsx'
import Loader from '../components/Loader.jsx'
import ErrorBox from '../components/ErrorBox.jsx'

export default function Arm() {
  const { data, loading, error } = useApi(api.arm, [])

  if (loading) return <Loader />
  if (error) return <ErrorBox error={error} />
  if (!data) return null

  return (
    <div className="space-y-6">
      <Card title="ARM Throughput Summary" subtitle="AWS Graviton2 (Neoverse-N1), Ubuntu 24.04 ARM64">
        <DataTable
          rows={data.summary}
          columns={['algorithm', 'throughput', 'execution_time', 'cycles', 'crypto_extensions_present']}
        />
      </Card>

      <Card title="ARM perf Hardware Counters" subtitle="armv8_pmuv3_0 events. N/A = PMU access restricted in this environment.">
        <DataTable rows={data.perf_summary} />
      </Card>

      <div className="grid md:grid-cols-2 gap-6">
        <Card title="PMU Event Validation">
          <DataTable rows={data.pmu_validation} columns={['event_name', 'supported', 'notes']} />
        </Card>
        <Card title={`Discovered PMU Events (${data.available_events.length})`}>
          <div className="max-h-72 overflow-y-auto rounded border border-slate-700/50 p-2 text-xs font-mono">
            {data.available_events.map((e) => (
              <div key={e} className="py-0.5 text-slate-300">
                {e}
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
