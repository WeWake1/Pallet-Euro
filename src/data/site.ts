// Company facts and site-wide settings, in one place. A value in {{braces}} is a visible placeholder until the owner
// sends the real one (docs/decisions.md, round 2): never replace a placeholder with a guess (CLAUDE.md, hard rule 4).
// The domain lives in astro.config.mjs (`site`).

// The launch gate. false: every page says noindex and robots.txt blocks crawlers. Set it to true only when the EPAL
// licence certificate exists and the launch blockers in docs/decisions.md are cleared (CLAUDE.md, hard rule 2).
export const LAUNCHED = false;

export const SITE = {
  name: 'Pallet Euro Packaging',
  lang: 'en-IN',
  locale: 'en_IN',
  address: '{{factory address}}',
  phone: '{{phone}}',
  email: '{{email}}',
  whatsapp: '', // digits with the country code (91…); while empty, the WhatsApp buttons lead to the contact page
};

export const QUOTE_HREF = '/contact/';

export const NAV = [
  { href: '/products/', label: 'Products' },
  { href: '/certifications/', label: 'Certifications' },
  { href: '/about/', label: 'About' },
  { href: '/contact/', label: 'Contact' },
];

export const FOOTER_NAV = [...NAV.slice(0, 2), { href: '/guides/', label: 'Guides' }, ...NAV.slice(2), { href: '/privacy/', label: 'Privacy' }];

export const isPlaceholder = (v: string) => v.startsWith('{{');
export const whatsappHref = () => (SITE.whatsapp ? `https://wa.me/${SITE.whatsapp}` : QUOTE_HREF);
