import { api } from './api'

export async function downloadCaseReport(caseId, language = 'en') {
  const response = await api.get(`/cases/${caseId}/report`, { params: { language }, responseType: 'blob' })
  const url = URL.createObjectURL(response.data)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `bovicare-case-${caseId}.pdf`
  anchor.click()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}
