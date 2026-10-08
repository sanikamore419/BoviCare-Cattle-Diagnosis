import { useEffect, useId } from 'react'
import {
  AlertCircle, AlertTriangle, CheckCircle2, CircleDashed, CircleDot, Clock3,
  LoaderCircle, X,
} from 'lucide-react'
import { useLanguage } from '../auth/LanguageContext'

const tr = (language, en, hi, mr) => ({ en, hi, mr })[language] || en

export function Card({ as: Element = 'section', children, className = '', ...props }) {
  return <Element className={`surface ${className}`} {...props}>{children}</Element>
}

const BADGE_CONFIG = {
  high: { tone: 'bg-red-50 text-red-800 ring-red-200', icon: AlertTriangle, label: ['High risk', 'उच्च जोखिम', 'उच्च जोखीम'] },
  critical: { tone: 'bg-red-50 text-red-800 ring-red-200', icon: AlertTriangle, label: ['Critical', 'गंभीर', 'गंभीर'] },
  medium: { tone: 'bg-amber-50 text-[#854D0E] ring-amber-200', icon: AlertCircle, label: ['Medium risk', 'मध्यम जोखिम', 'मध्यम जोखीम'] },
  moderate: { tone: 'bg-amber-50 text-[#854D0E] ring-amber-200', icon: AlertCircle, label: ['Moderate risk', 'मध्यम जोखिम', 'मध्यम जोखीम'] },
  low: { tone: 'bg-emerald-50 text-emerald-800 ring-emerald-200', icon: CheckCircle2, label: ['Low risk', 'कम जोखिम', 'कमी जोखीम'] },
  submitted: { tone: 'bg-slate-100 text-slate-800 ring-slate-300', icon: CircleDashed, label: ['Submitted', 'जमा किया', 'सबमिट केले'] },
  ai_complete: { tone: 'bg-blue-50 text-blue-800 ring-blue-200', icon: CheckCircle2, label: ['AI complete', 'AI पूरा हुआ', 'AI पूर्ण'] },
  pending_review: { tone: 'bg-sky-50 text-sky-800 ring-sky-200', icon: Clock3, label: ['Pending review', 'समीक्षा बाकी', 'पुनरावलोकन बाकी'] },
  in_review: { tone: 'bg-amber-50 text-[#854D0E] ring-amber-200', icon: CircleDot, label: ['In review', 'समीक्षा जारी', 'पुनरावलोकन सुरू'] },
  in_progress: { tone: 'bg-amber-50 text-[#854D0E] ring-amber-200', icon: CircleDot, label: ['In review', 'समीक्षा जारी', 'पुनरावलोकन सुरू'] },
  completed: { tone: 'bg-emerald-50 text-emerald-800 ring-emerald-200', icon: CheckCircle2, label: ['Completed', 'पूरा हुआ', 'पूर्ण'] },
  reviewed: { tone: 'bg-emerald-50 text-emerald-800 ring-emerald-200', icon: CheckCircle2, label: ['Completed', 'पूरा हुआ', 'पूर्ण'] },
  available: { tone: 'bg-emerald-50 text-emerald-800 ring-emerald-200', icon: CheckCircle2, label: ['Available', 'उपलब्ध', 'उपलब्ध'] },
  busy: { tone: 'bg-amber-50 text-[#854D0E] ring-amber-200', icon: Clock3, label: ['Busy', 'व्यस्त', 'व्यस्त'] },
  offline: { tone: 'bg-slate-100 text-slate-700 ring-slate-300', icon: CircleDot, label: ['Offline', 'ऑफ़लाइन', 'ऑफलाइन'] },
}

export function Badge({ value, label, className = '' }) {
  const { language } = useLanguage()
  const key = String(value || 'pending_review').trim().toLowerCase()
  const config = BADGE_CONFIG[key] || { tone: 'bg-slate-100 text-slate-800 ring-slate-300', icon: CircleDot }
  const Icon = config.icon
  const shown = label || (config.label ? config.label[['en', 'hi', 'mr'].indexOf(language)] : String(value || 'pending_review').replaceAll('_', ' '))
  return <span className={`inline-flex min-h-7 items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-bold ring-1 ring-inset ${config.tone} ${className}`}>
    <Icon aria-hidden="true" size={14} strokeWidth={2.2} /><span>{shown}</span>
  </span>
}

export function Button({ variant = 'primary', className = '', type = 'button', children, ...props }) {
  const base = 'inline-flex min-h-11 items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#166534] disabled:cursor-not-allowed disabled:opacity-50'
  const variants = {
    primary: 'bg-[#166534] text-white hover:bg-[#14532D]',
    secondary: 'border border-[#E7E5E4] bg-white text-slate-700 hover:bg-stone-50',
    ghost: 'bg-transparent text-slate-700 hover:bg-stone-100',
  }
  return <button type={type} className={`${base} ${variants[variant] || variants.primary} ${className}`} {...props}>{children}</button>
}

export function Input({ label, error, id, className = '', ...props }) {
  const generatedId = useId()
  const inputId = id || generatedId
  return <div className="min-w-0">
    {label && <label className="label" htmlFor={inputId}>{label}</label>}
    <input id={inputId} aria-invalid={Boolean(error)} aria-describedby={error ? `${inputId}-error` : undefined} className={`input ${error ? 'border-red-700' : ''} ${className}`} {...props} />
    {error && <p id={`${inputId}-error`} className="mt-1 text-sm font-medium text-red-800">{error}</p>}
  </div>
}

export function Modal({ open, title, onClose, children, footer, className = '' }) {
  const { language } = useLanguage()
  useEffect(() => {
    if (!open) return undefined
    const onKeyDown = event => { if (event.key === 'Escape') onClose?.() }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [open, onClose])
  if (!open) return null
  return <div className="fixed inset-0 z-[80] grid place-items-center overflow-y-auto bg-slate-950/50 p-4" onMouseDown={event => { if (event.target === event.currentTarget) onClose?.() }}>
    <section role="dialog" aria-modal="true" aria-labelledby="modal-title" className={`surface my-auto w-full max-w-xl p-5 shadow-2xl sm:p-7 ${className}`}>
      <header className="flex items-start justify-between gap-4"><h2 id="modal-title" className="text-xl font-bold">{title}</h2><Button variant="ghost" aria-label={tr(language, 'Close dialog', 'संवाद बंद करें', 'संवाद बंद करा')} className="min-h-11 !p-2" onClick={onClose}><X size={18} /></Button></header>
      <div className="mt-5">{children}</div>
      {footer && <footer className="mt-6 flex flex-wrap justify-end gap-3 border-t border-[#E7E5E4] pt-4">{footer}</footer>}
    </section>
  </div>
}

export function Drawer({ open, title, onClose, children, side = 'right', className = '' }) {
  const { language } = useLanguage()
  useEffect(() => {
    if (!open) return undefined
    const onKeyDown = event => { if (event.key === 'Escape') onClose?.() }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [open, onClose])
  if (!open) return null
  return <div className="fixed inset-0 z-[75] bg-slate-950/40" onMouseDown={event => { if (event.target === event.currentTarget) onClose?.() }}>
    <aside role="dialog" aria-modal="true" aria-labelledby="drawer-title" className={`fixed inset-y-0 ${side === 'left' ? 'left-0' : 'right-0'} flex w-[min(34rem,94vw)] flex-col overflow-y-auto bg-white p-5 shadow-2xl sm:p-7 ${className}`}>
      <header className="flex items-start justify-between gap-4 border-b border-[#E7E5E4] pb-4"><h2 id="drawer-title" className="text-xl font-bold">{title}</h2><Button variant="ghost" aria-label={tr(language, 'Close panel', 'पैनल बंद करें', 'पॅनेल बंद करा')} className="min-h-11 !p-2" onClick={onClose}><X size={18} /></Button></header>
      <div className="flex-1 py-5">{children}</div>
    </aside>
  </div>
}

export function Tabs({ tabs, value, onChange, label }) {
  return <div role="tablist" aria-label={label} className="flex max-w-full gap-1 overflow-x-auto rounded-xl bg-stone-100 p-1">
    {tabs.map(tab => <button key={tab.value} id={`tab-${tab.value}`} role="tab" aria-selected={value === tab.value} aria-controls={`panel-${tab.value}`} tabIndex={value === tab.value ? 0 : -1} onClick={() => onChange(tab.value)} className={`min-h-10 shrink-0 rounded-lg px-3 text-sm font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#166534] ${value === tab.value ? 'bg-white text-emerald-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}>{tab.label}</button>)}
  </div>
}

export function Table({ columns, rows, rowKey = 'id', caption, empty }) {
  return <div className="overflow-x-auto rounded-xl border border-[#E7E5E4]">
    <table className="w-full border-collapse text-left text-sm">
      {caption && <caption className="sr-only">{caption}</caption>}
      <thead className="bg-stone-50 text-xs uppercase tracking-wide text-slate-600"><tr>{columns.map(column => <th key={column.key} scope="col" className="whitespace-nowrap px-4 py-3 font-bold">{column.label}</th>)}</tr></thead>
      <tbody className="divide-y divide-stone-100 bg-white">{rows.map((row, index) => <tr key={row[rowKey] ?? index} className="hover:bg-emerald-50/40">{columns.map(column => <td key={column.key} className="px-4 py-3 align-top">{column.render ? column.render(row) : row[column.key]}</td>)}</tr>)}</tbody>
    </table>
    {!rows.length && empty && <div className="border-t border-stone-100">{empty}</div>}
  </div>
}

export function Pagination({ page, totalPages, onChange, className = '' }) {
  const { language } = useLanguage()
  const pages = Math.max(1, totalPages)
  return <nav aria-label={tr(language, 'Pagination', 'पृष्ठांकन', 'पृष्ठक्रम')} className={`flex items-center justify-between gap-3 ${className}`}>
    <Button variant="secondary" disabled={page <= 1} onClick={() => onChange(Math.max(1, page - 1))}>{tr(language, 'Previous', 'पिछला', 'मागील')}</Button>
    <span aria-live="polite" className="text-sm font-medium text-slate-700">{tr(language, `Page ${page} of ${pages}`, `पृष्ठ ${page} / ${pages}`, `पृष्ठ ${page} पैकी ${pages}`)}</span>
    <Button variant="secondary" disabled={page >= pages} onClick={() => onChange(Math.min(pages, page + 1))}>{tr(language, 'Next', 'अगला', 'पुढील')}</Button>
  </nav>
}

export function Toast({ message, onClose, tone = 'status', className = '' }) {
  const { language } = useLanguage()
  return <div role={tone === 'error' ? 'alert' : 'status'} className={`flex items-start gap-3 rounded-xl border bg-white p-4 shadow-lg ${tone === 'error' ? 'border-red-200 text-red-900' : 'border-[#E7E5E4] text-slate-900'} ${className}`}>
    {tone === 'error' ? <AlertCircle aria-hidden="true" className="mt-0.5 shrink-0" size={18} /> : <CircleDot aria-hidden="true" className="mt-0.5 shrink-0 text-[#166534]" size={18} />}
    <span className="min-w-0 flex-1">{message}</span>
    {onClose && <button type="button" aria-label={tr(language, 'Close notification', 'सूचना बंद करें', 'सूचना बंद करा')} className="rounded p-1 text-slate-600 hover:bg-stone-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#166534]" onClick={onClose}><X size={16} /></button>}
  </div>
}

export function Skeleton({ className = 'h-5 w-full', lines = 1 }) {
  return <div aria-hidden="true" className={`animate-pulse space-y-3 ${className}`}>{Array.from({ length: lines }, (_, index) => <div key={index} className="h-4 rounded-lg bg-stone-200" />)}</div>
}

export function LoadingState({ label }) {
  const { language } = useLanguage()
  const shown = label || tr(language, 'Loading clinical cases…', 'मामले लोड हो रहे हैं…', 'प्रकरणे लोड होत आहेत…')
  return <div role="status" className="flex min-h-40 items-center justify-center gap-2 text-sm text-slate-600"><LoaderCircle className="animate-spin" size={18} />{shown}</div>
}

export function ErrorAlert({ children }) { return <div role="alert" className="flex gap-3 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-950"><AlertCircle className="shrink-0" size={18} />{children}</div> }

export function EmptyState({ icon: Icon = CircleDot, title, message, action }) {
  return <div className="flex min-h-56 flex-col items-center justify-center px-6 py-8 text-center"><div className="rounded-2xl bg-emerald-50 p-3 text-emerald-800"><Icon aria-hidden="true" size={24} /></div><h3 className="mt-4 font-bold text-slate-900">{title}</h3><p className="mt-1 max-w-sm text-sm leading-6 text-slate-600">{message}</p>{action && <div className="mt-5">{action}</div>}</div>
}

export function ConfirmDialog({ open, title, message, confirmLabel, cancelLabel, onConfirm, onCancel, busy = false }) {
  const { language } = useLanguage()
  return <Modal open={open} title={title} onClose={onCancel} footer={<><Button variant="secondary" onClick={onCancel}>{cancelLabel || tr(language, 'Cancel', 'रद्द करें', 'रद्द करा')}</Button><Button onClick={onConfirm} disabled={busy}>{confirmLabel || tr(language, 'Confirm', 'पुष्टि करें', 'पुष्टी करा')}</Button></>}>
    <p className="text-sm leading-6 text-slate-700">{message}</p>
  </Modal>
}

export function StatCard({ label, value, detail, icon: Icon = CircleDot, className = '' }) {
  return <Card className={`p-5 ${className}`}><div className="flex items-start justify-between gap-3"><div className="min-w-0"><p className="text-sm font-semibold text-slate-600">{label}</p><p className="mt-2 text-3xl font-bold tracking-tight text-slate-950">{value}</p>{detail && <p className="mt-1 text-sm text-slate-600">{detail}</p>}</div><span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#F0FDF4] text-[#166534]"><Icon aria-hidden="true" size={20} /></span></div></Card>
}
