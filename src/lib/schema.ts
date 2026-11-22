// schema.org data for the head (JSON-LD). Pallet Euro stands alone: no sameAs, parentOrganization or any other link
// to another company (CLAUDE.md, hard rule 1). Only facts that exist go in: address, phone and founding date are
// added once the owner sends them.
import { SITE } from '../data/site';

const at = (site: URL, path: string) => new URL(path, site).href;

export function organization(site: URL) {
  return {
    '@type': 'Organization',
    '@id': at(site, '/#organization'),
    name: SITE.name,
    url: at(site, '/'),
    logo: at(site, '/favicon.svg'), // temporary mark until the real logo exists
  };
}

export function website(site: URL) {
  return {
    '@type': 'WebSite',
    '@id': at(site, '/#website'),
    name: SITE.name,
    url: at(site, '/'),
    inLanguage: SITE.lang,
    publisher: { '@id': at(site, '/#organization') },
  };
}
