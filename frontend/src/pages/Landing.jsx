import { useState } from 'react'
import {
  Activity,
  ArrowRight,
  BarChart3,
  BrainCircuit,
  Camera,
  CheckCircle2,
  ChevronRight,
  Gauge,
  HeartPulse,
  Menu,
  Microscope,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  X
} from 'lucide-react'
import { Link } from 'react-router-dom'
import CattleGraphic from '../components/CattleGraphic'
import LanguageToggle from '../components/LanguageToggle'
import { useLanguage } from '../auth/LanguageContext'

const navItems = [
  { label: 'Features', href: '#features' },
  { label: 'Workflow', href: '#workflow' },
  { label: 'Dashboard', href: '#dashboard' },
  { label: 'Safety', href: '#insights' }
]

const stats = [
  { value: '24/7', label: 'AI triage' },
  { value: '87%', label: 'confidence' },
  { value: '3.2x', label: 'faster review' }
]

const featureCards = [
  { icon: BrainCircuit, title: 'AI health analysis', description: 'Detect early risk patterns using symptoms, history, and visual indicators.' },
  { icon: ShieldCheck, title: 'Veterinary-grade safety', description: 'Escalate abnormal cases to trained professionals before issues worsen.' },
  { icon: Activity, title: 'Live case monitoring', description: 'Track recovery progress, alerts, and high-priority animals from one dashboard.' },
  { icon: Gauge, title: 'Faster decisions', description: 'Summaries and recommendations help teams act quickly with higher confidence.' }
]

const workflow = [
  { step: '01', title: 'Capture symptoms', text: 'Record visible signs and upload photos for AI review.', icon: Camera },
  { step: '02', title: 'Assess risk', text: 'Review AI confidence, priority flags, and serial patterns.', icon: Microscope },
  { step: '03', title: 'Act with confidence', text: 'Share insights with veterinary teams and monitor treatment progress.', icon: HeartPulse }
]

const insightCards = [
  { label: 'AI assessment', value: 'High risk', accent: 'bg-rose-50 text-rose-700 ring-rose-200' },
  { label: 'Confidence', value: '87%', accent: 'bg-emerald-50 text-emerald-700 ring-emerald-200' },
  { label: 'Priority queue', value: '24 active', accent: 'bg-amber-50 text-amber-700 ring-amber-200' }
]

export default function Landing() {
  const { translate } = useLanguage()
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-[#f7faf7] text-slate-900">
      <div className="absolute inset-x-0 top-0 -z-10 h-[640px] bg-[radial-gradient(circle_at_top_left,_rgba(34,197,94,0.14),transparent_32%),radial-gradient(circle_at_85%_15%,_rgba(134,239,172,0.18),transparent_22%),linear-gradient(180deg,#f8fcf8_0%,#f3faf3_100%)]" />

      <header className="sticky top-0 z-50 border-b border-emerald-100/80 bg-[#f7faf7]/85 backdrop-blur-xl">
        <div className="page-shell flex h-20 items-center justify-between">
          <Link to="/" className="flex items-center gap-3 text-lg font-extrabold text-emerald-950">
            <span className="rounded-2xl bg-emerald-700 p-2.5 text-white shadow-lg shadow-emerald-600/25">
              <Stethoscope size={18} />
            </span>
            <span className="tracking-tight">BoviCare AI</span>
          </Link>

          <nav className="hidden items-center gap-8 text-sm font-semibold text-slate-700 md:flex">
            {navItems.map((item) => (
              <a key={item.href} href={item.href} className="transition hover:text-emerald-700">{translate(item.label, item.label)}</a>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            <div className="hidden sm:block"><LanguageToggle /></div>
            <Link className="hidden text-base font-semibold text-emerald-800 transition hover:text-emerald-700 sm:inline-flex" to="/login">
              {translate('Sign in', 'प्रवेश करा')}
            </Link>
            <Link className="button-primary hidden sm:inline-flex" to="/new-case">
              {translate('Start a check', 'तपासणी सुरू करा')} <ArrowRight size={17} />
            </Link>

            <button
              type="button"
              onClick={() => setMenuOpen((value) => !value)}
              className="inline-flex h-11 w-11 items-center justify-center rounded-xl border border-emerald-200 bg-white text-emerald-900 shadow-sm md:hidden"
              aria-label="Toggle menu"
              aria-expanded={menuOpen}
            >
              {menuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>

        {menuOpen && (
          <div className="page-shell pb-4 md:hidden">
            <div className="rounded-2xl border border-emerald-100 bg-white/95 p-4 shadow-xl shadow-emerald-950/5">
              <nav className="flex flex-col gap-3 text-sm font-semibold text-slate-700">
                {navItems.map((item) => (
                  <a key={item.href} href={item.href} onClick={() => setMenuOpen(false)} className="rounded-xl px-2 py-2 hover:bg-emerald-50 hover:text-emerald-700">
                    {translate(item.label, item.label)}
                  </a>
                ))}
                <Link to="/login" onClick={() => setMenuOpen(false)} className="mt-2 rounded-xl border border-emerald-200 px-3 py-2 text-center text-emerald-800">
                  {translate('Sign in', 'प्रवेश करा')}
                </Link>
                <Link to="/new-case" onClick={() => setMenuOpen(false)} className="button-primary w-full">
                  {translate('Start a check', 'तपासणी सुरू करा')} <ArrowRight size={17} />
                </Link>
              </nav>
            </div>
          </div>
        )}
      </header>

      <main>
        <section className="page-shell relative grid items-center gap-12 pb-16 pt-10 lg:grid-cols-[1.02fr_.98fr] lg:pb-20 lg:pt-16">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50/80 px-3 py-1.5 text-sm font-medium text-emerald-800 shadow-sm">
              <Sparkles size={16} className="text-emerald-600" />
              {translate('AI-powered cattle health', 'एआय-चालित गायींची आरोग्य तपासणी')}
            </div>

            <h1 className="mt-6 max-w-2xl text-4xl font-black tracking-[-0.06em] text-emerald-950 sm:text-5xl lg:text-6xl">
              {translate('Check your cattle with ease', 'जनावराची तपासणी सोप्या पद्धतीने करा')}
            </h1>

            <p className="mt-5 max-w-xl text-lg leading-8 text-slate-700">
              {translate(
                'Record visible symptoms, add a photo if needed, and surface early-risk insights before clinical issues become serious.',
                'दिसणारी लक्षणे नोंदवा, गरज असल्यास फोटो जोडा आणि वैद्यकीय समस्या गंभीर होण्यापूर्वी प्रारंभिक धोक्यांचे संकेत पाहा.'
              )}
            </p>

            <div className="mt-8 flex flex-col gap-4 sm:flex-row">
              <Link className="button-primary min-h-12 px-5 text-base shadow-lg shadow-emerald-600/20" to="/new-case">
                {translate('Start a check', 'तपासणी सुरू करा')} <ArrowRight size={18} />
              </Link>
              <a href="#features" className="button-secondary min-h-12 px-5 text-base">
                {translate('Explore features', 'वैशिष्ट्ये पहा')}
              </a>
            </div>

            <div className="mt-8 flex flex-wrap items-center gap-4 text-sm text-slate-600">
              {['Vet-reviewed workflow', 'Photo-based screening', 'Early alerts'].map((item) => (
                <span key={item} className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5">
                  <CheckCircle2 size={16} className="text-emerald-600" />
                  {translate(item, item)}
                </span>
              ))}
            </div>

            <div className="mt-9 grid max-w-xl grid-cols-3 gap-3 sm:gap-4">
              {stats.map((stat) => (
                <div key={stat.label} className="rounded-2xl border border-emerald-100 bg-white/80 p-4 shadow-sm shadow-emerald-950/5">
                  <div className="text-2xl font-black tracking-tight text-emerald-900">{stat.value}</div>
                  <div className="mt-1 text-xs font-medium uppercase tracking-[0.12em] text-slate-500">{translate(stat.label, stat.label)}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="relative mx-auto w-full max-w-xl">
            <div className="absolute -left-7 top-12 h-20 w-20 rounded-full bg-emerald-300/40 blur-2xl" />
            <div className="absolute -right-10 bottom-10 h-28 w-28 rounded-full bg-lime-300/35 blur-2xl" />
            <div className="relative rounded-[2rem] border border-emerald-100 bg-white/70 p-4 shadow-[0_30px_80px_rgba(22,101,52,0.12)] backdrop-blur-sm">
              <CattleGraphic />
            </div>

            <div className="absolute -left-4 top-8 rounded-2xl border border-emerald-200 bg-white/90 p-3 shadow-xl shadow-emerald-950/10 backdrop-blur-sm">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em] text-emerald-700">
                <BrainCircuit size={14} /> AI health analysis
              </div>
              <div className="mt-2 text-2xl font-black text-emerald-950">87%</div>
              <div className="text-xs text-slate-500">confidence score</div>
            </div>

            <div className="absolute -right-2 bottom-6 rounded-2xl border border-rose-200 bg-white/90 p-3 shadow-xl shadow-rose-200/30 backdrop-blur-sm">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-rose-600">
                <HeartPulse size={14} /> High risk detected
              </div>
              <div className="mt-2 text-sm font-semibold text-slate-800">Cow-023 • Priority review</div>
            </div>
          </div>
        </section>

        <section id="features" className="page-shell pb-16 pt-5 lg:pb-20">
          <div className="mx-auto max-w-3xl text-center">
            <p className="eyebrow">Why BoviCare</p>
            <h2 className="mt-4 text-3xl font-black tracking-tight text-slate-900 sm:text-4xl">Professional insight for every herd</h2>
            <p className="mt-4 text-lg text-slate-600">Built to support farmers, field teams, and veterinarians with a cleaner path from symptoms to action.</p>
          </div>

          <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {featureCards.map(({ icon: Icon, title, description }) => (
              <article key={title} className="group rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_18px_40px_rgba(15,23,42,0.04)] transition duration-200 hover:-translate-y-1 hover:shadow-[0_20px_45px_rgba(22,101,52,0.08)]">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-700 transition duration-200 group-hover:scale-105 group-hover:bg-emerald-600 group-hover:text-white">
                  <Icon size={22} />
                </div>
                <h3 className="mt-5 text-xl font-bold text-slate-900">{title}</h3>
                <p className="mt-3 text-base leading-7 text-slate-600">{description}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="workflow" className="bg-white/80 py-16 lg:py-20">
          <div className="page-shell">
            <div className="mx-auto max-w-3xl text-center">
              <p className="eyebrow">How it works</p>
              <h2 className="mt-4 text-3xl font-black tracking-tight text-slate-900 sm:text-4xl">From symptoms to smart action</h2>
            </div>

            <div className="mt-10 grid gap-5 lg:grid-cols-3">
              {workflow.map(({ step, title, text, icon: Icon }) => (
                <div key={step} className="rounded-3xl border border-slate-200 bg-[#f9fbf9] p-6 shadow-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold uppercase tracking-[0.18em] text-emerald-700">{step}</span>
                    <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-700">
                      <Icon size={20} />
                    </span>
                  </div>
                  <h3 className="mt-6 text-2xl font-bold text-slate-900">{title}</h3>
                  <p className="mt-3 text-base leading-7 text-slate-600">{text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="dashboard" className="page-shell py-16 lg:py-20">
          <div className="grid gap-8 lg:grid-cols-[1.08fr_.92fr] lg:items-center">
            <div className="rounded-[2rem] border border-slate-200 bg-[#fbfdfb] p-4 shadow-[0_30px_80px_rgba(15,23,42,0.06)] sm:p-6">
              <div className="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm">
                <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                  <div>
                    <p className="text-sm font-semibold text-slate-500">Priority Inbox</p>
                    <h3 className="mt-1 text-2xl font-bold text-slate-900">Case queue</h3>
                  </div>
                  <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold uppercase tracking-[0.12em] text-emerald-700">Live</span>
                </div>

                <div className="mt-5 space-y-3">
                  {[
                    ['Cow-023', 'High risk', '02:14 PM'],
                    ['Cow-118', 'Monitor', '01:47 PM'],
                    ['Cow-206', 'Low risk', '11:30 AM']
                  ].map(([tag, status, time], index) => (
                    <div key={tag} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                      <div>
                        <div className="font-semibold text-slate-900">{tag}</div>
                        <div className="text-xs text-slate-500">Updated {time}</div>
                      </div>
                      <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${index === 0 ? 'bg-rose-50 text-rose-700' : index === 1 ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700'}`}>
                        {status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div>
              <p className="eyebrow">Clinical overview</p>
              <h2 className="mt-4 text-3xl font-black tracking-tight text-slate-900 sm:text-4xl">Designed for real veterinary workflows</h2>
              <p className="mt-4 max-w-xl text-lg leading-8 text-slate-600">View high-risk alerts, triage queue items, and AI explanations in a single, clear operating view that supports faster action.</p>

              <div className="mt-8 space-y-4">
                {insightCards.map((card) => (
                  <div key={card.label} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                    <div>
                      <div className="text-sm font-medium text-slate-500">{card.label}</div>
                      <div className="mt-1 text-2xl font-black text-slate-900">{card.value}</div>
                    </div>
                    <span className={`rounded-full px-3 py-1 text-xs font-semibold ring-1 ${card.accent}`}>{card.label === 'AI assessment' ? 'Needs review' : card.label === 'Confidence' ? 'Strong' : 'Queue'}</span>
                  </div>
                ))}
              </div>

              <div className="mt-8 flex items-center gap-3 text-emerald-800">
                <BarChart3 size={18} />
                <span className="font-semibold">Monitor herd health trends with actionable AI summaries.</span>
              </div>
            </div>
          </div>
        </section>

        <section id="insights" className="bg-[#edf7ef] py-16 lg:py-20">
          <div className="page-shell">
            <div className="grid gap-6 lg:grid-cols-3">
              <div className="rounded-3xl border border-emerald-100 bg-white p-6 shadow-sm">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700">
                  <ShieldCheck size={22} />
                </div>
                <h3 className="mt-5 text-2xl font-bold text-slate-900">Safety-first review</h3>
                <p className="mt-3 text-base leading-7 text-slate-600">Every recommendation is designed to support clinical judgment, not replace it.</p>
              </div>
              <div className="rounded-3xl border border-emerald-100 bg-white p-6 shadow-sm">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700">
                  <BrainCircuit size={22} />
                </div>
                <h3 className="mt-5 text-2xl font-bold text-slate-900">Actionable intelligence</h3>
                <p className="mt-3 text-base leading-7 text-slate-600">AI signals highlight patterns, risk scores, and key symptoms without overwhelming the team.</p>
              </div>
              <div className="rounded-3xl border border-emerald-100 bg-white p-6 shadow-sm">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700">
                  <Activity size={22} />
                </div>
                <h3 className="mt-5 text-2xl font-bold text-slate-900">Progress tracking</h3>
                <p className="mt-3 text-base leading-7 text-slate-600">Monitor each case over time to evaluate recovery, intervention outcomes, and herd trends.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="page-shell py-16 lg:py-20">
          <div className="rounded-[2rem] border border-emerald-200 bg-gradient-to-r from-emerald-700 to-emerald-900 p-8 text-white shadow-[0_30px_80px_rgba(22,101,52,0.28)] sm:p-10 lg:flex lg:items-center lg:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-100">Ready to start</p>
              <h2 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">Bring AI-backed cattle care to your herd</h2>
            </div>
            <div className="mt-6 flex flex-col gap-3 sm:flex-row lg:mt-0">
              <Link className="button-primary bg-white text-emerald-800 hover:bg-emerald-50" to="/new-case">
                {translate('Start a check', 'तपासणी सुरू करा')} <ArrowRight size={17} />
              </Link>
              <Link className="button-secondary border-white bg-transparent text-white hover:bg-white/10 hover:text-white" to="/login">
                {translate('Sign in', 'प्रवेश करा')} <ChevronRight size={17} />
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="page-shell pb-10 pt-2 text-sm text-slate-600">
        <div className="flex flex-col gap-3 border-t border-slate-200 pt-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2 font-semibold text-slate-700">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-700 text-white"><Stethoscope size={16} /></span>
            BoviCare AI
          </div>
          <div>© 2026 BoviCare AI</div>
        </div>
      </footer>
    </div>
  )
}
