import { ArrowLeft, Camera, CheckCircle2, FlaskConical, ImageOff, Save, Stethoscope } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { Badge, Card, ErrorAlert, LoadingState } from '../components/ui'
import { api } from '../lib/api'
import { formatIstDateTime, getWaitHours } from '../lib/dateTime'

function workflowLabel(status) {
  const value = String(status || '').toLowerCase()
  if (value.includes('progress')) return 'IN_PROGRESS'
  if (value.includes('complete') || value.includes('reviewed')) return 'COMPLETED'
  return 'PENDING'
}

// Authoritative persisted model identifiers. Each model is displayed separately.
const MODEL_NAMES = {
  general: 'general_cattle_disease',
  mastitis: 'mastitis_specialist',
  cattleImage: 'cattle_image_classifier',
  lumpy: 'lumpy_skin_specialist',
}

function RiskBar({ probability }) {
  const pct = Math.round((probability || 0) * 100)
  const color = pct >= 70 ? 'bg-red-500' : pct >= 40 ? 'bg-amber-400' : 'bg-emerald-500'
  return (
    <div className="mt-2 h-1.5 rounded-full bg-slate-100">
      <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${pct}%` }} />
    </div>
  )
}

function PredictionRow({ rank, label, probability }) {
  return (
    <div className="flex items-center gap-4 rounded-xl border border-slate-100 p-4">
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-100 text-sm font-bold text-slate-600">{rank}</span>
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-3">
          <p className="font-semibold text-slate-800 capitalize">{String(label || '').replace(/-/g, ' ')}</p>
          {typeof probability === 'number' && <span className="text-xs font-semibold text-slate-400">{(probability * 100).toFixed(1)}%</span>}
        </div>
        <RiskBar probability={probability} />
      </div>
    </div>
  )
}

// Renders the persisted results of a single model. Models are never merged.
function GeneralModelSection({ model }) {
  if (!model) return null
  const predictions = (model.predictions || []).slice(0, 5)
  if (!predictions.length) return null
  return (
    <Card className="p-5 sm:col-span-2">
      <div className="flex items-center gap-2">
        <Stethoscope className="text-emerald-700" size={20} />
        <div>
          <h2 className="font-bold">Symptom AI — probable diseases</h2>
          <p className="mt-0.5 text-xs text-slate-500">{model.model_name}{model.model_version ? ` — ${model.model_version}` : ''}</p>
        </div>
        <div className="ml-auto"><Badge value={model.risk_level} /></div>
      </div>
      <div className="mt-4 space-y-3">
        {predictions.map((p, index) => (
          <PredictionRow key={`${model.model_name}-${p.rank}-${index}`} rank={p.rank} label={p.disease_label} probability={p.probability} />
        ))}
      </div>
    </Card>
  )
}

function SingleModelSection({ title, icon: Icon, iconClass, model, label }) {
  if (!model || !model.predictions?.length) return null
  const prediction = model.predictions[0]
  return (
    <Card className="p-5">
      <div className="flex items-center gap-2">
        <Icon className={iconClass} size={20} />
        <div>
          <h2 className="font-bold">{title}</h2>
          <p className="mt-0.5 text-xs text-slate-500">{model.model_name}{model.model_version ? ` — ${model.model_version}` : ''}</p>
        </div>
      </div>
      <dl className="mt-4 space-y-3">
        <div>
          <dt className="text-xs font-bold uppercase tracking-wider text-slate-400">{label}</dt>
          <dd className="mt-1 font-semibold capitalize text-slate-800">{String(prediction.disease_label || '').replace(/-/g, ' ')}</dd>
        </div>
        <div>
          <dt className="text-xs font-bold uppercase tracking-wider text-slate-400">Probability</dt>
          <dd className="mt-1 text-sm text-slate-700">{(prediction.probability * 100).toFixed(1)}%</dd>
          <RiskBar probability={prediction.probability} />
        </div>
        <div>
          <dt className="text-xs font-bold uppercase tracking-wider text-slate-400">Risk level</dt>
          <dd className="mt-1"><Badge value={model.risk_level} /></dd>
        </div>
      </dl>
    </Card>
  )
}

export default function VeterinaryCaseDetails() {
  const { caseId } = useParams()
  const location = useLocation()
  const [item, setItem] = useState(location.state?.result)
  const [message, setMessage] = useState('')
  const [notes, setNotes] = useState(location.state?.result?.private_clinical_notes || location.state?.result?.veterinarian_notes || '')
  const [farmerAdvice, setFarmerAdvice] = useState(location.state?.result?.farmer_advice || '')
  const [reviewStatus, setReviewStatus] = useState(location.state?.result?.status || 'pending_review')
  const [error, setError] = useState('')
  const [predictionModels, setPredictionModels] = useState([])
  const [predictionsLoading, setPredictionsLoading] = useState(true)
  const [predictionsError, setPredictionsError] = useState('')
  const [notifications, setNotifications] = useState([])
  const [timeline, setTimeline] = useState([])
  const [imageUrl, setImageUrl] = useState('')

  // Load the case if it was not passed via router state.
  useEffect(() => {
    if (!item) {
      api.get('/cases')
        .then(response => setItem(response.data.find(caseItem => String(caseItem.id) === caseId)))
        .catch(() => setError('Could not retrieve this case from the API.'))
    }
  }, [caseId, item])

  // Load persisted AI predictions for this case. Failures are non-destructive.
  useEffect(() => {
    if (!caseId) return undefined
    let active = true
    setPredictionsLoading(true)
    setPredictionsError('')
    api.get(`/cases/${caseId}/predictions`)
      .then(response => { if (active) setPredictionModels(response.data?.models || []) })
      .catch(() => { if (active) setPredictionsError('AI predictions could not be loaded. The case details are still available.') })
      .finally(() => { if (active) setPredictionsLoading(false) })
    return () => { active = false }
  }, [caseId])

  useEffect(() => {
    if (!caseId) return undefined
    let active = true
    let objectUrl = ''
    api.get(`/cases/${caseId}/image`, { responseType: 'blob' })
      .then(response => {
        objectUrl = URL.createObjectURL(response.data)
        if (active) setImageUrl(objectUrl)
      })
      .catch(() => { if (active) setImageUrl('') })
    return () => {
      active = false
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [caseId])

  useEffect(() => {
    if (!caseId) return undefined
    api.get(`/cases/${caseId}/notifications`).then(response => setNotifications(response.data || [])).catch(() => setNotifications([]))
    return undefined
  }, [caseId])

  useEffect(() => {
    if (!caseId) return undefined
    api.get(`/cases/${caseId}/events`).then(response => setTimeline(response.data || [])).catch(() => setTimeline([]))
    return undefined
  }, [caseId])

  // Prefill the doctor notes textarea with previously saved veterinarian notes.
  useEffect(() => {
    if (item?.private_clinical_notes || item?.veterinarian_notes) setNotes(current => current || (item.private_clinical_notes || item.veterinarian_notes || ''))
    if (item?.farmer_advice) setFarmerAdvice(current => current || item.farmer_advice)
  }, [item])

  if (error) return <ErrorAlert>{error}</ErrorAlert>
  if (!item) return <LoadingState label="Loading clinical case…" />

  async function accept() {
    try {
      setMessage('')
      const response = await api.post(`/cases/${item.id}/accept`)
      setItem(response.data)
      setReviewStatus(response.data.status)
      setMessage('Case accepted and moved into active review.')
    } catch (requestError) {
      setMessage(requestError.response?.data?.detail || 'This case is no longer available for acceptance.')
    }
  }

  async function review() {
    if (!farmerAdvice.trim()) { setMessage('Add farmer-facing advice before submitting the review.'); return }
    try {
      const response = await api.put(`/cases/${item.id}/review`, {
        farmer_advice: farmerAdvice,
        private_clinical_notes: notes,
        veterinarian_notes: notes,
        review_status: reviewStatus,
      })
      setItem(response.data)
      setMessage('Veterinary advice saved and the case status was updated.')
    } catch (requestError) {
      setMessage(requestError.response?.data?.detail || 'Could not save the clinical review.')
    }
  }

  const context = location.state?.context || {}
  const generalModel = predictionModels.find(m => m.model_name === MODEL_NAMES.general) || null
  const mastitisModel = predictionModels.find(m => m.model_name === MODEL_NAMES.mastitis) || null
  const cattleImageModel = predictionModels.find(m => m.model_name === MODEL_NAMES.cattleImage) || null
  const lumpyModel = predictionModels.find(m => m.model_name === MODEL_NAMES.lumpy) || null
  const hasAnyModel = Boolean(generalModel || mastitisModel || cattleImageModel || lumpyModel)
  const waitingHours = getWaitHours(item.created_at)

  return (
    <div>
      <Link to="/veterinary" className="inline-flex items-center gap-1 text-sm font-bold text-emerald-700"><ArrowLeft size={16} />All clinical cases</Link>
      <div className="mt-5 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Clinical case review</p>
          <h1 className="mt-2 text-3xl font-bold text-emerald-950">{item.cattle_tag}</h1>
        </div>
        <Badge value={item.risk_level} />
      </div>
      <div className="mt-7 grid gap-6 xl:grid-cols-[1fr_.72fr]">
        <div className="grid gap-6 sm:grid-cols-2">
          <Info title="Farmer submitted information" rows={[
            ['Cattle ID', item.cattle_tag || 'Not provided'],
            ['Cattle name', item.cattle_name || context.cattleName || 'Not provided'],
            ['Breed', item.breed || 'Not provided'],
            ['Age', item.age_years ?? 'Not provided'],
            ['Sex', item.gender || context.gender || 'Not provided'],
            ['Temperature', item.temperature_c ? `${item.temperature_c} °C` : 'Not provided'],
            ['Symptoms', (item.symptoms || []).join(', ') || 'Not provided'],
            ['Farmer notes', item.notes || context.notes || 'Not provided'],
            ['Submitted', formatIstDateTime(item.created_at)],
          ]} />
          <Info title="AI assessment" rows={[
            ['AI suggestion', item.ai_prediction || 'Not provided'],
            ['Risk level', item.risk_level || 'Not provided'],
            ['Urgency level', (item.urgency_level || 'LOW').toUpperCase()],
            ['Urgency score', `${Math.round(item.urgency_score || 0)}/100`],
            ['Waiting time', `${waitingHours} hours`],
            ['Status', workflowLabel(item.workflow_status || item.status)],
          ]} />
          <Card className="p-5">
            <h2 className="font-bold">Uploaded image</h2>
            {imageUrl
              ? <img className="mt-4 h-44 w-full rounded-xl object-cover" src={imageUrl} alt="Uploaded cattle" />
              : <div className="mt-4 flex h-44 flex-col items-center justify-center rounded-xl bg-slate-50 text-sm text-slate-500"><ImageOff className="mb-2" />No image stored</div>}
          </Card>

          {notifications.length > 0 && <Card className="border-red-200 bg-red-50 p-5 sm:col-span-2"><h2 className="font-bold text-red-950">High-risk notification</h2><p className="mt-2 text-sm text-red-900">A doctor notification event was generated. Status: <strong>{notifications[0].status}</strong>.</p></Card>}

          <Card className="p-5 sm:col-span-2">
            <h2 className="font-bold">Case timeline</h2>
            {timeline.length ? (
              <ol className="mt-4 space-y-3">
                {timeline.map(entry => (
                  <li key={entry.id} className="border-l border-slate-200 pl-4">
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-semibold text-slate-800">{entry.title}</p>
                      <span className="text-xs text-slate-500">{formatIstDateTime(entry.created_at)}</span>
                    </div>
                    {entry.detail && <p className="mt-1 text-sm text-slate-600">{entry.detail}</p>}
                  </li>
                ))}
              </ol>
            ) : (
              <p className="mt-3 text-sm text-slate-500">No timeline events recorded for this case yet.</p>
            )}
          </Card>

          {/* Persisted AI predictions. Each model is shown independently. */}
          {predictionsLoading && <Card className="p-5 sm:col-span-2"><LoadingState label="Loading AI predictions…" /></Card>}

          {!predictionsLoading && predictionsError && (
            <Card className="p-5 sm:col-span-2"><ErrorAlert>{predictionsError}</ErrorAlert></Card>
          )}

          {!predictionsLoading && !predictionsError && !hasAnyModel && (
            <Card className="p-5 sm:col-span-2">
              <h2 className="font-bold">AI predictions</h2>
              <p className="mt-2 text-sm text-slate-500">No persisted AI prediction results are available for this case yet.</p>
            </Card>
          )}

          <GeneralModelSection model={generalModel} />
          <SingleModelSection title="Mastitis AI" icon={FlaskConical} iconClass="text-blue-600" model={mastitisModel} label="Prediction" />
          <SingleModelSection title="Cattle image AI" icon={Camera} iconClass="text-violet-600" model={cattleImageModel} label="Predicted label" />
          <SingleModelSection title="Lumpy skin AI" icon={Camera} iconClass="text-violet-600" model={lumpyModel} label="Predicted label" />

          {hasAnyModel && (
            <Card className="border-amber-200 bg-amber-50 p-5 sm:col-span-2">
              <p className="text-sm font-semibold text-amber-950">Each model above is independent. Probabilities from different models are never combined or averaged.</p>
            </Card>
          )}
        </div>

        <Card className="h-fit p-6">
          <p className="eyebrow">Doctor review</p>
          <h2 className="mt-2 text-xl font-bold">Clinical decision</h2>

          {item.farmer_advice && (
            <div className="mt-5 rounded-xl bg-emerald-50 p-4">
              <p className="text-xs font-bold uppercase tracking-wider text-emerald-700">Existing farmer-facing advice</p>
              <p className="mt-1 whitespace-pre-wrap text-sm text-slate-700">{item.farmer_advice}</p>
            </div>
          )}

          <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Doctor review</p>
            <p className="mt-1 text-sm text-slate-700">Use the farmer-submitted details above as the source-of-truth and add a clinician-facing recommendation below.</p>
          </div>

          <button onClick={accept} className="button-primary mt-5 w-full"><CheckCircle2 size={17} />Accept & Review</button>
          <label className="mt-5 block"><span className="label">Review status</span><select value={reviewStatus} onChange={event => setReviewStatus(event.target.value)} className="input"><option value="in_progress">In progress</option><option value="reviewed">Completed</option></select></label>
          <label className="mt-4 block"><span className="label">Farmer-facing advice</span><textarea value={farmerAdvice} onChange={event => setFarmerAdvice(event.target.value)} className="input resize-y" rows="4" placeholder="Guidance for the farmer" /></label>
          <label className="mt-4 block"><span className="label">Private clinical notes</span><textarea value={notes} onChange={event => setNotes(event.target.value)} className="input resize-y" rows="4" placeholder="Internal clinical notes visible only to the veterinarian" /></label>
          <button onClick={review} className="button-primary mt-5 w-full"><Save size={17} />Submit Advice</button>
          {message && <p className="mt-3 text-xs leading-5 text-amber-700">{message}</p>}
          <div className="mt-6 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-900"><CheckCircle2 className="mb-2" size={18} />Private notes remain internal; only farmer-facing advice is shown to the farmer.</div>
        </Card>
      </div>
    </div>
  )
}

function Info({ title, rows }) {
  return (
    <Card className="p-5">
      <h2 className="font-bold">{title}</h2>
      <dl className="mt-4 space-y-3">
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt className="text-xs font-bold uppercase tracking-wider text-slate-400">{label}</dt>
            <dd className="mt-1 text-sm text-slate-700">{value}</dd>
          </div>
        ))}
      </dl>
    </Card>
  )
}