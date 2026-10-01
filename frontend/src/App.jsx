import { Route, Routes } from 'react-router-dom'
import AppShell from './components/AppShell'
import ProtectedRoute from './auth/ProtectedRoute'
import { LoginPage, RegisterPage } from './pages/AuthPage'
import CattleManagement from './pages/CattleManagement'
import Dashboard from './pages/Dashboard'
import DiagnosisResult from './pages/DiagnosisResult'
import Landing from './pages/Landing'
import NewCase from './pages/NewCase'
import VeterinaryCaseDetails from './pages/VeterinaryCaseDetails'
import VeterinaryDashboard from './pages/VeterinaryDashboard'

export default function App() {
  const farmer = page => <ProtectedRoute roles={['farmer']}><AppShell>{page}</AppShell></ProtectedRoute>; const doctor = page => <ProtectedRoute roles={['doctor']}><AppShell>{page}</AppShell></ProtectedRoute>
  return <Routes><Route path="/" element={<Landing />} /><Route path="/login" element={<LoginPage />} /><Route path="/register" element={<RegisterPage />} /><Route path="/dashboard" element={farmer(<Dashboard />)} /><Route path="/cattle" element={farmer(<CattleManagement />)} /><Route path="/new-case" element={farmer(<NewCase />)} /><Route path="/diagnosis/:caseId" element={farmer(<DiagnosisResult />)} /><Route path="/veterinary" element={doctor(<VeterinaryDashboard />)} /><Route path="/veterinary/cases/:caseId" element={doctor(<VeterinaryCaseDetails />)} /><Route path="*" element={<Landing />} /></Routes>
}
