# -*- coding: utf-8 -*-
"""
PARALAKS — MVP Motoru (Adım 1)
Girdi : TUM_LIGLER_eslesmeler.xlsx (sheet: Eslesmeler)
Çıktı : paralaks_data.json  (frontend bunu okuyacak)

İki sistem:
  RADAR     = StatsLook gerçek maç metrikleri -> pozisyon kovası içi yüzdelik (percentile)
  BENZERLIK = FM attribute'ları -> arşetip frekans-ağırlıklı vektör -> kova içi cosine similarity
"""
import re, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

# Windows konsolu genelde cp1254/cp1252 gibi dar bir codepage kullanır ve script'teki
# Türkçe/matematiksel karakterleri (−, ı, ş, ğ...) print ederken UnicodeEncodeError ile
# çöker. stdout/stderr'i UTF-8'e zorla; reconfigure yoksa (ör. çıktı bir yere pipe'landıysa
# ve stream sarmalanmışsa) sessizce devam et.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        pass

BASE_DIR = Path(__file__).resolve().parent

SRC = str(BASE_DIR / "bigstatxdb_v8.xlsx")
SHEET = "Sheet1"
ROLLER_JSON = str(BASE_DIR / "roller.json")
UYUM_KALIBRASYON_JSON = str(BASE_DIR / "uyum_kalibrasyon.json")

# BigStatX 10 granüler kova
POS10 = ['GK','CB','LB','RB','DM','CM','AM','LW','RW','ST']
# radar/arşetip/benzerlik attribute setleri için taban kova
BASE  = {'GK':'GK','CB':'CB','LB':'FB','RB':'FB','DM':'CM','CM':'CM','AM':'CM','LW':'FW','RW':'FW','ST':'ST'}
# FM granular (parse_pos çıktısı) -> 10 kova
FM2B  = {'GK':'GK','CB':'CB','LB':'LB','RB':'RB','DM':'DM','CM':'CM','AMC':'AM',
         'LM':'LW','RM':'RW','LW':'LW','RW':'RW','ST':'ST'}
# FC pozisyon kodları (FC_En İyi / FC_Pozisyon / FC_Club position) -> 10 kova
FC2B  = {'KL':'GK',
         'STP':'CB','SĞMB':'CB','SLMB':'CB','MB':'CB',
         'SĞB':'RB','SĞKB':'RB','SLB':'LB','SLKB':'LB',
         'MDO':'DM','SDO':'DM','SĞDO':'DM',
         'MO':'CM','SLMO':'CM','SĞMO':'CM',
         'MOO':'AM','SLOO':'AM','SĞOO':'AM',
         'SĞO':'RW','SĞK':'RW','SLO':'LW','SLK':'LW',
         'SNT':'ST','SĞS':'ST','SLST':'ST','SLF':'ST','SĞF':'ST','OF':'ST'}
# YDK (yedek) / REZ (rezerv) ilk-11 slotu değildir -> kovaya eşlenmez
MIN_DK = 600          # radar percentile güvenilirlik filtresi
TOPN   = 60           # explorer/benzer havuzu (daha geniş liste + filtre payı)

# --- BENZERLİK: "Rol-İmza" (pozisyon-içi percentile profili) ---
# ŞEKİL = merkezlenmiş percentile cosine (genel profil dağılımı)
# SPIKE = ≥SPIKE_T percentile "imza" özelliklerinin örtüşmesi (öne çıkan yetenekler)
SHAPE_W  = 0.5        # şekil ağırlığı
SPIKE_W  = 0.5        # spike (öne çıkan özellik) ağırlığı
SPIKE_T  = 70.0       # imza eşiği: percentile ≥70 olan özellikler oyuncunun kimliği
CA_LIGHT = 0.05       # CA seviyesinin benzerliğe HAFİF etkisi (|ΔCA| * CA_LIGHT puan düşer)
HEIGHT_MAX = 8        # boy sert filtresi: |Δboy| > 8cm ise benzerlik/future'dan elenir (±6 etkisiz, tampon 6-8)
WK_AGE = 23           # wonderkid sınırı: future yalnız yaş < 23 oyuncuda
EST_AGE = 26          # olgun oyuncu eşiği: genç-yetenek (tersine) yalnız yaş >= 26
FUT_CA_MAX = 18       # future: aday ile oyuncu arası CA farkı bu kadarı geçemez (absürt sıçrama)

# ----------------------------------------------------------------------------
# 1) POZİSYON -> 6 KOVA  (FM_Mevki birincil, SL_Poz fallback)
# ----------------------------------------------------------------------------
def parse_buckets(mevki):
    b = set()
    if not isinstance(mevki, str) or not mevki.strip():
        return b
    area = ''.join(re.findall(r'\((.*?)\)', mevki))
    has_center = 'M' in area
    has_side   = ('Sl' in area) or ('Sğ' in area)
    codes = [c.strip().upper() for c in re.split(r'[ ,/]+', re.sub(r'\(.*?\)', '', mevki)) if c.strip()]
    for c in codes:
        if   c == 'KL': b.add('GK')
        elif c == 'ST': b.add('ST')
        elif c == 'KB': b.add('FB')
        elif c == 'D':
            if has_center: b.add('CB')
            if has_side:   b.add('FB')      # D yan oynuyorsa bek olarak da listele
        elif c in ('DOS', 'OS', 'OOS'):
            if has_center: b.add('CM')
            if has_side:   b.add('FW')      # yan oynuyorsa kanat olarak da listele
    return b

SLP = {'GK':'GK','CB':'CB','LB':'FB','RB':'FB','DM':'CM','CM':'CM','AM':'CM',
       'LM':'FW','RM':'FW','LW':'FW','RW':'FW','ST':'ST','SS':'ST'}

def parse_pos(mevki):
    """granular pozisyon, FM SIRASIYLA (ilk = en iyi/doğal mevki): GK,CB,LB,RB,DM,CM,LM,RM,AMC,LW,RW,ST"""
    out = []
    def add(x):
        if x not in out: out.append(x)
    if not isinstance(mevki, str) or not mevki.strip():
        return out
    for seg in mevki.split(','):
        seg = seg.strip()
        area = ''.join(re.findall(r'\((.*?)\)', seg))
        codes = [c.strip().upper() for c in re.split(r'[ /]+', re.sub(r'\(.*?\)', '', seg)) if c.strip()]
        M, L, R = ('M' in area), ('Sl' in area), ('Sğ' in area)
        if not (M or L or R): M = True            # alansız -> merkez varsay
        for c in codes:
            if   c == 'KL': add('GK')
            elif c == 'ST': add('ST')
            elif c == 'D':
                if M: add('CB')
                if L: add('LB')
                if R: add('RB')
            elif c == 'KB':
                if L: add('LB')
                if R: add('RB')
                if M and not (L or R): add('LB'); add('RB')
            elif c == 'DOS': add('DM')
            elif c == 'OS':
                if M: add('CM')
                if L: add('LM')
                if R: add('RM')
            elif c == 'OOS':
                if M: add('AMC')
                if L: add('LW')
                if R: add('RW')
    return out

# ----------------------------------------------------------------------------
# 2) RADAR METRİK SETLERİ (master data -> SL kolonları)  inv=True: düşük iyi
# ----------------------------------------------------------------------------
RADAR = {
 'GK': [('Kurtarış','SL_Kurtarışlar'),('Yenen Gol','SL_Kaleci Yediği Gol',True),
        ('C.S. İçi Kurtarış','SL_Ceza Sahası İçi Kurtarışlar'),('Yumruklama','SL_Yumruklama'),
        ('Hava Topu Hakimiyeti','SL_İyi Hava Topu Hakimiyeti'),('Uzun Top','SL_Uzun Toplar'),('Pas','SL_Toplam Pas')],
 'CB': [('Müdahale','SL_Müdahaleler'),('Top Kesme','SL_Top Kesme'),('Uzaklaştırma','SL_Uzaklaştırmalar'),
        ('Hava Topu Kazanma','SL_Kazanılan Hava Topu Mücadelesi'),('Hava Topu %','SL_Hava Topu Mücadelesi Kazanma Yüzdesi'),
        ('Şut Bloklama','SL_Engellenen Şutlar'),('Top Kazanma','SL_Top Kazanma'),('Pas','SL_Toplam Pas'),
        ('Uzun Top','SL_Uzun Toplar'),('İkili Mücadele','SL_Kazanılan İkili Mücadele'),('Gol','SL_Gol Sayısı')],
 'FB': [('Müdahale','SL_Müdahaleler'),('Top Kesme','SL_Top Kesme'),('Uzaklaştırma','SL_Uzaklaştırmalar'),
        ('Hava Topu Kazanma','SL_Kazanılan Hava Topu Mücadelesi'),('Hava Topu %','SL_Hava Topu Mücadelesi Kazanma Yüzdesi'),
        ('Şut Bloklama','SL_Engellenen Şutlar'),('Top Kazanma','SL_Top Kazanma'),('Pas','SL_Toplam Pas'),
        ('İsabetli Orta','SL_İsabetli Orta'),('Gol','SL_Gol Sayısı'),('Başarılı Dripling','SL_Başarılı Dribling'),
        ('İkili Mücadele','SL_Kazanılan İkili Mücadele')],
 'CM': [('Kilit Pas','SL_Kilit Paslar'),('Pas İsabeti %','SL_Pas İsabet Yüzdesi'),('Pas','SL_Toplam Pas'),
        ('İkili Mücadele','SL_Kazanılan İkili Mücadele'),('Top Kazanma','SL_Top Kazanma'),('Asist','SL_Asistler'),
        ('Gol','SL_Gol Sayısı'),('Başarılı Dripling','SL_Başarılı Dribling'),('Top Teması','SL_Topla Buluşma (Dokunuşlar)'),
        ('Top Kesme','SL_Top Kesme'),('Uzaklaştırma','SL_Uzaklaştırmalar'),('Müdahale','SL_Müdahaleler')],
 'FW': [('Gol','SL_Gol Sayısı'),('xG','SL_Beklenen Gol (xG)'),('Şut','SL_Toplam Şut'),('İsabetli Şut','SL_İsabetli Şut'),
        ('Asist','SL_Asistler'),('Kilit Pas','SL_Kilit Paslar'),('Büyük Şans Yaratma','SL_Yaratılan Büyük Şanslar'),
        ('Kaçan Büyük Şans','SL_Kaçırılan Büyük Şanslar'),('Orta','SL_Toplam Orta'),('Top Kazanma','SL_Top Kazanma'),
        ('Başarılı Dripling','SL_Başarılı Dribling'),('Top Teması','SL_Topla Buluşma (Dokunuşlar)')],
 'ST': [('Gol','SL_Gol Sayısı'),('xG','SL_Beklenen Gol (xG)'),('Şut','SL_Toplam Şut'),('İsabetli Şut','SL_İsabetli Şut'),
        ('Asist','SL_Asistler'),('Kilit Pas','SL_Kilit Paslar'),('Büyük Şans Yaratma','SL_Yaratılan Büyük Şanslar'),
        ('Kaçan Büyük Şans','SL_Kaçırılan Büyük Şanslar'),('Top Kazanma','SL_Top Kazanma'),
        ('İkili Mücadele','SL_Kazanılan İkili Mücadele'),('Hava Topu Kazanma','SL_Kazanılan Hava Topu Mücadelesi')],
}

# ----------------------------------------------------------------------------
# 3) ARŞETİP -> FM ATTRIBUTE SETLERİ  (kova içi, frekans ağırlıklı)
#    İsim eşleme: "Takım Oyunu"->İşbirliği, "Pozisyon Alma"->Mevki Alma
# ----------------------------------------------------------------------------
NAME_FIX = {'Takım Oyunu':'İşbirliği','Pozisyon Alma':'Mevki Alma'}
def fmcol(attr): return 'FM_' + NAME_FIX.get(attr, attr)
def fccol(attr): return 'FC_' + attr

# Havuza eklenecek SAHA-DIŞI FM (mental/kişilik) — normal ağırlık, tüm saha oyuncularında
OFF_PITCH = ['Agresiflik','Çalışkanlık','Çirkeflik','Kararlılık','Cesaret','Konsantrasyon',
             'Baskıya Dayanıklılık','Soğukkanlılık','Önemli Maçlardaki Formu']
# FC-only — v6 sözlüğü (FM_FC_SOZLUK_ESLEME.md §2.4): YALNIZ FM'de karşılığı OLMAYAN eksenler.
#   ÇİFT SAYIM DÜZELTMESİ (v6): Atak Poz. = FM Topsuz Alan'ın FC karşılığı (sınıf A, r=0.89),
#   Savunma Bilinci = FM Markaj (sınıf A), Reaksiyonlar = FM Önsezi (sınıf B). Bu üçü SIM_ATTRS'te
#   FM tarafıyla zaten temsil ediliyordu -> havuzdan çıkarıldı.
#   Kalanlar gerçek FC-native: Şut Gücü (FM_Güç r=0.08), Top Kesmeler (tackling != pas kesme),
#   Zayıf Ayak (FM'de yok, max|r|=0.31).
FC_EXTRA = ['Şut Gücü', 'Top Kesmeler', 'Zayıf Ayak']
FC_EXTRA_GK = []   # kaleci için FC ek sinyali yok (FM refleks/elle kontrol yeterli)

# ============================================================================
# BS KATMANI v6 — SEMANTİK DENETİMLİ (FM_FC_SOZLUK_ESLEME.md)
#   Kural: eşleme kararı RESMÎ TANIM semantiğine dayanır; korelasyon yalnız teyit.
#   Çelişirse semantik kazanır (kalite hâlesi r≈0.7'yi sahte üretir).
#   Sınıf A: |FC − FM×5| > 10 -> FC (simetrik ↑↓, yaş düşüşünü yakalar)
#   Sınıf B: FC − FM×5 > 10  -> FC (yalnız yukarı; kaba proxy, bayatlık düzeltir)
#   FM-only: FC'de karşılık yok/tanımsız -> FM×5
#   FC-native: FM'de karşılığı olmayan bağımsız eksen
#   v4->v6: Soğukkanlılık A->FM-only (FC Composure tanımı "N/A") ·
#           Top Kapma=(Ayakta+Kayarak)/2 (Interceptions semantik farklı, ayrıldı) ·
#           Birebir + Bölge Hakimiyeti FM-only (FC Diving↔Refleksler r=0.83 hâlesi) ·
#           Denge A->B · Mevki Alma yalnız GK'de sınıf B
# ============================================================================
BS_A_DIRECT = {   # Sınıf A birebir — tanımlar örtüşüyor
 'Hızlanma':'FC_Hızlanma','Hız':'FC_Sprint Hızı','Çeviklik':'FC_Çeviklik',
 'Güç':'FC_Güç','Zıplama':'FC_Zıplama','Dayanıklılık':'FC_Dayanıklılık',
 'Kafa Vuruşu':'FC_Kafa İsabeti','İlk Kontrol':'FC_Top Kontrolü',
 'Markaj':'FC_Savunma Bilinci',          # FC Def.Awareness tanımı literal "Marking"
 'Vizyon':'FC_Oyun Görüşü','Agresiflik':'FC_Saldırganlık',
 'Topsuz Alan':'FC_Atak Poz.',           # FC "attacking runs" = FM Off the Ball
 'Refleksler':'FC_KL Refleks','Elle Kontrol':'FC_KL Elle Kontrol','Degaj':'FC_KL Topa Vurma',
}
BS_A_COMPOSITE = {  # Sınıf A kompozit: [(FC kolonu, ağırlık, çarpan)]
 'Bitiricilik':[('FC_Bitiricilik',0.8,1.0),('FC_Voleler',0.2,1.0)],
 'Orta Yapma': [('FC_Orta Açma',0.75,1.0),('FC_Falso',0.25,1.0)],
 'Dripling':   [('FC_Dribling',0.8,1.0),('FC_Beceri Hareketleri',0.2,20.0)],
 'Pas':        [('FC_Kısa Pas',0.5,1.0),('FC_Uzun Paslar',0.5,1.0)],
 'Top Kapma':  [('FC_Ayakta Müdahale',0.5,1.0),('FC_Kayarak Müdahale',0.5,1.0)],
}
BS_B = {          # Sınıf B: yalnız yukarı
 'Önsezi':      [('FC_Reaksiyonlar',1.0,1.0)],
 'Özel Yetenek':[('FC_Beceri Hareketleri',0.6,20.0),('FC_Dribling',0.4,1.0)],
 'Uzaktan Şut': [('FC_Uzaktan Şut',1.0,1.0)],      # Şut Gücü ayrıldı (FC-native)
 'Denge':       [('FC_Denge',1.0,1.0)],            # FC tanımı daha geniş, r=0.52
}
BS_B_GK_ONLY = {  # yalnız kaleci havuzunda sınıf B; sahada FM-only
 'Mevki Alma':  [('FC_KL Yer Tutma',1.0,1.0)],     # GK'de r=0.80
}
BS_FM_ONLY = ['Soğukkanlılık','Birebir','Bölge Hakimiyeti','Hava Topları','Karar Alma','Teknik',
 'Cesaret','Konsantrasyon','Çalışkanlık','İşbirliği','Liderlik','Kararlılık','Vücut Zindeliği',
 'İletişim','Elle Oyun Başlatma','Yumruklama','Ani Çıkış Eğilimi','Eksantriklik']
BS_FC_NATIVE = {  # FM'de karşılığı YOK -> bağımsız eksen (roller.json'da FC_ önekiyle anılır)
 'FC_Şut Gücü':    ('FC_Şut Gücü', 1.0),      # FM_Güç ile r=0.08
 'FC_Top Kesmeler':('FC_Top Kesmeler', 1.0),  # tackling ≠ pas kesme (semantik)
 'FC_Zayıf Ayak':  ('FC_Zayıf Ayak', 20.0),   # 1-5 -> 20-100
}
# Hızlanma Türü (kategorik) -> iki ordinal eksen; kontrast_haric olarak kullanılır
BS_HIZ_TURU = {
 'FC_Patlayıcılık': {'Patlayıcı':100,'Çoğunlukla Patlayıcı':80,'Kontrollü Patlayıcı':60,
                     'Kontrollü':40,'Kontrollü Uzun':20},
 'FC_Uzun Adım':    {'Kontrollü Uzun':100,'Kontrollü':50,'Kontrollü Patlayıcı':35,
                     'Çoğunlukla Patlayıcı':20,'Patlayıcı':10},
}
BS_OVERRIDE_T = 10.0   # override eşiği

# ============================================================================
# ROL KATMANI — roller.json vektörleri + uyum_kalibrasyon.json sabitleri
#   Üç skor/rol: Uyum% (kimlik), CA_rol (seviye), Sıralama (rwa×kapı).
#   Havuz = Pozisyon (8'li); WB->FB eşlenir. Paylaşımlı DM rolleri CM havuzunda da
#   kendi yüzdeliğiyle skorlanır. ST_9 ebeveyn: kontrast≈0, Uyum güvensiz bayrağı.
# ============================================================================
def parse_mevki(s):
    """FM_Mevki string -> uygunluk seti. "OOS (SğSl), ST (M)" -> {'W','ST'}
       (yön raporu A1: Pozisyon sütunu %17.7 hatalı; havuz üyeliği buradan gelir)"""
    out = set()
    for part in str(s).split(','):
        m = re.match(r'^([A-ZÇĞİÖŞÜ/]+)\s*(?:\(([^)]*)\))?', part.strip())
        if not m: continue
        roles, sd = m.group(1), (m.group(2) or '')
        wide = ('Sğ' in sd) or ('Sl' in sd)
        mid  = ('M' in sd) or (sd == '')
        for r in roles.split('/'):
            if r in ('K', 'KL'): out.add('GK')
            elif r == 'D':   out |= ({'CB'} if mid else set()) | ({'FB'} if wide else set())
            elif r == 'KB':  out |= {'FB', 'WB'}
            elif r == 'DOS': out.add('DM')
            elif r == 'OS':  out |= ({'CM'} if mid else set()) | ({'W'} if wide else set())
            elif r == 'OOS': out |= ({'AM'} if mid else set()) | ({'W'} if wide else set())
            elif r == 'ST':  out.add('ST')
    if 'WB' in out: out.add('FB')        # WB -> FB havuzuna katlanır
    return out - {'WB'}

ROL_PARENT = {'ST_9'}                      # ebeveyn roller (kartta Sıralama gösterilir)
ROL_POOL_FIX = {'WB': 'FB'}
ROL_SHARED = {'DM_ANCHOR': ['DM', 'CM'], 'DM_DIN': ['DM', 'CM']}
ROL_GK_ONLY = ['Refleksler','Elle Kontrol','Degaj','Birebir','Elle Oyun Başlatma','Yumruklama',
               'Ani Çıkış Eğilimi','Bölge Hakimiyeti','İletişim','Hava Topları']
ROL_GK_EXC  = ['Bitiricilik','Orta Yapma','Uzaktan Şut','Kafa Vuruşu','Markaj','Top Kapma',
               'Dripling','Topsuz Alan','Özel Yetenek']

def build_rol_layer(df):
    """Rol skorlama bağlamı kurar. Dönen scorer(bucket, index) -> {rowid: pool-ROL bloğu}.
       Havuz üyeleri: rank-percentile (kalibre). Havuz-dışı: searchsorted, donmuş üye
       istatistikleriyle (doküman §2). CA_rol çapası: en-iyi-uyum rolü = tam CA;
       daha yüksek rwa'lı roller en fazla CA+2.

       roller.json / uyum_kalibrasyon.json eksikse (henüz yeniden oluşturulmadılar) ROL
       KATMANI atlanır: scorer her zaman boş sözlük döner, ROL_STATS/ROL_SAB boş kalır.
       Geri kalan pipeline (RADAR, BENZERLİK, takım reytingi) bundan etkilenmez; yalnız
       oyuncu kayıtlarındaki 'ROL' alanı None kalır."""
    try:
        with open(ROLLER_JSON, encoding='utf-8') as f:
            _roller_data = json.load(f)
        with open(UYUM_KALIBRASYON_JSON, encoding='utf-8') as f:
            kal = json.load(f)
    except FileNotFoundError as e:
        print(f"ROL KATMANI: DEVRE DIŞI — {e.filename} bulunamadı. "
              f"Rol uyum/CA_rol skorları üretilmeyecek (players[*].ROL = None).")
        return (lambda bucket, index: {}), {}, {}, {}
    R = _roller_data['roller']
    _rmeta = _roller_data.get('meta', {})
    _sab = _rmeta.get('rol_sabitler', {})
    BETA    = _sab.get('beta',  kal.get('beta', 0.35))
    S_LOJ   = _sab.get('s',     kal.get('lojistik_s', 0.55))      # v6: 0.55
    KAPI_Z0 = _sab.get('kapi_z0', 1.5); KAPI_S = _sab.get('kapi_s', 0.6)
    COV_T   = _sab.get('coverage', 0.5)

    axes_all = [c[3:] for c in df.columns if c.startswith('BS_') and not c.startswith('BS_src_')]
    FIELD_SET = [a for a in axes_all if a not in ROL_GK_ONLY]
    GK_SET    = [a for a in axes_all if a not in ROL_GK_EXC]
    # HAVUZ (v6 §8.1): FM_Mevki uygunluk seti — çoklu üyelik serbest
    uygun = df['FM_Mevki'].map(parse_mevki) if 'FM_Mevki' in df.columns else None
    POOLS8 = ['GK','CB','FB','DM','CM','AM','W','ST']
    if uygun is not None:
        pools = {p: df.index[uygun.map(lambda s, _p=p: _p in s)] for p in POOLS8}
        bos = [p for p in POOLS8 if len(pools[p]) == 0]
        if bos:   # parse tamamen boşsa eski sütuna düş (savunmacı)
            poz = df['Pozisyon'].astype(str).replace(ROL_POOL_FIX)
            for p in bos: pools[p] = df.index[poz == p]
    else:
        poz = df['Pozisyon'].astype(str).replace(ROL_POOL_FIX)
        pools = {p: df.index[poz == p] for p in POOLS8}
    BSM = {a: pd.to_numeric(df['BS_' + a], errors='coerce') for a in axes_all}
    ca_half = pd.to_numeric(df['FM_MY'], errors='coerce') / 2.0

    # kontrast vektörleri (rol w − pozisyon-ortalama w)
    by_pos = {}
    for rk, rv in R.items(): by_pos.setdefault(rv['pozisyon'], []).append(rk)
    contrast = {}
    for pos, rks in by_pos.items():
        axes_u = sorted({a for rk in rks for a in R[rk]['agirliklar']})
        meanw = {a: np.mean([R[r2]['agirliklar'].get(a, {}).get('w', 0.0) for r2 in rks]) for a in axes_u}
        for rk in rks:
            cw = {a: R[rk]['agirliklar'].get(a, {}).get('w', 0.0) - meanw[a] for a in axes_u}
            # kontrast_haric (kategorik eksen): SEVİYEYE girer, ŞEKİLDEN çıkar (yön raporu C3)
            kh = {a for a in axes_u if R[rk]['agirliklar'].get(a, {}).get('kontrast_haric')}
            contrast[rk] = {a: v for a, v in cw.items() if abs(v) >= 0.05 and a not in kh}

    # havuz başına: eksen seti, ÜYE percentile (rank) ve searchsorted için sıralı diziler
    pool_set, pool_pct, pool_sorted = {}, {}, {}
    for p, idxs in pools.items():
        sett = GK_SET if p == 'GK' else FIELD_SET
        pool_set[p] = sett
        sub = pd.DataFrame({a: BSM[a].loc[idxs] for a in sett})
        pool_pct[p] = sub.rank(pct=True) * 100.0
        pool_sorted[p] = {a: np.sort(sub[a].dropna().values) for a in sett}

    pool_roles = {p: [rk for rk, rv in R.items() if rv['pozisyon'] == p] for p in pools}
    for rk, pl in ROL_SHARED.items():
        for p in pl:
            if rk not in pool_roles[p]: pool_roles[p].append(rk)

    # rol×havuz DONMUŞ istatistikler + üye ham skorları
    rol_stats, member_raw = {}, {p: {} for p in pools}   # member_raw[p][rowid][rk]=(uyum,rwa,sira,cov)
    def _score_block(rk, p, pct_df, idxs, frozen=None):
        w_full = {a: v['w'] for a, v in R[rk]['agirliklar'].items()}
        wsum = sum(w_full.values())
        cw_use = {a: v for a, v in contrast[rk].items() if a in pct_df.columns}
        if not cw_use: return None, None
        csum = sum(abs(v) for v in cw_use.values())
        rowmean = pct_df.mean(axis=1)
        shape = sum(v * (pct_df[a] - rowmean) for a, v in cw_use.items()) / csum
        num = pd.Series(0.0, index=idxs); den = pd.Series(0.0, index=idxs)
        for a, wv in w_full.items():
            if a not in BSM: continue
            b = BSM[a].loc[idxs]
            num += b.fillna(0) * wv
            den += b.notna().astype(float) * wv
        rwa = num / den.replace(0, np.nan)
        cov = den / wsum
        if frozen is None:
            st = {'med_s': float(shape.median()), 'std_s': float(shape.std()) or 1.0,
                  'med_r': float(rwa.median()), 'std_r': float(rwa.std()) or 1.0}
            z_s = (shape - st['med_s']) / st['std_s']
            z_e = z_s + BETA * np.maximum(0, (rwa - st['med_r']) / st['std_r'])
            st['med_e'] = float(z_e.median())
        else:
            st = frozen
            z_s = (shape - st['med_s']) / st['std_s']
            z_e = z_s + BETA * np.maximum(0, (rwa - st['med_r']) / st['std_r'])
        uyum = 100.0 / (1.0 + np.exp(-(z_e - st['med_e']) / S_LOJ))
        kapi = 1.0 / (1.0 + np.exp(-(z_s + KAPI_Z0) / KAPI_S))
        return {'uyum': uyum, 'rwa': rwa, 'sira': rwa * kapi, 'cov': cov, 'shape': shape}, st

    for p, idxs in pools.items():
        if len(idxs) == 0: continue
        for rk in pool_roles[p]:
            res, st = _score_block(rk, p, pool_pct[p], idxs)
            if res is None: continue
            key = rk if p == R[rk]['pozisyon'] else f"{rk}@{p}"
            rol_stats[key] = {k: round(v, 3) for k, v in st.items()}
            kod = R[rk]['kod']
            bad = (res['cov'] < COV_T) | res['rwa'].isna() | res['shape'].isna()
            for i in idxs:
                if bad.loc[i]: continue
                member_raw[p].setdefault(i, {})[kod] = (
                    int(round(res['uyum'].loc[i])), float(res['rwa'].loc[i]),
                    float(res['sira'].loc[i]), float(res['cov'].loc[i]), (R[rk].get('ebeveyn') or rk in ROL_PARENT))

    BUCK2POOL = {'GK':'GK','CB':'CB','LB':'FB','RB':'FB','DM':'DM','CM':'CM','AM':'AM',
                 'LW':'W','RW':'W','ST':'ST','FB':'FB','W':'W'}   # havuz adları da kabul
    _nonmem_cache = {p: {} for p in pools}

    def _finalize(i, raw):
        # CA çapası: en-iyi-uyum (ebeveyn hariç) rolü tam CA; rwa oranı; tavan CA+2
        ch = ca_half.loc[i] if i in ca_half.index else np.nan
        if not pd.isna(ch): ch = float(round(ch))   # başlık CA'sına (yuvarlanmış) çapala
        nonpar = {k: v for k, v in raw.items() if not v[4]} or raw
        best = max(nonpar, key=lambda k: (nonpar[k][0], nonpar[k][2]))   # uyum, eşitlikte sıralama
        arwa = raw[best][1] or np.nan
        out = {}
        for kod, (uy, rw, si, cv, par) in raw.items():
            ca = None
            if not pd.isna(ch) and arwa and rw:
                ca = round(min(float(ch) * rw / arwa, float(ch) + 2.0), 1)
            out[kod] = {'uyum': uy, 'ca': ca, 'sira': round(si, 1), 'kaynak_kapsam': round(cv, 2)}
        out['_en_iyi'] = best
        eb = None
        if raw[best][4] or (best in ('9',) ):
            tend = {k: raw[k][0] for k in ('POA','TF','DLF') if k in raw}
            eb = max(tend, key=tend.get) if tend else None
        elif '9' in raw and raw['9'][4]:
            pass
        out['_ebeveyn_etiket'] = eb
        return out

    def scorer(bucket, index):
        p = BUCK2POOL.get(bucket)
        if p is None: return {}
        memset = set(pools[p])
        result = {}
        nonmem = [i for i in index if i not in memset and i not in _nonmem_cache[p]]
        if nonmem:
            # havuz-dışı: searchsorted percentile, donmuş istatistik
            sett = pool_set[p]
            sub = pd.DataFrame({a: BSM[a].loc[nonmem] for a in sett})
            pct = pd.DataFrame(index=sub.index)
            for a in sett:
                arr = pool_sorted[p][a]
                if len(arr) == 0: pct[a] = np.nan; continue
                v = sub[a].values.astype(float)
                pc = np.searchsorted(arr, v, side='right') / len(arr) * 100.0
                pc[np.isnan(v)] = np.nan
                pct[a] = pc
            raw_nm = {i: {} for i in nonmem}
            for rk in pool_roles[p]:
                key = rk if p == R[rk]['pozisyon'] else f"{rk}@{p}"
                if key not in rol_stats: continue
                res, _ = _score_block(rk, p, pct, pd.Index(nonmem), frozen=rol_stats[key])
                if res is None: continue
                kod = R[rk]['kod']
                bad = (res['cov'] < COV_T) | res['rwa'].isna() | res['shape'].isna()
                for i in nonmem:
                    if bad.loc[i]: continue
                    raw_nm[i][kod] = (int(round(res['uyum'].loc[i])), float(res['rwa'].loc[i]),
                                      float(res['sira'].loc[i]), float(res['cov'].loc[i]), (R[rk].get('ebeveyn') or rk in ROL_PARENT))
            for i in nonmem:
                _nonmem_cache[p][i] = raw_nm[i]
        for i in index:
            raw = member_raw[p].get(i) if i in memset else _nonmem_cache[p].get(i)
            if raw: result[i] = _finalize(i, raw)
        return result

    sabitler = {'beta': BETA, 's': S_LOJ, 'kapi_z0': KAPI_Z0, 'kapi_s': KAPI_S,
                'merkez_m': kal.get('merkez_m'), 'ca_tavan_bonus': 2.0}
    # kod -> {ad, pozisyon} kayıt defteri: arayüzde rol uyum filtresi için okunabilir isim
    # (players[*].ROL sözlüğü yalnız kısa 'kod'u taşıyor, ör. "DLP" — "Derin Oyun Kurucu" değil)
    registry = {rv['kod']: {'ad': rv.get('ad'), 'pozisyon': rv['pozisyon']} for rv in R.values()}
    return scorer, rol_stats, sabitler, registry


def build_bs_layer(df, gk_mask=None):
    """BS_<eksen> (0-100) + BS_src_<eksen> (int8) üretir.
       kaynak kodu: 0=FM 1=A-fm 2=A-override 3=B-fm 4=B-override 5=FC-native"""
    def fc_comp(parts):
        tot = None
        for col, w, mult in parts:
            if col not in df.columns: return None
            v = pd.to_numeric(df[col], errors='coerce') * mult
            tot = v * w if tot is None else tot + v * w
        return tot

    def apply_override(axis, fc, cls_b, restrict=None):
        """restrict: yalnız bu maskede override uygula (ör. GK)."""
        fmc = 'FM_' + axis
        fm5 = pd.to_numeric(df[fmc], errors='coerce') * 5.0 if fmc in df.columns \
              else pd.Series(np.nan, index=df.index)
        if fc is None:
            df['BS_' + axis] = np.clip(fm5, 1, 100); df['BS_src_' + axis] = np.int8(0); return
        diff = fc - fm5
        use = (diff > BS_OVERRIDE_T) if cls_b else (diff.abs() > BS_OVERRIDE_T)
        use = use.fillna(False)
        if restrict is not None: use = use & restrict
        src_c = np.where(use, (4 if cls_b else 2), (3 if cls_b else 1))
        val = np.where(use & fc.notna(), fc, fm5)
        fill = fm5.isna() & fc.notna()                 # FM eksik + FC var -> FC
        if restrict is not None: fill = fill & restrict
        val = np.where(fill, fc, val)
        src_c = np.where(fill, (4 if cls_b else 2), src_c)
        df['BS_' + axis] = np.clip(val, 1, 100)
        df['BS_src_' + axis] = src_c.astype(np.int8)

    n = 0
    for axis, col in BS_A_DIRECT.items():
        apply_override(axis, pd.to_numeric(df[col], errors='coerce') if col in df.columns else None, False); n += 1
    for axis, parts in BS_A_COMPOSITE.items():
        apply_override(axis, fc_comp(parts), False); n += 1
    for axis, parts in BS_B.items():
        apply_override(axis, fc_comp(parts), True); n += 1
    for axis, parts in BS_B_GK_ONLY.items():           # yalnız GK'de override
        apply_override(axis, fc_comp(parts), True, restrict=gk_mask); n += 1
    for axis in BS_FM_ONLY:
        fmc = 'FM_' + axis
        if fmc in df.columns:
            df['BS_' + axis] = np.clip(pd.to_numeric(df[fmc], errors='coerce') * 5.0, 1, 100)
            df['BS_src_' + axis] = np.int8(0); n += 1
    for axis, (col, mult) in BS_FC_NATIVE.items():
        if col in df.columns:
            df['BS_' + axis] = np.clip(pd.to_numeric(df[col], errors='coerce') * mult, 1, 100)
            df['BS_src_' + axis] = np.int8(5); n += 1
    if 'FC_Hızlanma Türü' in df.columns:               # kategorik -> ordinal
        cat = df['FC_Hızlanma Türü'].astype(str).str.strip()
        for axis, mp in BS_HIZ_TURU.items():
            df['BS_' + axis] = cat.map(mp).astype('float64')
            df['BS_src_' + axis] = np.int8(5); n += 1
    return n


def natural_breaks(values, k=6, bins=128):
    """Ağırlıklı Fisher-Jenks ("doğal kırılma") kesim noktaları — histogram-
    sıkıştırılmış DP ile sınıf-içi varyansı minimize eden k sınıflı bölünmeyi
    bulur. Sabit eşit-aralık/eşit-percentile YERİNE eksenin KENDİ dağılım
    şekline uyar: oyuncuların yığıldığı yoğun bölge geniş bir kademeye düşer,
    seyrek/ayrışan uç (ör. Hız'da 17-19 FM bandı) kendi dar kademesine ayrılır.
    Bu yüzden iki farklı BS ekseni (ör. Hız vs Teknik) aynı ham aralığa denk
    gelen kademe sınırları üretmez — kasıtlı ve beklenen bir sonuç, bkz. CLAUDE.md.

    values: 1D sayısal dizi (NaN'lar atılır). Döner: artan sırada k-1 kesim
    noktası (k sınıf sınırı verir). Yetersiz/dejenere veri (n<=k ya da tüm
    değerler eşit) durumunda eşit-aralık fallback'e düşer.
    """
    v = np.asarray(values, dtype=float)
    v = v[~np.isnan(v)]
    if len(v) == 0:
        return list(np.linspace(1, 100, k + 1)[1:-1])
    lo, hi = float(v.min()), float(v.max())
    if hi <= lo or len(v) <= k:
        return list(np.linspace(lo, hi, k + 1)[1:-1]) if hi > lo else [lo] * (k - 1)

    # ham veriyi 'bins' histogram kovasına sıkıştır (DP'yi n yerine bins üzerinde
    # çalıştırmak için) — yalnız dolu kovalar tutulur, ağırlık = kova sayacı
    edges = np.linspace(lo, hi, bins + 1)
    counts, _ = np.histogram(v, bins=edges)
    centers = (edges[:-1] + edges[1:]) / 2
    mask = counts > 0
    w = counts[mask].astype(float)
    x = centers[mask]
    edge_lo = edges[:-1][mask]
    m = len(x)
    if m <= k:
        return sorted(x.tolist())

    # ağırlıklı prefix toplamları -> herhangi bir [i,j) aralığının ağırlıklı
    # kareler-toplamı-sapması (within-class SSD) O(1)'de hesaplanabilir
    W = np.concatenate([[0.0], np.cumsum(w)])
    S = np.concatenate([[0.0], np.cumsum(w * x)])
    Q = np.concatenate([[0.0], np.cumsum(w * x * x)])

    def cost_vec(i_arr, j):
        wsum = W[j] - W[i_arr]
        ssum = S[j] - S[i_arr]
        qsum = Q[j] - Q[i_arr]
        with np.errstate(invalid='ignore', divide='ignore'):
            mean = np.where(wsum > 0, ssum / np.where(wsum > 0, wsum, 1), 0.0)
        return qsum - 2 * mean * ssum + mean * mean * wsum

    # DP[c][j]: ilk j kova 1..c sınıfa optimal bölündüğünde min toplam SSD
    DP = np.full((k + 1, m + 1), np.inf)
    SPLIT = np.zeros((k + 1, m + 1), dtype=int)
    DP[0, 0] = 0.0
    for c in range(1, k + 1):
        for j in range(c, m + 1):
            i_arr = np.arange(c - 1, j)
            prev = DP[c - 1, i_arr]
            valid = np.isfinite(prev)
            if not valid.any():
                continue
            costs = prev[valid] + cost_vec(i_arr[valid], j)
            best_local = int(np.argmin(costs))
            DP[c, j] = costs[best_local]
            SPLIT[c, j] = i_arr[valid][best_local]

    # geri iz: sınıf sınırı indekslerini bul -> kesim noktası = o kovanın alt kenarı
    bounds_idx = []
    j = m
    for c in range(k, 1, -1):
        i = int(SPLIT[c, j])
        bounds_idx.append(i)
        j = i
    bounds_idx.sort()
    return [round(float(edge_lo[i]), 1) for i in bounds_idx]


# ROL-BELİRLEYİCİ keskin özellikler (granular 10 pozisyon) — spike'ta ROLE_MULT kat ağırlık.
# Amaç: aynı pozisyondaki ZIT arketipleri ayırmak (DM: presçi vs DLP gibi). Yalnız saha-içi.
ROLE_KEY = {
 'GK': ['Refleksler','Birebir','Elle Kontrol','Hava Topları','Ani Çıkış Eğilimi','Elle Oyun Başlatma','Bölge Hakimiyeti'],
 'CB': ['Markaj','Top Kapma','Hava Topları','Güç','Kafa Vuruşu','Hız','Pas','İlk Kontrol','FC:Top Kesmeler'],
 'RB': ['Orta Yapma','Hız','Çalışkanlık','Dripling','Top Kapma','Markaj','Dayanıklılık'],
 'LB': ['Orta Yapma','Hız','Çalışkanlık','Dripling','Top Kapma','Markaj','Dayanıklılık'],
 'DM': ['Top Kapma','Agresiflik','Markaj','Çalışkanlık','Pas','Vizyon','FC:Top Kesmeler','Güç'],
 'CM': ['Pas','Vizyon','Çalışkanlık','Dripling','Uzaktan Şut','Top Kapma','Topsuz Alan','Dayanıklılık'],
 'AM': ['Vizyon','Pas','Dripling','Uzaktan Şut','İlk Kontrol','Teknik','Topsuz Alan','Çeviklik'],
 'RW': ['Dripling','Hız','Çeviklik','Orta Yapma','Bitiricilik','Uzaktan Şut','Topsuz Alan','İlk Kontrol'],
 'LW': ['Dripling','Hız','Çeviklik','Orta Yapma','Bitiricilik','Uzaktan Şut','Topsuz Alan','İlk Kontrol'],
 'ST': ['Bitiricilik','Kafa Vuruşu','Hava Topları','Güç','Hız','Topsuz Alan','İlk Kontrol','Dripling','Önsezi'],
}
ROLE_MULT   = 2.5    # rol-belirleyici özelliklerin spike ağırlığı
SPIKE_EXP   = 2.0    # spike üstelliği: (percentile fazlası)^SPIKE_EXP -> uç özellikler baskın

def parse_money(s):
    """'Vergi sonrası €3,3M yıllık' / '€832B' / '€114M' -> euro (M=milyon, B=bin)."""
    if s is None: return None
    if isinstance(s, (int, float)):
        try:
            f = float(s); return None if (np.isnan(f) or np.isinf(f)) else round(f)
        except Exception:
            return None
    s = str(s)
    m = re.search(r'([\d.,]+)\s*([MBmb])', s)
    if m:
        try: val = float(m.group(1).replace('.', '').replace(',', '.'))
        except Exception: return None
        suf = m.group(2).upper()
        return round(val * (1e6 if suf == 'M' else 1e3))
    m2 = re.search(r'([\d.,]+)', s)
    if not m2: return None
    try: return round(float(m2.group(1).replace('.', '').replace(',', '.')))
    except Exception: return None

def contract_parts(v):
    """-> (display 'MM/YYYY', year int) ya da (None, None).
    FM_Bitiş Excel seri sayısı (ör. 47299.0 = 2029-06-30) olarak gelir."""
    if v is None or (isinstance(v, float) and pd.isna(v)): return None, None
    try:
        num = float(v)
        # Excel seri tarih aralığı (~2020-2040 için 43800-51500). Bu aralıktaysa seri kabul et.
        if 20000 < num < 80000:
            ts = pd.Timestamp('1899-12-30') + pd.Timedelta(days=num)
        else:
            ts = pd.Timestamp(v)
        if pd.isna(ts): return None, None
        return f"{ts.month:02d}/{ts.year}", int(ts.year)
    except (ValueError, TypeError):
        try:
            ts = pd.Timestamp(v)
            if pd.isna(ts): return None, None
            return f"{ts.month:02d}/{ts.year}", int(ts.year)
        except Exception:
            return None, None

# her kova: arşetip listesi (her arşetip = attribute listesi)
ARCH = {
 'GK': [
   ['Birebir','Bölge Hakimiyeti','Degaj','Elle Kontrol','Hava Topları','İletişim','İlk Kontrol','Pas','Refleksler','Karar Alma','Kararlılık','Konsantrasyon','Önsezi','Pozisyon Alma','Soğukkanlılık','Çeviklik','Denge','Hızlanma','Zıplama'],
   ['Birebir','Bölge Hakimiyeti','Degaj','Elle Kontrol','Elle Oyun Başlatma','Hava Topları','İletişim','İlk Kontrol','Pas','Refleksler','Karar Alma','Kararlılık','Konsantrasyon','Önsezi','Pozisyon Alma','Soğukkanlılık','Vizyon','Çeviklik','Denge','Hızlanma','Zıplama'],
   ['Birebir','Bölge Hakimiyeti','Hava Topları','Refleksler','Karar Alma','Kararlılık','Konsantrasyon','Pozisyon Alma','Soğukkanlılık','Çeviklik','Zıplama'],
 ],
 'CB': [
   ['İlk Kontrol','Kafa Vuruşu','Markaj','Pas','Teknik','Top Kapma','Cesaret','Karar Alma','Kararlılık','Konsantrasyon','Önsezi','Pozisyon Alma','Soğukkanlılık','Takım Oyunu','Dayanıklılık','Denge','Güç','Hız','Hızlanma','Vücut Zindeliği','Zıplama'],
   ['Dripling','İlk Kontrol','Kafa Vuruşu','Markaj','Pas','Teknik','Top Kapma','Cesaret','Karar Alma','Kararlılık','Konsantrasyon','Önsezi','Pozisyon Alma','Soğukkanlılık','Takım Oyunu','Topsuz Alan','Vizyon','Çeviklik','Dayanıklılık','Denge','Güç','Hız','Hızlanma','Vücut Zindeliği','Zıplama'],
   ['Orta Yapma','Pas','Top Kapma','Çalışkanlık','Karar Alma','Kararlılık','Konsantrasyon','Önsezi','Pozisyon Alma','Soğukkanlılık','Takım Oyunu','Çeviklik','Dayanıklılık','Denge','Güç','Hız','Hızlanma','Vücut Zindeliği'],
   ['Kafa Vuruşu','Markaj','Top Kapma','Cesaret','Karar Alma','Kararlılık','Konsantrasyon','Önsezi','Pozisyon Alma','Soğukkanlılık','Dayanıklılık','Güç','Hız','Vücut Zindeliği','Zıplama'],
   ['Markaj','Top Kapma','Agresiflik','Cesaret','Çalışkanlık','Karar Alma','Kararlılık','Konsantrasyon','Önsezi','Pozisyon Alma','Soğukkanlılık','Takım Oyunu','Çeviklik','Dayanıklılık','Denge','Güç','Hız','Hızlanma','Vücut Zindeliği','Zıplama'],
   ['Kafa Vuruşu','Markaj','Top Kapma','Cesaret','Kararlılık','Konsantrasyon','Pozisyon Alma','Güç','Vücut Zindeliği','Zıplama'],
 ],
 'FB': [
   ['Dripling','İlk Kontrol','Orta Yapma','Pas','Teknik','Top Kapma','Çalışkanlık','Karar Alma','Kararlılık','Konsantrasyon','Önsezi','Soğukkanlılık','Takım Oyunu','Topsuz Alan','Çeviklik','Dayanıklılık','Denge','Hız','Hızlanma','Vücut Zindeliği'],
   ['Kafa Vuruşu','Markaj','Pas','Top Kapma','Agresiflik','Cesaret','Çalışkanlık','Karar Alma','Kararlılık','Konsantrasyon','Önsezi','Pozisyon Alma','Soğukkanlılık','Takım Oyunu','Çeviklik','Dayanıklılık','Denge','Güç','Hız','Hızlanma','Vücut Zindeliği','Zıplama'],
   ['İlk Kontrol','Markaj','Pas','Teknik','Top Kapma','Çalışkanlık','Karar Alma','Kararlılık','Konsantrasyon','Önsezi','Pozisyon Alma','Soğukkanlılık','Takım Oyunu','Vizyon','Çeviklik','Dayanıklılık','Denge','Hız','Hızlanma','Vücut Zindeliği'],
   ['Dripling','İlk Kontrol','Pas','Teknik','Top Kapma','Çalışkanlık','Karar Alma','Kararlılık','Konsantrasyon','Önsezi','Soğukkanlılık','Takım Oyunu','Topsuz Alan','Vizyon','Çeviklik','Dayanıklılık','Denge','Hız','Hızlanma','Vücut Zindeliği'],
   ['Markaj','Orta Yapma','Pas','Top Kapma','Çalışkanlık','Karar Alma','Kararlılık','Konsantrasyon','Önsezi','Pozisyon Alma','Soğukkanlılık','Takım Oyunu','Çeviklik','Dayanıklılık','Denge','Hız','Hızlanma','Vücut Zindeliği'],
 ],
 'CM': [
   ['İlk Kontrol','Pas','Teknik','Karar Alma','Kararlılık','Konsantrasyon','Önsezi','Soğukkanlılık','Takım Oyunu','Topsuz Alan','Vizyon','Çeviklik','Dayanıklılık','Denge','Vücut Zindeliği'],
   ['İlk Kontrol','Pas','Teknik','Karar Alma','Kararlılık','Önsezi','Soğukkanlılık','Takım Oyunu','Vizyon','Denge'],
   ['Markaj','Pas','Top Kapma','Çalışkanlık','Karar Alma','Kararlılık','Konsantrasyon','Önsezi','Pozisyon Alma','Soğukkanlılık','Takım Oyunu','Dayanıklılık','Güç','Hızlanma','Vücut Zindeliği'],
   ['İlk Kontrol','Markaj','Pas','Teknik','Top Kapma','Çalışkanlık','Karar Alma','Kararlılık','Konsantrasyon','Önsezi','Soğukkanlılık','Takım Oyunu','Topsuz Alan','Çeviklik','Dayanıklılık','Denge','Hızlanma','Vücut Zindeliği'],
   ['Kafa Vuruşu','Markaj','Pas','Top Kapma','Cesaret','Çalışkanlık','Karar Alma','Kararlılık','Konsantrasyon','Önsezi','Pozisyon Alma','Soğukkanlılık','Takım Oyunu','Dayanıklılık','Güç','Hız','Hızlanma','Vücut Zindeliği','Zıplama'],
   ['İlk Kontrol','Pas','Teknik','Karar Alma','Kararlılık','Önsezi','Soğukkanlılık','Takım Oyunu','Topsuz Alan','Vizyon','Çeviklik','Dayanıklılık','Hızlanma'],
   ['İlk Kontrol','Pas','Teknik','Karar Alma','Kararlılık','Önsezi','Soğukkanlılık','Takım Oyunu','Topsuz Alan','Vizyon','Çeviklik','Hızlanma'],
   ['İlk Kontrol','Pas','Top Kapma','Çalışkanlık','Karar Alma','Kararlılık','Konsantrasyon','Önsezi','Pozisyon Alma','Soğukkanlılık','Takım Oyunu','Dayanıklılık','Vücut Zindeliği'],
   # Smit/Wirtz (merkez ofansif orta saha):
   ['Bitiricilik','Dripling','İlk Kontrol','Pas','Teknik','Uzaktan Şut','Karar Alma','Kararlılık','Önsezi','Soğukkanlılık','Topsuz Alan','Vizyon','Çeviklik','Hızlanma'],
   ['Bitiricilik','Dripling','İlk Kontrol','Pas','Teknik','Uzaktan Şut','Karar Alma','Kararlılık','Önsezi','Özel Yetenek','Soğukkanlılık','Takım Oyunu','Topsuz Alan','Vizyon','Çeviklik','Hızlanma'],
   ['Bitiricilik','İlk Kontrol','Pas','Teknik','Karar Alma','Kararlılık','Önsezi','Soğukkanlılık','Takım Oyunu','Topsuz Alan','Vizyon','Çeviklik','Dayanıklılık','Hızlanma'],
 ],
 'FW': [
   ['Dripling','İlk Kontrol','Orta Yapma','Pas','Teknik','Top Kapma','Çalışkanlık','Karar Alma','Kararlılık','Konsantrasyon','Önsezi','Pozisyon Alma','Takım Oyunu','Dayanıklılık','Hız','Hızlanma'],
   ['Bitiricilik','Dripling','İlk Kontrol','Orta Yapma','Pas','Teknik','Karar Alma','Kararlılık','Önsezi','Özel Yetenek','Soğukkanlılık','Topsuz Alan','Çeviklik','Hızlanma'],
   ['Bitiricilik','Dripling','İlk Kontrol','Orta Yapma','Pas','Teknik','Karar Alma','Kararlılık','Önsezi','Özel Yetenek','Soğukkanlılık','Takım Oyunu','Topsuz Alan','Çeviklik','Hız','Hızlanma'],
   ['Dripling','İlk Kontrol','Orta Yapma','Pas','Teknik','Karar Alma','Kararlılık','Önsezi','Özel Yetenek','Soğukkanlılık','Takım Oyunu','Topsuz Alan','Vizyon','Çeviklik','Hızlanma'],
   ['Dripling','İlk Kontrol','Orta Yapma','Pas','Teknik','Karar Alma','Kararlılık','Önsezi','Özel Yetenek','Soğukkanlılık','Takım Oyunu','Çeviklik','Hız','Hızlanma'],
 ],
 'ST': [
   ['Bitiricilik','İlk Kontrol','Kafa Vuruşu','Karar Alma','Kararlılık','Önsezi','Soğukkanlılık','Topsuz Alan','Çeviklik','Hız','Hızlanma','Zıplama'],
   ['Bitiricilik','İlk Kontrol','Kafa Vuruşu','Teknik','Cesaret','Karar Alma','Kararlılık','Önsezi','Soğukkanlılık','Takım Oyunu','Topsuz Alan','Dayanıklılık','Güç','Hız','Hızlanma','Vücut Zindeliği','Zıplama'],
   ['Bitiricilik','İlk Kontrol','Pas','Teknik','Karar Alma','Kararlılık','Önsezi','Soğukkanlılık','Takım Oyunu','Topsuz Alan','Vizyon','Çeviklik','Dayanıklılık','Güç','Hızlanma'],
   ['İlk Kontrol','Kafa Vuruşu','Cesaret','Kararlılık','Takım Oyunu','Güç','Vücut Zindeliği','Zıplama'],
   ['Bitiricilik','Dripling','İlk Kontrol','Pas','Teknik','Karar Alma','Kararlılık','Önsezi','Soğukkanlılık','Takım Oyunu','Topsuz Alan','Çeviklik','Hız','Hızlanma'],
   ['Dripling','İlk Kontrol','Pas','Teknik','Karar Alma','Kararlılık','Önsezi','Soğukkanlılık','Takım Oyunu','Topsuz Alan','Vizyon','Çeviklik','Hızlanma'],
 ],
}

def bucket_weights(bucket):
    """frekans ağırlıklı attribute sözlüğü: {FM_kolon: ağırlık}"""
    w = {}
    for arch in ARCH[bucket]:
        for a in arch:
            col = fmcol(a)
            w[col] = w.get(col, 0) + 1
    return w

# ----------------------------------------------------------------------------
# 5) OYUN MODELLERİ (M3-D)  her model = {attribute_TR: ağırlık}
# ----------------------------------------------------------------------------
MODELS = {
 'tiki':   ('Tiki-Taka',        {'Pas':3,'İlk Kontrol':2,'Teknik':2,'Vizyon':2,'Topsuz Alan':2,'Karar Alma':2,'Soğukkanlılık':1,'Takım Oyunu':1,'Çeviklik':1}),
 'vtiki':  ('Vertical Tiki-Taka',{'Pas':2,'Vizyon':2,'İlk Kontrol':2,'Topsuz Alan':2,'Hızlanma':2,'Karar Alma':2,'Teknik':1,'Çeviklik':1}),
 'poss':   ('Possession',       {'Pas':3,'İlk Kontrol':2,'Teknik':2,'Karar Alma':2,'Konsantrasyon':1,'Soğukkanlılık':1,'Takım Oyunu':1,'Vizyon':1}),
 'gegen':  ('Gegenpress',       {'Çalışkanlık':3,'Top Kapma':2,'Önsezi':2,'Agresiflik':2,'Hızlanma':2,'Dayanıklılık':2,'Kararlılık':1,'Topsuz Alan':1,'Karar Alma':1}),
 'highp':  ('High Press',       {'Çalışkanlık':3,'Hızlanma':2,'Agresiflik':2,'Önsezi':2,'Dayanıklılık':2,'Cesaret':1,'Top Kapma':1,'Karar Alma':1}),
 'counter':('Counter Attack',   {'Hız':3,'Hızlanma':3,'Bitiricilik':2,'Topsuz Alan':2,'Karar Alma':1,'Çeviklik':1,'Dripling':1,'Soğukkanlılık':1}),
 'direct': ('Direct Play',      {'Güç':2,'Kafa Vuruşu':2,'Zıplama':2,'Vücut Zindeliği':2,'Hız':2,'Bitiricilik':2,'Topsuz Alan':1,'Cesaret':1}),
 'wing':   ('Wing Play',        {'Orta Yapma':3,'Dripling':2,'Hız':2,'Hızlanma':2,'Çeviklik':2,'Çalışkanlık':1,'Pas':1,'Kafa Vuruşu':1}),
 'caten':  ('Catenaccio',       {'Markaj':3,'Pozisyon Alma':2,'Konsantrasyon':2,'Top Kapma':2,'Kafa Vuruşu':1,'Cesaret':1,'Soğukkanlılık':1,'Güç':1}),
 'lowb':   ('Low Block',        {'Pozisyon Alma':3,'Konsantrasyon':2,'Markaj':2,'Top Kapma':2,'Dayanıklılık':2,'Cesaret':1,'Kafa Vuruşu':1,'Soğukkanlılık':1}),
}
MODEL_ATTRS = sorted({NAME_FIX.get(a, a) for _, w in MODELS.values() for a in w})

# Benzerlik için kullanıcı-tanımlı FM attribute setleri (kova içi, eşit ağırlık)
SIM_ATTRS = {
 'GK': ['Birebir','Bölge Hakimiyeti','Degaj','Elle Kontrol','Elle Oyun Başlatma','Hava Topları',
        'İletişim','İlk Kontrol','Pas','Refleksler','Karar Alma','Kararlılık','Konsantrasyon',
        'Önsezi','Soğukkanlılık','Pozisyon Alma','Vizyon','Çeviklik','Denge','Hızlanma','Zıplama'],
 'CB': ['Dripling','İlk Kontrol','Kafa Vuruşu','Markaj','Orta Yapma','Pas','Teknik','Top Kapma',
        'Agresiflik','Cesaret','Çalışkanlık','Karar Alma','Kararlılık','Konsantrasyon','Önsezi',
        'Soğukkanlılık','Pozisyon Alma','Takım Oyunu','Topsuz Alan','Vizyon','Çeviklik','Dayanıklılık',
        'Denge','Güç','Hız','Hızlanma','Vücut Zindeliği','Zıplama'],
 'FB': ['Dripling','İlk Kontrol','Kafa Vuruşu','Markaj','Orta Yapma','Pas','Teknik','Top Kapma',
        'Agresiflik','Cesaret','Çalışkanlık','Karar Alma','Kararlılık','Konsantrasyon','Önsezi',
        'Soğukkanlılık','Pozisyon Alma','Takım Oyunu','Topsuz Alan','Vizyon','Çeviklik','Dayanıklılık',
        'Denge','Güç','Hız','Hızlanma','Vücut Zindeliği','Zıplama'],
 'CM': ['İlk Kontrol','Kafa Vuruşu','Markaj','Pas','Teknik','Top Kapma','Cesaret','Çalışkanlık',
        'Karar Alma','Kararlılık','Konsantrasyon','Önsezi','Soğukkanlılık','Pozisyon Alma','Takım Oyunu',
        'Topsuz Alan','Vizyon','Çeviklik','Dayanıklılık','Denge','Güç','Hız','Hızlanma',
        'Vücut Zindeliği','Zıplama'],
 'FW': ['Bitiricilik','Dripling','İlk Kontrol','Orta Yapma','Pas','Teknik','Top Kapma','Uzaktan Şut',
        'Çalışkanlık','Karar Alma','Kararlılık','Konsantrasyon','Önsezi','Özel Yetenek',
        'Soğukkanlılık','Pozisyon Alma','Takım Oyunu','Topsuz Alan','Vizyon','Çeviklik','Dayanıklılık','Hız','Hızlanma'],
 'ST': ['Bitiricilik','Dripling','İlk Kontrol','Kafa Vuruşu','Pas','Teknik','Cesaret','Karar Alma',
        'Kararlılık','Önsezi','Soğukkanlılık','Pozisyon Alma','Takım Oyunu','Topsuz Alan','Vizyon','Çeviklik',
        'Dayanıklılık','Güç','Hız','Hızlanma','Vücut Zindeliği','Zıplama'],
}

# ----------------------------------------------------------------------------
# 4) ANA AKIŞ
# ----------------------------------------------------------------------------
def main():
    # v8 master: openpyxl 'nan' tipli hücrelerde kırılıyor -> calamine ile ham okuma.
    # FM_Donusum_Notu yalnız iç izleme içindir; JSON/frontend'e sızmaması için hemen düşürülür.
    from python_calamine import CalamineWorkbook
    _wb = CalamineWorkbook.from_path(SRC)
    _rows = _wb.get_sheet_by_name(SHEET).to_python(skip_empty_area=False)
    raw = pd.DataFrame(_rows[1:], columns=[str(c) for c in _rows[0]]).replace('', pd.NA)
    raw = raw.drop(columns=['FM_Donusum_Notu'], errors='ignore')
    del _wb, _rows
    # BigStatX_finaldb pozisyon-genişletilmiş gelir: her oyuncu-pozisyon bir satır.
    # Oyuncu başına tek satıra indirgeriz (Poz_Birincil=True öncelikli), kovaları tüm satırlarından toplarız.
    def _sc(col):  # NA-güvenli string (pandas 3.0'da NA, birleştirmede yayılıp satırları çöktürür)
        return raw[col].map(lambda v: '' if pd.isna(v) else str(v))
    raw['_pkey'] = _sc('Oyuncu') + '||' + _sc('Takım') + '||' + _sc('Lig')
    prim = raw.sort_values('Poz_Birincil', ascending=False, kind='stable')
    df = prim.drop_duplicates(subset=['_pkey']).reset_index(drop=True)

    # ------------------------------------------------------------------
    # QSL_ KATMANI: SL yüzde kolonları scrape row-shift ile bozuk
    #   (şut isabet %99 sapma, müdahale %87, dribling %83). Ham sayaçlardan yeniden hesapla.
    #   pct = kazanılan/toplam*100, clamp 0-100. Yeterli hacim yoksa (payda<3) NaN.
    # ------------------------------------------------------------------
    QSL_MAP = {
        'QSL_Dribling Başarı':   ('SL_Başarılı Dribling',            'SL_Dribling Denemesi'),
        'QSL_Pas İsabet':        ('SL_İsabetli Pas',                 'SL_Toplam Pas'),
        'QSL_Şut İsabet':        ('SL_İsabetli Şut',                 'SL_Toplam Şut'),
        'QSL_Müdahale Başarı':   ('SL_Kazanılan Müdahaleler',        'SL_Müdahaleler'),
        'QSL_Orta İsabet':       ('SL_İsabetli Orta',                'SL_Toplam Orta'),
        'QSL_İkili Mücadele':    ('SL_Kazanılan İkili Mücadele',     'SL_Toplam İkili Mücadele'),
        'QSL_Hava Mücadele':     ('SL_Kazanılan Hava Topu Mücadelesi','SL_Hava Topu Mücadelesi'),
        'QSL_Yer Mücadele':      ('SL_Kazanılan Yer Mücadelesi',     'SL_Yer Mücadelesi'),
    }
    n_qsl = 0
    for qcol, (succ_c, att_c) in QSL_MAP.items():
        if succ_c in df.columns and att_c in df.columns:
            s = pd.to_numeric(df[succ_c], errors='coerce')
            a = pd.to_numeric(df[att_c], errors='coerce')
            # değerler per-90; payda >0 yeterli (per-90'da 3 deneme nadir). Düşük hacim gürültüsü
            # için minik bir eşik (0.5 deneme/90) uygula.
            pct = np.where(a >= 0.5, np.clip(s / a * 100.0, 0, 100), np.nan)
            df[qcol] = pct
            n_qsl += 1
    print(f"QSL_ KATMANI: {n_qsl} yüzde kolonu ham sayaçlardan yeniden hesaplandı (scrape hatası düzeltildi)")

    # BİTİRİCİLİK VERİMİ: Gol − xG (per-90). Pozitif = xG'den fazla gol (klinik bitirici),
    #   negatif = xG'yi harcayan. FM Bitiricilik'ten farklı: gerçek maç verimi.
    if 'SL_Gol Sayısı' in df.columns and 'SL_Beklenen Gol (xG)' in df.columns:
        g = pd.to_numeric(df['SL_Gol Sayısı'], errors='coerce')
        xg = pd.to_numeric(df['SL_Beklenen Gol (xG)'], errors='coerce')
        df['QSL_Bitiricilik Verimi'] = g - xg          # per-90 aşırı/düşük performans
        df['QSL_xG'] = xg
        print(f"BİTİRİCİLİK VERİMİ: Gol−xG hesaplandı ({(g-xg).notna().sum()} oyuncu)")

    # BS KATMANI v2 (Rol Sistemi altyapısı): FM taban + FC kompozit override
    _gk_mask = df['FM_Mevki'].map(lambda s: 'GK' in parse_mevki(s)) if 'FM_Mevki' in df.columns \
               else df['Pozisyon'].astype(str).eq('GK')
    n_bs = build_bs_layer(df, gk_mask=_gk_mask)
    print(f"BS KATMANI: {n_bs} eksen üretildi (A simetrik / B yukarı / FM-only / FC-native)")

    # BS_ birleşik eksenlerini (0-100, FM+FC harmanlı) oyuncu kaydına serileştirmek için
    # satır -> {eksen: değer} önbelleği. Filtreleme arayüzünün sayısal attribute havuzu budur.
    bs_axes = [c[3:] for c in df.columns if c.startswith('BS_') and not c.startswith('BS_src_')]
    _bs_cols = ['BS_' + a for a in bs_axes]
    _bs_pairs = list(zip(bs_axes, _bs_cols))
    _bs_records = df[_bs_cols].round(1).to_dict(orient='index')
    def bs_for_row(rowid):
        rec = _bs_records.get(rowid)
        if not rec: return {}
        out = {}
        for a, col in _bs_pairs:
            v = rec[col]
            if v is not None and not (isinstance(v, float) and np.isnan(v)):
                out[a] = v
        return out
    bs_axes_gk = [a for a in bs_axes if a not in ROL_GK_EXC]
    bs_axes_field = [a for a in bs_axes if a not in ROL_GK_ONLY]

    ROL_SCORER, ROL_STATS, ROL_SAB, ROL_REGISTRY = build_rol_layer(df)
    print(f"ROL KATMANI: scorer hazır, {len(ROL_STATS)} rol-havuz istatistiği (bucket başına havuz-uyumlu blok)")

    RE_CONTRACT = re.compile(r'\s*(?:19|20)\d{2}\s*~\s*(?:19|20)\d{2}\s*$')      # "Real Madrid2024 ~ 2029"
    RE_LOANTAG  = re.compile(r'\s*\d{1,2}\s+[^\d\s]{3,5}\.?\s+(?:19|20)\d{2}\s*Kirada\s*$')  # "FC Schalke 0430 Haz 2026Kirada"

    def fc_parse(s):
        """FC_Takım Sözleşme -> (temiz takım adı, kirada_mı)"""
        if not isinstance(s, str) or not s.strip(): return None, False
        if RE_LOANTAG.search(s):  return RE_LOANTAG.sub('', s).strip(), True
        if RE_CONTRACT.search(s): return RE_CONTRACT.sub('', s).strip(), False
        return s.strip(), False

    def strip_years(s):
        return RE_CONTRACT.sub('', RE_LOANTAG.sub('', s)).strip() if isinstance(s, str) else s

    pfc = df['FC_Takım Sözleşme'].map(fc_parse)
    df['_fc_team'] = pfc.map(lambda x: x[0])
    df['_fc_loan'] = pfc.map(lambda x: x[1])

    # Takım boş satırlar: FC sözleşme takımı (kirada değilse), yoksa FM_Kulüp
    fill_mask = df['Takım'].isna()
    n_team_fill = int(fill_mask.sum())
    if n_team_fill:
        fv = np.where(df.loc[fill_mask, '_fc_team'].notna() & ~df.loc[fill_mask, '_fc_loan'],
                      df.loc[fill_mask, '_fc_team'], df.loc[fill_mask, 'FM_Kulüp'])
        df.loc[fill_mask, 'Takım'] = fv

    # Grup-seviyesi kanonik ad: eski Takım -> modal FC adı; korumalar:
    #   FC kapsamı >=%50, mod payı >=%60, n>=5, çakışmada büyük kulüp kazanır
    #   (aksi halde adaş/kiralık FC eşleşmeleri kulüp adını zehirler: Aris->Fiorentina vb.)
    base = df[df['_fc_team'].notna() & ~df['_fc_loan'] & df['FM_Kiralık'].isna() & df['Takım'].notna()]
    cand = {}
    for old, g in base.groupby('Takım'):
        tot_rows = int((df['Takım'] == old).sum())
        vc = g['_fc_team'].value_counts()
        if len(vc) == 0: continue
        cover = len(g) / max(tot_rows, 1)
        share = vc.iloc[0] / vc.sum()
        if cover >= 0.5 and share >= 0.6 and vc.iloc[0] >= 5:
            cand[old] = (vc.index[0], int(vc.iloc[0]))
    # çakışma: aynı hedefe giden eski adlardan yalnız en kalabalık olanı rename edilir
    best = {}
    for old, (new, n) in cand.items():
        if new not in best or n > best[new][1]: best[new] = (old, n)
    tmap = {old: new for new, (old, n) in best.items()}
    n_renamed = sum(1 for o, nw in tmap.items() if o != nw)

    def canon_old(t):
        return tmap.get(t, strip_years(t)) if isinstance(t, str) else t

    kiralik  = df['FM_Kiralık'].notna()
    serbest  = df['Not'].astype(str).eq('Serbest')
    # Sezonu kirada geçirmiş oyuncu: FC_Takım Sözleşme'de "Kirada" varsa fiilen oynadığı
    # (kiralık) kulübe yaz — FM_Kiralık işareti olmasa da FC "Kirada" tag'i tek başına yeterli.
    loan_fix = (df['_fc_loan'] & df['_fc_team'].notna() & ~serbest).values

    team_final = np.where(loan_fix, df['_fc_team'], df['Takım'].map(canon_old))
    df['_team0'] = df['Takım']          # rapor için
    df['_lig0']  = df['Lig']
    df['Takım']  = team_final

    # FM+FC konsensüs düzeltmesi: iki kaynak aynı kulübü söylüyor ama master Takım farklıysa taşı
    def _norm(sx):
        sx = str(sx).lower()
        for a2, b2 in zip('ışğüöçâîûé', 'isguocaiue'): sx = sx.replace(a2, b2)
        return re.sub(r'[^a-z0-9]', '', sx)
    n_consensus = 0
    for i in df.index:
        if loan_fix[i] or df.at[i, '_fc_loan']: continue
        ft = df.at[i, '_fc_team']; fk = df.at[i, 'FM_Kulüp']; tk = df.at[i, 'Takım']
        if not (isinstance(ft, str) and isinstance(fk, str) and isinstance(tk, str)): continue
        a2, b2, c2 = _norm(fk), _norm(ft), _norm(tk)
        if not a2 or not b2: continue
        if (a2 in b2 or b2 in a2) and not (c2 in b2 or b2 in c2):
            df.at[i, 'Takım'] = tmap.get(ft, ft); n_consensus += 1

    # Bölünmüş takımları birleştir — DOĞRU SİNYAL: her master etiketin KENDİ non-loan
    # FC-modal adı. İki etiket ancak aynı FC-modal ada çözülürse birleşir.
    # (Independiente kendi FC-modali "Independiente"dir -> Rivadavia'ya KARIŞMAZ;
    #  "Istanbul Basaksehir" FC-modali "Medipol Başakşehir FK" -> oraya döner.)
    def _norm(sx):
        sx = str(sx).lower()
        for a2, b2 in zip('ışğüöçâîûé', 'isguocaiue'): sx = sx.replace(a2, b2)
        return re.sub(r'[^a-z0-9]', '', sx)
    label_canon = {}   # master etiket -> kanonik ad (kendi FC-modali)
    from collections import defaultdict as _dd
    # Bir etiketin FC-modali ancak GÜÇLÜ destekle kanonik sayılır:
    #   n>=8 non-loan FC satırı VE modal payı>=0.85. Böylece 1-3 satırlı çöp SL-eşleşmeli
    #   etiketler (Aris->Fiorentina, CSKA 1948->Preston, S.Gijón n=1) modal üretemez.
    for t, g in df.groupby('Takım'):
        if not isinstance(t, str): continue
        nl = g[~g['_fc_loan'] & g['_fc_team'].notna()]
        if len(nl) >= 8:
            vc = nl['_fc_team'].value_counts()
            if vc.iloc[0] / vc.sum() >= 0.85:
                label_canon[t] = vc.index[0]
    canon_by_norm = _dd(set); canon_display = {}
    for t, cn in label_canon.items():
        canon_by_norm[_norm(cn)].add(t); canon_display[_norm(cn)] = cn
    team_merges = {}
    for key, labels in canon_by_norm.items():
        target = canon_display[key]
        exact = [t for t in labels if _norm(t) == key]
        tgt = exact[0] if exact else target
        for t in labels:
            if t != tgt: team_merges[t] = tgt
    # loanee etiketleri (tüm satırları 'Kiralık→ana kulüp', kendi FC'si yok) ana kulübe bağla:
    #   normalize adı bir kanonik hedefin öz-alt-dizisiyse ("Başakşehir FK" ⊂ "Medipol Başakşehir FK")
    for t, g in df.groupby('Takım'):
        if not isinstance(t, str) or t in team_merges: continue
        notv = g['Not'].astype(str)
        loan_share = (notv == 'Kiralık→ana kulüp').mean()
        if loan_share < 0.6: continue   # ağırlıklı loanee-etiketi (NaN Not toleransı)
        nt = _norm(t)
        if len(nt) < 6: continue
        hits = [full for k, full in canon_display.items() if nt in k and nt != k]
        if len(hits) == 1:
            lt = set(g['Lig'].dropna()); lg = set(df.loc[df['Takım'] == hits[0], 'Lig'].dropna())
            if not (lt and lg and not (lt & lg)):
                team_merges[t] = hits[0]
    if team_merges:
        df['Takım'] = df['Takım'].map(lambda t: team_merges.get(t, t) if isinstance(t, str) else t)

    # Brezilya 3-harfli kulüp kodları -> tam ad (12'si FC sözleşmesiyle doğrulandı, 7'si
    # standart CBF kısaltması). Aynı kulüp hem "FLA" hem "Flamengo" olarak bölünmesin.
    BR_CODE = {
        'FLA':'Flamengo','BOT':'Botafogo','FLU':'Fluminense','VDG':'Vasco da Gama',
        'COR':'Corinthians','SAN':'Santos','SPO':'São Paulo','SEP':'Palmeiras',
        'GRE':'Grêmio','INT':'Internacional','ATM':'Atlético Mineiro','CEC':'Cruzeiro',
        'BAH':'Bahia','VIT':'Vitória','FOR':'Fortaleza','CEA':'Ceará',
        'MFC':'Mirassol','BRA':'Bragantino','SPT':'Sport Recife',
    }
    br_mask = df['Lig'].astype(str).eq('Brezilya')
    n_br = 0
    for code, full in BR_CODE.items():
        m = br_mask & df['Takım'].astype(str).eq(code)
        n = int(m.sum())
        if n:
            df.loc[m, 'Takım'] = full; n_br += n
            team_merges[code] = full
    if n_br:
        print(f"BREZİLYA KODLARI: {n_br} kayıt tam kulüp adına çevrildi ({len([c for c in BR_CODE if (br_mask & df['Takım'].astype(str).eq(BR_CODE[c])).any()])} kulüp)")

    # GENEL 3-HARFLİ KOD ÇÖZÜMÜ: Brezilya dışı kodlar (AEK, AZ, PSV, OL, PAOK, BRG…)
    #   FC sözleşmesindeki gerçek kulüp adıyla çözülür. Kiralık sözleşmeler HARİÇ
    #   (parent-club sızıntısını önler); kapsam >=%50 & n>=3 şartı yanlış eşlemeyi keser.
    def _fc_realname(s):
        if not isinstance(s, str) or s == 'nan': return None
        if RE_LOANTAG.search(s): return None        # kiralık: parent club sızmasın
        return RE_CONTRACT.sub('', s).strip() or None
    all_codes = [t for t in df['Takım'].dropna().unique()
                 if isinstance(t, str) and len(t) <= 4 and t.isupper()]
    n_code = 0; code_resolved = 0
    for c in all_codes:
        cm = df['Takım'].astype(str).eq(c)
        nonloan = cm & ~df['FC_Takım Sözleşme'].astype(str).str.contains('Kirada', na=False)
        names = df.loc[nonloan, 'FC_Takım Sözleşme'].map(_fc_realname).dropna()
        if len(names) == 0: continue
        vc = names.value_counts()
        top, top_n = vc.index[0], vc.iloc[0]
        if top_n >= max(3, 0.5 * int(cm.sum())) and top != c:
            df.loc[cm, 'Takım'] = top; team_merges[c] = top
            n_code += int(cm.sum()); code_resolved += 1
    if n_code:
        print(f"KOD ÇÖZÜMÜ (genel): {n_code} kayıt {code_resolved} kod FC sözleşme adına çevrildi")

    # KALAN KOD FRAGMANLARI: FC adı yoksa SL_Takım (StatLeague gerçek kulüp adı) ile çöz.
    #   Kod=gerçek ad olanlar (PSV, AIK, PAOK…) dokunulmaz; yalnız SL farklı GERÇEK ad verirse çevir.
    if 'SL_Takım' in df.columns:
        n_sl = 0
        left_codes = [t for t in df['Takım'].dropna().unique()
                      if isinstance(t, str) and len(t) <= 4 and t.isupper()]
        for c in left_codes:
            cm = df['Takım'].astype(str).eq(c)
            sl = df.loc[cm, 'SL_Takım'].dropna().astype(str)
            sl = sl[sl.str.len() > 4]                 # kısa/kod-benzeri SL adını atla
            if len(sl) == 0: continue
            vc = sl.value_counts()
            if vc.iloc[0] >= max(1, 0.5 * int(cm.sum())) and vc.index[0] != c:
                df.loc[cm, 'Takım'] = vc.index[0]; team_merges[c] = vc.index[0]; n_sl += int(cm.sum())
        if n_sl:
            print(f"KOD ÇÖZÜMÜ (SL_Takım): {n_sl} kalan kod-fragman kaydı gerçek kulübe çevrildi")

    # FC lisans-adı düzeltmeleri: aynı kulübün FC ve FM adları farklı olabiliyor.
    #   Real San Sebastián (FC lisanssız adı) = Real Sociedad. FM_Kulüp'e göre ana/B ayrımı:
    #   'B' içeren -> Real Sociedad B; diğerleri -> Real Sociedad (ana).
    ss_mask = df['Takım'].astype(str).eq('Real San Sebastián')
    if ss_mask.any():
        fmk = df['FM_Kulüp'].astype(str)
        is_b = fmk.str.contains(r'B$| B\b', regex=True, na=False)
        main = ss_mask & ~is_b
        bteam = ss_mask & is_b
        nm = int(main.sum()); nb = int(bteam.sum())
        if nm: df.loc[main, 'Takım'] = 'Real Sociedad'
        if nb: df.loc[bteam, 'Takım'] = 'Real Sociedad B'
        team_merges['Real San Sebastián'] = 'Real Sociedad'
        print(f"FC ALIAS: Real San Sebastián -> Real Sociedad ({nm} ana + {nb} B-takım)")
    # Sociedad B isim varyantlarını tek ada topla
    socb = df['Takım'].astype(str).isin(['Real Sociedad de Fútbol B', 'Real Sociedad de Futbol B'])
    if socb.any():
        df.loc[socb, 'Takım'] = 'Real Sociedad B'

    # YAZIM VARYANTI BİRLEŞTİRME: "1. FC X" / "1.FC X", "Al Okhdood" / "Al-Okhdood" gibi
    #   aynı kulübün boşluk/tire/nokta farklı yazımları tek kadroda toplanır (fragman önler).
    def _norm_team(s):
        return re.sub(r'[^a-z0-9]', '', str(s).lower())
    _tcounts = df['Takım'].dropna().astype(str).value_counts()
    _variant_groups = {}
    for t in _tcounts.index:
        _variant_groups.setdefault(_norm_team(t), []).append(t)
    n_variant = 0
    for _nk, _vs in _variant_groups.items():
        if len(_vs) > 1:
            canon = max(_vs, key=lambda t: _tcounts[t])   # en çok kadrolu yazım kanonik
            for v in _vs:
                if v != canon:
                    m = df['Takım'].astype(str).eq(v)
                    df.loc[m, 'Takım'] = canon; team_merges[v] = canon; n_variant += int(m.sum())
    if n_variant:
        print(f"YAZIM VARYANTI: {n_variant} kayıt boşluk/tire/nokta farklı yazımdan tek ada toplandı")

    print("TAKIM BİRLEŞTİRME:", len(team_merges), "ad tek kanonik ada toplandı (FC-modal n>=8 & pay>=0.85)")
    for old, new in sorted(team_merges.items()):
        print(f"   {old}  ->  {new}")
    print(f"KONSENSÜS DÜZELTMESİ: {n_consensus} oyuncu FM+FC hemfikirliğiyle doğru kulübüne taşındı | Takım boş doldurulan: {n_team_fill}")

    # takım -> kanonik lig (loan-fix görmemiş satırlardan; >=%80 tek lig şartı)
    pool_l = df[~pd.Series(loan_fix, index=df.index) & df['Takım'].notna() & df['Lig'].notna()]
    canon_lig = {}
    for t, ls in pool_l.groupby('Takım')['Lig'].agg(list).items():
        s = pd.Series(ls).value_counts()
        if s.iloc[0] / s.sum() >= 0.8: canon_lig[t] = s.index[0]
    flmap = {}
    fl = df[df['FM_Lig'].notna() & df['Lig'].notna() & ~kiralik]
    if len(fl):
        flmap = fl.groupby('FM_Lig')['Lig'].agg(lambda x: x.mode().iloc[0]).to_dict()

    lig_new, n_lig_loan, n_lig_other = [], 0, 0
    for i in df.index:
        L0 = df.at[i, 'Lig']; t = df.at[i, 'Takım']
        if loan_fix[i]:
            L = canon_lig.get(t) or flmap.get(df.at[i, 'FM_Lig']) or L0
            if L != L0: n_lig_loan += 1
        else:
            L = canon_lig.get(t, L0)
            if pd.notna(L0) and L != L0: n_lig_other += 1
        lig_new.append(L)
    df['Lig'] = lig_new

    # --- TRANSFER LİG DÜZELTMESİ (FM_Lig otoritesi) ---
    #   Transfer olmuş oyuncuda Lig eski kulübünün ligi kalabilir (ör. Xavi Simons: Spurs
    #   ama Lig=Almanya). Düzeltme: oyuncunun FM_Lig eşlemesi HEM takımının ev-ligine HEM
    #   de mevcut Lig'den farklıya işaret ediyorsa, takımın ev-ligine çek. İki bağımsız
    #   sinyal (takım ev-ligi + FM_Lig) aynı hedefte buluşmalı -> güvenli.
    _ml = df[df['FM_Lig'].notna() & df['Lig'].notna()]
    FML2LIG = {}
    for fml, g in _ml.groupby(df['FM_Lig'].astype(str)):
        vc = g['Lig'].astype(str).value_counts()
        if vc.iloc[0] / vc.sum() >= 0.80 and vc.sum() >= 20:
            FML2LIG[fml] = vc.index[0]
    team_home = {}
    for t, g in df[df['Takım'].notna()].groupby('Takım'):
        team_home[t] = g['Lig'].astype(str).value_counts().index[0]
    n_transfer_lig = 0
    for idx in df.index[df['Takım'].notna() & df['FM_Lig'].notna()]:
        t = df.at[idx, 'Takım']; lig = str(df.at[idx, 'Lig'])
        home = team_home.get(t); fm_target = FML2LIG.get(str(df.at[idx, 'FM_Lig']))
        if fm_target and home and lig != home and fm_target == home:
            df.at[idx, 'Lig'] = home; n_transfer_lig += 1
    # NaN-takım / takımsız kayıt: FM_Kulüp'ü takım yap + FM_Lig'i lig yap (iki FM sinyali)
    n_fmk_fill = 0
    for idx in df.index[df['Takım'].isna() & df['FM_Kulüp'].notna() & df['FM_Lig'].notna()]:
        fmk = str(df.at[idx, 'FM_Kulüp']).strip()
        fm_target = FML2LIG.get(str(df.at[idx, 'FM_Lig']))
        if fmk and fm_target:
            df.at[idx, 'Takım'] = fmk
            if str(df.at[idx, 'Lig']) != fm_target:
                df.at[idx, 'Lig'] = fm_target
            n_fmk_fill += 1
    print(f"TRANSFER LİG DÜZELTMESİ: {n_transfer_lig} oyuncu doğru lige çekildi | "
          f"{n_fmk_fill} takımsız kayıt FM_Kulüp+FM_Lig ile dolduruldu")

    # Az-oyunculu (≤2) takım tek başına yanlış ligde olabilir (ev-ligi güvenilmez).
    #   Tüm oyuncularının FM_Lig'i tek ve net bir lige işaret ediyorsa doğrudan ona çek.
    n_small_lig = 0
    for t, g in df[df['Takım'].notna()].groupby('Takım'):
        if len(g) > 2: continue
        fmls = g['FM_Lig'].dropna().astype(str).map(FML2LIG).dropna()
        if len(fmls) == 0: continue
        if fmls.nunique() == 1:
            target = fmls.iloc[0]
            cur = g['Lig'].astype(str).value_counts().index[0]
            if target != cur:
                df.loc[g.index, 'Lig'] = target; n_small_lig += len(g)
    if n_small_lig:
        print(f"KÜÇÜK-TAKIM LİG DÜZELTMESİ: {n_small_lig} kayıt FM_Lig otoritesiyle doğru lige çekildi")

    # --- LİG KİRLİLİĞİ TEMİZLEME ---
    # Her takım tek gerçek lige ait. Bir takımın oyuncularının çoğunluğu bir ligdeyse,
    # azınlık-ligdeki parçalar çöp SL-eşleşmesidir. FM otoritesiyle karar:
    #   * FM aynı takımı doğruluyorsa -> lig, takımın çoğunluk ligine çekilir
    #   * FM farklı kulüp diyorsa      -> master 'Takım' yanlış eşleşme; kayıt çöp (drop)
    df['_drop'] = False
    tl_after = df[df['Takım'].notna() & df['Lig'].notna()]
    # takım -> çoğunluk (plurality) lig ve oyuncu-lig dağılımı
    team_major_lig = {}
    for t, g in tl_after.groupby('Takım'):
        vc = g['Lig'].value_counts()
        team_major_lig[t] = (vc.index[0], int(vc.iloc[0]), int(vc.sum()))
    orphan_rows, relabel_n = [], 0
    for (t, L), g in tl_after.groupby(['Takım', 'Lig']):
        maj, maj_n, tot = team_major_lig[t]
        if L == maj:
            continue
        # azınlık lig parçası: bu ligdeki oyuncu sayısı, çoğunluk liginden az olmalı
        this_n = len(g)
        if this_n >= maj_n:
            continue   # baskın değil, dokunma (belirsiz)
        for i in g.index:
            fk = df.at[i, 'FM_Kulüp']
            if isinstance(fk, str) and fk.strip():
                nfk, nt = _norm(fk), _norm(t)
                contain = (len(nt) >= 4 and nt in nfk) or (len(nfk) >= 4 and nfk in nt)
                if nfk == nt or nfk.startswith(nt) or nt.startswith(nfk) or contain:
                    # FM aynı kulüp / B-II-rezerv uzantısı / yazım varyantı -> aynı kulüp; lig çoğunluğa
                    df.at[i, 'Lig'] = maj; relabel_n += 1
                else:
                    # FM NET ilgisiz kulüp -> master Takım yanlış SL eşleşmesi; çöp
                    orphan_rows.append(i)
            else:
                df.at[i, 'Lig'] = maj; relabel_n += 1
    if orphan_rows:
        df.loc[orphan_rows, '_drop'] = True
    print(f"LİG KİRLİLİĞİ: {relabel_n} kayıt çoğunluk lige çekildi | "
          f"{len(orphan_rows)} çöp (yanlış-lig) kayıt gözatmadan çıkarıldı")
    for i in orphan_rows[:25]:
        print(f"   ELENDİ: {df.at[i,'Oyuncu']} | Takım(now)={df.at[i,'Takım']} | "
              f"FM_Kulüp={df.at[i,'FM_Kulüp']!r} | master0={df.at[i,'_team0']}/{df.at[i,'_lig0']}")

    # yaş: FM_DT'den bugüne göre hesap (fallback: SL_Yaş, FM_Yaş)
    today = pd.Timestamp.today().normalize()
    dtv = pd.to_datetime(df['FM_DT'], errors='coerce')
    df['_age'] = np.floor((today - dtv).dt.days / 365.2425)
    df['_age'] = df['_age'].fillna(pd.to_numeric(df['SL_Yaş'], errors='coerce'))
    df['_age'] = df['_age'].fillna(pd.to_numeric(df['FM_Yaş'], errors='coerce'))

    # boy (cm): FM_Boy birincil (%97 dolu, "178 cm") -> FC_Boy -> SL_Boy fallback
    def _cm(series):
        return pd.to_numeric(series.astype(str).str.extract(r'(\d{3})')[0], errors='coerce')
    _boy = _cm(df['FM_Boy']) if 'FM_Boy' in df.columns else pd.Series(np.nan, index=df.index)
    if 'FC_Boy' in df.columns: _boy = _boy.fillna(_cm(df['FC_Boy']))
    if 'SL_Boy' in df.columns: _boy = _boy.fillna(pd.to_numeric(df['SL_Boy'], errors='coerce'))
    df['_boy'] = _boy

    print(f"ÖN-İŞLEME: {n_renamed} takım adı kanonikleştirildi | kiralık düzeltmesi {int(loan_fix.sum())} oyuncu "
          f"(lig değişen {n_lig_loan}) | kiralık-dışı lig düzeltmesi {n_lig_other} | "
          f"yaş DT'den hesaplanan {int(dtv.notna().sum())}")

    # ------------------------------------------------------------------
    # ATTRIBUTE (BS) KADEMELERİ: 48 eksenin HER BİRİ için ayrı ayrı "doğal
    # kırılma" (ağırlıklı Fisher-Jenks, bkz. natural_breaks()) sınırı — sabit
    # FM 1-20 bandı yerine, eksenin gözatmadan çıkarılmış (_drop=False) nihai
    # oyuncu havuzundaki GERÇEK dağılımına göre 6 kademeye (Çok Kötü/Kötü/
    # Ortalama/İyi/Çok İyi/Elit) bölünür. Kademe adları burada değil,
    # frontend'de (sunum katmanı) — bu sözlük yalnız ham kesim noktalarını taşır.
    # ------------------------------------------------------------------
    _bs_pool = df[~df['_drop']]
    bs_tiers = {a: natural_breaks(pd.to_numeric(_bs_pool['BS_' + a], errors='coerce').values)
                for a in bs_axes}
    print(f"ATTRIBUTE KADEMELERİ: {len(bs_tiers)} eksen için doğal-kırılma sınırı hesaplandı "
          f"(6 kademe / eksen, {_bs_pool.shape[0]} oyuncu havuzu)")

    # POTANSİYEL (PA) KADEMESİ: bs eksenlerinden farklı olarak TEK global eksen — FM_PY
    # (0-200 ham) -> /2 -> 0-100, aynı ölçekte CA ile (bkz. aşağıdaki ca_rating hesabı).
    # natural_breaks() burada da PA'nın KENDİ dağılımına uygulanır; CA ile aynı sabit
    # eşikler KULLANILMAZ (PA çarpıklığı CA'dan farklı — çoğunlukla PA>=CA, üst-ağırlıklı).
    _pa_raw = pd.to_numeric(_bs_pool['FM_PY'], errors='coerce').values.astype(float) / 2.0
    _pa_raw = np.clip(_pa_raw, 0, 100)
    pa_tiers = natural_breaks(_pa_raw)
    print(f"POTANSİYEL KADEMESİ: doğal-kırılma sınırı hesaplandı -> {pa_tiers}")

    def to_native(v):
        if v is None: return None
        if isinstance(v, (np.integer,)): return int(v)
        if isinstance(v, (np.floating,)):
            v = float(v); return None if (np.isnan(v) or np.isinf(v)) else v
        if isinstance(v, (np.bool_, bool)): return bool(v)
        if isinstance(v, (pd.Timestamp,)): return v.strftime('%Y-%m-%d')
        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)): return None
        return v

    def gv(r, *cols):
        for c in cols:
            if c in r and pd.notna(r[c]): return to_native(r[c])
        return None

    def foot_norm(r):
        """Ayak -> Sol / Sağ / Çift (5 ham varyantı 3 temiz kategoriye indirger)."""
        v = r.get('FM_Kullandığı Ayak')
        if not isinstance(v, str): return None
        s = v.lower()
        if 'iki' in s or 'çift' in s or 'her' in s: return 'Çift ayaklı'
        if 'sol' in s: return 'Sol ayaklı'
        if 'sağ' in s: return 'Sağ ayaklı'
        return None

    # 4a) entry tablosu: 10 granüler kova, YALNIZ veride açık yazan pozisyonlardan
    #     sıra: FC_En İyi (otorite) -> FM_Mevki (parse_pos sırası) -> FC_Pozisyon listesi
    def player_positions(r):
        out = []
        def add(b):
            if b and b not in out: out.append(b)
        best = None
        v = r.get('FC_En İyi')
        if isinstance(v, str) and v.strip() in FC2B:
            best = FC2B[v.strip()]; add(best)
        for x in parse_pos(r.get('FM_Mevki')):
            add(FM2B.get(x))
        v = r.get('FC_Pozisyon')
        if isinstance(v, str):
            for c in v.split(','):
                add(FC2B.get(c.strip()))
        if best is None and out: best = out[0]
        return out, best

    rows, posmap = [], {}
    for idx, r in df.iterrows():
        if df.at[idx, '_drop']:
            continue
        ps, best = player_positions(r)
        posmap[idx] = (ps, best)
        for b in ps:
            rows.append({'row': idx, 'bucket': b})
    edf = pd.DataFrame(rows)

    players, sim_index = {}, {}   # entry_id -> player dict ; bucket -> (ids, NN)
    player_chunks, n_entries = [], 0   # bellek: kova biter bitmez serileştir
    team_roster = []                   # takım reytingi için (team, best_poz, ca, name)
    league_roster = []                 # lig kalite kademesi için (league, name, ca)

    # JSON çıktısı
    def clean(o):
        if isinstance(o, (np.integer,)): return int(o)
        if isinstance(o, (np.floating,)):
            o = float(o); return None if (np.isnan(o) or np.isinf(o)) else o
        if isinstance(o, (np.bool_,)): return bool(o)
        if isinstance(o, (pd.Timestamp,)): return o.strftime('%Y-%m-%d')
        return str(o)
    # Lig -> takım listesi (tam veriden; gözatma için)
    lt_map = {}
    if 'Lig' in df.columns and 'Takım' in df.columns:
        for L, sub in df.dropna(subset=['Lig']).groupby('Lig'):
            if not isinstance(L, str): continue
            teams = sorted({str(t).strip() for t in sub['Takım'].dropna().astype(str) if str(t).strip()})
            if teams: lt_map[L] = teams
    league_list = [{'name': L, 'teams': lt_map[L]} for L in sorted(lt_map, key=lambda x: -len(lt_map[x]))]

    out_buckets = {}
    bucket_avg = {}
    bucket_xscale = {}

    # --- Eklenebilir metrik kataloğu: SL per-90 kolonları + QSL_ düzeltilmiş katman ---
    SKIP_SL = {
        'SL_Dk', 'SL_Maç Sayısı', 'SL_Yaş', 'SL_Boy',
        # eşleşme/meta kolonları
        'SL_takim_raw_flag', 'SL_fm_idx', 'SL_match_score', 'SL_match_tier', 'SL_lig_id_final',
        # BOZUK yüzde kolonları (scrape row-shift) — QSL_ ile değiştirildi, ham hali gizlenir
        'SL_Dribling Başarı Yüzdesi', 'SL_Müdahale Başarı Yüzdesi', 'SL_Orta İsabet Yüzdesi',
        'SL_Şut Performansı', 'SL_İkili Mücadele Kazanma Yüzdesi',
        'SL_Hava Topu Mücadelesi Kazanma Yüzdesi', 'SL_Yer Mücadelesi Kazanma Yüzdesi',
        'SL_Pas İsabet Yüzdesi', 'SL_Uzun Top İsabet Yüzdesi',
    }
    QSL_LABEL = {
        'QSL_Dribling Başarı': 'Dribling Başarı % ✓', 'QSL_Pas İsabet': 'Pas İsabet % ✓',
        'QSL_Şut İsabet': 'Şut İsabet % ✓', 'QSL_Müdahale Başarı': 'Müdahale Başarı % ✓',
        'QSL_Orta İsabet': 'Orta İsabet % ✓', 'QSL_İkili Mücadele': 'İkili Mücadele % ✓',
        'QSL_Hava Mücadele': 'Hava Mücadele % ✓', 'QSL_Yer Mücadele': 'Yer Mücadele % ✓',
        'QSL_Bitiricilik Verimi': 'Bitiricilik Verimi (Gol−xG)', 'QSL_xG': 'xG (90dk)',
    }
    def xlabel(c): return QSL_LABEL.get(c, c[3:] if c.startswith('SL_') else c)
    xcat_cols = []
    for c in df.columns:
        if not (c.startswith('SL_') or c.startswith('QSL_')) or c in SKIP_SL: continue
        s = pd.to_numeric(df[c], errors='coerce')
        if s.notna().mean() < 0.15: continue
        xcat_cols.append(c)
    xcat = {c: xlabel(c) for c in xcat_cols}

    for b in POS10:
        sub = edf[edf['bucket'] == b]
        ridx = sub['row'].values
        D = df.loc[ridx]

        # --- RADAR percentile (>=600 dk havuzunda rank) ---
        radar_specs = RADAR[BASE[b]]
        pool = D[D['SL_Dk'] >= MIN_DK]
        pcts = {}  # col -> Series(percentile) hesaplanacak referans havuzu
        ref = {}
        for spec in radar_specs:
            col = spec[1]; inv = len(spec) > 2 and spec[2]
            vals = pd.to_numeric(pool[col], errors='coerce')
            if inv: vals = -vals
            ref[col] = vals.dropna()

        # --- Pozisyon × Lig: ortalama (kırmızı) + MAX/MIN (eksen tepesi = en yüksek) + rank dizileri ---
        avg_lp = {}
        lg_arr = {}    # L -> {col: değerler dizisi} (lig-içi sıra VE lig-içi percentile için)
        if 'Lig' in pool.columns and len(pool):
            for L, g in pool.groupby('Lig'):
                if not isinstance(L, str) or len(g) < 3: continue
                rv_a, pct_a, mx_a, mn_a = {}, {}, {}, {}
                arrs = {}
                for spec in radar_specs:
                    name, col = spec[0], spec[1]; inv = len(spec) > 2 and spec[2]
                    vals = pd.to_numeric(g[col], errors='coerce').dropna()
                    if not len(vals):
                        rv_a[name] = pct_a[name] = mx_a[name] = mn_a[name] = None; continue
                    mean = float(vals.mean()); rv_a[name] = round(mean, 2)
                    mx_a[name] = round(float(vals.max()), 2); mn_a[name] = round(float(vals.min()), 2)
                    arrs[col] = vals.values
                    vv = -mean if inv else mean; base = ref[col]
                    pct_a[name] = round(float((base < vv).mean() * 100)) if len(base) else 50
                avg_lp[L] = {'rv': rv_a, 'pct': pct_a, 'mx': mx_a, 'mn': mn_a}
                lg_arr[L] = arrs
        bucket_avg[b] = avg_lp

        # eklenebilir metrikler: lig-pozisyon min/max/ort (radar dışı tüm SL metrikleri)
        xsc = {}
        if 'Lig' in pool.columns and len(pool):
            for L, g in pool.groupby('Lig'):
                if not isinstance(L, str) or len(g) < 3: continue
                dd = {}
                for c in xcat_cols:
                    vals = pd.to_numeric(g[c], errors='coerce').dropna()
                    if len(vals):
                        dd[c] = [round(float(vals.min()), 2), round(float(vals.max()), 2), round(float(vals.mean()), 2)]
                xsc[L] = dd
        bucket_xscale[b] = xsc

        def radar_for(rowid, r):
            pct, raw, pctL = {}, {}, {}
            Lp = r.get('Lig'); larr = lg_arr.get(Lp, {}) if isinstance(Lp, str) else {}
            for spec in radar_specs:
                name, col = spec[0], spec[1]; inv = len(spec) > 2 and spec[2]
                v = pd.to_numeric(pd.Series([r[col]]), errors='coerce').iloc[0]
                if pd.isna(v):
                    pct[name] = None; raw[name] = None; pctL[name] = None; continue
                raw[name] = round(float(v), 2)
                vv = -v if inv else v
                base = ref[col]
                p = float((base < vv).mean() * 100) if len(base) else 50.0
                pct[name] = round(p)
                # lig-içi (pozisyon×lig havuzu) percentile
                la = larr.get(col)
                if la is not None and len(la):
                    la2 = -la if inv else la
                    pctL[name] = round(float((la2 < vv).mean() * 100))
                else:
                    pctL[name] = None
            return pct, raw, pctL

        # --- BENZERLİK attribute havuzu ---
        #   FM saha-içi (SIM_ATTRS) + FM saha-dışı (OFF_PITCH) + FC-only yeni sinyaller (FC_EXTRA)
        #   Örtüşende FM ana; FC'den yalnız FM'de karşılığı olmayanlar. Hepsi kova-içi percentile'a döner.
        fm_names = list(dict.fromkeys(SIM_ATTRS[BASE[b]] + OFF_PITCH))   # sıra korunur, tekrarsız
        fm_cols  = [(fmcol(a), a) for a in fm_names if fmcol(a) in df.columns]
        fc_list  = FC_EXTRA_GK if b == 'GK' else FC_EXTRA
        fc_cols  = [(fccol(a), 'FC:'+a) for a in fc_list if fccol(a) in df.columns]
        attr_pairs = fm_cols + fc_cols
        attr_cols  = [c for c, _ in attr_pairs]
        # NAME_FIX burada da uygulanır — fm_names bazı eksenlerde eski/ham etiketi taşıyor
        # (ör. 'Takım Oyunu'), gösterime kanonik isimle (İşbirliği) çıkmalı.
        attr_lbls  = [NAME_FIX.get(a, a) for _, a in attr_pairs]
        # rol-belirleyici maske: bu granular pozisyonun ROLE_KEY özellikleri (yalnız FM saha-içi)
        rolekeys = set(ROLE_KEY.get(b, []))
        role_w = np.array([ROLE_MULT if lbl in rolekeys else 1.0 for lbl in attr_lbls], dtype=np.float32)

        ROL_BUCKET = ROL_SCORER(b, D.index)   # bu kovanın havuzuna uygun rol blokları
        fm_ok = D['FM_Oyuncu'].notna() & pd.to_numeric(D['FM_MY'], errors='coerce').notna()
        Dsim = D[fm_ok]
        X = Dsim[attr_cols].apply(pd.to_numeric, errors='coerce').values.astype(np.float32)
        # eksik attribute -> kova ortalaması
        colmean = np.nanmean(X, axis=0)
        colmean = np.where(np.isnan(colmean), 0.0, colmean)
        inds = np.where(np.isnan(X))
        X[inds] = np.take(colmean, inds[1])

        # SEVİYE: FM_MY (CA, 0-200) -> 0-100 rating (÷2, FM standart gösterimi). Headline budur.
        #   Ayrıca kova-içi percentile ("pozisyon sırası") ikincil metrik olarak saklanır.
        ca_raw = pd.to_numeric(Dsim['FM_MY'], errors='coerce').values.astype(float)   # ham 0-200
        pa_raw = pd.to_numeric(Dsim['FM_PY'], errors='coerce').values.astype(float)   # potansiyel 0-200
        ca_fill = np.where(np.isnan(ca_raw), np.nanmean(ca_raw), ca_raw)
        ca_rating = np.clip(np.round(ca_fill / 2.0), 0, 100)                          # 0-100 CA
        fm_pct = ca_fill.argsort().argsort() / max(len(ca_fill) - 1, 1) * 100         # kova-içi percentile
        caZ = (ca_fill - ca_fill.mean()) / (ca_fill.std() or 1.0)

        # oyun modeli attribute percentile'ları (kova içi)
        ma_col = [fmcol(a) for a in MODEL_ATTRS]
        MX = Dsim[ma_col].apply(pd.to_numeric, errors='coerce').values.astype(float)
        cm = np.nanmean(MX, axis=0); ii = np.where(np.isnan(MX)); MX[ii] = np.take(cm, ii[1])
        MXP = MX.argsort(0).argsort(0) / max(len(MX) - 1, 1) * 100

        sim_ids = [f"{ri}_{b}" for ri in Dsim.index]
        sim_rows = list(Dsim.index)      # j -> rowid (ROL bloğu anahtarı)
        pos_sets = [set(posmap[ri][0]) for ri in Dsim.index]
        best_arr = [posmap[ri][1] for ri in Dsim.index]   # ana mevki (FC_En İyi -> best)
        age_arr = pd.to_numeric(Dsim.get('_age'), errors='coerce')
        age_arr = age_arr.fillna(pd.to_numeric(Dsim.get('SL_Yaş'), errors='coerce')).values
        boy_arr = pd.to_numeric(Dsim.get('_boy'), errors='coerce').values   # cm; NaN olabilir

        # BENZERLİK = "Rol-İmza": pozisyon-içi PERCENTILE profili üzerinde
        #   ŞEKİL (merkezli percentile cosine) + SPIKE (üstel + rol-belirleyici ağırlıklı imza örtüşmesi)
        #   → herkeste yüksek/düşük olan sönümlenir; UÇ ve ROL-BELİRLEYİCİ özellikler baskın olur.
        #   Böylece aynı pozisyondaki zıt arketipler (DM: presçi vs DLP) ayrışır.
        mu  = X.mean(axis=0)                              # yalnız "öne çıkan" gösterimi için
        P   = (X.argsort(0).argsort(0) / max(len(X) - 1, 1) * 100.0).astype(np.float32)  # pozisyon-içi percentile
        # ŞEKİL: merkezlenmiş percentile cosine — SADECE pozitif korelasyon (taban şişmesini önler)
        Pc  = P - P.mean(0)
        Pn  = (Pc / (np.linalg.norm(Pc, axis=1, keepdims=True) + 1e-6)).astype(np.float32)
        del Pc
        SIMS = np.clip(Pn @ Pn.T, 0, 1)                   # 0-1 şekil (n×n, tek matris)
        SIMS *= (SHAPE_W * 100.0)
        del Pn
        # SPIKE: ≥SPIKE_T imza; ÜSTEL + ROL-BELİRLEYİCİ ağırlık — SIMS üzerine ekle, ayrı matris tutma
        SP  = np.clip((P - SPIKE_T) / (100.0 - SPIKE_T), 0, 1) ** SPIKE_EXP
        SP  = (SP * role_w[None, :]).astype(np.float32)
        SPn = (SP / (np.linalg.norm(SP, axis=1, keepdims=True) + 1e-6)).astype(np.float32)
        del SP
        SPK = np.clip(SPn @ SPn.T, 0, 1)                  # ikinci ve son n×n çarpım
        del SPn
        SIMS += (SPIKE_W * 100.0) * SPK
        del SPK
        # CA hafif etki — satır satır çıkar (n×n broadcast matrisi oluşturma)
        caA = ca_fill.astype(np.float32)
        SIMS -= CA_LIGHT * np.abs(caA[:, None] - caA[None, :]).astype(np.float32)
        SIMS = SIMS.astype(np.float32)                    # 0-100, YÜKSEK = benzer


        # İSTATİSTİK BENZERLİĞİ = radar (per-90 gerçek çıktı) üzerinde Öklid (kova-içi normalize)
        rad_cols = [s[1] for s in radar_specs]
        RV = Dsim[rad_cols].apply(pd.to_numeric, errors='coerce').values.astype(np.float32)
        rmed = np.nanmedian(RV, axis=0); jj = np.where(np.isnan(RV)); RV[jj] = np.take(rmed, jj[1])
        rmin = RV.min(0); rmax = RV.max(0); rng = np.where((rmax - rmin) < 1e-9, 1.0, rmax - rmin)
        RN = (RV - rmin) / rng
        for k, spec in enumerate(radar_specs):
            if len(spec) > 2 and spec[2]: RN[:, k] = 1.0 - RN[:, k]   # düşük=iyi metrik
        Gs = RN @ RN.T; sqs = np.einsum('ij,ij->i', RN, RN)
        DS = np.sqrt(np.clip(sqs[:, None] + sqs[None, :] - 2.0 * Gs, 0, None)).astype(np.float32)
        del Gs

        # --- entry kayıtları ---
        bucket_ids = []
        for pos_i, (rowid, r) in enumerate(zip(Dsim.index, Dsim.itertuples(index=False))):
            r = Dsim.loc[rowid]
            eid = f"{rowid}_{b}"
            rad, rawd, radL = radar_for(rowid, r)
            overall = int(ca_rating[pos_i])              # 0-100 CA rating (headline)
            ca_val = int(ca_rating[pos_i])               # aynı 0-100 CA (kadro rozetleri geriye uyum)
            pct_bucket = round(float(fm_pct[pos_i]))      # kova-içi percentile (pozisyon sırası)
            pa_val = None if np.isnan(pa_raw[pos_i]) else int(round(min(pa_raw[pos_i] / 2.0, 100)))

            attr_pct = {MODEL_ATTRS[c]: round(float(MXP[pos_i, c])) for c in range(len(MODEL_ATTRS))}
            ap_list = [attr_pct[a] for a in MODEL_ATTRS]
            fit = {}
            for mk, (mn, mw) in MODELS.items():
                tot = sum(mw.values())
                # mw (MODELS ağırlık sözlüğü) hâlâ eski/ham isimleri kullanıyor (ör. 'Takım
                # Oyunu') — attr_pct artık NAME_FIX'lenmiş kanonik isimlerle anahtarlı
                # (bkz. MODEL_ATTRS), o yüzden burada da NAME_FIX ile çözülmeli.
                fit[mk] = round(sum(attr_pct[NAME_FIX.get(a, a)] * wt for a, wt in mw.items()) / tot)

            sims, fut = [], []
            n = len(SIMS)
            if n > 1:
                sc = SIMS[pos_i].astype(float)           # 0-100 benzerlik skoru
                sc[pos_i] = -np.inf
                order = np.argsort(-sc)                   # en yüksek skor önce
                my_pos = pos_sets[pos_i]
                my_best = best_arr[pos_i]
                def same_mevki(j):
                    # ANA MEVKİ ŞART: adayın best'i hedefin best'iyle aynı olmalı
                    # (kanat oyuncusu AM oynayabiliyor diye AM'ciyle eşleşmesin)
                    if my_best and best_arr[j] and best_arr[j] != my_best:
                        return False
                    pj = pos_sets[j]
                    return (not my_pos) or (not pj) or bool(my_pos & pj)
                hi = boy_arr[pos_i]
                def height_ok(j):
                    hj = boy_arr[j]
                    if hi != hi or hj != hj: return True          # boy yoksa filtre atlanır
                    return abs(hi - hj) <= HEIGHT_MAX             # sert filtre: >8cm ele
                ai = age_arr[pos_i]; ci = ca_fill[pos_i]
                # ROL UYUMU: aday, HEDEFİN en iyi rolünde kaç uyum alıyor?
                #   "Alan Kaplayan OS, Mezzala'ya benzeyemez" — rol kimliği çok farklıysa
                #   gelecek-benzerliği anlamsız. Düşükse listede uyarı etiketiyle işaretlenir.
                _tgt_blk = ROL_BUCKET.get(rowid) or {}
                _tgt_rol = _tgt_blk.get('_en_iyi')
                def _rol_fit(j):
                    if not _tgt_rol: return None, None
                    blk = ROL_BUCKET.get(sim_rows[j]) or {}
                    return (blk.get(_tgt_rol) or {}).get('uyum'), blk.get('_en_iyi')

                # BENZER: rol-imza en yakın + aynı mevki + boy uyumlu (dca = seviye filtresi için)
                for j in order:
                    if j == pos_i or not np.isfinite(sc[j]): continue
                    if not same_mevki(j) or not height_ok(j): continue
                    sims.append({'id': sim_ids[j], 'sim': round(float(max(0, min(100, sc[j]))), 1),
                                 'dca': int(round(ca_rating[j] - ca_rating[pos_i]))})
                    if len(sims) >= TOPN: break

                # GELECEKTE BENZEYEBİLECEĞİ (yalnız wonderkid: yaş < WK_AGE)
                #   Ham (bugünkü) Rol-İmza profiline göre en yakın, aynı mevki + boy uyumlu,
                #   kendinden ileri (senden yüksek CA'lı) örnekler. Gerçekçi-tavan projeksiyonu YOK.
                if ai == ai and ai < WK_AGE:
                    ci = ca_rating[pos_i]
                    for j in order:
                        if j == pos_i or not np.isfinite(sc[j]): continue
                        if not same_mevki(j) or not height_ok(j): continue
                        if ca_rating[j] < ci: continue          # gelecekteki hali = kendinden ileri
                        if ca_rating[j] - ci > FUT_CA_MAX: continue   # absürt CA sıçraması olmasın
                        _ru, _rk = _rol_fit(j)
                        fut.append({'id': sim_ids[j], 'sim': round(float(max(0, min(100, sc[j]))), 1),
                                    'ru': _ru, 'rk': _rk})
                        if len(fut) >= 5: break

                # GENÇ YETENEKLER (yalnız olgun oyuncu: yaş >= EST_AGE) — tersine future
                #   Öne çıkan özellik profiline (Rol-İmza sc) benzeyen, gelişebilecek gençler.
                #   Pozisyon: ana mevki (best) aynı olmalı — farklı mevki oyuncusu önerilmez.
                prosp = []
                if ai == ai and ai >= EST_AGE:
                    for j in order:
                        if j == pos_i or not np.isfinite(sc[j]): continue
                        if not same_mevki(j) or not height_ok(j): continue
                        aj = age_arr[j]
                        if not (aj == aj and aj < WK_AGE): continue      # aday genç olmalı
                        if ca_rating[j] > ca_rating[pos_i]: continue     # henüz bu seviyeye ulaşmamış
                        if ca_rating[pos_i] - ca_rating[j] > FUT_CA_MAX: continue  # absürt fark olmasın
                        _ru, _rk = _rol_fit(j)
                        prosp.append({'id': sim_ids[j], 'sim': round(float(max(0, min(100, sc[j]))), 1),
                                      'ru': _ru, 'rk': _rk})
                        if len(prosp) >= 6: break

            # İSTATİSTİK BENZER (radar çıktısı) — aynı mevki, en yakın 12
            statsim = []
            if len(DS) > 1:
                mp = pos_sets[pos_i]
                ds = DS[pos_i].astype(float); ds[pos_i] = np.inf
                for j in np.argsort(ds):
                    if j == pos_i or not np.isfinite(ds[j]): continue
                    pj = pos_sets[j]
                    if not ((not mp) or (not pj) or (mp & pj)): continue
                    statsim.append(sim_ids[j])
                    if len(statsim) >= 12: break

            # LİG-İÇİ SIRA (radar metrikleri): "bu alanda ligde kaçıncı"
            Lp = r.get('Lig'); arrs = lg_arr.get(Lp, {}) if isinstance(Lp, str) else {}
            rankd = {}
            for spec in radar_specs:
                name, col = spec[0], spec[1]; inv = len(spec) > 2 and spec[2]
                v = rawd.get(name); arr = arrs.get(col)
                if v is None or arr is None or not len(arr): rankd[name] = None; continue
                rnk = int((arr < v).sum()) + 1 if inv else int((arr > v).sum()) + 1
                rankd[name] = [rnk, int(len(arr))]

            # eklenebilir metrik değerleri (oyuncunun tüm SL per-maç değerleri)
            xm = {}
            for c in xcat_cols:
                vv = pd.to_numeric(pd.Series([r.get(c)]), errors='coerce').iloc[0]
                if not pd.isna(vv): xm[c] = round(float(vv), 2)

            # ÖNE ÇIKAN ÖZELLİKLER (gösterim): pozisyon ort.'nın en çok ÜSTÜNDEKİ güçlü yanlar
            #   yalnız FM (1-20) özellikleri; rol-belirleyiciler öne alınır (imza)
            val_i = X[pos_i]
            fm_idx = [k for k in range(len(attr_lbls)) if not attr_lbls[k].startswith('FC:')]
            order_s = sorted(fm_idx,
                             key=lambda k: -((val_i[k] - mu[k]) * (1.4 if attr_lbls[k] in rolekeys else 1.0)))
            standout = [{'a': attr_lbls[k], 'v': int(round(float(val_i[k])))}
                        for k in order_s if val_i[k] > mu[k]][:6]

            players[eid] = {
                'id': eid, 'bucket': b,
                'name': gv(r, 'FM_Oyuncu', 'Oyuncu'),
                'alt': gv(r, 'Oyuncu'),
                'team': gv(r, 'Takım', 'FM_Kulüp', 'SL_Takım'),
                'league': gv(r, 'Lig', 'FM_Lig'),
                'age': gv(r, '_age'),
                'dob': gv(r, 'FM_DT'),
                'minutes': gv(r, 'SL_Dk'),
                'matches': gv(r, 'SL_Maç Sayısı'),
                'value': gv(r, 'FM_İstenen Bedel'),
                'value_eur': parse_money(gv(r, 'FM_İstenen Bedel')),
                'wage': gv(r, 'FM_Vergi Sonrası Maaş'),
                'wage_eur': parse_money(r.get('FM_Vergi Sonrası Maaş')),
                'contract': contract_parts(r.get('FM_Bitiş'))[0],
                'cyear': contract_parts(r.get('FM_Bitiş'))[1],
                'foot': foot_norm(r),
                'boy': gv(r, '_boy'),
                'pos': posmap[rowid][0],
                'best': posmap[rowid][1],
                'cpos': gv(r, 'FC_Club position'),
                'kit': gv(r, 'FC_Club kit number'),
                'overall': overall,
                'ca': ca_val,
                'pa': pa_val,
                'pct': pct_bucket,
                'standout': standout,
                'radar': rad,
                'radarL': radL,
                'rv': rawd,
                'rank': rankd,
                'xm': xm,
                'similar': sims,
                'statsim': statsim,
                'future': fut,
                'prosp': prosp,
                'prospects': prosp,
                'fit': fit,
                'ap': ap_list,
                'ROL': ROL_BUCKET.get(rowid),
                'bs': bs_for_row(rowid),
            }
            bucket_ids.append(eid)
        out_buckets[b] = {
            'metrics': [s[0] for s in RADAR[BASE[b]]],
            'inv': [s[0] for s in RADAR[BASE[b]] if len(s) > 2 and s[2]],
            'count': len(bucket_ids),
        }

        # --- FM'SİZ OYUNCULAR (SL+FC): görüntülenebilir giriş, FM benzerlik havuzu DIŞINDA ---
        # FM ratingi yok -> attribute/benzerlik hesaplanamaz; ama isim, takım, lig, pozisyon,
        # SL radar (gerçek per-90 çıktı) ve FC genel reyting ile kadroda/gözatmada görünürler.
        Dfm0 = D[~fm_ok]
        # bu kova için lig-içi radar sırası referansı (yukarıda hesaplanan lg_arr/ref kullanılır)
        for rowid, r in zip(Dfm0.index, [Dfm0.loc[i] for i in Dfm0.index]):
            eid = f"{rowid}_{b}"
            rad, rawd, radL = radar_for(rowid, r)
            fcov = pd.to_numeric(pd.Series([r.get('FC_Genel reyting')]), errors='coerce').iloc[0]
            overall = None if pd.isna(fcov) else int(round(float(fcov)))
            Lp = r.get('Lig'); arrs = lg_arr.get(Lp, {}) if isinstance(Lp, str) else {}
            rankd = {}
            for spec in radar_specs:
                name, col = spec[0], spec[1]; inv = len(spec) > 2 and spec[2]
                v = rawd.get(name); arr = arrs.get(col)
                if v is None or arr is None or not len(arr): rankd[name] = None; continue
                rankd[name] = [int((arr < v).sum()) + 1 if inv else int((arr > v).sum()) + 1, int(len(arr))]
            xm = {}
            for c in xcat_cols:
                vv = pd.to_numeric(pd.Series([r.get(c)]), errors='coerce').iloc[0]
                if not pd.isna(vv): xm[c] = round(float(vv), 2)
            players[eid] = {
                'id': eid, 'bucket': b,
                'name': gv(r, 'FM_Oyuncu', 'Oyuncu'),
                'alt': gv(r, 'Oyuncu'),
                'team': gv(r, 'Takım', 'FM_Kulüp', 'SL_Takım'),
                'league': gv(r, 'Lig', 'FM_Lig'),
                'age': gv(r, '_age'),
                'dob': gv(r, 'FM_DT'),
                'minutes': gv(r, 'SL_Dk'),
                'matches': gv(r, 'SL_Maç Sayısı'),
                'value': gv(r, 'FM_İstenen Bedel'),
                'value_eur': parse_money(gv(r, 'FM_İstenen Bedel')),
                'wage': gv(r, 'FM_Vergi Sonrası Maaş'),
                'wage_eur': parse_money(r.get('FM_Vergi Sonrası Maaş')),
                'contract': contract_parts(r.get('FM_Bitiş'))[0],
                'cyear': contract_parts(r.get('FM_Bitiş'))[1],
                'foot': foot_norm(r),
                'boy': gv(r, '_boy'),
                'pos': posmap[rowid][0],
                'best': posmap[rowid][1],
                'cpos': gv(r, 'FC_Club position'),
                'kit': gv(r, 'FC_Club kit number'),
                'overall': overall,
                'ca': overall,          # FM CA yok -> FC genel reyting başlık değeri (0-100)
                'pa': None,
                'pct': None,
                'nofm': True,           # arayüz: FM türevli alanlar (attribute/benzerlik) yok
                'standout': [],
                'radar': rad,
                'radarL': radL,
                'rv': rawd,
                'rank': rankd,
                'xm': xm,
                'similar': [],
                'statsim': [],
                'future': [],
                'prosp': [],
                'prospects': [],
                'fit': {},
                'ap': [],
                'ROL': ROL_BUCKET.get(rowid),
                'bs': bs_for_row(rowid),
            }
            bucket_ids.append(eid)
        out_buckets[b]['count'] = len(bucket_ids)

        # --- bellek boşaltma: bu kovanın girişlerini serileştir ---
        for pd_ in players.values():
            # takım reytingi için hafif kayıt (benzersiz oyuncu, en iyi kova)
            if pd_.get('team') and pd_.get('ca') is not None and not pd_.get('nofm', False):
                team_roster.append((pd_['team'], pd_.get('best') or pd_['bucket'],
                                    float(pd_['ca']), pd_['name']))
            elif pd_.get('team') and pd_.get('ca') is not None:
                team_roster.append((pd_['team'], pd_.get('best') or pd_['bucket'],
                                    float(pd_['ca']), pd_['name']))
            # lig kalite kademesi: yalnız gerçek FM CA'sı olan (nofm değil) oyuncular —
            # FC-only reyting takım reytingine de dahil edilmiyor, aynı tutarlılık burada da.
            if pd_.get('league') and pd_.get('ca') is not None and not pd_.get('nofm', False):
                league_roster.append((pd_['league'], pd_['name'], float(pd_['ca'])))
            player_chunks.append(json.dumps(pd_, ensure_ascii=False, default=clean, separators=(',', ':')))
        n_entries += len(players)
        players.clear()
        del X, SIMS, DS, MX, MXP, RV, RN, P
        import gc; gc.collect()
        print(f"  [{b}] tamam ({n_entries} kümülatif giriş)", flush=True)


    # ------------------------------------------------------------------
    # TAKIM REYTİNGİ: pozisyon-bazlı en iyi 11 (ağırlıklı) + kademeli yedek bonusu
    #   - Her takımda benzersiz oyuncular (aynı isim tek kez, en yüksek CA'lı kaydı)
    #   - Formasyon iskeleti: 1 GK, 4 DEF, 3 MID, 3 FWD (esnek eşleme)
    #   - En iyi 11'in AĞIRLIKLI ort. (yıldıza daha çok pay) = belkemiği
    #   - 12-20. oyuncular azalan ağırlıkla küçük derinlik bonusu
    #   - Sonuç 0-100 (oyuncu CA ile aynı ölçek)
    # ------------------------------------------------------------------
    from collections import defaultdict as _ddict
    POS_GROUP = {'GK': 'GK', 'CB': 'DEF', 'LB': 'DEF', 'RB': 'DEF',
                 'DM': 'MID', 'CM': 'MID', 'AM': 'MID',
                 'LW': 'FWD', 'RW': 'FWD', 'ST': 'FWD'}
    FORM_NEED = {'GK': 1, 'DEF': 4, 'MID': 3, 'FWD': 3}   # 11 iskelet
    team_best = _ddict(dict)   # team -> name -> (ca, group)
    team_gpos = _ddict(lambda: _ddict(list))  # team -> granular_poz -> [ca...] (kadro açığı için)
    for tm, best, ca, nm in team_roster:
        grp = POS_GROUP.get(best, 'MID')
        if nm not in team_best[tm] or ca > team_best[tm][nm][0]:
            team_best[tm][nm] = (ca, grp)
        team_gpos[tm][best].append(ca)

    # ------------------------------------------------------------------
    # LİG KALİTE KADEMESİ ("bu seviyedeki rakiplerin ortalaması"): ham
    # UEFA-tarzı katsayı sayısı YOK — ligler kendi aralarında (bu veri
    # setindeki) ortalama CA'ya göre 5 göreli dilime (yüzdelik 20/40/60/80
    # kesim) yerleştirilir. Küçük örneklemli ligler (<MIN_LEAGUE_N gerçek-
    # CA'lı benzersiz oyuncu) kademesiz bırakılır — yanıltıcı olmasın diye.
    # ------------------------------------------------------------------
    MIN_LEAGUE_N = 15
    league_best = _ddict(dict)   # league -> name -> ca (en yüksek, çoklu-kova tekilleştirme)
    for L, nm, ca in league_roster:
        if nm not in league_best[L] or ca > league_best[L][nm]:
            league_best[L][nm] = ca
    league_avg_ca = {L: sum(d.values()) / len(d) for L, d in league_best.items() if len(d) >= MIN_LEAGUE_N}
    LEAGUE_TIER_LABELS = ['Gelişmekte Olan Lig', 'Orta Seviye Lig', 'Orta-Üst Seviye Lig',
                          'Üst Seviye Lig', 'Elit Lig']
    league_tier = {}
    if league_avg_ca:
        vals = np.array(sorted(league_avg_ca.values()))
        q20, q40, q60, q80 = np.percentile(vals, [20, 40, 60, 80])
        def _league_tier_for(v):
            if v < q20: return LEAGUE_TIER_LABELS[0]
            if v < q40: return LEAGUE_TIER_LABELS[1]
            if v < q60: return LEAGUE_TIER_LABELS[2]
            if v < q80: return LEAGUE_TIER_LABELS[3]
            return LEAGUE_TIER_LABELS[4]
        league_tier = {L: _league_tier_for(v) for L, v in league_avg_ca.items()}
    for _entry in league_list:
        _t = league_tier.get(_entry['name'])
        if _t: _entry['tier'] = _t
    print(f"LİG KADEME: {len(league_tier)}/{len(league_list)} lig kademelendirildi "
          f"(eşik: {MIN_LEAGUE_N}+ CA'lı benzersiz oyuncu)")

    def _team_rating(roster):
        # roster: list of (ca, group)
        by_grp = _ddict(list)
        for ca, g in roster:
            by_grp[g].append(ca)
        for g in by_grp: by_grp[g].sort(reverse=True)
        # 1) formasyon iskeletini doldur (pozisyon-bazlı en iyi)
        xi = []
        leftover = []
        for g, need in FORM_NEED.items():
            pool = by_grp.get(g, [])
            xi += pool[:need]
            leftover += pool[need:]
        # iskelet eksikse (ör. kanat yok) en iyi kalanlarla tamamla
        leftover.sort(reverse=True)
        while len(xi) < 11 and leftover:
            xi.append(leftover.pop(0))
        if not xi: return None, 0
        xi.sort(reverse=True)
        # 2) en iyi 11 ağırlıklı ort. (lineer azalan pay: en iyi 11x, 11.'ye 1x)
        n = len(xi)
        w = np.arange(n, 0, -1, dtype=float)     # 11,10,...,1
        core = float(np.dot(xi, w) / w.sum())
        # 3) yedek derinlik bonusu (12-20. oyuncu, hızla azalan)
        depth = leftover[:9]
        bonus = 0.0
        if depth:
            dw = 0.5 ** np.arange(1, len(depth) + 1)          # 0.5,0.25,...
            # yedeğin core'a katkısı: yedek ne kadar core'a yakınsa o kadar bonus
            dcontrib = np.clip(np.array(depth) - (core - 12), 0, None) * dw
            bonus = float(dcontrib.sum() / max(w.sum(), 1)) * 1.5
            bonus = min(bonus, 3.0)                            # tavan +3
        return round(min(core + bonus, 100.0), 1), n

    team_ratings = {}
    for tm, players_d in team_best.items():
        roster = list(players_d.values())
        if len(roster) < 5: continue        # 5'ten az -> en iyi 11 anlamsız
        rt, nx = _team_rating(roster)
        if rt is not None:
            entry = {'rating': rt, 'squad': len(roster)}
            if len(roster) < 11: entry['partial'] = True   # eksik kadro: reyting temkinli
            # KADRO AÇIĞI: 10 granular pozisyonun en iyi oyuncusu; takım ort.'nın çok altındakiler açık
            best_by_pos = {}
            for gp, cas in team_gpos[tm].items():
                if gp in POS10: best_by_pos[gp] = max(cas)
            if best_by_pos:
                team_avg = sum(best_by_pos.values()) / len(best_by_pos)
                # eksik pozisyonlar (hiç oyuncu yok) + zayıf pozisyonlar (ort'un 8+ altında)
                gaps = []
                for pos in POS10:
                    if pos not in best_by_pos:
                        gaps.append({'pos': pos, 'ca': None, 'sev': 'eksik'})
                    elif best_by_pos[pos] < team_avg - 8:
                        gaps.append({'pos': pos, 'ca': round(best_by_pos[pos]), 'sev': 'zayıf'})
                if gaps:
                    # en kritik önce: eksik > en düşük CA
                    gaps.sort(key=lambda g: (g['ca'] is not None, g['ca'] if g['ca'] else 0))
                    entry['gaps'] = gaps[:3]
                    entry['pos_ca'] = {p: round(c) for p, c in best_by_pos.items()}
            team_ratings[tm] = entry
    n_partial = sum(1 for v in team_ratings.values() if v.get('partial'))
    n_gaps = sum(1 for v in team_ratings.values() if v.get('gaps'))
    print(f"TAKIM REYTİNGİ: {len(team_ratings)} takım ({n_partial} kısmi kadro; {n_gaps} takımda kadro açığı tespit edildi)")

    meta = {'min_dk': MIN_DK, 'topn': TOPN,
            'buckets': out_buckets,
            'avg': bucket_avg,
            'xcat': xcat,
            'xscale': bucket_xscale,
            'leagues': league_list,
            'team_ratings': team_ratings,
            'rol_istatistik': ROL_STATS,
            'rol_sabitler': ROL_SAB,
            'rol_registry': ROL_REGISTRY,
            'bs_axes': bs_axes,
            'bs_axes_gk': bs_axes_gk,
            'bs_axes_field': bs_axes_field,
            'bs_tiers': bs_tiers,
            'pa_tiers': pa_tiers,
            # attrs anahtarları NAME_FIX'lenir — frontend'e eski/ham isim (ör. 'Takım Oyunu')
            # değil, kanonik BS-ekseni ismi (İşbirliği) sızsın; MODEL_ATTRS/attr_pct zaten
            # aynı kanonik isimle anahtarlı (bkz. yukarısı).
            'models': {k: {'name': v[0], 'attrs': {NAME_FIX.get(a, a): w for a, w in v[1].items()}}
                       for k, v in MODELS.items()},
            'attr_order': MODEL_ATTRS,
            'total_entries': n_entries}
    with open('paralaks_data.json', 'w', encoding='utf-8') as f:
        f.write('{"meta":')
        f.write(json.dumps(meta, ensure_ascii=False, default=clean, separators=(',', ':')))
        f.write(',"players":[')
        f.write(','.join(player_chunks))
        f.write(']}')
    print('OK ->', n_entries, 'giriş yazıldı')
    for b in POS10:
        print(f"  {b}: {out_buckets[b]['count']:5d} giriş | {len(out_buckets[b]['metrics'])} radar metriği")
    return n_entries

if __name__ == '__main__':
    players = main()
