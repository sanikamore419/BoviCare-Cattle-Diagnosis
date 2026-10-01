import { ArrowRight, Stethoscope } from 'lucide-react'
import { Link } from 'react-router-dom'
import CattleGraphic from '../components/CattleGraphic'
import LanguageToggle from '../components/LanguageToggle'
import { useLanguage } from '../auth/LanguageContext'

export default function Landing() {
  const { translate } = useLanguage()
  return (
    <div className="min-h-screen bg-[#f7faf7]">
      <header className="page-shell flex h-20 items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-lg font-extrabold text-emerald-950">
          <span className="rounded-xl bg-emerald-700 p-2 text-white"><Stethoscope size={19} /></span>
          BoviCare AI
        </Link>
        <div className="flex items-center gap-3"><LanguageToggle /><Link className="text-base font-semibold text-emerald-800" to="/login">{translate('Sign in', 'प्रवेश करा')}</Link></div>
      </header>
      <main className="page-shell grid items-center gap-10 pb-14 pt-8 lg:grid-cols-[1fr_.9fr] lg:pb-20 lg:pt-14">
        <section>
          <p className="text-base font-semibold text-emerald-800">{translate('Cattle care', 'जनावरांची काळजी')}</p>
          <h1 className="mt-4 max-w-2xl text-4xl font-bold leading-tight text-emerald-950 sm:text-5xl">{translate('Check your cattle with ease', 'जनावराची तपासणी सोप्या पद्धतीने करा')}</h1>
          <p className="mt-5 max-w-xl text-lg leading-8 text-slate-700">{translate('Record visible symptoms, add a photo if needed, and view the result.', 'दिसणारी लक्षणे नोंदवा, गरज असल्यास फोटो जोडा आणि तपासणीचा निकाल पहा.')}</p>
          <Link className="button-primary mt-7 min-h-12 text-base" to="/new-case">
            {translate('Start a check', 'तपासणी सुरू करा')} <ArrowRight size={18} />
          </Link>
          <p className="mt-5 max-w-xl text-base leading-7 text-slate-600">{translate('This is a preliminary result. Please consult a veterinarian for a final diagnosis.', 'निकाल हा प्राथमिक अंदाज आहे. अंतिम निदानासाठी पशुवैद्यकांचा सल्ला घ्या.')}</p>
        </section>
        <div className="mx-auto w-full max-w-xl"><CattleGraphic /></div>
      </main>
    </div>
  )
}
