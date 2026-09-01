# -*- coding: utf-8 -*-
"""
paralaks_data.json (tam veri) -> paralaks_demo.json (küçük alt-küme)
build_frontend (1).py'nin gömdüğü demo veriyi üretir.

Seçim: her pozisyon kovasından 'overall' (CA rating) en yüksek ilk DEMO_PER_BUCKET
oyuncu. meta aynen korunur (popülasyon referans istatistikleri — radar/xscale/
takım reytingi/rol istatistikleri hep TAM veriden gelmeli, demo alt-kümesinden
değil); yalnız meta.buckets[*].count ve meta.total_entries demo sayılarına
güncellenir ki arayüzdeki "kaç oyuncu" göstergeleri gömülü veriyle tutarlı olsun.
"""
import json
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent
SRC = BASE_DIR / "paralaks_data.json"
OUT = BASE_DIR / "paralaks_demo.json"
DEMO_PER_BUCKET = 400          # ~25 MB hedefi (bkz. CLAUDE.md: demo ~25 MB)

with open(SRC, encoding='utf-8') as f:
    data = json.load(f)

by_bucket = defaultdict(list)
for p in data['players']:
    by_bucket[p['bucket']].append(p)

def sort_key(p):
    v = p.get('overall')
    return v if v is not None else -1

demo_players = []
demo_counts = {}
for b, plist in by_bucket.items():
    plist.sort(key=sort_key, reverse=True)
    chosen = plist[:DEMO_PER_BUCKET]
    demo_players.extend(chosen)
    demo_counts[b] = len(chosen)

meta = dict(data['meta'])
meta['buckets'] = {
    b: {**bd, 'count': demo_counts.get(b, 0)}
    for b, bd in meta['buckets'].items()
}
meta['total_entries'] = len(demo_players)
meta['demo'] = True   # frontend/tanılama için: bu meta'nın demo alt-kümesine ait olduğu açık olsun

out = {'meta': meta, 'players': demo_players}
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, separators=(',', ':'))

size_mb = OUT.stat().st_size / (1024 * 1024)
print(f"OK -> {OUT.name}: {len(demo_players)} oyuncu (kova başına <= {DEMO_PER_BUCKET}), {size_mb:.1f} MB")
for b in sorted(demo_counts):
    print(f"  {b}: {demo_counts[b]}")
