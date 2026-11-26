#!/usr/bin/env python3
"""Structural checks only; never certifies source accuracy or forecast validity."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import re
ROOT = Path(__file__).resolve().parents[1]
errors=[]
class Check(HTMLParser):
    def __init__(self,path):
        super().__init__(); self.path=path; self.rows=[]; self.row=None; self.ids=set(); self.refs=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.add(a['id'])
        if tag=='tr':self.row=[]
        if tag=='a' and self.row is not None:self.row.append(a.get('href',''))
        if tag=='script':errors.append(f'{self.path}: script not permitted in integration pages')
        for key in ('href','src'):
            if key not in a:continue
            u=urlsplit(a[key])
            if u.scheme:
                if u.scheme!='https':errors.append(f'{self.path}: non-HTTPS link')
            elif u.path:
                target=(ROOT/self.path).parent/unquote(u.path)
                if not target.is_file():errors.append(f'{self.path}: missing {target}')
            elif u.fragment:self.refs.append(u.fragment)
        if any(k.startswith('on') for k in a):errors.append('inline event handler')
    def handle_endtag(self,tag):
        if tag=='tr' and self.row is not None:self.rows.append(self.row);self.row=None
for name in ('index.html','integration-review.html'):
    text=(ROOT/name).read_text(); p=Check(name);p.feed(text)
    if not all(f in p.ids for f in p.refs):errors.append(f'{name}: broken fragment')
    if any(not r for r in p.rows[1:]):errors.append(f'{name}: unsourced data row')
    if re.search(r'(localStorage|sessionStorage|fetch\(|XMLHttpRequest|<form|<input|<iframe)',text):errors.append(f'{name}: intake, persistence or network code')
    if 'name="viewport"' not in text:errors.append(f'{name}: viewport absent')
    print(f'{name}: {len(p.rows)-1} evidence-linked rows checked')
# Whole-repository internal file targets, including retained historical trees.
count=0
for path in ROOT.rglob('*.html'):
    if '.git' in path.parts:continue
    class Links(HTMLParser):
        def handle_starttag(self,tag,attrs):
            global count
            for k,v in attrs:
                if k not in ('href','src') or not v:continue
                u=urlsplit(v)
                if u.scheme or u.netloc or not u.path or u.path.startswith('/'):continue
                target=path.parent/unquote(u.path)
                count+=1
                if not target.exists():errors.append(f'{path.relative_to(ROOT)}: missing {v}')
    Links().feed(path.read_text())
print(f'Whole repository: {count} relative link targets checked')
if errors:
    print('\n'.join(errors));raise SystemExit(1)
print('PASS — structural checks only; no factual verification implied')
