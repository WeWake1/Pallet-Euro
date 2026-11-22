// PROTOTYPE sample data. Numbers in {{braces}} or with X are placeholders: never publish them.
// Real values come from the owner (docs/decisions.md, round 2 question 4).
export type Cert = {
  id: string;
  name: string;
  short: string;
  issuer: string;
  number: string;
  valid: string;
  icon: string;
  verifyUrl?: string;
  verifyLabel?: string;
};

export const CERTS: Cert[] = [
  {
    id: 'epal',
    name: 'EPAL licence',
    short: 'EPAL',
    issuer: 'European Pallet Association e.V., Düsseldorf',
    number: 'IND-0XX',
    valid: 'Audited by EPAL’s inspectors',
    icon: 'seal-check',
    verifyUrl: 'https://www.epal-pallets.org/eu-en/licensee-search',
    verifyLabel: 'EPAL licensee register',
  },
  {
    id: 'ispm15',
    name: 'ISPM-15 heat treatment',
    short: 'ISPM-15 HT',
    issuer: 'Directorate of Plant Protection, Quarantine & Storage, India',
    number: 'IN-XXX HT',
    valid: 'Valid to Mar 20XX',
    icon: 'fire',
    verifyUrl: 'https://ppqs.gov.in/',
    verifyLabel: 'PPQS',
  },
  {
    id: 'iso9001',
    name: 'ISO 9001:2015',
    short: 'ISO 9001',
    issuer: '{{certification body}}',
    number: '{{certificate no.}}',
    valid: 'Valid to Jun 20XX',
    icon: 'certificate',
    verifyUrl: 'https://www.iafcertsearch.org/',
    verifyLabel: 'IAF CertSearch',
  },
  {
    id: 'fsc',
    name: 'FSC chain of custody',
    short: 'FSC',
    issuer: '{{certification body}}',
    number: 'FSC-C000000',
    valid: 'Valid to Jan 20XX',
    icon: 'tree',
    verifyUrl: 'https://search.fsc.org/',
    verifyLabel: 'FSC certificate search',
  },
  {
    id: 'pefc',
    name: 'PEFC chain of custody',
    short: 'PEFC',
    issuer: '{{certification body}}',
    number: 'PEFC/00-00-000',
    valid: 'Valid to Jan 20XX',
    icon: 'leaf',
    verifyUrl: 'https://www.pefc.org/find-certified',
    verifyLabel: 'PEFC certificate search',
  },
  {
    id: 'iip',
    name: 'Indian Institute of Packaging',
    short: 'IIP',
    issuer: 'Indian Institute of Packaging, Mumbai',
    number: '{{no.}}',
    valid: '{{date}}',
    icon: 'package',
    verifyUrl: 'https://www.iip-in.com/',
    verifyLabel: 'IIP',
  },
  {
    id: 'tm',
    name: 'Registered trade mark',
    short: 'Trade mark',
    issuer: 'Trade Marks Registry, India',
    number: '{{application no.}}',
    valid: '{{status}}',
    icon: 'trademark',
    verifyUrl: 'https://tmrsearch.ipindia.gov.in/estatus',
    verifyLabel: 'IP India e-status',
  },
  {
    id: 'sop',
    name: 'Standard operating procedures',
    short: 'SOP',
    issuer: 'Pallet Euro quality system',
    number: '{{SOP set}}',
    valid: 'Available on request',
    icon: 'clipboard-text',
  },
];

// Official EPAL figures (EPAL product sheets) where they exist.
export const RANGE = [
  { id: 'epal1', code: 'EPAL 1', name: 'Euro pallet', L: 1200, W: 800, H: 144, swl: 1500, stack: 5500, kg: 25, boards: 11, blocks: 9, nails: 78 },
  { id: 'epal2', code: 'EPAL 2', name: 'Industrial pallet', L: 1200, W: 1000, H: 162, swl: 1250, stack: 4250, kg: 35, boards: 17, blocks: 9, nails: 133 },
  { id: 'epal3', code: 'EPAL 3', name: 'Industrial pallet', L: 1000, W: 1200, H: 144, swl: 1500, stack: 4500, kg: 30, boards: 13, blocks: 9, nails: 84 },
  { id: 'cp1', code: 'CP1', name: 'Chemical pallet', L: 1000, W: 1200, H: 138, boards: 15, blocks: 9, nails: 81 },
  { id: 'cp3', code: 'CP3', name: 'Chemical pallet', L: 1140, W: 1140, H: 138, boards: 15, blocks: 9, nails: 81 },
  { id: 'cp6', code: 'CP6', name: 'Chemical pallet', L: 1200, W: 1000, H: 156, boards: 20, blocks: 9, nails: 84 },
  { id: 'cp7', code: 'CP7', name: 'Chemical pallet', L: 1300, W: 1100, H: 156, boards: 22, blocks: 9, nails: 96 },
  { id: 'collar', code: 'PC-1208', name: 'Pallet collar', L: 1200, W: 800, H: 195 },
  { id: 'gma', code: 'GMA', name: 'GMA pallet, 48 × 40 in', L: 1220, W: 1016, H: 132 },
  { id: 'hw01', code: 'HW-01', name: 'Hardwood pallet', L: 1000, W: 1200, H: 161 },
  { id: 'pw02', code: 'PW-02', name: 'Pinewood pallet', L: 1000, W: 1200, H: 130 },
];
