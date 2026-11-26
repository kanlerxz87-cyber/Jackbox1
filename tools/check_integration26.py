#!/usr/bin/env python3
"""Structural checks only. Does not verify external source content or private facts."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import re

ROOT = Path(__file__).resolve().parents[1]
NEW = [ROOT / 'release-review.html']
OFFICIAL = {'www.census.gov', 'www.conservation.ca.gov', 'osfm.fire.ca.gov',
            'msc.fema.gov', 'www.irs.gov', 'leginfo.legislature.ca.gov',
            'www.investor.gov', 'docs.github.com'}

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.text = text
        self.links, self.ids, self.rows, self.blank_cells = [], set(), [], []
        self.row = None
        self.blank = None
        self.scripts = self.forms = self.h1 = 0
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.add(a['id'])
        for key in ('href', 'src'):
            if a.get(key):
                self.links.append(a[key])
        if tag == 'tr':
            self.row = {'data': False, 'links': []}
        if tag == 'td' and self.row is not None:
            self.row['data'] = True
        if tag == 'a' and self.row is not None:
            self.row['links'].append(a.get('href', ''))
        if tag == 'td' and a.get('data-missing') == 'true':
            self.blank = ''
        self.scripts += tag == 'script'
        self.forms += tag in ('form', 'input', 'textarea')
        self.h1 += tag == 'h1'
    def handle_data(self, data):
        if self.blank is not None:
            self.blank += data
    def handle_endtag(self, tag):
        if tag == 'td' and self.blank is not None:
            self.blank_cells.append(self.blank)
            self.blank = None
        if tag == 'tr' and self.row is not None:
            if self.row['data']:
                self.rows.append(self.row)
            self.row = None


def check_new(page, path):
    errors = []
    if page.h1 != 1:
        errors.append(f'{path.name}: expected one h1')
    if page.scripts or page.forms:
        errors.append(f'{path.name}: unexpected script or personal-input surface')
    for i, row in enumerate(page.rows, 1):
        if not any(urlsplit(u).scheme == 'https' and urlsplit(u).hostname in OFFICIAL
                   for u in row['links']):
            errors.append(f'{path.name}: table row {i} has no official reference')
    if any(x.strip() for x in page.blank_cells):
        errors.append(f'{path.name}: missing-answer cell is not blank')
    text = page.text
    patterns = [r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', r'\b\d{3}-\d{2}-\d{4}\b',
                r'\b\d{4}-\d{3}-\d{3}\b',
                r'\b\d{2,6}\s+[A-Za-z]+\s+(?:Street|Avenue|Boulevard|Road|Drive)\b']
    if any(re.search(pattern, text, re.I) for pattern in patterns):
        errors.append(f'{path.name}: possible personal-information pattern')
    return errors


def main():
    errors = []
    files = sorted(p for p in ROOT.rglob('*.html') if '.git' not in p.parts)
    pages = {p.resolve(): Page(p.read_text()) for p in files}
    links = 0
    for path, page in pages.items():
        for href in page.links:
            u = urlsplit(href)
            if u.scheme or u.netloc:
                continue
            # Repository-relative project site links, not host-root paths.
            if u.path.startswith('/'):
                target = ROOT / u.path.removeprefix('/Jackbox1/').lstrip('/')
            elif not u.path:
                target = path
            else:
                target = path.parent / unquote(u.path)
            target = target.resolve()
            if target.is_dir():
                target /= 'index.html'
            if not target.exists():
                errors.append(f'{path.relative_to(ROOT)}: missing local target {href}')
            elif path in NEW and u.fragment and target in pages and unquote(u.fragment) not in pages[target].ids:
                errors.append(f'{path.name}: missing anchor {href}')
            links += 1
    for path in NEW:
        errors.extend(check_new(pages[path], path))
    # Regression test: a status label alone is NOT an official reference.
    fake = Page('<h1>Test</h1><table><tr><td>Unverified</td></tr></table>')
    assert any('official reference' in x for x in check_new(fake, Path('fixture.html')))
    fake = Page('<h1>Test</h1><td data-missing="true">invented</td>')
    assert any('not blank' in x for x in check_new(fake, Path('fixture.html')))
    if errors:
        print('\n'.join('FAIL ' + x for x in errors))
        return 1
    print(f'PASS: {len(files)} HTML files, {links} local links; new-page table rows officially linked.')
    print('PASS: new-page anchors, privacy-pattern scan, no forms/scripts; negative regression fixtures rejected.')
    print('LIMIT: structure and patterns only, not fresh numerical/source-content verification or a privacy guarantee.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
