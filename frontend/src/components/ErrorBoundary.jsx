import { Component } from 'react'
import { AlertTriangle, RotateCcw } from 'lucide-react'
import { Link } from 'react-router-dom'

export default class ErrorBoundary extends Component {
  state = { hasError: false }

  static getDerivedStateFromError() { return { hasError: true } }

  componentDidCatch(error) {
    // Keep the route boundary observable in browser developer tools without exposing details to farmers.
    console.error('BoviCare route render failed', error)
  }

  render() {
    if (!this.state.hasError) return this.props.children
    return <main className="grid min-h-screen place-items-center bg-[#F7F5EF] p-5">
      <section className="surface w-full max-w-lg p-8 text-center">
        <AlertTriangle className="mx-auto text-amber-700" size={24} />
        <h1 className="mt-4 text-2xl font-bold">Something went wrong</h1>
        <p className="mt-2 text-slate-600">This page could not be displayed. Try reloading it or return to your dashboard.</p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <button className="button-secondary" onClick={() => window.location.reload()}><RotateCcw size={16} />Reload</button>
          <Link className="button-primary" to={this.props.home}>Back to dashboard</Link>
        </div>
      </section>
    </main>
  }
}
