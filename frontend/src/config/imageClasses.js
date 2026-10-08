// Display metadata for the frozen seven-class image model. This file does not
// load weights, alter inference, or combine outputs from separate models.
export const IMAGE_CLASS_MAPPING = Object.freeze({
  HEALTHY: {
    displayName: { en: 'Healthy appearance', hi: 'स्वस्थ दिखाई देता है', mr: 'निरोगी दिसते' },
    severity: 'LOW',
    characteristics: {
      en: ['No obvious visible sign in the submitted image'],
      hi: ['दी गई तस्वीर में कोई स्पष्ट बाहरी संकेत नहीं दिखता'],
      mr: ['दिलेल्या छायाचित्रात स्पष्ट बाह्य लक्षण दिसत नाही'],
    },
  },
  LSD: {
    displayName: { en: 'Lumpy skin disease', hi: 'लम्पी त्वचा रोग', mr: 'लम्पी त्वचा रोग' },
    severity: 'HIGH',
    characteristics: {
      en: ['Firm skin nodules; fever and reduced milk yield may also occur'],
      hi: ['त्वचा पर कड़ी गांठें; बुखार और दूध में कमी भी हो सकती है'],
      mr: ['त्वचेवर घट्ट गाठी; ताप आणि दूध कमी होणेही संभवते'],
    },
  },
  RINGWORM: {
    displayName: { en: 'Ringworm (dermatophytosis)', hi: 'दाद (डर्माटोफाइटोसिस)', mr: 'गजकर्ण (डर्मॅटोफायटोसिस)' },
    severity: 'MEDIUM',
    characteristics: {
      en: ['Scaly, crusted patches with areas of hair loss'],
      hi: ['पपड़ीदार धब्बे और उन जगहों पर बाल झड़ना'],
      mr: ['खवलेदार, खपलीयुक्त डाग आणि त्या भागातील केस गळणे'],
    },
  },
  FMD: {
    displayName: { en: 'Foot-and-mouth disease', hi: 'खुरपका-मुँहपका रोग', mr: 'फूट-अँड-माउथ रोग' },
    severity: 'HIGH',
    characteristics: {
      en: ['Fever and blisters or sores around the mouth, feet, or teats'],
      hi: ['बुखार और मुँह, खुरों या थनों के आसपास छाले या घाव'],
      mr: ['ताप आणि तोंड, खुर किंवा कासेजवळ फोड अथवा जखमा'],
    },
  },
  IBK: {
    displayName: { en: 'Infectious bovine keratoconjunctivitis', hi: 'संक्रामक गोजातीय नेत्रशोथ', mr: 'संसर्गजन्य गोवंशीय नेत्रशोथ' },
    severity: 'MEDIUM',
    characteristics: {
      en: ['Watery or painful eyes, light sensitivity, or cloudy cornea'],
      hi: ['आँखों से पानी, दर्द, रोशनी से परेशानी या धुंधली कॉर्निया'],
      mr: ['डोळ्यांतून पाणी, वेदना, प्रकाशाची संवेदनशीलता किंवा धूसर नेत्रपटल'],
    },
  },
  PEDICULOSIS: {
    displayName: { en: 'Lice infestation (pediculosis)', hi: 'जूँ का प्रकोप (पेडिक्युलोसिस)', mr: 'उवांचा प्रादुर्भाव (पेडिक्युलोसिस)' },
    severity: 'MEDIUM',
    characteristics: {
      en: ['Itching, hair loss, or visible lice and eggs'],
      hi: ['खुजली, बाल झड़ना या जूँ और अंडे दिखाई देना'],
      mr: ['खाज, केस गळणे किंवा उवा आणि अंडी दिसणे'],
    },
  },
  DERMATOPHILOSIS: {
    displayName: { en: 'Dermatophilosis', hi: 'डर्माटोफिलोसिस', mr: 'डर्मॅटोफिलोसिस' },
    severity: 'MEDIUM',
    characteristics: {
      en: ['Matted hair, crusts, or wart-like skin lesions'],
      hi: ['चिपके हुए बाल, पपड़ी या मस्से जैसे त्वचा के घाव'],
      mr: ['चिकटलेले केस, खपल्या किंवा मस्स्यासारखे त्वचेवरील घाव'],
    },
  },
})

export const IMAGE_CLASS_ORDER = Object.freeze([
  'HEALTHY', 'LSD', 'RINGWORM', 'FMD', 'IBK', 'PEDICULOSIS', 'DERMATOPHILOSIS',
])

export const SEPARATE_MODEL_OUTPUTS = Object.freeze({
  mastitis: {
    displayName: { en: 'Mastitis assessment', hi: 'मास्टाइटिस आकलन', mr: 'स्तनदाह मूल्यांकन' },
    availability: 'available',
    note: {
      en: 'Provided by a separate model output; it is not one of the seven image classes.',
      hi: 'यह अलग मॉडल का परिणाम है; यह सात छवि वर्गों में शामिल नहीं है।',
      mr: 'हा स्वतंत्र मॉडेलचा परिणाम आहे; तो सात प्रतिमा वर्गांपैकी नाही.',
    },
  },
})

export const IMAGE_CLASS_DISCLAIMER = Object.freeze({
  en: 'Image labels and severity are decision-support information, not a confirmed diagnosis. Ask a veterinarian to assess the animal.',
  hi: 'छवि के लेबल और गंभीरता केवल निर्णय-सहायता की जानकारी हैं, पक्का निदान नहीं। पशु का आकलन पशुचिकित्सक से करवाएँ।',
  mr: 'प्रतिमेवरील लेबले आणि तीव्रता ही निर्णय-सहाय्य माहिती आहे, निश्चित निदान नाही. जनावराची तपासणी पशुवैद्यांकडून करून घ्या.',
})
