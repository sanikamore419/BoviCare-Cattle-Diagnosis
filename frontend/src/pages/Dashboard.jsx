import { ClipboardList, Plus, Stethoscope } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, EmptyState, ErrorAlert, LoadingState } from '../components/ui'
import { api } from '../lib/api'
import { farmerDiseaseLabel, farmerRiskLabel } from '../lib/farmerText'
import { useLanguage } from '../auth/LanguageContext'

export default function Dashboard() {
  const { language, translate } = useLanguage()
  const [cases, setCases] = useState([])
  const [cattle, setCattle] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([api.get('/cases'), api.get('/cattle')])
      .then(([caseResponse, cattleResponse]) => {
        setCases(caseResponse.data)
        setCattle(cattleResponse.data)
      })
      .catch(() => setError(translate('Could not load information. Please try again.', 'माहिती मिळवता आली नाही. कृपया पुन्हा प्रयत्न करा.')))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="mx-auto max-w-5xl">
      <div className="flex flex-wrap items-end justify-between gap-5">
        <div>
          <p className="text-sm font-semibold text-emerald-800">BoviCare AI</p>
          <h1 className="mt-2 text-3xl font-bold text-emerald-950">{translate('Your cattle', 'आपली जनावरे')}</h1>
          <p className="mt-2 text-base text-slate-600">{translate('Start a check or view a previous result.', 'जनावराची तपासणी सुरू करा किंवा आधीचा निकाल पहा.')}</p>
        </div>
        <Link to="/new-case" className="button-primary min-h-12"><Plus size={18} />{translate('New check', 'नवीन तपासणी')}</Link>
      </div>

      {error && <div className="mt-6"><ErrorAlert>{error}</ErrorAlert></div>}

      <div className="mt-7 flex flex-wrap gap-x-8 gap-y-2 text-base text-slate-700">
        <span className="inline-flex items-center gap-2"><Stethoscope size={18} className="text-emerald-700" />{translate('Cattle:', 'जनावरे:')} {loading ? '—' : cattle.length}</span>
        <span className="inline-flex items-center gap-2"><ClipboardList size={18} className="text-emerald-700" />{translate('Checks:', 'तपासण्या:')} {loading ? '—' : cases.length}</span>
        <Link to="/cattle" className="font-semibold text-emerald-800">{translate('View cattle information', 'जनावरांची माहिती पहा')}</Link>
      </div>

      <Card className="mt-7 overflow-hidden">
        <div className="border-b border-slate-100 px-5 py-4 sm:px-6">
          <h2 className="text-xl font-bold text-slate-900">{translate('Previous checks', 'मागील तपासण्या')}</h2>
        </div>
        {loading ? <LoadingState label={translate('Loading information…', 'माहिती मिळवत आहोत…')} /> : cases.length ? (
          <div className="divide-y divide-slate-100">
            {cases.slice(0, 6).map(item => (
              <Link key={item.id} to={`/diagnosis/${item.id}`} state={{ result: item }} className="flex items-center justify-between gap-4 px-5 py-4 transition hover:bg-emerald-50/40 sm:px-6">
                <div className="min-w-0">
                  <p className="truncate text-lg font-semibold text-slate-900">{item.cattle_tag}</p>
                  <p className="mt-1 truncate text-base text-slate-600">{farmerDiseaseLabel(item.ai_prediction, language)}</p>
                </div>
                <span className={`shrink-0 rounded-md px-3 py-1.5 text-sm font-bold ${item.risk_level === 'high' ? 'bg-red-100 text-red-800' : item.risk_level === 'moderate' || item.risk_level === 'medium' ? 'bg-amber-100 text-amber-900' : 'bg-emerald-100 text-emerald-900'}`}>
                  {farmerRiskLabel(item.risk_level, language)}
                </span>
              </Link>
            ))}
          </div>
        ) : (
          <EmptyState icon={ClipboardList} title={translate('No checks yet', 'अजून तपासणी नाही')} message={translate('Start your first check to save a result.', 'तपासणी सुरू करून पहिला निकाल नोंदवा.')} action={<Link to="/new-case" className="button-primary"><Plus size={16} />{translate('New check', 'नवीन तपासणी')}</Link>} />
        )}
      </Card>
    </div>
  )
}
