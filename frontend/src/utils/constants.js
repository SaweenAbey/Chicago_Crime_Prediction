export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const CRIME_TYPES = [
  'THEFT',
  'BATTERY',
  'CRIMINAL DAMAGE',
  'ASSAULT',
  'DECEPTIVE PRACTICE',
  'OTHER OFFENSE',
  'MOTOR VEHICLE THEFT',
  'ROBBERY',
  'BURGLARY',
  'NARCOTICS',
  'WEAPONS VIOLATION',
  'PUBLIC PEACE VIOLATION',
  'CRIMINAL TRESPASS',
  'OFFENSE INVOLVING CHILDREN',
  'SEX OFFENSE',
  'INTERFERENCE WITH PUBLIC OFFICER',
  'HOMICIDE',
  'ARSON',
  'CRIMINAL SEXUAL ASSAULT',
  'PROSTITUTION'
];

export const LOCATION_DESCRIPTIONS = [
  'STREET',
  'RESIDENCE',
  'APARTMENT',
  'SIDEWALK',
  'OTHER',
  'PARKING LOT / GARAGE(NON.RESID.)',
  'SMALL RETAIL STORE',
  'RESTAURANT',
  'ALLEY',
  'RESIDENCE-GARAGE',
  'COMMERCIAL / BUSINESS OFFICE',
  'VEHICLE NON-COMMERCIAL',
  'GROCERY FOOD STORE',
  'DEPARTMENT STORE',
  'GAS STATION',
  'PARK PROPERTY',
  'BANK',
  'CTA PLATFORM / TRAIN',
  'HIGHWAY / EXPRESSWAY',
  'HOSPITAL BUILDING / GROUNDS'
];

export const CHICAGO_COMMUNITY_AREAS = [
  { id: 1, name: 'Rogers Park' },
  { id: 8, name: 'Near North Side' },
  { id: 24, name: 'West Town' },
  { id: 25, name: 'Austin' },
  { id: 28, name: 'Near West Side' },
  { id: 32, name: 'Loop (Downtown)' },
  { id: 43, name: 'South Shore' },
  { id: 49, name: 'Roseland' },
  { id: 67, name: 'West Englewood' },
  { id: 68, name: 'Englewood' },
  { id: 71, name: 'Auburn Gresham' }
];

export const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: 'LayoutDashboard' },
  { id: 'predict', label: 'Crime Predictor', icon: 'BrainCircuit' },
  { id: 'trends', label: 'Historical Trends', icon: 'TrendingUp' },
  { id: 'map', label: 'Hotspot Map', icon: 'MapPin' }
];
