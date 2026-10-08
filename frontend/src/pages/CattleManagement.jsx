import { Edit2, Plus, Trash2, X, Check, LoaderCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Card, EmptyState, ErrorAlert, LoadingState } from '../components/ui'
import { api } from '../lib/api'
import { useLanguage } from '../auth/LanguageContext'

const EMPTY_FORM = { tag_number: '', name: '', breed: '', date_of_birth: '', sex: 'unknown', weight_kg: '' }

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="label">{label}</span>
      {children}
    </label>
  )
}

function CattleForm({ initial = EMPTY_FORM, onSave, onCancel, saving }) {
  const { translate } = useLanguage()
  const [form, setForm] = useState(initial)
  const update = e => setForm({ ...form, [e.target.name]: e.target.value })
  function handleSubmit(e) {
    e.preventDefault()
    onSave({
      tag_number: form.tag_number,
      name: form.name || null,
      breed: form.breed || null,
      date_of_birth: form.date_of_birth || null,
      sex: form.sex,
      weight_kg: form.weight_kg ? Number(form.weight_kg) : null,
    })
  }
  return (
    <form onSubmit={handleSubmit} className="mt-5 grid gap-4 sm:grid-cols-2">
      <Field label={translate('Tag number *', 'टॅग क्रमांक *')}>
        <input required name="tag_number" value={form.tag_number} onChange={update} className="input" placeholder="e.g. COW-024" />
      </Field>
      <Field label={translate('Animal name', 'जनावराचे नाव')}>
        <input name="name" value={form.name} onChange={update} className="input" placeholder={translate('Optional', 'ऐच्छिक')} />
      </Field>
      <Field label={translate('Breed', 'जात')}>
        <input name="breed" value={form.breed} onChange={update} className="input" placeholder="e.g. Holstein" />
      </Field>
      <Field label={translate('Date of birth', 'जन्मतारीख')}>
        <input name="date_of_birth" type="date" value={form.date_of_birth} onChange={update} className="input" />
      </Field>
      <Field label={translate('Sex', 'लिंग')}>
        <select name="sex" value={form.sex} onChange={update} className="input">
          <option value="unknown">{translate('Unknown', 'माहित नाही')}</option>
          <option value="female">{translate('Female', 'मादी')}</option>
          <option value="male">{translate('Male', 'नर')}</option>
        </select>
      </Field>
      <Field label={translate('Weight (kg)', 'वजन (किलो)')}>
        <input name="weight_kg" type="number" min="0" step="0.1" value={form.weight_kg} onChange={update} className="input" placeholder="Optional" />
      </Field>
      <div className="sm:col-span-2 flex gap-3 pt-1">
        <button type="submit" disabled={saving} className="button-primary">
          {saving ? <LoaderCircle className="animate-spin" size={16} /> : <Check size={16} />}
          {translate('Save', 'जतन करा')}
        </button>
        <button type="button" onClick={onCancel} className="button-secondary"><X size={16} />{translate('Cancel', 'रद्द करा')}</button>
      </div>
    </form>
  )
}

export default function CattleManagement() {
  const { translate } = useLanguage()
  const [cattle, setCattle] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [adding, setAdding] = useState(false)
  const [editId, setEditId] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.get('/cattle')
      .then(r => setCattle(r.data))
      .catch(() => setError(translate('Could not load cattle information. Please try again.', 'जनावरांची माहिती मिळवता आली नाही. कृपया पुन्हा प्रयत्न करा.')))
      .finally(() => setLoading(false))
  }, [translate])

  async function handleCreate(payload) {
    setSaving(true); setError('')
    try {
      const r = await api.post('/cattle', payload)
      setCattle([r.data, ...cattle])
      setAdding(false)
    } catch (e) {
      setError(e.response?.data?.detail || translate('Could not save the cattle information.', 'जनावराची माहिती जतन करता आली नाही.'))
    } finally { setSaving(false) }
  }

  async function handleUpdate(id, payload) {
    setSaving(true); setError('')
    try {
      const r = await api.put(`/cattle/${id}`, payload)
      setCattle(cattle.map(c => c.id === id ? r.data : c))
      setEditId(null)
    } catch (e) {
      setError(e.response?.data?.detail || translate('Could not update the cattle information.', 'जनावराची माहिती बदलता आली नाही.'))
    } finally { setSaving(false) }
  }

  async function handleDelete(id) {
    if (!window.confirm(translate('Remove this animal? This cannot be undone.', 'हे जनावर काढायचे आहे का? ही कृती पुन्हा बदलता येणार नाही.'))) return
    setError('')
    try {
      await api.delete(`/cattle/${id}`)
      setCattle(cattle.filter(c => c.id !== id))
    } catch (e) {
      setError(e.response?.data?.detail || translate('Could not remove the cattle information.', 'जनावराची माहिती काढता आली नाही.'))
    }
  }

  return (
    <div className="mx-auto max-w-5xl">
      <div className="flex flex-wrap items-end justify-between gap-5">
        <div>
          <p className="text-sm font-semibold text-emerald-800">BoviCare AI</p>
          <h1 className="mt-2 text-3xl font-bold text-emerald-950">{translate('My cattle', 'माझी जनावरे')}</h1>
          <p className="mt-2 text-base text-slate-600">{translate('Save your cattle information here.', 'जनावरांची माहिती येथे जतन करा.')}</p>
        </div>
        {!adding && (
          <button onClick={() => { setAdding(true); setEditId(null) }} className="button-primary">
            <Plus size={17} />{translate('Add cattle', 'जनावर जोडा')}
          </button>
        )}
      </div>

      {error && <div className="mt-6"><ErrorAlert>{error}</ErrorAlert></div>}

      {adding && (
        <Card className="mt-6 p-6">
          <h2 className="text-xl font-bold">{translate('New cattle information', 'नवीन जनावराची माहिती')}</h2>
          <CattleForm onSave={handleCreate} onCancel={() => setAdding(false)} saving={saving} />
        </Card>
      )}

      {loading ? (
        <div className="mt-8"><LoadingState label={translate('Loading cattle records…', 'जनावरांची माहिती मिळवत आहोत…')} /></div>
      ) : cattle.length === 0 && !adding ? (
        <Card className="mt-8">
          <EmptyState
            icon={Plus}
            title={translate('No cattle yet', 'जनावरांची माहिती नाही')}
            message={translate('Add cattle information to get started.', 'सुरू करण्यासाठी जनावराची माहिती जोडा.')}
            action={<button onClick={() => setAdding(true)} className="button-primary"><Plus size={16} />{translate('Add cattle', 'जनावर जोडा')}</button>}
          />
        </Card>
      ) : (
        <div className="mt-6 space-y-4">
          {cattle.map(c => (
            <Card key={c.id} className="p-5">
              {editId === c.id ? (
                <>
                  <h2 className="font-bold">{translate('Edit', 'बदला')} — {c.tag_number}</h2>
                  <CattleForm
                    initial={{ tag_number: c.tag_number, name: c.name || '', breed: c.breed || '', date_of_birth: c.date_of_birth || '', sex: c.sex, weight_kg: c.weight_kg ?? '' }}
                    onSave={payload => handleUpdate(c.id, payload)}
                    onCancel={() => setEditId(null)}
                    saving={saving}
                  />
                </>
              ) : (
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="grid gap-x-8 gap-y-1 sm:grid-cols-3">
                    <div>
                      <p className="text-sm font-semibold text-slate-500">{translate('Tag number', 'टॅग क्रमांक')}</p>
                      <p className="mt-1 font-semibold">{c.tag_number}</p>
                    </div>
                    {c.name && (
                      <div>
                        <p className="text-sm font-semibold text-slate-500">{translate('Name', 'नाव')}</p>
                        <p className="mt-1 text-sm">{c.name}</p>
                      </div>
                    )}
                    {c.breed && (
                      <div>
                        <p className="text-sm font-semibold text-slate-500">{translate('Breed', 'जात')}</p>
                        <p className="mt-1 text-sm">{c.breed}</p>
                      </div>
                    )}
                    <div>
                      <p className="text-sm font-semibold text-slate-500">{translate('Sex', 'लिंग')}</p>
                      <p className="mt-1 text-sm">{translate(c.sex === 'female' ? 'Female' : c.sex === 'male' ? 'Male' : 'Unknown', c.sex === 'female' ? 'मादी' : c.sex === 'male' ? 'नर' : 'माहित नाही')}</p>
                    </div>
                    {c.date_of_birth && (
                      <div>
                        <p className="text-sm font-semibold text-slate-500">{translate('Date of birth', 'जन्मतारीख')}</p>
                        <p className="mt-1 text-sm">{c.date_of_birth}</p>
                      </div>
                    )}
                    {c.weight_kg != null && (
                      <div>
                        <p className="text-sm font-semibold text-slate-500">{translate('Weight', 'वजन')}</p>
                        <p className="mt-1 text-sm">{c.weight_kg} kg</p>
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => { setEditId(c.id); setAdding(false) }} className="button-secondary py-2 px-3">
                      <Edit2 size={15} />
                    </button>
                    <button onClick={() => handleDelete(c.id)} className="inline-flex items-center justify-center gap-2 rounded-xl border border-red-200 bg-white px-3 py-2 text-sm font-semibold text-red-600 transition hover:bg-red-50">
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
