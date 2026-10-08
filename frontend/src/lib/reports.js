import { api } from './api'

export async function downloadCaseReport(caseId, language = 'en') {
  const response = await api.get(`/cases/${caseId}/report`, { params: { language }, responseType: 'blob' })
  const url = URL.createObjectURL(response.data)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `bovicare-case-${caseId}.pdf`
  anchor.style.display = 'none'
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  window.setTimeout(() => URL.revokeObjectURL(url), 30000)
}
