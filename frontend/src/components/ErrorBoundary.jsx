import { Component } from 'react'
import { AlertTriangle, RotateCcw } from 'lucide-react'
import { Link } from 'react-router-dom'
import { LanguageContext } from '../auth/LanguageContext'

export default class ErrorBoundary extends Component {
  static contextType = LanguageContext
  state = { hasError: false }

  static getDerivedStateFromError() { return { hasError: true } }

  componentDidCatch(error) {
    // Keep the route boundary observable in browser developer tools without exposing details to farmers.
    console.error('BoviCare route render failed', error)
  }

  render() {
    if (!this.state.hasError) return this.props.children
    const translate = this.context?.translate || (english => english)
    return <main className="grid min-h-screen place-items-center bg-[#F7F5EF] p-5">
      <section className="surface w-full max-w-lg p-8 text-center">
        <AlertTriangle className="mx-auto text-amber-700" size={24} />
        <h1 className="mt-4 text-2xl font-bold">{translate('Something went wrong', 'कुछ गलत हुआ', 'काहीतरी चूकले')}</h1>
        <p className="mt-2 text-slate-600">{translate('This page could not be displayed. Try reloading it or return to your dashboard.', 'यह पृष्ठ नहीं दिखाया जा सका। फिर से लोड करें या डैशबोर्ड पर लौटें।', 'हे पृष्ठ दाखवता आले नाही. पुन्हा लोड करा किंवा आढाव्यावर परत जा.')}</p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <button className="button-secondary" onClick={() => window.location.reload()}><RotateCcw size={16} />{translate('Reload', 'फिर से लोड करें', 'पुन्हा लोड करा')}</button>
          <Link className="button-primary" to={this.props.home}>{translate('Back to dashboard', 'डैशबोर्ड पर लौटें', 'आढाव्यावर परत जा')}</Link>
        </div>
      </section>
    </main>
  }
}
