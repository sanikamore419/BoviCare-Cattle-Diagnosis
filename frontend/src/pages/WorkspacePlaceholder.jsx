import { ArrowRight, ClipboardList } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Card } from '../components/ui'

export default function WorkspacePlaceholder({ title, description, actionTo, actionLabel }) {
  return <div>
    <p className="eyebrow">BoviCare workspace</p>
    <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">{title}</h1>
    <Card className="mt-7 flex flex-col items-start gap-4 p-6 sm:flex-row sm:items-center">
      <span className="rounded-xl bg-emerald-50 p-3 text-emerald-800"><ClipboardList size={24} /></span>
      <div className="flex-1"><h2 className="font-bold text-slate-900">{description}</h2><p className="mt-1 text-sm leading-6 text-slate-600">This workspace is being prepared. Your existing case and animal records remain available from their current pages.</p></div>
      {actionTo && <Link className="button-secondary" to={actionTo}>{actionLabel}<ArrowRight size={16} /></Link>}
    </Card>
  </div>
}
