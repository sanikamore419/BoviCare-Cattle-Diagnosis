const diseaseNames = {
  HEALTHY: { en: 'Healthy', mr: 'निरोगी (Healthy)' },
  LSD: { en: 'LSD', mr: 'लम्पी स्किन डिसीज (LSD)' },
  RINGWORM: { en: 'Ringworm', mr: 'रिंगवर्म (Ringworm)' },
  FMD: { en: 'FMD', mr: 'फूट-अँड-माउथ डिसीज (FMD)' },
  'foot-and-mouth': { en: 'Foot-and-mouth', mr: 'फूट-अँड-माउथ डिसीज (Foot-and-mouth)' },
  foot_and_mouth: { en: 'Foot and mouth', mr: 'फूट-अँड-माउथ डिसीज (Foot and mouth)' },
  'Lumpy Skin': { en: 'Lumpy Skin', mr: 'लम्पी स्किन (Lumpy Skin)' },
  'Normal Skin': { en: 'Normal Skin', mr: 'सामान्य त्वचा (Normal Skin)' },
  mastitis: { en: 'Mastitis', mr: 'स्तनदाह (Mastitis)' },
  Mastitis: { en: 'Mastitis', mr: 'स्तनदाह (Mastitis)' },
  'No Mastitis': { en: 'No Mastitis', mr: 'No Mastitis' },
}

const symptomNames = {
  'loss of appetite': 'भूक न लागणे',
  lethargy: 'सुस्ती',
  'weight loss': 'वजन कमी होणे',
  coughing: 'खोकला',
  'difficulty breathing': 'श्वास घेण्यास त्रास',
  'nasal discharge': 'नाकातून स्राव',
  diarrhea: 'जुलाब',
  bloating: 'पोट फुगणे',
  'reduced rumination': 'रवंथ कमी होणे',
  'cannot stand': 'उभे राहता न येणे',
  seizure: 'आकडी येणे',
  'severe bleeding': 'जास्त रक्तस्राव',
}

function readableLabel(label) {
  const value = String(label || '').replaceAll('_', ' ').replaceAll('-', ' ')
  return value ? value[0].toLocaleUpperCase() + value.slice(1) : ''
}

export function farmerDiseaseLabel(label, language = 'en') {
  if (!label) return language === 'mr' ? 'निकाल उपलब्ध नाही' : 'No result available'
  return diseaseNames[label]?.[language] || readableLabel(label)
}

export function farmerSymptomLabel(label, language = 'en') {
  if (language === 'en') return readableLabel(label)
  return symptomNames[String(label).toLowerCase()] || readableLabel(label)
}

export function farmerRiskLabel(level, language = 'en') {
  const risk = String(level || '').toLowerCase()
  const english = ({ high: 'High', moderate: 'Moderate', medium: 'Moderate', low: 'Low' })[risk] || 'Moderate'
  if (language === 'en') return english
  return ({ High: 'जास्त', Moderate: 'मध्यम', Low: 'कमी' })[english]
}
