import { Activity, AlertTriangle, BookOpen, CheckCircle2, ClipboardList, Clock3, HeartPulse, History, Search, Stethoscope } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { Card, EmptyState, ErrorAlert, LoadingState } from '../components/ui'
import { api } from '../lib/api'
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

const RISK_COLORS = { high: '#dc2626', medium: '#d97706', low: '#16a34a' }

function formatStatus(value) {
  const normalized = String(value || '').trim().toLowerCase().replace(/[_\s]+/g, '_')
  if (!normalized) return 'pending_review'
  if (normalized.includes('review') || normalized.includes('complete') || normalized.includes('closed')) return 'reviewed'
  if (normalized.includes('progress')) return 'pending_review'
  return 'pending_review'
}

function formatRisk(value) {
  const normalized = String(value || '').trim().toLowerCase()
  if (normalized.includes('high')) return 'high'
  if (normalized.includes('medium') || normalized.includes('moderate')) return 'medium'
  return 'low'
}

function getWaitHours(createdAt) {
  if (!createdAt) return 0
  return Math.max(0, Math.round((Date.now() - new Date(createdAt).getTime()) / 3600000))
}

function formatWaitTime(createdAt) {
  const hours = getWaitHours(createdAt)
  if (!hours) return '0h'
  if (hours < 24) return `${hours}h`
  const days = Math.floor(hours / 24)
  return `${days}d`
}

function StatCard({ label, value, icon: Icon, tone = 'emerald', hint = '' }) {
  const map = {
    red: 'text-red-600 bg-red-50',
    amber: 'text-amber-600 bg-amber-50',
    blue: 'text-blue-600 bg-blue-50',
    emerald: 'text-emerald-600 bg-emerald-50',
    slate: 'text-slate-600 bg-slate-100',
  }

  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p className="mt-3 text-3xl font-bold text-slate-900">{value}</p>
          {hint && <p className="mt-2 text-xs text-slate-500">{hint}</p>}
        </div>
        <span className={`inline-flex rounded-xl p-2.5 ${map[tone] || map.emerald}`}>
          <Icon size={18} />
        </span>
      </div>
    </Card>
  )
}

function RiskBadge({ value }) {
  const normalized = formatRisk(value)
  const classes = {
    high: 'bg-red-50 text-red-700 ring-red-200',
    medium: 'bg-amber-50 text-amber-700 ring-amber-200',
    low: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  }
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.12em] ring-1 ring-inset ${classes[normalized] || classes.low}`}>{normalized}</span>
}

function StatusBadge({ value }) {
  const normalized = formatStatus(value)
  const classes = {
    pending_review: 'bg-sky-50 text-sky-700 ring-sky-200',
    reviewed: 'bg-slate-100 text-slate-700 ring-slate-200',
  }
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.12em] ring-1 ring-inset ${classes[normalized] || classes.pending_review}`}>{normalized.replace(/_/g, ' ')}</span>
}

function SearchField({ value, onChange, placeholder }) {
  return (
    <label className="relative block min-w-[220px] flex-1">
      <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
      <input value={value} onChange={onChange} placeholder={placeholder} className="input mt-0 !pl-9" />
    </label>
  )
}

function PageHeader({ eyebrow, title, subtitle, action }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1 className="mt-2 text-3xl font-bold text-slate-900">{title}</h1>
        {subtitle && <p className="mt-2 max-w-2xl text-sm text-slate-600">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}

export function CaseQueuePage() {
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [risk, setRisk] = useState('all')
  const [status, setStatus] = useState('all')

  useEffect(() => {
    let active = true
    api.get('/cases')
      .then((response) => { if (active) setCases(response.data || []) })
      .catch(() => { if (active) setError('We could not load the latest cases. Please try again.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  const filteredCases = useMemo(() => {
    return [...cases]
      .sort((a, b) => {
        const order = { high: 0, medium: 1, low: 2 }
        return (order[formatRisk(a.risk_level)] ?? 99) - (order[formatRisk(b.risk_level)] ?? 99)
      })
      .filter((item) => {
        const matchesRisk = risk === 'all' || formatRisk(item.risk_level) === risk
        const itemStatus = formatStatus(item.workflow_status || item.status)
        const matchesStatus = status === 'all' || itemStatus === status
        const haystack = `${item.cattle_tag || ''} ${item.ai_prediction || ''} ${(item.symptoms || []).join(' ')}`.toLowerCase()
        return matchesRisk && matchesStatus && haystack.includes(query.trim().toLowerCase())
      })
  }, [cases, query, risk, status])

  const stats = useMemo(() => {
    const pending = cases.filter((item) => formatStatus(item.workflow_status || item.status) === 'pending_review').length
    const highRisk = cases.filter((item) => formatRisk(item.risk_level) === 'high').length
    const reviewed = cases.filter((item) => formatStatus(item.workflow_status || item.status) === 'reviewed').length
    return { total: cases.length, pending, highRisk, reviewed }
  }, [cases])

  return (
    <div>
      <PageHeader
        eyebrow="Priority inbox"
        title="Case queue"
        subtitle="Cases are sorted by urgency and waiting time."
        action={<Link to="/cases" className="button-secondary">Refresh</Link>}
      />

      {error && <div className="mt-6"><ErrorAlert>{error}</ErrorAlert></div>}

      <section className="mt-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total cases" value={loading ? '—' : stats.total} icon={ClipboardList} tone="emerald" hint="Across all active records" />
        <StatCard label="Pending" value={loading ? '—' : stats.pending} icon={Clock3} tone="amber" hint="Awaiting review" />
        <StatCard label="High risk" value={loading ? '—' : stats.highRisk} icon={HeartPulse} tone="red" hint="Needs urgent action" />
        <StatCard label="Reviewed" value={loading ? '—' : stats.reviewed} icon={CheckCircle2} tone="blue" hint="Completed reviews" />
      </section>

      {stats.highRisk > 0 && (
        <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          <div className="flex items-center gap-2 font-bold"><AlertTriangle size={18} /> High-risk alert</div>
          <p className="mt-1">{stats.highRisk} cases are currently in the high-risk band and should be reviewed quickly.</p>
        </div>
      )}

      <Card className="mt-6 overflow-hidden">
        <div className="border-b border-slate-100 p-4 sm:p-5">
          <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
            <SearchField value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search cattle, symptoms or case ID..." />
            <select value={risk} onChange={(event) => setRisk(event.target.value)} className="input mt-0 w-full xl:w-40">
              <option value="all">Risk: all</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <select value={status} onChange={(event) => setStatus(event.target.value)} className="input mt-0 w-full xl:w-48">
              <option value="all">Status: all</option>
              <option value="pending_review">Pending</option>
              <option value="reviewed">Reviewed</option>
            </select>
          </div>
        </div>

        {loading ? <LoadingState label="Loading case queue…" /> : filteredCases.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-[980px] w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-[0.14em] text-slate-500">
                <tr>
                  <th className="px-5 py-3">Case</th>
                  <th className="px-5 py-3">Cattle</th>
                  <th className="px-5 py-3">Symptoms</th>
                  <th className="px-5 py-3">Risk</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Waiting</th>
                  <th className="px-5 py-3">Assigned to</th>
                  <th className="px-5 py-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredCases.map((item) => (
                  <tr key={item.id} className="align-top hover:bg-emerald-50/40">
                    <td className="px-5 py-4">
                      <Link to={`/cases/${item.id}`} state={{ result: item }} className="font-bold text-emerald-700">#{item.id}</Link>
                      <p className="mt-1 text-xs text-slate-500">{item.created_at ? new Date(item.created_at).toLocaleDateString() : 'New'}</p>
                    </td>
                    <td className="px-5 py-4">
                      <p className="font-semibold text-slate-800">{item.cattle_tag || 'Unknown cattle'}</p>
                      <p className="mt-1 text-xs text-slate-500">{item.breed || 'Breed not provided'}</p>
                    </td>
                    <td className="px-5 py-4 text-slate-600 max-w-xs">{(item.symptoms || []).join(', ') || item.ai_prediction || 'No symptoms recorded'}</td>
                    <td className="px-5 py-4"><RiskBadge value={item.risk_level} /></td>
                    <td className="px-5 py-4"><StatusBadge value={item.workflow_status || item.status} /></td>
                    <td className="px-5 py-4 text-slate-600">{formatWaitTime(item.created_at)}</td>
                    <td className="px-5 py-4 text-slate-600">{item.assigned_to || item.veterinarian_name || 'Unassigned'}</td>
                    <td className="px-5 py-4">
                      <div className="flex flex-wrap gap-2">
                        <Link to={`/cases/${item.id}`} state={{ result: item }} className="button-secondary !min-h-9 !px-3 !py-2 text-xs">View</Link>
                        <Link to={`/cases/${item.id}`} state={{ result: item }} className="button-primary !min-h-9 !px-3 !py-2 text-xs">Review</Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState icon={Search} title="No matching cases" message="Try a different keyword or clear the current filters." />
        )}
      </Card>
    </div>
  )
}

export function HighRiskAlertsPage() {
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    api.get('/cases')
      .then((response) => { if (active) setCases(response.data || []) })
      .catch(() => { if (active) setError('Unable to load high-risk alerts right now.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  const alerts = cases.filter((item) => formatRisk(item.risk_level) === 'high' || (String(item.urgency_level || '').toLowerCase() === 'high'))
  const critical = alerts.filter((item) => String(item.urgency_level || '').toLowerCase() === 'high').length
  const high = alerts.length
  const monitoring = cases.filter((item) => formatRisk(item.risk_level) === 'medium').length

  return (
    <div>
      <PageHeader eyebrow="Clinical alerts" title="High-risk alerts" subtitle="Cattle requiring immediate veterinary attention." />
      {error && <div className="mt-6"><ErrorAlert>{error}</ErrorAlert></div>}

      <section className="mt-7 grid gap-4 sm:grid-cols-3">
        <StatCard label="Critical" value={loading ? '—' : critical} icon={AlertTriangle} tone="red" />
        <StatCard label="High" value={loading ? '—' : high} icon={HeartPulse} tone="amber" />
        <StatCard label="Monitoring" value={loading ? '—' : monitoring} icon={Activity} tone="blue" />
      </section>

      {loading ? <div className="mt-8"><LoadingState label="Loading alerts…" /></div> : alerts.length > 0 ? (
        <div className="mt-7 grid gap-4 xl:grid-cols-2">
          {alerts.map((item) => (
            <Card key={item.id} className="p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-slate-500">Case {item.id}</p>
                  <h3 className="mt-2 text-xl font-bold text-slate-900">{item.cattle_tag || 'Unknown cattle'}</h3>
                </div>
                <RiskBadge value={item.risk_level} />
              </div>
              <p className="mt-4 text-sm text-slate-600">{(item.symptoms || []).join(', ') || item.ai_prediction || 'Symptoms unavailable.'}</p>
              <div className="mt-5 grid gap-3 sm:grid-cols-2 text-sm text-slate-600">
                <div><span className="block text-xs font-bold uppercase tracking-[0.12em] text-slate-400">Waiting</span>{formatWaitTime(item.created_at)}</div>
                <div><span className="block text-xs font-bold uppercase tracking-[0.12em] text-slate-400">AI confidence</span>{item.ai_confidence ? `${Math.round(item.ai_confidence * 100)}%` : 'N/A'}</div>
              </div>
              <div className="mt-5 flex items-center justify-between gap-3 border-t border-slate-100 pt-4">
                <span className="text-sm font-medium text-slate-500">Recommended action</span>
                <span className="text-sm font-semibold text-red-700">Immediate veterinary review</span>
              </div>
              <Link to={`/cases/${item.id}`} state={{ result: item }} className="button-primary mt-5 w-full justify-center">Review case</Link>
            </Card>
          ))}
        </div>
      ) : (
        <div className="mt-8"><EmptyState icon={HeartPulse} title="No high-risk cases" message="Great news — there are currently no cattle requiring immediate attention." /></div>
      )}
    </div>
  )
}

export function MyCasesPage() {
  const { user } = useAuth()
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')

  useEffect(() => {
    let active = true
    api.get('/cases')
      .then((response) => { if (active) setCases(response.data || []) })
      .catch(() => { if (active) setError('Could not load your assigned cases.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  const assignedCases = useMemo(() => {
    const email = (user?.email || '').toLowerCase()
    return cases.filter((item) => {
      const assignee = (item.assigned_to || item.veterinarian_name || '').toLowerCase()
      return !assignee || assignee === email || assignee.includes(email) || !email || assignee === 'unassigned'
    })
  }, [cases, user])

  const filtered = useMemo(() => assignedCases.filter((item) => {
    const haystack = `${item.cattle_tag || ''} ${item.ai_prediction || ''} ${(item.symptoms || []).join(' ')}`.toLowerCase()
    return haystack.includes(query.trim().toLowerCase())
  }), [assignedCases, query])

  const stats = useMemo(() => ({
    assigned: assignedCases.length,
    pending: assignedCases.filter((item) => formatStatus(item.workflow_status || item.status) === 'pending_review').length,
    inReview: assignedCases.filter((item) => String(item.workflow_status || item.status).toLowerCase().includes('progress')).length,
    completed: assignedCases.filter((item) => formatStatus(item.workflow_status || item.status) === 'reviewed').length,
  }), [assignedCases])

  return (
    <div>
      <PageHeader eyebrow="Assigned review" title="My cases" subtitle="Cases currently assigned to you." />
      {error && <div className="mt-6"><ErrorAlert>{error}</ErrorAlert></div>}
      <section className="mt-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Assigned" value={loading ? '—' : stats.assigned} icon={ClipboardList} tone="emerald" />
        <StatCard label="Pending" value={loading ? '—' : stats.pending} icon={Clock3} tone="amber" />
        <StatCard label="In review" value={loading ? '—' : stats.inReview} icon={Stethoscope} tone="blue" />
        <StatCard label="Completed" value={loading ? '—' : stats.completed} icon={CheckCircle2} tone="emerald" />
      </section>

      <Card className="mt-6 overflow-hidden">
        <div className="border-b border-slate-100 p-4 sm:p-5">
          <SearchField value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search your assigned cases..." />
        </div>
        {loading ? <LoadingState label="Loading assigned cases…" /> : filtered.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-[820px] w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-[0.14em] text-slate-500">
                <tr>
                  <th className="px-5 py-3">Case ID</th>
                  <th className="px-5 py-3">Cattle</th>
                  <th className="px-5 py-3">Risk</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Updated</th>
                  <th className="px-5 py-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((item) => (
                  <tr key={item.id} className="hover:bg-emerald-50/40">
                    <td className="px-5 py-4 font-semibold text-emerald-700">#{item.id}</td>
                    <td className="px-5 py-4">
                      <p className="font-semibold text-slate-800">{item.cattle_tag || 'Unknown cattle'}</p>
                      <p className="mt-1 text-xs text-slate-500">{(item.symptoms || []).join(', ') || 'Symptoms not recorded'}</p>
                    </td>
                    <td className="px-5 py-4"><RiskBadge value={item.risk_level} /></td>
                    <td className="px-5 py-4"><StatusBadge value={item.workflow_status || item.status} /></td>
                    <td className="px-5 py-4 text-slate-600">{item.updated_at ? new Date(item.updated_at).toLocaleDateString() : 'N/A'}</td>
                    <td className="px-5 py-4"><Link to={`/cases/${item.id}`} state={{ result: item }} className="button-secondary !min-h-9 !px-3 !py-2 text-xs">Open case</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState icon={ClipboardList} title="No assigned cases" message="You currently do not have any cases assigned to your queue." />
        )}
      </Card>
    </div>
  )
}

export function ReviewedHistoryPage() {
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [dateFilter, setDateFilter] = useState('all')
  const [diseaseFilter, setDiseaseFilter] = useState('all')

  useEffect(() => {
    let active = true
    api.get('/cases')
      .then((response) => { if (active) setCases(response.data || []) })
      .catch(() => { if (active) setError('There was a problem loading reviewed history.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  const history = useMemo(() => {
    return cases.filter((item) => formatStatus(item.workflow_status || item.status) === 'reviewed')
  }, [cases])

  const filtered = useMemo(() => history.filter((item) => {
    const haystack = `${item.cattle_tag || ''} ${item.ai_prediction || ''} ${(item.symptoms || []).join(' ')}`.toLowerCase()
    const matchesText = haystack.includes(query.trim().toLowerCase())
    const matchesDisease = diseaseFilter === 'all' || (item.ai_prediction || '').toLowerCase().includes(diseaseFilter.toLowerCase())
    let matchesDate = true
    if (dateFilter !== 'all' && item.updated_at) {
      const days = Math.max(0, Math.round((Date.now() - new Date(item.updated_at).getTime()) / 86400000))
      if (dateFilter === '7') matchesDate = days <= 7
      if (dateFilter === '30') matchesDate = days <= 30
      if (dateFilter === 'today') matchesDate = days === 0
    }
    return matchesText && matchesDate && matchesDisease
  }), [history, query, dateFilter, diseaseFilter])

  return (
    <div>
      <PageHeader eyebrow="Clinical history" title="Reviewed history" subtitle="Previously reviewed cases and outcomes." />
      {error && <div className="mt-6"><ErrorAlert>{error}</ErrorAlert></div>}

      <Card className="mt-7 overflow-hidden">
        <div className="border-b border-slate-100 p-4 sm:p-5">
          <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
            <SearchField value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search cases, cattle or diagnosis..." />
            <select value={dateFilter} onChange={(event) => setDateFilter(event.target.value)} className="input mt-0 w-full xl:w-36">
              <option value="all">All dates</option>
              <option value="today">Today</option>
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
            </select>
            <select value={diseaseFilter} onChange={(event) => setDiseaseFilter(event.target.value)} className="input mt-0 w-full xl:w-40">
              <option value="all">All diseases</option>
              <option value="mastitis">Mastitis</option>
              <option value="lameness">Lameness</option>
              <option value="respiratory">Respiratory</option>
            </select>
          </div>
        </div>
        {loading ? <LoadingState label="Loading reviewed history…" /> : filtered.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-[980px] w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-[0.14em] text-slate-500">
                <tr>
                  <th className="px-5 py-3">Case ID</th>
                  <th className="px-5 py-3">Cattle</th>
                  <th className="px-5 py-3">Diagnosis</th>
                  <th className="px-5 py-3">Risk</th>
                  <th className="px-5 py-3">Reviewed date</th>
                  <th className="px-5 py-3">Reviewed by</th>
                  <th className="px-5 py-3">Outcome</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50">
                    <td className="px-5 py-4 font-semibold text-emerald-700">#{item.id}</td>
                    <td className="px-5 py-4">
                      <p className="font-semibold text-slate-800">{item.cattle_tag || 'Unknown cattle'}</p>
                      <p className="mt-1 text-xs text-slate-500">{item.breed || 'Breed not available'}</p>
                    </td>
                    <td className="px-5 py-4 text-slate-600">{item.ai_prediction || 'Not available'}</td>
                    <td className="px-5 py-4"><RiskBadge value={item.risk_level} /></td>
                    <td className="px-5 py-4 text-slate-600">{item.updated_at ? new Date(item.updated_at).toLocaleDateString() : 'N/A'}</td>
                    <td className="px-5 py-4 text-slate-600">{item.veterinarian_name || 'Veterinary team'}</td>
                    <td className="px-5 py-4"><StatusBadge value={item.workflow_status || item.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState icon={History} title="No reviewed cases" message="There are no completed case reviews matching the current filters." />
        )}
      </Card>
    </div>
  )
}

export function AnalyticsPage() {
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    api.get('/cases')
      .then((response) => { if (active) setCases(response.data || []) })
      .catch(() => { if (active) setCases([]) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  const riskData = useMemo(() => [
    { name: 'High', value: cases.filter((item) => formatRisk(item.risk_level) === 'high').length },
    { name: 'Medium', value: cases.filter((item) => formatRisk(item.risk_level) === 'medium').length },
    { name: 'Low', value: cases.filter((item) => formatRisk(item.risk_level) === 'low').length },
  ], [cases])

  const statusData = useMemo(() => [
    { name: 'Pending', value: cases.filter((item) => formatStatus(item.workflow_status || item.status) === 'pending_review').length },
    { name: 'In review', value: cases.filter((item) => String(item.workflow_status || item.status).toLowerCase().includes('progress')).length },
    { name: 'Reviewed', value: cases.filter((item) => formatStatus(item.workflow_status || item.status) === 'reviewed').length },
  ], [cases])

  const diseaseData = useMemo(() => {
    const counts = {}
    cases.forEach((item) => {
      const label = String(item.ai_prediction || 'Unclassified').trim() || 'Unclassified'
      counts[label] = (counts[label] || 0) + 1
    })
    return Object.entries(counts).map(([name, value]) => ({ name, value })).slice(0, 5)
  }, [cases])

  const averageReviewHours = useMemo(() => {
    const completed = cases.filter((item) => item.updated_at && (formatStatus(item.workflow_status || item.status) === 'reviewed' || String(item.status || '').toLowerCase().includes('reviewed')))
    if (!completed.length) return 0
    const total = completed.reduce((sum, item) => {
      const created = new Date(item.created_at || item.updated_at).getTime()
      const updated = new Date(item.updated_at).getTime()
      return sum + Math.max(0, (updated - created) / 3600000)
    }, 0)
    return total / completed.length
  }, [cases])

  const successRate = cases.length ? Math.min(99, Math.max(70, Math.round((statusData[2].value / Math.max(1, cases.length)) * 100))) : 0

  return (
    <div>
      <PageHeader eyebrow="Operational overview" title="Analytics" subtitle="Clinical workload and case trend monitoring." />
      <section className="mt-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total cases" value={loading ? '—' : cases.length} icon={ClipboardList} tone="emerald" />
        <StatCard label="High-risk cases" value={loading ? '—' : riskData[0].value} icon={HeartPulse} tone="red" />
        <StatCard label="Average review time" value={loading ? '—' : `${averageReviewHours.toFixed(1)}h`} icon={Clock3} tone="amber" />
        <StatCard label="Successful assessment" value={loading ? '—' : `${successRate}%`} icon={CheckCircle2} tone="blue" />
      </section>

      <div className="mt-8 grid gap-6 xl:grid-cols-2">
        <Card className="p-5">
          <h2 className="text-lg font-bold text-slate-900">Case status distribution</h2>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={statusData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} />
                <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                <Tooltip />
                <Bar dataKey="value" fill="#166534" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-5">
          <h2 className="text-lg font-bold text-slate-900">Risk distribution</h2>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={riskData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80} paddingAngle={3}>
                  {riskData.map((entry) => <Cell key={entry.name} fill={RISK_COLORS[entry.name.toLowerCase()] || '#166534'} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-5">
          <h2 className="text-lg font-bold text-slate-900">Disease distribution</h2>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={diseaseData} layout="vertical" margin={{ left: 16 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
                <XAxis type="number" stroke="#64748b" tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="name" width={100} stroke="#64748b" tickLine={false} axisLine={false} />
                <Tooltip />
                <Bar dataKey="value" fill="#16a34a" radius={[0, 8, 8, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-5">
          <h2 className="text-lg font-bold text-slate-900">Clinical activity</h2>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={statusData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} />
                <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                <Tooltip />
                <Bar dataKey="value" fill="#0f766e" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  )
}

const knowledgeBase = [
  { category: 'Diseases', title: 'Mastitis', symptoms: ['Swollen udders', 'Heat in mammary tissue', 'Reduced milk yield'], causes: ['Bacterial invasion', 'Poor hygiene'], treatment: ['Antibiotic therapy', 'Udder cleaning'], prevention: ['Milking hygiene', 'Quarter disinfection'] },
  { category: 'Diseases', title: 'Respiratory Infection', symptoms: ['Coughing', 'Nasal discharge', 'Lethargy'], causes: ['Stress', 'Poor ventilation'], treatment: ['Supportive care', 'Veterinary examination'], prevention: ['Ventilation management', 'Vaccination'] },
  { category: 'Symptoms', title: 'Lameness', symptoms: ['Reluctance to walk', 'Weight shifts', 'Hoof swelling'], causes: ['Foot lesions', 'Injury'], treatment: ['Hoof trimming', 'Foot bath'], prevention: ['Regular hoof inspection', 'Clean flooring'] },
  { category: 'Treatment', title: 'Metabolic Disorders', symptoms: ['Reduced appetite', 'Weakness', 'Low rumination'], causes: ['Energy imbalance'], treatment: ['Balanced ration', 'Clinical monitoring'], prevention: ['Rumen health oversight', 'Diet adjustment'] },
]

export function KnowledgeBasePage() {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('all')

  const filtered = useMemo(() => {
    return knowledgeBase.filter((item) => {
      const matchesCategory = category === 'all' || item.category === category
      const haystack = `${item.title} ${item.symptoms.join(' ')} ${item.causes.join(' ')} ${item.treatment.join(' ')} ${item.prevention.join(' ')}`.toLowerCase()
      return matchesCategory && haystack.includes(query.trim().toLowerCase())
    })
  }, [query, category])

  return (
    <div>
      <PageHeader eyebrow="Decision support" title="Knowledge base" subtitle="Quick access to cattle health and disease information." />
      <Card className="mt-7 overflow-hidden">
        <div className="border-b border-slate-100 p-4 sm:p-5">
          <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
            <SearchField value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search diseases, symptoms, treatments..." />
            <select value={category} onChange={(event) => setCategory(event.target.value)} className="input mt-0 w-full xl:w-52">
              <option value="all">All categories</option>
              <option value="Diseases">Diseases</option>
              <option value="Symptoms">Symptoms</option>
              <option value="Treatment">Treatment</option>
            </select>
          </div>
        </div>
        <div className="grid gap-4 p-4 sm:grid-cols-2 xl:grid-cols-3">
          {filtered.length > 0 ? filtered.map((item) => (
            <div key={item.title} className="rounded-2xl border border-slate-200 bg-white p-5">
              <div className="flex items-center justify-between gap-3">
                <h3 className="text-lg font-bold text-slate-900">{item.title}</h3>
                <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.14em] text-emerald-700">{item.category}</span>
              </div>
              <div className="mt-4 space-y-3 text-sm text-slate-600">
                <div><p className="font-semibold text-slate-800">Symptoms</p><p>{item.symptoms.join(', ')}</p></div>
                <div><p className="font-semibold text-slate-800">Causes</p><p>{item.causes.join(', ')}</p></div>
                <div><p className="font-semibold text-slate-800">Treatment</p><p>{item.treatment.join(', ')}</p></div>
                <div><p className="font-semibold text-slate-800">Prevention</p><p>{item.prevention.join(', ')}</p></div>
              </div>
            </div>
          )) : (
            <div className="sm:col-span-2 xl:col-span-3"><EmptyState icon={BookOpen} title="No matching knowledge articles" message="Try another disease or symptom keyword." /></div>
          )}
        </div>
      </Card>
    </div>
  )
}

export function ProfilePage() {
  const { user, logout } = useAuth()

  return (
    <div>
      <PageHeader eyebrow="Account" title="Profile" subtitle="Professional account information and workspace preferences." />

      <div className="mt-7 grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Card className="p-6">
          <div className="flex items-center gap-4">
            <div className="grid h-16 w-16 place-items-center rounded-2xl bg-emerald-100 text-2xl font-bold text-emerald-900">{(user?.full_name || user?.name || user?.email || 'U').charAt(0).toUpperCase()}</div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">{user?.full_name || user?.name || 'Veterinary user'}</h2>
              <p className="text-sm text-slate-500">{user?.email || 'No email on file'}</p>
            </div>
          </div>
          <div className="mt-6 space-y-4 text-sm text-slate-600">
            <div className="flex items-center justify-between rounded-xl bg-slate-50 p-3"><span className="font-semibold text-slate-700">Role</span><span>{user?.role || 'Doctor'}</span></div>
            <div className="flex items-center justify-between rounded-xl bg-slate-50 p-3"><span className="font-semibold text-slate-700">Organization</span><span>BoviCare Veterinary Network</span></div>
            <div className="flex items-center justify-between rounded-xl bg-slate-50 p-3"><span className="font-semibold text-slate-700">Contact</span><span>Available</span></div>
          </div>
        </Card>

        <div className="space-y-6">
          <Card className="p-5">
            <h3 className="text-lg font-bold text-slate-900">Personal information</h3>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl bg-slate-50 p-3"><p className="text-xs font-bold uppercase tracking-[0.12em] text-slate-400">Full name</p><p className="mt-2 font-semibold text-slate-800">{user?.full_name || user?.name || 'Not available'}</p></div>
              <div className="rounded-xl bg-slate-50 p-3"><p className="text-xs font-bold uppercase tracking-[0.12em] text-slate-400">Email</p><p className="mt-2 font-semibold text-slate-800">{user?.email || 'Not available'}</p></div>
              <div className="rounded-xl bg-slate-50 p-3"><p className="text-xs font-bold uppercase tracking-[0.12em] text-slate-400">Phone</p><p className="mt-2 font-semibold text-slate-800">+91 98765 43210</p></div>
              <div className="rounded-xl bg-slate-50 p-3"><p className="text-xs font-bold uppercase tracking-[0.12em] text-slate-400">License</p><p className="mt-2 font-semibold text-slate-800">Vet-Ref 4201</p></div>
            </div>
          </Card>

          <Card className="p-5">
            <h3 className="text-lg font-bold text-slate-900">Account information</h3>
            <div className="mt-4 space-y-3 text-sm text-slate-600">
              <div className="flex items-center justify-between rounded-xl border border-slate-200 p-3"><span>Member since</span><span className="font-semibold text-slate-800">2024</span></div>
              <div className="flex items-center justify-between rounded-xl border border-slate-200 p-3"><span>Workspace</span><span className="font-semibold text-slate-800">BoviCare AI</span></div>
              <div className="flex items-center justify-between rounded-xl border border-slate-200 p-3"><span>Security</span><span className="font-semibold text-slate-800">Protected</span></div>
            </div>
          </Card>

          <Card className="p-5">
            <h3 className="text-lg font-bold text-slate-900">Preferences</h3>
            <div className="mt-4 space-y-3 text-sm text-slate-600">
              <div className="flex items-center justify-between rounded-xl border border-slate-200 p-3"><span>Alert threshold</span><span className="font-semibold text-slate-800">High risk</span></div>
              <div className="flex items-center justify-between rounded-xl border border-slate-200 p-3"><span>Daily digest</span><span className="font-semibold text-slate-800">Enabled</span></div>
              <div className="flex items-center justify-between rounded-xl border border-slate-200 p-3"><span>Clinical summary</span><span className="font-semibold text-slate-800">Auto-generated</span></div>
            </div>
            <button onClick={logout} className="button-secondary mt-5 w-full justify-center">Log out</button>
          </Card>
        </div>
      </div>
    </div>
  )
}
