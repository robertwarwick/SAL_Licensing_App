import csv, json, re, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser

MONTHS = {
    'january':'01','february':'02','march':'03','april':'04','may':'05','june':'06',
    'july':'07','august':'08','september':'09','october':'10','november':'11','december':'12',
    'jan':'01','feb':'02','mar':'03','apr':'04','jun':'06','jul':'07','aug':'08',
    'sep':'09','oct':'10','nov':'11','dec':'12',
}

def parse_date(s):
    if not s: return None
    s = s.strip()
    if re.match(r'^\d{4}-\d{2}-\d{2}$', s): return s
    m = re.search(r'([a-z]+)\s+(?:cy)?(\d{4})', s.lower())
    if m and m.group(1) in MONTHS:
        return f"{m.group(2)}-{MONTHS[m.group(1)]}-01"
    return None

# Ordered most-specific first so Copilot Studio beats M365 Copilot on dual-tagged items
PROD_PRIORITY = [
    ('Microsoft Copilot Studio', 'Copilot Studio'),
    ('Power Automate',           'Power Automate'),
    ('Power Apps',               'Power Apps'),
    ('Microsoft Copilot (Microsoft 365)', 'M365 Copilot'),
]
STATUSES  = {'Rolling out', 'In development'}
PLATFORMS = {'Desktop', 'Web'}


# ── M365 roadmap CSV ──────────────────────────────────────────────

def parse_m365_csv(path):
    items = []
    with open(path, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            prods  = [p.strip() for p in row.get('Tags - Product', '').split(',')]
            plats  = [p.strip() for p in row.get('Tags - Platform', '').split(',')]
            status = row.get('Status', '').strip()
            match  = next(((n, l) for n, l in PROD_PRIORITY if n in prods), None)
            if not match: continue
            if status not in STATUSES: continue
            if not any(p in PLATFORMS for p in plats): continue
            raw_date = row.get('Release', '') or row.get('General availability', '')
            date = parse_date(raw_date)
            if not date: continue
            title   = row.get('Description', '').strip() or 'Untitled'
            desc    = row.get('Details', '').strip() or title
            feat_id = row.get('Feature ID', '').strip()
            items.append({
                'p':      match[1],
                'title':  title,
                'sum':    desc[:107] + '…' if len(desc) > 110 else desc,
                'desc':   desc,
                'status': status,
                'plat':   ', '.join(p for p in plats if p in PLATFORMS),
                'date':   date,
                'url':    row.get('More Info', '') or
                          f'https://www.microsoft.com/en-gb/microsoft-365/roadmap?filters=&searchterms={feat_id}',
            })
    return items


# ── Power Platform release plan HTML scraper ──────────────────────

class _TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self._t = self._r = self._c = False
        self._cur_t = []; self._cur_r = []
        self._txt = []; self._href = None; self._check = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'table':   self._t = True;  self._cur_t = []
        elif tag == 'tr' and self._t:  self._r = True;  self._cur_r = []
        elif tag in ('td','th') and self._r:
            self._c = True; self._txt = []; self._href = None; self._check = False
        elif tag == 'a' and self._c and not self._href:
            h = a.get('href','')
            if h and not h.startswith('#'): self._href = h
        elif tag == 'img' and self._c:
            src = a.get('src',''); alt = a.get('alt','').lower()
            if 'checkmark' in src or 'checkmark' in alt: self._check = True

    def handle_endtag(self, tag):
        if tag == 'table':
            self._t = False
            if self._cur_t: self.tables.append(self._cur_t)
        elif tag == 'tr' and self._r:
            self._r = False
            if self._cur_r: self._cur_t.append(self._cur_r)
        elif tag in ('td','th') and self._c:
            self._c = False
            text = ' '.join(self._txt).strip()
            if self._check: text = '✓' + (' ' + text if text else '')
            self._cur_r.append({'text': text, 'href': self._href})

    def handle_data(self, data):
        if self._c:
            t = data.strip()
            if t: self._txt.append(t)


def fetch_pp_items(url, product_label):
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"  Warning: could not fetch {product_label}: {e}")
        return []

    parser = _TableParser()
    parser.feed(html)

    items = []
    for table in parser.tables:
        if len(table) < 2: continue
        hdr = table[0]
        if len(hdr) < 4: continue
        if 'feature' not in hdr[0]['text'].lower(): continue

        for row in table[1:]:
            if len(row) < 4: continue
            feat = row[0]; ga = row[3]
            title   = feat['text'].strip()
            href    = feat['href'] or ''
            ga_text = ga['text'].strip()
            if not title or not ga_text: continue
            if '✓' in ga_text: continue        # already released
            date = parse_date(ga_text)
            if not date: continue
            status = 'Rolling out' if date <= today else 'In development'
            if href and not href.startswith('http'):
                href = 'https://learn.microsoft.com' + href
            items.append({
                'p':      product_label,
                'title':  title,
                'sum':    title[:107] + '…' if len(title) > 110 else title,
                'desc':   title,
                'status': status,
                'plat':   'Web',
                'date':   date,
                'url':    href or url,
            })

    print(f"  {product_label} (release plan): {len(items)} items")
    return items


# ── Main ──────────────────────────────────────────────────────────

m365_items = parse_m365_csv('roadmap.csv')
print(f"M365 CSV: {len(m365_items)} items")
from collections import Counter
print(' ', Counter(i['p'] for i in m365_items))

pp_items = []
pp_items += fetch_pp_items(
    'https://learn.microsoft.com/en-us/power-platform/release-plan/2026wave1/power-apps/planned-features',
    'Power Apps',
)
pp_items += fetch_pp_items(
    'https://learn.microsoft.com/en-us/power-platform/release-plan/2026wave1/microsoft-copilot-studio/planned-features',
    'Copilot Studio',
)

# Deduplicate: drop PP items whose title already appears in M365 data for the same product
m365_titles = {(i['p'], i['title']) for i in m365_items}
pp_items = [i for i in pp_items if (i['p'], i['title']) not in m365_titles]

all_items = m365_items + pp_items
print(f"Total: {len(all_items)} items")
print(' ', Counter(i['p'] for i in all_items))

out = {'items': all_items, 'updated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
with open('roadmap-data.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False)
