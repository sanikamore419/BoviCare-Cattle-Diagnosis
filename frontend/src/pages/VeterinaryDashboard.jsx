import { AlertTriangle, CheckCircle2, Clock3, FileDown, Search } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Badge, Card, EmptyState, ErrorAlert, LoadingState } from '../components/ui'
import { api } from '../lib/api'
import { formatIstDateTime, getWaitHours, sortCasesByPriorityAndSubmission } from '../lib/dateTime'
import { downloadCaseReport } from '../lib/reports'

function Metric({ label, value, icon: Icon, tone = 'emerald' }) {
  const color = tone === 'red' ? 'text-red-600' : tone === 'amber' ? 'text-amber-600' : 'text-emerald-700'
  return <Card className="p-5"><Icon className={color} /><p className="mt-4 text-3xl font-bold">{value}</p><p className="mt-1 text-sm text-slate-500">{label}</p></Card>
}

function formatWorkflowStatus(status) {
  if (!status) return 'PENDING'
  const normalized = status.toString().toLowerCase().replace(/_/g, ' ')
  if (normalized.includes('progress')) return 'IN_PROGRESS'
  if (normalized.includes('complete') || normalized.includes('reviewed')) return 'COMPLETED'
  return 'PENDING'
}

export default function VeterinaryDashboard() {
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [risk, setRisk] = useState('all')
  const [status, setStatus] = useState('all')

  useEffect(() => {
    api.get('/cases')
      .then(response => setCases(response.data))
      .catch(() => setError('The API is unavailable. Start the backend to review cases.'))
      .finally(() => setLoading(false))
  }, [])

  const filtered = sortCasesByPriorityAndSubmission(cases).filter(item => {
    const matchesRisk = risk === 'all' || item.risk_level === risk
    const matchesStatus = status === 'all' || formatWorkflowStatus(item.workflow_status || item.status) === status.toUpperCase()
    const searchable = `${item.cattle_tag} ${item.ai_prediction} ${(item.symptoms || []).join(' ')} ${(item.urgency_level || '').toLowerCase()}`.toLowerCase()
    return matchesRisk && matchesStatus && searchable.includes(query.toLowerCase())
  })
  const pending = cases.filter(item => formatWorkflowStatus(item.workflow_status || item.status) === 'PENDING').length
  const inProgress = cases.filter(item => formatWorkflowStatus(item.workflow_status || item.status) === 'IN_PROGRESS').length
  const high = cases.filter(item => (item.urgency_level || 'LOW').toUpperCase() === 'HIGH').length

  async function download(id) {
    try {
      await downloadCaseReport(id)
    } catch {
      setError('A protected report could not be downloaded. Please sign in again and retry.')
    }
  }

  return (
    <div>
      <p className="eyebrow">Veterinary portal</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight text-emerald-950">Priority inbox</h1>
      <p className="mt-2 text-sm text-slate-600">Cases are sorted by urgency and waiting time so the highest-priority review is handled first.</p>
      {error && <div className="mt-6"><ErrorAlert>{error}</ErrorAlert></div>}

      <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Total cases" value={loading ? '-' : cases.length} icon={CheckCircle2} />
        <Metric label="Pending" value={loading ? '-' : pending} icon={Clock3} tone="amber" />
        <Metric label="In progress" value={loading ? '-' : inProgress} icon={CheckCircle2} />
        <Metric label="High priority" value={loading ? '-' : high} icon={AlertTriangle} tone="red" />
      </section>

      {high > 0 && <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-4"><p className="flex items-center gap-2 text-sm font-bold text-red-900"><AlertTriangle size={18} />High-priority alert</p><p className="mt-1 text-sm text-red-800">{high} case{high === 1 ? '' : 's'} are currently in the HIGH urgency band.</p></div>}

      <Card className="mt-6 overflow-hidden">
        <div className="border-b border-slate-100 p-5">
          <div className="flex flex-wrap gap-3">
            <div className="relative min-w-52 flex-1"><Search className="absolute left-3 top-3 text-slate-400" size={17} /><input value={query} onChange={event => setQuery(event.target.value)} className="input mt-0 pl-9" placeholder="Search cattle or symptom" /></div>
            <select value={risk} onChange={event => setRisk(event.target.value)} className="input mt-0 w-auto"><option value="all">All risks</option><option value="high">High risk</option><option value="medium">Moderate risk</option><option value="low">Low risk</option></select>
            <select value={status} onChange={event => setStatus(event.target.value)} className="input mt-0 w-auto"><option value="all">All workflow</option><option value="PENDING">PENDING</option><option value="IN_PROGRESS">IN_PROGRESS</option><option value="COMPLETED">COMPLETED</option></select>
          </div>
        </div>
        {loading ? <LoadingState /> : filtered.length ? <div className="overflow-x-auto"><table className="w-full min-w-[860px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500"><tr><th className="px-5 py-3">Case</th><th className="px-5 py-3">Cattle</th><th className="px-5 py-3">Urgency priority</th><th className="px-5 py-3">AI suggestion</th><th className="px-5 py-3">Status</th><th className="px-5 py-3">Action</th></tr></thead><tbody className="divide-y divide-slate-100">{filtered.map(item => <tr key={item.id} className="transition hover:bg-emerald-50/40"><td className="px-5 py-4"><Link to={`/veterinary/cases/${item.id}`} state={{ result: item }} className="font-bold text-emerald-800">#{item.id}</Link><p className="mt-1 text-xs text-slate-500">{formatIstDateTime(item.created_at)}</p><p className="mt-1 text-xs text-slate-500">Waiting: {getWaitHours(item.created_at)}h</p></td><td className="px-5 py-4"><p className="font-medium text-slate-800">{item.cattle_tag}</p><p className="mt-1 text-xs text-slate-500">{(item.symptoms || []).join(', ')}</p></td><td className="px-5 py-4"><div className="font-semibold text-slate-800">Priority: {(item.urgency_level || 'LOW').toUpperCase()}</div><div className="mt-1 text-xs text-slate-500">Score: {Number(item.urgency_score ?? 0).toFixed(2)} / 100</div></td><td className="px-5 py-4 text-slate-700">{item.ai_prediction || 'No triage provided'}</td><td className="px-5 py-4"><Badge value={formatWorkflowStatus(item.workflow_status || item.status)} /></td><td className="px-5 py-4"><div className="flex items-center gap-2"><Link to={`/veterinary/cases/${item.id}`} state={{ result: item }} className="inline-flex items-center rounded-md bg-emerald-700 px-3 py-2 text-xs font-semibold text-white hover:bg-emerald-800">Accept & Review</Link><button onClick={() => download(item.id)} className="inline-flex text-emerald-700 hover:text-emerald-900" title="Download case report"><FileDown size={18} /></button></div></td></tr>)}</tbody></table></div> : <EmptyState icon={Search} title="No matching cases" message="Try a different search term or clear the active filters." />}
      </Card>
    </div>
  )
}
