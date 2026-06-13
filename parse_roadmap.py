import csv, json, re, sys
from datetime import datetime, timezone

PRODS = {
    'Microsoft Copilot (Microsoft 365)': 'M365 Copilot',
    'Microsoft Copilot Studio': 'Copilot Studio',
    'Power Automate': 'Power Automate',
    'Power Apps': 'Power Apps',
}
STATUSES = {'Rolling out', 'In development'}
PLATFORMS = {'Desktop', 'Web'}
MONTHS = {
    'january':'01','february':'02','march':'03','april':'04','may':'05','june':'06',
    'july':'07','august':'08','september':'09','october':'10','november':'11','december':'12',
    'jan':'01','feb':'02','mar':'03','apr':'04','jun':'06','jul':'07','aug':'08',
    'sep':'09','oct':'10','nov':'11','dec':'12',
}

def parse_date(s):
    if not s: return None
    if re.match(r'^\d{4}-\d{2}-\d{2}$', s): return s
    m = re.search(r'([a-z]+)\s+(?:cy)?(\d{4})', s.lower())
    if m and m.group(1) in MONTHS:
        return f"{m.group(2)}-{MONTHS[m.group(1)]}-01"
    return None

items = []
with open('roadmap.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        prods = [p.strip() for p in row.get('Tags - Product', '').split(',')]
        plats = [p.strip() for p in row.get('Tags - Platform', '').split(',')]
        status = row.get('Status', '').strip()
        match_prod = next((p for p in prods if p in PRODS), None)
        if not match_prod: continue
        if status not in STATUSES: continue
        if not any(p in PLATFORMS for p in plats): continue
        raw_date = row.get('Release', '') or row.get('General availability', '')
        date = parse_date(raw_date)
        if not date: continue
        title = row.get('Description', '').strip() or 'Untitled'
        desc = row.get('Details', '').strip() or title
        feat_id = row.get('Feature ID', '').strip()
        items.append({
            'p': PRODS[match_prod],
            'title': title,
            'sum': desc[:107] + '…' if len(desc) > 110 else desc,
            'desc': desc,
            'status': status,
            'plat': ', '.join(p for p in plats if p in PLATFORMS),
            'date': date,
            'url': row.get('More Info', '') or
                   f'https://www.microsoft.com/en-gb/microsoft-365/roadmap?filters=&searchterms={feat_id}',
        })

out = {'items': items, 'updated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
with open('roadmap-data.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False)

print(f"Wrote {len(items)} items to roadmap-data.json")
