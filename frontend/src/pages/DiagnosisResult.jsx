import { ArrowLeft, Download } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { Card, ErrorAlert, LoadingState } from '../components/ui'
import { api } from '../lib/api'
import { farmerDiseaseLabel, farmerRiskLabel, farmerSymptomLabel } from '../lib/farmerText'
import { downloadCaseReport } from '../lib/reports'
import { useLanguage } from '../auth/LanguageContext'

function predictionGroups(locationState, apiModels, language) {
  const groups = new Map()
  const add = (key, englishTitle, marathiTitle, model) => {
    if (!model?.predictions?.length || groups.has(key)) return
    groups.set(key, {
      title: language === 'mr' ? marathiTitle : englishTitle,
      risk: model.risk_level,
      predictions: model.predictions.slice(0, 5).map((item, index) => ({
        rank: item.rank || index + 1,
        label: item.label || item.disease || item.disease_label,
        probability: item.probability,
      })),
    })
  }

  add('general_cattle_disease', 'Possible diseases based on symptoms', 'लक्षणांवर आधारित संभाव्य आजार', locationState?.generalResult)
  if (locationState?.mastitisResult?.condition) {
    const item = locationState.mastitisResult
    add('mastitis_specialist', 'Estimate based on milk information', 'दुधाच्या माहितीवर आधारित अंदाज', {
      risk_level: item.risk_level,
      predictions: [{ rank: 1, label: item.condition, probability: item.probability }],
    })
  }
  add('cattle_image_classifier', 'Possible diseases based on image', 'फोटोवर आधारित संभाव्य आजार', locationState?.imageResult)

  for (const model of apiModels) {
    if (model.model_name === 'general_cattle_disease') {
      add(model.model_name, 'Possible diseases based on symptoms', 'लक्षणांवर आधारित संभाव्य आजार', model)
    } else if (model.model_name === 'mastitis_specialist') {
      add(model.model_name, 'Estimate based on milk information', 'दुधाच्या माहितीवर आधारित अंदाज', model)
    } else if (model.model_name === 'cattle_image_classifier') {
      add(model.model_name, 'Possible diseases based on image', 'फोटोवर आधारित संभाव्य आजार', model)
    } else if (model.model_name === 'lumpy_skin_specialist') {
      add(model.model_name, 'Skin estimate based on image', 'फोटोवर आधारित त्वचेचा अंदाज', model)
    }
  }
  return [...groups.values()]
}

function ResultsGroup({ group, language }) {
  const formatProbability = probability => `${Number((probability * 100).toFixed(4)).toString()}%`
  return (
    <section className="mt-7 border-t border-slate-200 pt-6">
      <h2 className="text-lg font-bold text-slate-900">{group.title}</h2>
      <p className="mt-2 text-base text-slate-700">
        {language === 'mr' ? 'जोखीम पातळी:' : 'Risk Level:'} {farmerRiskLabel(group.risk, language)}
      </p>
      <ol className="mt-3 space-y-2">
        {group.predictions.map(item => (
          <li key={`${item.rank}-${item.label}`} className="flex items-baseline justify-between gap-4 rounded-md bg-slate-50 px-4 py-3">
            <span className="text-base font-medium text-slate-900">{item.rank}. {farmerDiseaseLabel(item.label, language)}</span>
            <span className="shrink-0 text-sm font-semibold text-slate-700">{formatProbability(item.probability)}</span>
          </li>
        ))}
      </ol>
    </section>
  )
}

export default function DiagnosisResult() {
  const { caseId } = useParams()
  const location = useLocation()
  const { language, translate } = useLanguage()
  const [result, setResult] = useState(location.state?.result || null)
  const [apiModels, setApiModels] = useState([])
  const [error, setError] = useState('')
  const [reportError, setReportError] = useState('')
  const [loading, setLoading] = useState(!location.state?.result)

  useEffect(() => {
    if (!caseId || caseId === 'image') return undefined
    let active = true
    Promise.all([api.get(`/cases/${caseId}`), api.get(`/cases/${caseId}/predictions`)])
      .then(([caseResponse, predictionResponse]) => {
        if (!active) return
        setResult(current => ({ ...current, ...caseResponse.data }))
        setApiModels(predictionResponse.data.models || [])
      })
      .catch(() => { if (active) setError('तपासणीची माहिती मिळवता आली नाही.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [caseId])

  async function download() {
    try {
      setReportError('')
      await downloadCaseReport(result.id, language)
    } catch {
      setReportError(translate('Could not download the report. Please try again.', 'अहवाल डाउनलोड करता आला नाही. कृपया पुन्हा प्रयत्न करा.'))
    }
  }

  if (loading) return <LoadingState label="तपासणीचा निकाल मिळवत आहोत…" />
  if (error) return <ErrorAlert>{error}</ErrorAlert>

  const groups = predictionGroups(location.state, apiModels, language)
  const risk = farmerRiskLabel(result?.risk_level, language)
  const urgencyScore = typeof result?.urgency_score === 'number' && Number.isFinite(result.urgency_score)
    ? String(Number(result.urgency_score.toFixed(2)))
    : null
  const symptoms = Array.isArray(result?.symptoms) ? result.symptoms : []
  const reportDate = result?.created_at ? new Date(result.created_at).toLocaleDateString(language === 'mr' ? 'mr-IN' : 'en-GB') : ''

  return (
    <div className="mx-auto max-w-3xl">
      <Link to="/dashboard" className="inline-flex items-center gap-2 text-base font-semibold text-emerald-800">
        <ArrowLeft size={18} />{translate('Home', 'मुख्य पान')}
      </Link>

      <Card className="mt-6 p-6 sm:p-9">
        <p className="text-sm font-semibold text-emerald-800">{result?.cattle_tag ? `${translate('Tag number', 'टॅग क्रमांक')}: ${result.cattle_tag}` : 'BoviCare AI'}</p>
        <h1 className="mt-3 text-3xl font-bold text-emerald-950 sm:text-4xl">{translate('Diagnosis Result', 'तपासणीचा निकाल')}</h1>
        {reportDate && <p className="mt-2 text-base text-slate-600">{translate('Date', 'तारीख')}: {reportDate}</p>}
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <span className="rounded-md bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-700">{String(result?.workflow_status || result?.status || 'PENDING').replace(/_/g, ' ')}</span>
          {result?.urgency_level && <span className="rounded-md bg-emerald-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-800">{result.urgency_level}</span>}
        </div>

        <div className="mt-8 border-t border-slate-200 pt-7">
          {groups.length ? groups.map((group, index) => <ResultsGroup key={`${group.title}-${index}`} group={group} language={language} />) : (
            <>
              <p className="text-base font-semibold text-slate-600">{translate('Possible disease', 'संभाव्य आजार')}</p>
              <p className="mt-2 text-2xl font-bold leading-snug text-slate-950 sm:text-3xl">{farmerDiseaseLabel(result?.ai_prediction, language)}</p>
            </>
          )}
        </div>

        <div className="mt-7 flex flex-wrap items-center gap-3">
          <p className="text-base font-semibold text-slate-600">{translate('Risk Level', 'जोखीम पातळी')}</p>
          <span className={`rounded-md px-4 py-2 text-lg font-bold ${result?.risk_level === 'high' ? 'bg-red-100 text-red-800' : result?.risk_level === 'moderate' || result?.risk_level === 'medium' ? 'bg-amber-100 text-amber-900' : 'bg-emerald-100 text-emerald-900'}`}>
            {risk}
          </span>
        </div>

        <section className="mt-7 rounded-md border border-slate-200 bg-slate-50 p-5" aria-label={translate('Urgency priority', 'तातडीचे प्राधान्य')}>
          <h2 className="text-base font-bold text-slate-900">{translate('Urgency Priority', 'तातडीचे प्राधान्य')}</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <p className="text-sm font-semibold text-slate-600">{translate('Urgency Priority', 'तातडीचे प्राधान्य')}</p>
              <p className="mt-1 text-2xl font-bold text-emerald-800">{result?.urgency_level ? String(result.urgency_level).toUpperCase() : translate('Not available', 'उपलब्ध नाही')}</p>
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-600">{translate('Urgency Score', 'तातडीचा गुण')}</p>
              <p className="mt-1 text-2xl font-bold text-slate-900">{urgencyScore === null ? translate('Not available', 'उपलब्ध नाही') : `${urgencyScore} / 100`}</p>
            </div>
          </div>
        </section>

        <div className="mt-7">
          <p className="text-base font-semibold text-slate-600">{translate('Reported Symptoms', 'नोंदवलेली लक्षणे')}</p>
          <p className="mt-2 text-lg leading-relaxed text-slate-900">
            {symptoms.length ? symptoms.map(item => farmerSymptomLabel(item, language)).join(', ') : translate('No symptoms reported', 'लक्षणे नोंदवलेली नाहीत')}
          </p>
        </div>

        {result?.farmer_advice && (
          <div className="mt-8 rounded-md bg-emerald-50 p-5">
            <h2 className="text-xl font-bold text-emerald-950">{translate('Veterinary advice', 'पशुवैद्यकांचा सल्ला')}</h2>
            <p className="mt-3 whitespace-pre-wrap text-lg leading-relaxed text-emerald-950">{result.farmer_advice}</p>
          </div>
        )}

        <div className="mt-8 rounded-md bg-emerald-50 p-5">
          <h2 className="text-xl font-bold text-emerald-950">{translate('What should you do?', 'काय करावे?')}</h2>
          <p className="mt-2 text-lg leading-relaxed text-emerald-950">{translate('Please consult a veterinarian.', 'कृपया पशुवैद्यकांचा सल्ला घ्या.')}</p>
        </div>

        <p className="mt-5 text-sm leading-relaxed text-slate-600">{translate('This is an AI-based preliminary result. Please consult a veterinarian for a final diagnosis.', 'हा AI आधारित प्राथमिक अंदाज आहे. अंतिम निदानासाठी पशुवैद्यकांचा सल्ला घ्या.')}</p>

        {result?.id && (
          <button onClick={download} className="button-primary mt-7 min-h-12 w-full justify-center text-base sm:w-auto">
            <Download size={18} />{translate('Download Report', 'अहवाल डाउनलोड करा')}
          </button>
        )}
        {reportError && <p role="alert" className="mt-3 text-sm text-red-700">{reportError}</p>}
      </Card>
    </div>
  )
}
