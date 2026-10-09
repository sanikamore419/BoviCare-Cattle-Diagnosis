import { ChevronDown, ChevronUp, ImagePlus, LoaderCircle, X } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, ErrorAlert } from '../components/ui'
import { api } from '../lib/api'
import { farmerSymptomLabel } from '../lib/farmerText'
import { useLanguage } from '../auth/LanguageContext'

const groups = [
  { en: 'General signs', mr: 'सामान्य लक्षणे', items: ['loss of appetite', 'lethargy', 'weight loss'] },
  { en: 'Breathing', mr: 'श्वासाशी संबंधित', items: ['coughing', 'difficulty breathing', 'nasal discharge'] },
  { en: 'Digestion', mr: 'पचनाशी संबंधित', items: ['diarrhea', 'bloating', 'reduced rumination'] },
  { en: 'Urgent signs', mr: 'तातडीची लक्षणे', items: ['cannot stand', 'seizure', 'severe bleeding'] },
]
const EMPTY_MILK = { Milk_Temperature: '', Milk_pH: '', Milk_Conductivity: '', Somatic_Cell_Count: '', Milk_Yield: '', Clotting: '' }
const DRAFT_KEY = 'bovicare_new_case_draft'
function loadDraft() {
  try { return JSON.parse(sessionStorage.getItem(DRAFT_KEY) || 'null') || {} } catch { return {} }
}
function Field({ label, children }) { return <label className="block"><span className="label">{label}</span>{children}</label> }

function requestErrorMessage(error, translate) {
  const detail = error.response?.data?.detail
  if (error.response?.status === 422) {
    const reason = Array.isArray(detail)
      ? detail.map(item => `${item.loc?.at(-1) || 'Input'}: ${item.msg}`).join(' ')
      : typeof detail === 'string' ? detail : ''
    return `${translate('Please check your information:', 'कृपया माहिती तपासा:')} ${reason}`.trim()
  }
  if (Array.isArray(detail)) return detail.map(item => `${item.loc?.at(-1) || 'Input'}: ${item.msg}`).join(' ')
  return typeof detail === 'string' ? detail : translate('Could not save the check. Please try again.', 'तपासणी जतन करता आली नाही. कृपया पुन्हा प्रयत्न करा.')
}

export default function NewCase() {
  const navigate = useNavigate()
  const { language, translate } = useLanguage()
  const inputRef = useRef(null)
  const submitLock = useRef(false)
  const [form, setForm] = useState(() => loadDraft().form || { cattle_tag: '', cattle_name: '', breed: '', gender: '', age_years: '', temperature_c: '', notes: '' })
  const [symptoms, setSymptoms] = useState(() => loadDraft().symptoms || [])
  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [imageModel, setImageModel] = useState(() => loadDraft().imageModel || 'cattle')
  const [milkOpen, setMilkOpen] = useState(() => loadDraft().milkOpen || false)
  const [milkForm, setMilkForm] = useState(() => loadDraft().milkForm || EMPTY_MILK)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [cattleList, setCattleList] = useState([])
  const [selectedCattleId, setSelectedCattleId] = useState(() => loadDraft().selectedCattleId || '')

  useEffect(() => { api.get('/cattle').then(r => setCattleList(r.data)).catch(() => {}) }, [])
  useEffect(() => {
    try { sessionStorage.setItem(DRAFT_KEY, JSON.stringify({ form, symptoms, imageModel, milkOpen, milkForm, selectedCattleId })) } catch { /* Draft persistence is best-effort. */ }
  }, [form, symptoms, imageModel, milkOpen, milkForm, selectedCattleId])

  const update = e => setForm({ ...form, [e.target.name]: e.target.value })
  const updateMilk = e => setMilkForm({ ...milkForm, [e.target.name]: e.target.value })
  const toggle = symptom => setSymptoms(cur => cur.includes(symptom) ? cur.filter(s => s !== symptom) : [...cur, symptom])
  const handleImageModelChange = useCallback(e => setImageModel(e.target.value), [])

  function selectCattle(e) {
    const id = e.target.value
    setSelectedCattleId(id)
    if (!id) return
    const c = cattleList.find(c => String(c.id) === id)
    if (c) setForm(f => ({ ...f, cattle_tag: c.tag_number, cattle_name: c.name || '', breed: c.breed || '', gender: c.sex === 'unknown' ? '' : c.sex }))
  }

  function selectImage(file) {
    if (!file) return
    if (!file.type.startsWith('image/')) { setError(translate('Please choose a photo (JPEG, PNG, or WEBP).', 'कृपया फोटो निवडा (JPEG, PNG किंवा WEBP).')); return }
    if (file.size > 10 * 1024 * 1024) { setError(translate('Photo must be smaller than 10 MB.', 'फोटोचा आकार १० MB पेक्षा कमी असावा.')); return }
    setImageFile(file)
    setImagePreview({ name: file.name, url: URL.createObjectURL(file) })
  }

  function removeImage() { setImageFile(null); setImagePreview(null) }

  function buildMilkData() {
    const v = milkForm
    const filledFields = Object.values(v).filter(value => value !== '').length
    if (filledFields === 0) return null
    if (filledFields !== Object.keys(EMPTY_MILK).length) throw new Error('Complete all six milk fields or leave the milk section empty.')
    return {
      Milk_Temperature: Number(v.Milk_Temperature),
      Milk_pH: Number(v.Milk_pH),
      Milk_Conductivity: Number(v.Milk_Conductivity),
      Somatic_Cell_Count: Number(v.Somatic_Cell_Count),
      Milk_Yield: Number(v.Milk_Yield),
      Clotting: Number(v.Clotting),
    }
  }

  async function submit(e) {
    e.preventDefault()
    if (submitLock.current) return
    setError('')
    let milkData
    try { milkData = buildMilkData() } catch (validationError) {
      setError(translate(validationError.message, 'दुधाची सर्व सहा माहिती भरा किंवा दूध विभाग रिकामा ठेवा.'))
      return
    }
    if (!symptoms.length && !imageFile && !milkData) { setError(translate('Select a symptom, enter milk information, or add a cattle photo.', 'किमान एक लक्षण निवडा, दुधाची माहिती भरा किंवा जनावराचा फोटो जोडा.')); return }
    submitLock.current = true
    setLoading(true)
    try {
      // Step 1: triage — only if symptoms selected
      let triageResult = null
      if (symptoms.length || milkData || imageFile) {
        const r = await api.post('/cases/triage', {
          cattle_tag: form.cattle_tag,
          cattle_id: selectedCattleId ? Number(selectedCattleId) : null,
          cattle_name: form.cattle_name || null,
          breed: form.breed || null,
          gender: form.gender || null,
          age_years: form.age_years ? Number(form.age_years) : null,
          temperature_c: form.temperature_c ? Number(form.temperature_c) : null,
          symptoms,
          notes: form.notes || null,
        })
        triageResult = r.data
      }

      // Step 2: real Model A (and optional Model B) prediction
      let generalResult = null
      let mastitisResult = null
      if (symptoms.length && triageResult) {
        const predPayload = {
          symptoms,
          case_id: triageResult.id,
          cattle_id: selectedCattleId ? Number(selectedCattleId) : null,
        }
        if (milkData) predPayload.milk_data = milkData
        const r = await api.post('/predictions', predPayload)
        generalResult = r.data.general || null
        mastitisResult = r.data.mastitis || null
      } else if (milkData) {
        // milk data only (no symptoms) — Model B only
        const r = await api.post('/predictions', {
          milk_data: milkData,
          case_id: triageResult?.id,
          cattle_id: selectedCattleId ? Number(selectedCattleId) : null,
        })
        mastitisResult = r.data.mastitis || null
      }

      // Step 3: image prediction — only if image uploaded
      let imageResult = null
      if (imageFile) {
        const fd = new FormData()
        fd.append('file', imageFile)
        fd.append('model', imageModel)
        if (selectedCattleId) fd.append('cattle_id', selectedCattleId)
        if (triageResult?.id) fd.append('case_id', triageResult.id)
        const r = await api.post('/predictions/image', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
        imageResult = r.data
      }

      // Image inference persists its own rows. Verify those stored rows through
      // the predictions resource so image-only submissions use the same flow.
      if (!symptoms.length && !milkData && imageFile) {
        await api.post('/predictions', {
          case_id: triageResult.id,
          cattle_id: selectedCattleId ? Number(selectedCattleId) : null,
          image_only: true,
        })
      }

      sessionStorage.removeItem(DRAFT_KEY)
      navigate(`/diagnosis/${triageResult.id}`, {
        state: {
          result: triageResult,
          generalResult,
          mastitisResult,
          imageResult,
          context: { cattleName: form.cattle_name, gender: form.gender, notes: form.notes, imagePreview }
        }
      })
    } catch (err) {
      setError(requestErrorMessage(err, translate))
    } finally { setLoading(false); submitLock.current = false }
  }

  return (
    <div className="mx-auto max-w-5xl">
      <p className="text-sm font-semibold text-emerald-800">BoviCare AI</p>
      <h1 className="mt-2 text-3xl font-bold text-emerald-950">{translate('Check your cattle', 'जनावराची तपासणी')}</h1>
      <p className="mt-2 text-base leading-6 text-slate-600">{translate('Enter the cattle information and select the signs you notice.', 'जनावराची माहिती द्या आणि दिसणारी लक्षणे निवडा.')}</p>
      <form onSubmit={submit} className="mt-8 grid gap-6 lg:grid-cols-[1fr_.68fr]">
        <div className="space-y-6">
          <Card className="p-6">
            <h2 className="text-xl font-bold">{translate('Cattle information', 'जनावराची माहिती')}</h2>
            {cattleList.length > 0 && (
              <div className="mt-4">
                <Field label={translate('Choose a registered animal', 'नोंदवलेल्या जनावरातून निवडा')}>
                  <select value={selectedCattleId} onChange={selectCattle} className="input">
                    <option value="">— {translate('Enter information manually', 'स्वतः माहिती भरा')} —</option>
                    {cattleList.map(c => <option key={c.id} value={c.id}>{c.tag_number}{c.name ? ` — ${c.name}` : ''}{c.breed ? ` (${c.breed})` : ''}</option>)}
                  </select>
                </Field>
                <p className="mt-1 text-sm text-slate-500">{translate('Choosing an animal fills its saved information below.', 'जनावर निवडल्यावर त्याची माहिती आपोआप भरली जाईल.')}</p>
              </div>
            )}
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <Field label={translate('Tag number *', 'टॅग क्रमांक *')}><input required name="cattle_tag" value={form.cattle_tag} onChange={update} className="input" placeholder="e.g. COW-024" /></Field>
              <Field label={translate('Animal name', 'जनावराचे नाव')}><input name="cattle_name" value={form.cattle_name} onChange={update} className="input" placeholder={translate('Optional', 'ऐच्छिक')} /></Field>
              <Field label={translate('Age (years)', 'वय (वर्षे)')}><input name="age_years" type="number" min="0" step="0.1" value={form.age_years} onChange={update} className="input" placeholder={translate('Optional', 'ऐच्छिक')} /></Field>
              <Field label={translate('Breed', 'जात')}><input name="breed" value={form.breed} onChange={update} className="input" placeholder={translate('Optional', 'ऐच्छिक')} /></Field>
              <Field label={translate('Sex', 'लिंग')}>
                <select name="gender" value={form.gender} onChange={update} className="input">
                  <option value="">{translate('Choose if known', 'माहित असल्यास निवडा')}</option>
                  <option value="Female">{translate('Female', 'मादी')}</option><option value="Male">{translate('Male', 'नर')}</option>
                </select>
              </Field>
              <Field label={translate('Temperature (°C)', 'तापमान (°C)')}><input name="temperature_c" type="number" min="30" max="45" step="0.1" value={form.temperature_c} onChange={update} className="input" placeholder={translate('Optional', 'ऐच्छिक')} /></Field>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div><h2 className="text-xl font-bold">{translate('Symptoms', 'दिसणारी लक्षणे')}</h2><p className="mt-1 text-base text-slate-500">{translate('Select each sign you notice.', 'जनावराला दिसणारी सर्व लक्षणे निवडा.')}</p></div>
              <span className="rounded-full bg-emerald-50 px-3 py-1 text-sm font-bold text-emerald-800">{translate('Selected:', 'निवडलेली:')} {symptoms.length}</span>
            </div>
            <div className="mt-5 space-y-5">
              {groups.map(group => (
                <div key={group.en}>
                    <p className="text-sm font-bold text-slate-600">{translate(group.en, group.mr)}</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {group.items.map(symptom => (
                      <button type="button" key={symptom} onClick={() => toggle(symptom)} className={`rounded-md border px-3 py-2.5 text-base font-semibold transition ${symptoms.includes(symptom) ? 'border-emerald-700 bg-emerald-700 text-white' : 'border-slate-200 bg-white text-slate-700 hover:border-emerald-300'}`}>{farmerSymptomLabel(symptom, language)}</button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-6">
            <button type="button" onClick={() => setMilkOpen(o => !o)} className="flex w-full items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-left">{translate('Milk information', 'दुधाची माहिती')} <span className="ml-1 text-sm font-normal text-slate-500">({translate('optional', 'ऐच्छिक')})</span></h2>
                <p className="mt-1 text-base text-slate-600 text-left">{translate('Enter if available.', 'माहिती उपलब्ध असल्यास भरा.')}</p>
              </div>
              {milkOpen ? <ChevronUp size={18} className="text-slate-400 shrink-0" /> : <ChevronDown size={18} className="text-slate-400 shrink-0" />}
            </button>
            {milkOpen && (
              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                <Field label={translate('Milk temperature (°C)', 'दुधाचे तापमान (°C)')}><input name="Milk_Temperature" type="number" step="0.1" value={milkForm.Milk_Temperature} onChange={updateMilk} className="input" placeholder="30–45" /></Field>
                <Field label={translate('Milk pH', 'दुधाचा pH')}><input name="Milk_pH" type="number" step="0.01" value={milkForm.Milk_pH} onChange={updateMilk} className="input" placeholder="5.0–9.0" /></Field>
                <Field label={translate('Milk conductivity', 'दुधाची विद्युत चालकता')}><input name="Milk_Conductivity" type="number" step="0.01" value={milkForm.Milk_Conductivity} onChange={updateMilk} className="input" placeholder={translate('If available', 'माहित असल्यास')} /></Field>
                <Field label={translate('Milk cell count', 'दुधातील पेशींची संख्या')}><input name="Somatic_Cell_Count" type="number" step="1" value={milkForm.Somatic_Cell_Count} onChange={updateMilk} className="input" placeholder={translate('If available', 'माहित असल्यास')} /></Field>
                <Field label={translate('Milk yield (litres)', 'दुधाचे प्रमाण (लिटर)')}><input name="Milk_Yield" type="number" step="0.1" value={milkForm.Milk_Yield} onChange={updateMilk} className="input" placeholder={translate('Litres', 'लिटर')} /></Field>
                <Field label={translate('Clots in milk', 'दुधात गुठळ्या')}>
                  <select name="Clotting" value={milkForm.Clotting} onChange={updateMilk} className="input">
                    <option value="">{translate('Choose', 'निवडा')}</option>
                    <option value="0">{translate('No', 'नाही')}</option>
                    <option value="1">{translate('Yes', 'आहे')}</option>
                  </select>
                </Field>
              </div>
            )}
          </Card>

          <Card className="p-6">
            <h2 className="text-lg font-bold">{translate('Other information (optional)', 'इतर माहिती (ऐच्छिक)')}</h2>
            <Field label={translate('Anything else the veterinarian should know', 'पशुवैद्यकांना सांगायची इतर माहिती')}><textarea name="notes" value={form.notes} onChange={update} rows="3" className="input resize-y" placeholder={translate('Write here', 'इथे लिहा')} /></Field>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="p-6">
            <h2 className="text-lg font-bold">{translate('Cattle photo', 'जनावराचा फोटो')}</h2>
            <p className="mt-1 text-base leading-6 text-slate-600">{translate('Adding a photo is optional. Maximum size 10 MB.', 'फोटो जोडणे ऐच्छिक आहे. कमाल आकार १० MB.')}</p>
            <input ref={inputRef} type="file" accept="image/jpeg,image/png,image/webp,image/bmp" className="hidden" onChange={e => selectImage(e.target.files?.[0])} />
            <div onDrop={e => { e.preventDefault(); selectImage(e.dataTransfer.files?.[0]) }} onDragOver={e => e.preventDefault()} className="mt-4 rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 p-5 text-center">
              {imagePreview ? (
                <div>
                  <img src={imagePreview.url} alt={translate('Cattle photo', 'जनावराचा फोटो')} className="mx-auto h-40 w-full rounded-md object-cover" />
                  <p className="mt-3 truncate text-sm font-semibold">{imagePreview.name}</p>
                  <button type="button" onClick={removeImage} className="mt-3 inline-flex items-center gap-1 text-base font-bold text-red-700"><X size={16} />{translate('Remove photo', 'फोटो काढा')}</button>
                </div>
              ) : (
                <>
                  <ImagePlus className="mx-auto text-emerald-700" size={28} />
                  <p className="mt-3 text-base font-bold">{translate('Choose a photo', 'फोटो निवडा')}</p>
                  <p className="mt-1 text-sm text-slate-600">JPG, PNG {translate('or', 'किंवा')} WEBP</p>
                  <button type="button" onClick={() => inputRef.current?.click()} className="button-secondary mt-4 min-h-11">{translate('Add photo', 'फोटो जोडा')}</button>
                </>
              )}
            </div>
            {imagePreview && (
              <div className="mt-4">
                <Field label={translate('Choose photo check', 'फोटोचा प्रकार निवडा')}>
                  <select value={imageModel} onChange={handleImageModelChange} className="input">
                    <option value="cattle">{translate('General cattle check', 'जनावराच्या आजारांची तपासणी')}</option>
                    <option value="lumpy">{translate('Skin lump check', 'त्वचेवरील गाठींची तपासणी')}</option>
                  </select>
                </Field>
              </div>
            )}
          </Card>

          {error && <ErrorAlert>{error}</ErrorAlert>}

          <Card className="border-emerald-100 bg-emerald-50/50 p-6">
            <p className="text-base font-bold text-emerald-950">{translate('Important note', 'महत्त्वाची सूचना')}</p>
            <p className="mt-1 text-base leading-6 text-emerald-900">{translate('This is a preliminary result. Please consult a veterinarian.', 'तपासणीचा निकाल हा प्राथमिक अंदाज आहे. पशुवैद्यकांचा सल्ला घ्या.')}</p>
          </Card>

          <button disabled={loading} className="button-primary w-full py-3">
            {loading ? <><LoaderCircle className="animate-spin" size={18} />{translate('Checking…', 'तपासणी सुरू आहे…')}</> : translate('Check cattle', 'तपासणी करा')}
          </button>
        </div>
      </form>
    </div>
  )
}
