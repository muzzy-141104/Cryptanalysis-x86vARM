import { api } from '../lib/api.js'
import { useApi } from '../lib/useApi.js'
import Card from '../components/Card.jsx'
import DataTable from '../components/DataTable.jsx'
import Loader from '../components/Loader.jsx'
import ErrorBox from '../components/ErrorBox.jsx'

const DBI_COLS = ['instruction_count', 'memory_reads', 'memory_writes']
const AES_COLS = ['aesenc_count', 'aesenclast_count', 'aesdec_count', 'aesdeclast_count']
const SHA_COLS = ['sha256rnds2_count', 'sha256msg1_count', 'sha256msg2_count']
const PERF_COLS = ['cpu-cycles', 'instructions', 'branch-instructions', 'branch-misses', 'cache-references', 'cache-misses', 'ipc', 'branch_miss_ratio', 'cache_miss_ratio']

export default function X86() {
  const { data, loading, error } = useApi(api.x86, [])

  if (loading) return <Loader />
  if (error) return <ErrorBox error={error} />
  if (!data) return null

  return (
    <div className="space-y-6">
      <Card title="x86 DBI Summary" subtitle="Intel Pin tool on AMD Ryzen 5 7535HS">
        <DataTable rows={data.summary} columns={['algorithm', ...DBI_COLS, ...AES_COLS, ...SHA_COLS]} />
      </Card>

      <Card title="x86 perf Hardware Counters">
        <DataTable rows={data.perf_summary} columns={['algorithm', ...PERF_COLS]} />
      </Card>

      <div className="grid md:grid-cols-2 gap-6">
        <Card title="AES-NI Usage">
          <DataTable rows={data.summary} columns={['algorithm', ...AES_COLS]} />
        </Card>
        <Card title="SHA-NI Usage">
          <DataTable rows={data.summary} columns={['algorithm', ...SHA_COLS]} />
        </Card>
      </div>
    </div>
  )
}
