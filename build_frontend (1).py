# -*- coding: utf-8 -*-
"""PARALAKS frontend builder: gömülü demo verisiyle tek dosya HTML üretir.
Tam veriyi (paralaks_data.json) aynı klasörde sunucuyla açarsan otomatik onu kullanır."""
import json, datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUT_PATH = BASE_DIR / "paralaks.html"

DATA = open(BASE_DIR / 'paralaks_demo.json', encoding='utf-8').read()
BUILD = datetime.date.today().isoformat()

TPL = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"/>
<title>BigStatX — Scouting</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%230D0E10'/%3E%3Cpolygon points='16,6 25,12 22,24 10,24 7,12' fill='none' stroke='%237C93B8' stroke-width='2'/%3E%3Cpolygon points='16,11 20,14 18,21 14,21 12,14' fill='%237C93B8' fill-opacity='.55'/%3E%3C/svg%3E"/>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700;800&family=Spline+Sans+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  /* zemin: grafit tabanlı iki koyu ton — bölümler arası "nefes" için hafif değişir (bkz. .section:nth-of-type) */
  --bg:#0D0E10; --bg-alt:#101216; --surface:#15181D; --elev:#191D23; --hover:#1F242B;
  --chalk:rgba(231,233,236,.06); --chalk2:rgba(231,233,236,.13);
  --tx:#E7E9EC; --mut:#8B9096; --faint:#5C636B;
  /* veri-terminali renk dili: mat gök mavisi seçim/etkileşim vurgusu, mat pirinç öne çıkan
     sayı vurgusu — ESKİ isimler (--live/--focus/--pos/--neu) korunuyor ki yüzlerce çağrı
     noktası tek tek değişmesin; yalnız DEĞERLERİ yeniden atanıyor. */
  --pitch:#7C93B8; --gold:#D9A441;
  --live:var(--pitch); --focus:var(--pitch); --pos:var(--pitch); --neu:var(--gold); --neg:#C4776A;
  --rad-p:var(--pitch); --rad-a:var(--gold);
  /* pozisyon-grubu renk kodu (GK/DEF/MID/FWD) — bkz. POS_GROUP_COLOR */
  --pg-gk:#D9A441; --pg-def:#5B8AA6; --pg-mid:#7C93B8; --pg-fwd:#C4776A;
  /* tipografi: tek disiplinli aile — Instrument Sans başlık/gövde/rakam (CA/skor dahil),
     Spline Sans Mono veri/etiket */
  --disp:"Instrument Sans","Inter",system-ui,sans-serif; --kit:"Instrument Sans","Inter",system-ui,sans-serif;
  --ui:"Instrument Sans","Inter",system-ui,sans-serif; --mono:"Spline Sans Mono",ui-monospace,monospace;
  /* köşe ölçeği — terminal hissi için sıfıra yakın: dış panel/tablo/dropdown = 0,
     küçük kontrol (buton/input) = 2px, rozet/pill/tag (üst sınır) = 4px.
     Dairesel göstergeler (nokta, disk, avatar: border-radius:50%) bu ölçeğin dışında. */
  --r0:0px; --r1:2px; --r2:4px;
  --shadow-tint:rgba(124,147,184,.16);
}
*{box-sizing:border-box} html,body{margin:0}
@media (prefers-reduced-motion:no-preference){
  body{
    /* çok ince nokta ızgara — dekoratif değil, ambiyans; göz ile zor seçilecek kadar düşük
       opaklıkta, veri-yoğun alanlarda zaten opak yüzeylerin altında kalır */
    background:radial-gradient(rgba(255,255,255,.028) 1px,transparent 1px) 0 0/24px 24px,var(--bg);
  }
}
body{background-color:var(--bg);color:var(--tx);font-family:var(--ui);font-size:15px;line-height:1.5;-webkit-font-smoothing:antialiased}
select{background:var(--elev);color:var(--tx)} select option{background:var(--elev);color:var(--tx)}
.mono{font-family:var(--mono);font-feature-settings:"tnum"} .num{font-feature-settings:"tnum"}
a{color:inherit;text-decoration:none}
button{font-family:inherit;color:inherit;cursor:pointer;border:none;background:none}
/* genel tıklanabilir durum sözleşmesi: her buton + tabindex taşıyan her eleman için
   görünür klavye-focus halkası ve basma geri bildirimi (özellikle .ckbtn/.tabbtn/.fltpill/
   .lcard/.fcard için — bkz. ilgili bloklar) */
button:focus-visible,[tabindex]:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
button:active{transform:translateY(1px)}

/* top bar */
header{position:sticky;top:0;z-index:30;background:rgba(13,14,16,.86);backdrop-filter:blur(12px);border-bottom:1px solid var(--chalk)}
.bar{position:relative;z-index:1;max-width:1600px;margin:0 auto;padding:14px 32px;display:flex;align-items:center;gap:18px}
.brand{font-family:var(--mono);font-weight:500;letter-spacing:.28em;font-size:14px;color:var(--tx);cursor:pointer;white-space:nowrap}
.brand b{color:var(--live);font-weight:500}
.searchwrap{position:relative;flex:1;max-width:480px;margin-left:auto}
.searchicon{position:absolute;left:13px;top:50%;transform:translateY(-50%);width:15px;height:15px;color:var(--faint);pointer-events:none}
.search{width:100%;background:var(--surface);border:1px solid var(--chalk);border-radius:var(--r1);padding:10px 34px 10px 36px;color:var(--tx);font-size:14px;outline:none;transition:border-color .18s,background-color .18s}
.search:focus{border-color:var(--focus);background:var(--elev)}
.search::placeholder{color:var(--faint)}
.searchclear{position:absolute;right:7px;top:50%;transform:translateY(-50%);width:22px;height:22px;border-radius:var(--r2);display:none;align-items:center;justify-content:center;color:var(--faint);font-size:16px;line-height:1;transition:color .15s,background-color .15s}
.searchclear:hover{color:var(--tx);background:var(--hover)}
.results{position:absolute;top:46px;left:0;right:0;background:var(--elev);border:1px solid var(--chalk2);border-radius:var(--r0);overflow:hidden;max-height:64vh;overflow-y:auto;box-shadow:0 14px 34px -12px rgba(6,9,16,.55);animation:resIn .15s cubic-bezier(.16,1,.3,1)}
@keyframes resIn{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:none}}
@media(prefers-reduced-motion:reduce){.results{animation:none}}
.ressec{font-family:var(--mono);font-size:10px;letter-spacing:.14em;color:var(--faint);text-transform:uppercase;padding:9px 14px 5px}
.res{display:flex;align-items:center;gap:10px;padding:9px 14px;border-bottom:1px solid var(--chalk);cursor:pointer}
.res:last-child{border-bottom:none} .res:hover,.res.active{background:var(--hover)}
.pgdot{width:7px;height:7px;border-radius:50%;flex:none}
.res .nm{font-weight:500} .res .nm mark,.cmpresit .nm mark{background:none;color:var(--live);font-weight:600}
.res .sub{color:var(--mut);font-size:12.5px;margin-top:1px}
.resca{font-family:var(--mono);font-size:13px;font-weight:600;font-variant-numeric:tabular-nums;flex:none;width:28px;text-align:right}
.resempty{padding:16px 14px;color:var(--faint);font-size:13px;text-align:center}
.tag{font-family:var(--mono);font-size:10.5px;letter-spacing:.06em;padding:2px 7px;border-radius:var(--r2);background:var(--surface);border:1px solid var(--chalk2);color:var(--mut)}

main{max-width:1600px;margin:0 auto;padding:28px 32px 80px}
@media(max-width:720px){.bar{padding:14px 16px}main{padding:20px 16px 60px}}

/* ---- terminal hero: veri panosu kapağı, imza radar motifini büyütülmüş halde önizler ---- */
/* tam-genişlik (full-bleed): main'in max-width kısıtından viewport genişliğine taşar —
   negatif margin tekniği, main'in kendi kutusunu bozmadan. */
.dashhero{position:relative;overflow:hidden;background:var(--bg);border-bottom:1px solid var(--chalk);
  width:100vw;margin-left:calc(50% - 50vw);margin-right:calc(50% - 50vw);margin-top:0;margin-bottom:40px;
  min-height:74vh;min-height:74dvh;display:flex;flex-direction:column;justify-content:center}
@media(max-width:720px){.dashhero{min-height:auto;padding-top:26px}}
.dhrow{position:relative;z-index:5;max-width:1600px;width:100%;margin:0 auto;box-sizing:border-box;
  padding:clamp(26px,5vw,58px);display:flex;align-items:center;justify-content:space-between;gap:clamp(20px,5vw,60px);flex-wrap:wrap}
.dhcontent{position:relative;flex:1 1 460px;min-width:280px;opacity:0;transform:translateY(14px);animation:dhrise .8s .1s ease forwards}
@keyframes dhrise{to{opacity:1;transform:none}}
.dheye{font-family:var(--mono);font-size:11.5px;letter-spacing:.32em;color:var(--live);text-transform:uppercase;margin-bottom:20px}
.dhh1{font-family:var(--disp);font-weight:800;font-size:clamp(40px,7vw,80px);line-height:.98;letter-spacing:-.03em;color:var(--tx);text-wrap:balance}
.dhh1 .x{position:relative;color:var(--live)}
.dhh1 .x::after{content:"";position:absolute;left:0;right:0;bottom:6px;height:3px;background:var(--live);opacity:.4}
.dhsub{margin-top:20px;max-width:460px;font-size:clamp(15px,2vw,17px);line-height:1.55;color:var(--mut);text-wrap:pretty}
.dhcta{margin-top:28px;display:flex;gap:12px;flex-wrap:wrap}
.dhbtn{font-family:var(--mono);font-size:13px;letter-spacing:.03em;padding:12px 20px;border-radius:var(--r1);cursor:pointer;border:1px solid var(--chalk2);background:rgba(255,255,255,.03);color:var(--tx);transition:.18s;display:inline-flex;align-items:center;gap:8px}
.dhbtn:hover{transform:translateY(-2px);border-color:var(--tx)}
.dhbtn:focus-visible{outline:2px solid var(--live);outline-offset:2px}
.dhbtn:active{transform:translateY(0px) scale(.98)}
.dhbtn.pri{background:var(--live);color:#0C0F14;border-color:var(--live);font-weight:500}
.dhbtn.pri:hover{box-shadow:0 6px 18px -8px var(--shadow-tint)}
.dhradar{position:relative;flex:0 0 auto;width:clamp(240px,30vw,400px);opacity:0;animation:dhrise .8s .25s ease forwards}
.dhradar svg{width:100%;height:auto;display:block}
@media(max-width:900px){.dhradar{display:none}}
.dhstats{position:relative;z-index:5;max-width:1600px;margin:0 auto;width:100%;box-sizing:border-box;
  display:flex;gap:clamp(20px,5vw,52px);flex-wrap:wrap;padding:0 clamp(26px,5vw,58px) clamp(24px,4vw,40px);opacity:0;animation:dhrise .8s .4s ease forwards}
.dhst .n{font-family:var(--kit);font-weight:700;font-size:clamp(22px,3.2vw,32px);letter-spacing:-.01em;color:var(--tx);font-variant-numeric:tabular-nums}
.dhst .l{font-family:var(--mono);font-size:10.5px;letter-spacing:.16em;color:var(--faint);text-transform:uppercase;margin-top:3px}
@media (prefers-reduced-motion:reduce){.dhcontent,.dhradar,.dhstats{opacity:1!important;transform:none!important;animation:none!important}}

/* ---- imza animasyon 1/3: radar veri poligonu sıfırdan çizilir (hero'daki ckln/ckrt ile
   aynı teknik — pathLength=1 + stroke-dashoffset), dolgu çizgiyi takiben belirir ---- */
.radardraw{stroke-dasharray:1;stroke-dashoffset:1;fill-opacity:0;animation:raddraw 1s cubic-bezier(.16,1,.3,1) forwards}
@keyframes raddraw{0%{stroke-dashoffset:1;fill-opacity:0}55%{fill-opacity:0}100%{stroke-dashoffset:0;fill-opacity:1}}
@media (prefers-reduced-motion:reduce){.radardraw{stroke-dashoffset:0!important;fill-opacity:1!important;animation:none!important}}
/* ---- imza animasyon 2/3: uyum/benzerlik bar'ları sıfırdan hedef genişliğe dolar —
   JS zaten inline style="width:X%" yazıyor, animasyon bunu "to" hedefi kabul eder ---- */
@keyframes barfill{from{width:0}}
.rolbar i,.mbar i,.sbar i{animation:barfill .9s cubic-bezier(.16,1,.3,1) both}
@media (prefers-reduced-motion:reduce){.rolbar i,.mbar i,.sbar i{animation:none!important}}

/* landing */
.feat-h{font-family:var(--mono);font-size:11px;letter-spacing:.18em;color:var(--faint);text-transform:uppercase;margin:6px 0 14px}
.fgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px}
.lgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:10px}
/* .lcard = lig gözatma (navigasyonel liste girişi) — düz yüzey + sol kenar çizgisi,
   hover'da vurgu rengine döner: "bu bir kapı, bir veri kartı değil" hissi */
.lcard{background:var(--surface);border:1px solid var(--chalk);border-left:2px solid var(--chalk2);border-radius:var(--r0);padding:12px 15px;cursor:pointer;transition:border-color .15s}
.lcard:hover,.lcard:focus-visible{border-left-color:var(--focus)}
.lcard:active{background:var(--hover)}
.lcard .ln2{font-weight:500;font-size:14px;color:var(--tx)}
.lcard .ls{color:var(--mut);font-size:12px;margin-top:3px}
/* .fcard = öne çıkan oyuncu (skor öne çıkan bir istatistik karosu) — kenarlık yok,
   üstte tek renkli şerit + hover'da yüzey aydınlanır; .lcard'dan kasıtlı olarak farklı */
.fcard{background:var(--surface);border-top:2px solid var(--live);border-radius:var(--r0);padding:14px;cursor:pointer;transition:background-color .15s,transform .15s}
.fcard:hover{background:var(--hover);transform:translateY(-2px)}
.fcard:active{transform:translateY(0)}
.fcard .nm{font-weight:600} .fcard .sub{color:var(--mut);font-size:12.5px;margin-top:2px}
.fcard .ov{float:right;font-family:var(--kit);font-size:20px}

/* profile */
.phead{display:flex;flex-wrap:wrap;gap:22px;align-items:flex-start;border-bottom:1px solid var(--chalk);padding-bottom:22px;margin-bottom:24px}
.pid{flex:1;min-width:240px}
.pid h2{font-family:var(--disp);font-weight:700;font-size:clamp(24px,4.5vw,38px);margin:0;letter-spacing:-.01em;line-height:1.08}
.pmeta{color:var(--mut);margin-top:8px;font-size:14px}
.ligtier{display:inline-block;font-family:var(--mono);font-size:9.5px;letter-spacing:.04em;padding:2px 7px;margin-left:3px;border-radius:var(--r2);background:rgba(124,147,184,.10);border:1px solid rgba(124,147,184,.30);color:var(--live);vertical-align:middle;cursor:default}
.pmeta b{color:var(--tx);font-weight:500}
.chips{display:flex;gap:20px 28px;flex-wrap:wrap;margin-top:18px}
.chip{display:flex;flex-direction:column;gap:3px}
.chip .k{font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--faint)}
.chip .v{font-size:13.5px;color:var(--tx);font-weight:500;font-variant-numeric:tabular-nums}
.chip.vchip{flex-direction:row;align-items:center;gap:7px;padding:5px 11px;background:rgba(124,147,184,.08);border:1px solid rgba(124,147,184,.28);border-radius:var(--r2);align-self:flex-start}
.chip.vchip .k{color:var(--live)}
.score{text-align:center;background:var(--surface);border:1px solid var(--chalk);border-top:2px solid var(--live);border-radius:var(--r0);padding:16px 22px;min-width:120px}
.score .n{font-family:var(--kit);font-weight:700;font-size:48px;line-height:1;font-variant-numeric:tabular-nums}
.score .n .toPA{font-size:26px;opacity:.85;font-weight:600}
.vchip .v{color:var(--live)!important;font-weight:600}
.rolrow{display:grid;grid-template-columns:1fr 180px 52px 52px 52px;gap:10px;align-items:center;padding:7px 0;border-bottom:1px solid rgba(255,255,255,.04)}
.rolhead{display:grid;grid-template-columns:1fr 180px 52px 52px 52px;gap:10px;font-size:10.5px;color:var(--faint);text-transform:uppercase;letter-spacing:.05em}
.rolnm{font-size:13.5px}
.rolbar{height:7px;background:rgba(255,255,255,.06);border-radius:var(--r1);overflow:hidden}
.rolbar i{display:block;height:100%;background:var(--live);border-radius:var(--r1)}
.rolbar.par{height:auto;background:none;font-size:10.5px;color:var(--neu)}
.rolv{font-family:var(--mono);font-size:12.5px;text-align:right}
.rolbest{font-size:9.5px;background:var(--live);color:#0C0F14;padding:1px 6px;border-radius:var(--r2);font-weight:700;margin-left:6px}
.roltend{font-size:10.5px;color:var(--neu);margin-left:6px}

.gapgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}
/* .gapcard = kadro açığı — zaten bir "sev" (eksik/zayıf) taşıdığı için o durumu sol
   kenar şeridiyle kodluyoruz; kutu-içinde-kutu değil, bir durum paneli */
.gapcard{background:var(--surface);border-radius:var(--r0);padding:14px;border-left:3px solid var(--chalk2)}
.gapcard[data-sev="eksik"]{border-left-color:var(--neg)}
.gapcard[data-sev="zayıf"]{border-left-color:var(--neu)}
.gaphd{font-size:13px;margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid var(--chalk)}
.gapc{display:flex;justify-content:space-between;align-items:center;padding:7px 0;cursor:pointer;border-bottom:1px solid rgba(255,255,255,.03)}
.gapc:hover .gnm{color:var(--live)}
.gnm{font-size:13.5px;font-weight:500}.gsub{font-size:11px;color:var(--mut)}
.gveff{font-size:10.5px;color:var(--live);font-family:var(--mono)}
.score .lab{font-family:var(--mono);font-size:10px;letter-spacing:.14em;color:var(--mut);text-transform:uppercase;margin-top:6px}
.score .lab2{font-family:var(--ui);font-size:11px;color:var(--faint);margin-top:5px}
.score .lab2 b{color:var(--mut)}

/* position tabs */
.ptabs{display:flex;gap:6px;margin-bottom:20px;flex-wrap:wrap}
.ptab{font-family:var(--mono);font-size:12px;letter-spacing:.08em;padding:7px 13px;border-radius:var(--r1);background:var(--surface);border:1px solid var(--chalk);border-left:3px solid var(--pgc,var(--chalk));color:var(--mut)}
.ptab.on{border-color:var(--focus);border-left-color:var(--pgc,var(--focus));color:var(--tx);background:rgba(124,147,184,.12)}
.ptab.allpos{margin-left:auto;border-style:dashed;color:var(--live)}
.allpostbl{width:100%;border-collapse:collapse;font-size:13.5px;margin-bottom:8px}
.allpostbl th{text-align:left;color:var(--faint);font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;font-family:var(--mono);padding:7px 10px;border-bottom:1px solid var(--chalk2)}
.allpostbl th.num,.allpostbl td.num{text-align:right}
.allpostbl td{padding:9px 10px;border-bottom:1px solid var(--chalk)}
.allpostbl tr.cur{background:rgba(124,147,184,.06)}
.posdot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:7px;vertical-align:middle}
.possec{color:var(--faint);font-size:11px;font-family:var(--mono)}

.cols{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:26px}
@media(max-width:820px){.cols{grid-template-columns:1fr}}
/* profil sayfasının ana bilgi katmanı: Radar / Benzer Oyuncular / Rol Uyumu artık gerçekten
   yan yana — ayrı tam-genişlik section'lar değil, editoryal 3-panelli bir grid */
.cols3{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr) minmax(0,1fr);gap:30px}
@media(max-width:1280px){.cols3{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}}
@media(max-width:820px){.cols3{grid-template-columns:1fr}}
.scrollpanel{max-height:640px;overflow-y:auto;padding-right:6px}
.panel-h{font-family:var(--mono);font-size:11px;letter-spacing:.16em;color:var(--faint);text-transform:uppercase;margin:0 0 16px;display:flex;align-items:center;gap:9px}
.panel-h::before{content:"";width:5px;height:5px;border-radius:50%;background:var(--gold);flex:none}

/* radar */
.radar-wrap{display:flex;justify-content:center}
svg.radar{width:100%;max-width:380px;height:auto}
.rnote{color:var(--faint);font-size:11.5px;text-align:center;margin-top:8px;line-height:1.5}
.axisval{display:grid;grid-template-columns:1fr auto;gap:2px 12px;margin-top:14px;font-size:13px}
.axisval .k{color:var(--mut)} .axisval .v{font-family:var(--mono);text-align:right}
.axisval.avg3{grid-template-columns:1fr auto auto;gap:2px 14px}
.axisval.avg4{grid-template-columns:1fr auto auto auto;gap:2px 14px}
.axisval .vp{color:var(--faint);font-size:11px}
.radhead{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.radttl{font-size:12px;color:var(--mut)}
.radtog{font-family:var(--mono);font-size:12px;border:1px solid var(--chalk2);border-radius:var(--r1);padding:4px 11px;color:var(--mut);min-width:40px;cursor:pointer;background:none}
.radtog.on{border-color:var(--rad-p);color:var(--rad-p)}
.radleg{display:flex;gap:20px;justify-content:center;font-size:12px;color:var(--mut);margin-top:6px}
.radleg .d{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px;vertical-align:middle}
.radleg .dp{background:var(--rad-p)} .radleg .da{background:var(--rad-a)}
.radarval{text-align:center;font-family:var(--mono);font-size:12.5px;color:var(--mut);background:rgba(255,255,255,.03);border:1px solid var(--chalk);border-radius:var(--r0);padding:9px 12px;margin-top:10px}
.radadd{display:flex;gap:8px;margin-top:10px}
.radadd select{flex:1;background:var(--elev);border:1px solid var(--chalk2);border-radius:var(--r1);padding:8px 10px;color:var(--tx);font-size:13px}
.radadd select option{background:var(--elev);color:var(--tx)}
.radadd select:focus{outline:none;border-color:var(--focus)}
.radadd button{background:rgba(124,147,184,.14);border:1px solid var(--focus);color:var(--focus);border-radius:var(--r1);padding:8px 14px;cursor:pointer;font-size:13px}
.rmchips{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.rmchip{background:rgba(124,147,184,.10);border:1px solid rgba(124,147,184,.3);border-radius:var(--r2);padding:3px 9px;font-size:12px;color:#C9D3E3;font-family:var(--mono)}
.rmchip b{cursor:pointer;color:#D99C90;margin-left:3px}

/* similar */
.sim{display:flex;align-items:center;gap:12px;padding:11px 0;border-bottom:1px solid var(--chalk);cursor:pointer}
.sim:hover .snm{color:var(--focus)}
.srank{font-family:var(--mono);color:var(--faint);font-size:12px;width:18px}
.sinfo{flex:1;min-width:0}
.snm{font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;transition:color .15s}
.ssub{color:var(--mut);font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sbarwrap{width:96px;flex-shrink:0}
.sbar{height:5px;background:var(--surface);border-radius:var(--r1);overflow:hidden}
.sbar i{display:block;height:100%;background:var(--focus);border-radius:var(--r1)}
.spct{font-family:var(--mono);font-size:12px;color:var(--mut);text-align:right;margin-top:3px}
.sov{font-family:var(--kit);font-size:17px;width:34px;text-align:right;position:relative}
.sov .dca{display:block;font-family:var(--ui);font-size:9px;color:var(--faint);font-weight:400}
.simlvl{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--mut);margin-bottom:10px;flex-wrap:wrap}
.lvlb{font-family:var(--ui);font-size:11px;padding:3px 10px;border-radius:var(--r1);border:1px solid var(--chalk);background:var(--surface);color:var(--mut);cursor:pointer}
.lvlb.on{background:var(--live);color:#0C0F14;border-color:var(--live);font-weight:600}
.morebtn{margin-top:14px;width:100%;padding:10px;border:1px solid var(--chalk);border-radius:var(--r1);color:var(--mut);font-size:13px;transition:border-color .15s,color .15s}
.morebtn:hover{border-color:var(--focus);color:var(--tx)}
.back{font-size:13px;color:var(--mut);margin-bottom:18px;display:inline-block}
.back:hover{color:var(--tx)}
/* .backrow/.backbtn = Karşılaştırma sayfasının "← geri" ve "↺ farklı oyuncuyla başla"
   düğmeleri — .back ile aynı görünüm ama <a> değil <button> olduğu için ayrı kural */
.backrow{margin-bottom:18px}
.backbtn{font-size:13px;color:var(--mut);transition:color .15s}
.backbtn:hover{color:var(--tx)}
.empty{color:var(--faint);text-align:center;padding:30px;font-size:13px}
/* "nefes alan yoğunluk": her bölüm arasında ince bir ayraç + hafif ton değişimi (sec-a/sec-b
   sırayla) — kullanıcı yeni bir bilgi katmanına girdiğini hissetsin, kesintisiz akış değil.
   main'in yatay padding'ini negatif margin ile telafi ederek ton, konteynerin tam genişliğine
   yayılıyor (tam ekran taşması değil — düşük risk, main'in kendi kutusunda kalıyor). */
.section{position:relative;margin-top:56px;padding:30px 20px;margin-left:-20px;margin-right:-20px}
.section::before{content:"";position:absolute;top:0;left:20px;right:20px;height:1px;background:linear-gradient(90deg,transparent,var(--chalk2) 15%,var(--chalk2) 85%,transparent)}
.section.sec-b{background:var(--bg-alt)}
.section .panel-h{padding-top:2px}
.frow{display:flex;gap:12px;overflow-x:auto;padding-bottom:8px}
/* .fcard2 = benzer/gelecek-yetenek karuseli — kenarlık VARSAYILAN olarak yok, yalnız
   etkileşimde belirir ("bilet kökü" hissi); .lcard (hep sınırlı) ve .fcard (üst şerit)'ten
   kasıtlı olarak ayrışıyor */
.fcard2{min-width:188px;max-width:188px;background:var(--surface);border:1px solid transparent;border-radius:var(--r0);padding:13px;cursor:pointer;transition:border-color .15s,transform .15s}
.fcard2:hover,.fcard2:focus-visible{border-color:var(--focus);transform:translateY(-2px)}
.fcard2:active{transform:translateY(0)}
.fcard2 .top{display:flex;justify-content:space-between;align-items:center}
.fcard2 .nm{font-weight:600;font-size:14px;margin-top:9px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.fcard2 .sub{color:var(--mut);font-size:12px;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.fcard2 .mini{font-family:var(--mono);font-size:11px;color:var(--mut);margin-top:8px}
.devbadge{font-family:var(--mono);font-size:9px;letter-spacing:.05em;color:var(--live);border:1px solid rgba(124,147,184,.3);border-radius:var(--r2);padding:2px 6px}
.rfit{font-size:10.5px;margin-top:6px;padding:3px 6px;border-radius:var(--r2);line-height:1.35}
.rfit.ok{color:var(--live);background:rgba(124,147,184,.10)}
.rfit.mid{color:var(--neu);background:rgba(255,207,61,.10)}
.rfit.bad{color:var(--neg);background:rgba(196,119,106,.12)}
.rfit .ro{opacity:.75}
.futnote{font-size:12px;color:var(--mut);margin-bottom:12px;line-height:1.5}
.futnote b{color:var(--live)}
.filters{display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end;margin-bottom:14px}
.fld{display:flex;flex-direction:column;gap:5px}
.fld label{font-size:10px;color:var(--faint);font-family:var(--mono);letter-spacing:.1em;text-transform:uppercase}
.filters select,.filters input{background:var(--surface);border:1px solid var(--chalk);border-radius:var(--r1);color:var(--tx);padding:7px 10px;font-family:var(--ui);font-size:13px;outline:none}
.filters select:focus,.filters input:focus{border-color:var(--focus)}
.filters input[type=number]{width:84px}
.rst{color:var(--mut);font-size:12px;padding:8px 10px;border:1px solid var(--chalk);border-radius:var(--r1)}
.rst:hover{color:var(--tx);border-color:var(--focus)}
.exrow{display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--chalk);cursor:pointer}
.exrow:hover .snm{color:var(--focus)}
.exinfo{flex:1;min-width:0}
.exage,.exval{width:52px;text-align:right;font-family:var(--mono);font-size:12.5px;color:var(--mut)}
.exsim{width:92px;flex-shrink:0}
.exov{width:32px;text-align:right;font-family:var(--kit);font-size:16px}
.excount{color:var(--faint);font-size:12px;margin-bottom:10px}
@media(max-width:600px){.exage,.exval{display:none}}
/* squad — .tcard = takım listesi girişi, sıralı bir tabloya ait: kutu değil, satır.
   .lcard/.fcard/.fcard2/.gapcard'ın hiçbirinin formülünü paylaşmıyor kasıtlı olarak */
.tcard{background:transparent;border:none;border-bottom:1px solid var(--chalk);border-radius:var(--r0);padding:13px 4px;cursor:pointer;transition:background-color .15s;display:flex;justify-content:space-between;align-items:center}
.trbadge{font-family:var(--kit);font-size:16px;color:#0C0F14;padding:3px 9px;border-radius:var(--r2);font-weight:700}
.tcard:hover,.tcard:focus-visible{background:var(--hover)}
.tcard:active{background:var(--surface)}
.tcard .tn{font-weight:600} .tcard .ts{color:var(--mut);font-size:12px}
.fsel{display:flex;gap:6px;flex-wrap:wrap}
.fbtn.htg{margin-left:auto}
.fbtn.htg.on{border-color:rgba(124,147,184,.5);color:#C9D3E3;background:rgba(124,147,184,.10)}
.zheat{position:absolute;inset:0;z-index:0;pointer-events:none;border-radius:inherit;overflow:hidden}
.zcell{position:absolute;box-sizing:border-box;border:1px solid rgba(255,255,255,.04)}
.zcell.zg{background:rgba(40,199,120,.13)}
.zcell.zy{background:rgba(232,178,58,.20)}
.zcell.zr{background:rgba(196,119,106,.26)}
.zcell.zn{background:rgba(196,119,106,.10)}
.pitch>.pchip,.pitch>.ln{z-index:2}
.fbtn{font-family:var(--mono);font-size:12px;letter-spacing:.06em;padding:7px 12px;border-radius:var(--r1);background:var(--surface);border:1px solid var(--chalk);color:var(--mut)}
.fbtn.on{border-color:var(--focus);color:var(--tx);background:rgba(124,147,184,.12)}
.squad{display:grid;grid-template-columns:minmax(0,480px) minmax(0,1fr);gap:40px;align-items:start}
@media(max-width:820px){.squad{grid-template-columns:1fr}}
.pitch{position:relative;width:100%;max-width:480px;margin:0 auto;aspect-ratio:68/104;
  background:repeating-linear-gradient(180deg,#103a24 0,#103a24 12.5%,#0d3320 12.5%,#0d3320 25%);
  border:1px solid rgba(255,255,255,.07);border-radius:var(--r0);overflow:hidden;box-shadow:inset 0 0 40px rgba(0,0,0,.35)}
.pitch .ln{position:absolute;border:1.5px solid rgba(233,237,225,.20);pointer-events:none}
.pitch .mid{left:0;right:0;top:50%;border:none;border-top:1.5px solid rgba(233,237,225,.20)}
.pitch .circ{left:50%;top:50%;width:80px;height:80px;border-radius:50%;transform:translate(-50%,-50%)}
.pitch .boxT{left:25%;right:25%;top:0;height:13%;border-top:none}
.pitch .boxB{left:25%;right:25%;bottom:0;height:13%;border-bottom:none}
.pchip{position:absolute;transform:translate(-50%,-50%);width:76px;text-align:center;cursor:pointer;z-index:2}
.pchip .dwrap{position:relative;width:46px;height:46px;margin:0 auto}
.pchip .disc{width:46px;height:46px;border-radius:50%;background:#14181D;border:2px solid rgba(255,255,255,.55);
  display:flex;align-items:center;justify-content:center;font-family:var(--ui);font-weight:700;font-size:16px;color:#fff;
  transition:transform .15s,border-color .15s;box-shadow:0 2px 6px rgba(0,0,0,.3)}
.pchip:hover .disc{border-color:#fff;transform:scale(1.07)}
.pchip.sel .disc{border-color:var(--live)}
.pchip .rbadge{position:absolute;top:-7px;right:-11px;min-width:24px;padding:1.5px 5px;border-radius:var(--r2);
  font-family:var(--ui);font-weight:800;font-size:11px;color:#0C0F14;box-shadow:0 1px 4px rgba(0,0,0,.35)}
.pchip .nm{font-size:10.5px;font-weight:600;margin-top:4px;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-shadow:0 1px 4px rgba(0,0,0,.9)}
.pchip .pos{font-family:var(--ui);font-size:8px;color:rgba(255,255,255,.6)}
.pchip.empty .disc{border-style:dashed;border-color:rgba(255,255,255,.35);color:rgba(255,255,255,.5);background:rgba(0,0,0,.18)}
.pchip .plabel{font-family:var(--ui);font-weight:700;font-size:8.5px;letter-spacing:.06em;color:rgba(255,255,255,.85);background:rgba(0,0,0,.38);border-radius:var(--r2);padding:1px 6px;display:inline-block;margin-bottom:3px;text-transform:uppercase}
.pchip .bk{font-size:8.5px;color:rgba(255,255,255,.55);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:86px;margin:2px auto 0;text-shadow:0 1px 3px #000}
.bench{margin-top:8px}
.benchrow{display:flex;gap:8px;overflow-x:auto;padding-bottom:6px}
.zonewarn{background:rgba(196,119,106,.08);border-left:3px solid rgba(196,119,106,.6);border-radius:var(--r0);padding:11px 14px;margin-bottom:16px}
.zwh{color:#E3A79A;font-weight:600;font-size:13px;margin-bottom:7px;letter-spacing:.3px}
.zwl{display:flex;flex-wrap:wrap;gap:7px}
.zwl span{background:rgba(196,119,106,.14);border:1px solid rgba(196,119,106,.4);color:#EAC0B6;border-radius:var(--r2);padding:3px 10px;font-size:12px;font-family:var(--mono)}
.benchcol{display:flex;flex-direction:column;gap:14px;min-height:80px}
.bcat .bcath{font-size:11px;letter-spacing:.6px;text-transform:uppercase;color:var(--focus);margin-bottom:6px}
.brow{display:flex;justify-content:space-between;align-items:center;gap:10px;background:var(--card2,rgba(255,255,255,.03));border:1px solid var(--chalk);border-radius:var(--r1);padding:8px 12px;margin-bottom:6px;cursor:grab}
.brow:hover{border-color:var(--focus)}
.brow:active{cursor:grabbing}
.brow .bn{font-size:13.5px}
.brow .bs2{font-size:11px;color:var(--mut);font-family:var(--mono)}
.pchip[draggable="true"]{cursor:grab}
.pchip[draggable="true"]:active{cursor:grabbing}
.pchip.moved .plabel{color:var(--live)}
.tlink{cursor:pointer;border-bottom:1px dotted rgba(255,255,255,.32)}
.standout{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:4px 0 20px}
.standout .solbl{font-size:11px;letter-spacing:.6px;text-transform:uppercase;color:var(--rad-a);margin-right:4px}
.sochip{background:rgba(196,119,106,.10);border:1px solid rgba(196,119,106,.32);border-radius:var(--r2);padding:4px 11px;font-size:13px;color:#F0D6CE;font-family:var(--mono)}
.sochip b{color:#fff}
.tlink:hover{color:var(--focus);border-color:var(--focus)}
.bchip{min-width:118px;background:var(--surface);border:1px solid var(--chalk);border-radius:var(--r1);padding:9px 11px;cursor:pointer;transition:border-color .15s}
.bchip:hover{border-color:var(--focus)}
.bchip .bn{font-size:12.5px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bchip .bs{font-family:var(--mono);font-size:10.5px;color:var(--mut);margin-top:2px}
.ovl{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:40;display:flex;justify-content:flex-end}
.draw{background:var(--surface);border-left:1px solid var(--chalk2);width:400px;max-width:92vw;height:100%;overflow-y:auto;padding:22px}
.draw h3{font-family:var(--disp);margin:.2em 0 .1em;font-size:22px}
.drsec{margin-top:20px} .drsec .panel-h{margin-bottom:10px}
.tgtinput{width:100%;padding:9px 12px;border:1px solid var(--chalk);border-radius:var(--r1);background:var(--surface);color:var(--tx);font-family:var(--ui);font-size:13px;box-sizing:border-box}
.tgtres{margin-top:6px}
.tgtrow{display:flex;justify-content:space-between;align-items:center;padding:7px 10px;border-radius:var(--r1);cursor:pointer;font-size:13px}
.tgtrow:hover{background:var(--surface)}
.tgtrow .tgtm{color:var(--mut);font-size:11px}
.tgthead{border-left:3px solid;padding:8px 12px;margin:12px 0 10px;background:var(--surface);border-radius:var(--r0);font-size:13px}
.tgtv{display:flex;gap:9px;align-items:flex-start;padding:7px 0;border-top:1px solid var(--chalk2)}
.tgtvb{flex:none;width:18px;height:18px;border-radius:50%;color:#0C0F14;font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;margin-top:1px}
.tgtv b{font-size:12.5px} .tgtvd{font-size:11.5px;color:var(--mut);margin-top:2px;line-height:1.45}
.altrow{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid var(--chalk)}
.altrow .ai{flex:1;min-width:0} .altrow .an{font-weight:500;font-size:13.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.altrow .as{color:var(--mut);font-size:11.5px}
.altrow .av{font-family:var(--kit);font-size:16px;width:30px;text-align:right}
.swapb{font-family:var(--mono);font-size:11px;color:var(--focus);border:1px solid var(--chalk2);border-radius:var(--r1);padding:5px 9px}
.swapb:hover{background:rgba(124,147,184,.12)}
.drclose{float:right;color:var(--mut);font-size:20px;line-height:1;padding:2px 6px}
.drlink{display:inline-block;margin-top:14px;font-size:13px;color:var(--focus)}
@media(max-width:600px){.ovl{align-items:flex-end}.draw{width:100%;max-width:100%;height:auto;max-height:86vh;border-left:none;border-top:1px solid var(--chalk2);border-radius:var(--r2) var(--r2) 0 0}}
/* model fit */
.mfit{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:26px}
@media(max-width:820px){.mfit{grid-template-columns:1fr}}
.mrow{display:flex;align-items:center;gap:12px;padding:7px 0;cursor:pointer}
.mname{width:120px;font-size:13px;color:var(--mut);flex-shrink:0}
.mrow.on .mname{color:var(--tx)}
.mbarwrap{flex:1} .mbar{height:8px;background:var(--surface);border-radius:var(--r1);overflow:hidden}
.mbar i{display:block;height:100%;border-radius:var(--r1)}
.mpct{width:40px;text-align:right;font-family:var(--mono);font-size:12.5px}
/* .mdet = seçili oyun-modelinin "cihaz paneli" — kutu değil, üst kenarı vurgu renkli
   bir enstrüman etiketi gibi okunsun */
.mdet{background:var(--surface);border:1px solid var(--chalk);border-top:2px solid var(--live);border-radius:var(--r0);padding:18px;align-self:start}
.mdet .dh{font-family:var(--mono);font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--faint)}
.mdet .df{font-family:var(--kit);font-size:40px;line-height:1;margin:6px 0 2px;font-variant-numeric:tabular-nums}
.swlabel{font-family:var(--mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--faint);margin:16px 0 8px}
.swchip{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;border-radius:var(--r2);padding:5px 9px;margin:0 6px 6px 0}
.swpos{background:var(--data-pos-bg,rgba(63,208,122,.12));color:var(--pos);border:1px solid rgba(63,208,122,.3)}
.swneg{background:rgba(196,119,106,.12);color:var(--neg);border:1px solid rgba(196,119,106,.3)}
.swchip b{font-family:var(--mono)}
.tsf{margin-top:16px;padding-top:14px;border-top:1px solid var(--chalk);font-size:13px;color:var(--mut)}
.tsf b{color:var(--tx)}
/* comparison */
.cmptablewrap{overflow-x:auto;margin-bottom:16px}
.cmptable{border-collapse:collapse;width:100%;font-size:12.5px;white-space:nowrap}
.cmptable th{font-family:var(--mono);font-size:9.5px;letter-spacing:.03em;color:var(--faint);text-transform:uppercase;padding:6px 9px;text-align:right;border-bottom:1px solid var(--chalk);font-weight:500}
.cmptable th:first-child{text-align:left}
.cmptable td{padding:8px 9px;text-align:right;font-family:var(--mono);font-feature-settings:"tnum";border-bottom:1px solid var(--chalk);color:var(--tx)}
.cmptable td.pcell{text-align:left;font-family:var(--ui);min-width:140px}
.cmptable .ps{font-size:11px;color:var(--mut);font-family:var(--ui)}
.xbtn{color:var(--faint);font-size:13px}.xbtn:hover{color:var(--neg)}
.cmpradar{display:flex;justify-content:center;margin-bottom:8px}
.cmpadd{display:flex;flex-wrap:wrap;gap:8px;align-items:center;border-top:1px solid var(--chalk);padding-top:14px;margin-top:6px}
.cmpaddlbl{font-size:12px;color:var(--mut)}
.addchip{font-size:12.5px;border:1px solid var(--chalk2);border-radius:var(--r2);padding:6px 10px;color:var(--focus)}
.addchip:hover{background:rgba(124,147,184,.12)}
.cmpfull{font-size:12px;color:var(--neu)}
.cmpsearch{position:relative;margin-bottom:14px}
.cmppos{display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:14px}
.cmpposl{font-size:11px;letter-spacing:.5px;text-transform:uppercase;color:var(--mut)}
.cmpsearch input{width:100%;background:var(--card2,rgba(255,255,255,.04));border:1px solid var(--chalk2);border-radius:var(--r1);padding:10px 13px;color:var(--tx);font-size:14px;font-family:var(--ui)}
.cmpsearch input:focus{outline:none;border-color:var(--focus)}
.simmx{margin:20px 0}
.radmode{display:inline-flex;gap:0;margin:10px 0 4px;border:1px solid var(--chalk2);border-radius:var(--r1);overflow:hidden}
.rmb{background:var(--surface);color:var(--mut);border:none;padding:7px 15px;font-family:var(--ui);font-size:12.5px;cursor:pointer}
.rmb.on{background:var(--live);color:#0C0F14;font-weight:600}
.radmins{font-size:12.5px;color:var(--mut);margin-top:5px}
.radmins b{color:var(--tx);font-family:var(--kit);font-size:14px}
.cmpsubh{font-size:12px;color:var(--mut);margin-bottom:9px;font-family:var(--mono);letter-spacing:.04em;text-transform:uppercase}
.smx td,.smx th{text-align:center;padding:8px 10px;font-family:var(--kit);font-size:14px;min-width:52px;border:1px solid var(--chalk2)}
.smx .smx-name,.smx thead th:first-child{font-family:var(--ui);font-size:12px;text-align:left;font-weight:600}
.smx .smx-self{color:var(--faint)}
.smx th{font-family:var(--ui);font-size:11px;color:var(--mut);font-weight:600}
.cmpres{position:absolute;left:0;right:0;top:46px;z-index:20;background:var(--elev);border:1px solid var(--chalk2);border-radius:var(--r0);overflow:hidden;max-height:280px;overflow-y:auto;box-shadow:0 4px 22px -6px var(--shadow-tint)}
.cmpres:empty{display:none}
.cmpresit{display:flex;align-items:center;gap:10px;padding:9px 13px;cursor:pointer;font-size:13.5px;border-bottom:1px solid var(--chalk)}
.cmpresit:last-child{border-bottom:none}
.cmpresit:hover{background:var(--hover)}
.cmpresit .nm{font-weight:500}
.cmpresm{color:var(--mut);font-size:12px;margin-top:1px}
.cmpresno{padding:10px 13px;color:var(--faint);font-size:12.5px}
.bvbar{border-top:1px solid var(--chalk);padding-top:14px;margin-top:6px}
.bvgrp{margin-top:12px}
.bvglabel{display:flex;align-items:center;gap:7px;font-size:12.5px;font-weight:500;color:var(--tx);margin-bottom:7px}
.bvdot{width:9px;height:9px;border-radius:50%;display:inline-block;flex:none}
.bvlabel{text-align:center;color:var(--focus);font-size:13px;margin-bottom:12px}
.bvrow{display:flex;flex-wrap:wrap;gap:8px;justify-content:flex-start}
.bvchip{display:flex;flex-direction:column;align-items:center;gap:2px;font-size:12.5px;border:1px solid var(--chalk2);border-radius:var(--r1);padding:7px 13px;color:var(--mut);min-width:92px}
.bvchip:hover{border-color:var(--focus)}
.bvchip.on{background:rgba(255,255,255,.04)}
.bvsub{font-size:10px;color:var(--faint);font-family:var(--mono)}

/* ---- tab bar ---- */
.tabbar{display:flex;gap:4px;background:var(--surface);border:1px solid var(--chalk);border-radius:var(--r1);padding:3px}
.tabbtn{padding:7px 15px;border-radius:var(--r1);font-size:13px;color:var(--mut);white-space:nowrap;transition:.15s}
.tabbtn:hover{color:var(--tx)}
.tabbtn:focus-visible{outline:2px solid var(--focus);outline-offset:-2px}
.tabbtn:active{transform:scale(.97)}
.tabbtn.on{background:var(--live);color:#0C0F14;font-weight:500}

/* ---- filtreleme sekmesi ---- */
.fltwrap{display:flex;flex-direction:column;gap:18px}
.fltbuckets{display:flex;flex-wrap:wrap;gap:6px}
.fltpill{padding:8px 15px;border-radius:var(--r1);border:1px solid var(--chalk2);border-left:3px solid var(--pgc,var(--chalk2));color:var(--mut);font-size:13px;font-family:var(--mono)}
.fltpill:hover{border-color:var(--focus)}
.fltpill:focus-visible{outline:2px solid var(--focus);outline-offset:1px}
.fltpill:active{transform:scale(.97)}
.fltpill.on{background:var(--live);color:#0C0F14;border-color:var(--live);border-left-color:var(--pgc,var(--live));font-weight:500}
.fltbar{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.fltaddbtn{padding:9px 16px;border-radius:var(--r1);border:1px dashed var(--chalk2);color:var(--live);font-size:13px}
.fltaddbtn:hover{border-color:var(--live);background:rgba(124,147,184,.06)}
.fltcount{color:var(--mut);font-size:12.5px;font-family:var(--mono);margin-left:auto}
.fltcombine{display:flex;align-items:center;gap:6px}
.ccword{color:var(--faint);font-size:11.5px}
.ccbtn{padding:6px 12px;border-radius:var(--r1);font-size:12px;color:var(--mut);border:1px solid var(--chalk2);background:var(--surface)}
.ccbtn.on{background:var(--live);color:#0C0F14;border-color:var(--live);font-weight:500}
.rowcombine{display:inline-flex;gap:3px;margin-left:8px}
.ccmini{padding:4px 9px;border-radius:var(--r2);font-size:10.5px;color:var(--faint);border:1px solid var(--chalk2)}
.ccmini.on{background:rgba(124,147,184,.16);color:var(--live);border-color:var(--live)}
.fltrows{display:flex;flex-direction:column;gap:8px}
.fltrow{display:flex;align-items:center;gap:10px;background:var(--surface);border:1px solid var(--chalk);border-radius:var(--r0);padding:10px 13px;flex-wrap:wrap}
.fltrow .fname{font-size:13px;font-weight:500;min-width:150px}
.fltrow .fgrp{font-family:var(--mono);font-size:10px;letter-spacing:.05em;color:var(--faint);text-transform:uppercase}
.fltnum{width:76px;background:var(--elev);border:1px solid var(--chalk2);border-radius:var(--r1);padding:6px 9px;color:var(--tx);font-size:13px;font-family:var(--mono)}
.fltnum:focus{outline:none;border-color:var(--focus)}
.fltsel{background:var(--elev);border:1px solid var(--chalk2);border-radius:var(--r1);padding:6px 9px;color:var(--tx);font-size:12.5px;max-width:220px}
.fltchips{display:flex;gap:6px;flex-wrap:wrap}
.fltchip{padding:5px 11px;border-radius:var(--r2);border:1px solid var(--chalk2);color:var(--mut);font-size:12px}
.fltchip.on{background:rgba(124,147,184,.14);border-color:var(--live);color:var(--tx)}
.fltrm{margin-left:auto;color:var(--faint);font-size:16px;padding:2px 8px;border-radius:var(--r2)}
.fltrm:hover{color:var(--neg);background:rgba(196,119,106,.1)}
.fltempty{color:var(--faint);font-size:13px;padding:10px 2px}
.fieldpicker{background:var(--elev);border:1px solid var(--chalk2);border-radius:var(--r0);padding:14px;box-shadow:0 4px 24px -6px var(--shadow-tint)}
.fpchead{font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;color:var(--faint);text-transform:uppercase;margin-bottom:8px}
.fpcats{display:flex;gap:7px;margin-bottom:12px;flex-wrap:wrap}
.fpcat{padding:9px 16px;border-radius:var(--r1);font-size:13.5px;font-weight:500;color:var(--tx);background:var(--surface);border:1px solid var(--chalk2);transition:.15s}
.fpcat:hover{border-color:var(--focus)}
.fpcat .n{color:var(--faint);font-family:var(--mono);font-size:11px;margin-left:5px}
.fpcat.on{background:var(--live);color:#0C0F14;border-color:var(--live)}
.fpcat.on .n{color:rgba(6,18,31,.6)}
.fplist{display:flex;flex-direction:column;max-height:260px;overflow-y:auto;gap:1px}
.fpitem{padding:8px 10px;border-radius:var(--r1);font-size:13px;color:var(--tx);display:flex;justify-content:space-between}
.fpitem:hover{background:rgba(255,255,255,.05)}
.fpitem .sub{color:var(--faint);font-size:11px;font-family:var(--mono)}
.fpitemwrap{display:flex;align-items:center;gap:2px}
.fpitemwrap .fpitem{flex:1}
.fpdel{padding:6px 9px;color:var(--faint);border-radius:var(--r2);cursor:pointer}
.fpdel:hover{color:var(--neg);background:rgba(196,119,106,.1)}
.cmbox{margin-bottom:10px}
.cmtogglebtn{padding:8px 14px;border-radius:var(--r1);border:1px dashed var(--live);color:var(--live);font-size:12.5px}
.cmtogglebtn:hover{background:rgba(124,147,184,.06)}
.cmform{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-top:9px;padding:11px;background:var(--surface);border-radius:var(--r0);border:1px solid var(--chalk2)}
.fltnumtext{background:var(--elev);border:1px solid var(--chalk2);border-radius:var(--r1);padding:6px 9px;color:var(--tx);font-size:12.5px;min-width:150px}
.fltnumtext:focus{outline:none;border-color:var(--focus)}
.cmcreatebtn{padding:7px 15px;border-radius:var(--r1);background:var(--live);color:#0C0F14;font-weight:500;font-size:12.5px}
.fltresults{overflow-x:auto}
.flttable{min-width:100%;width:max-content;border-collapse:collapse;font-size:13px}
.flttable th{text-align:left;color:var(--faint);font-size:11px;letter-spacing:.05em;text-transform:uppercase;font-family:var(--mono);padding:8px 10px;border-bottom:1px solid var(--chalk2);white-space:nowrap}
.flttable th.srt{cursor:pointer;user-select:none}
.flttable th.srt:hover{color:var(--tx)}
.flttable td{padding:9px 10px;border-bottom:1px solid var(--chalk);white-space:nowrap;max-width:220px;overflow:hidden;text-overflow:ellipsis}
.flttable tr.pr{cursor:pointer}
.flttable tr.pr:hover td{background:rgba(255,255,255,.03)}
.flttable tr.pr:hover td.stk{background:var(--hover)}
.flttable td.nm{font-weight:500;color:var(--tx)}
.fltmore{color:var(--faint);font-size:12px;padding:10px 2px}
/* temel sütunlar (Oyuncu/Takım/Lig/Yaş/CA) sabit kalır, metrik sütunları yatay scroll olur —
   çok filtre eklenince tablo daralmak yerine kayar, kimlik sütunları hep görünür kalır */
.flttable th.stk,.flttable td.stk{position:sticky;background:var(--bg);z-index:1}
.flttable .stk1{left:0;width:150px;max-width:150px}
.flttable .stk2{left:150px;width:140px;max-width:140px}
.flttable .stk3{left:290px;width:100px;max-width:100px}
.flttable .stk4{left:390px;width:46px;max-width:46px}
.flttable .stk5{left:436px;width:52px;max-width:52px;box-shadow:6px 0 8px -6px var(--shadow-tint)}
.flttable th.stk{z-index:2}
</style>
</head>
<body>
<header>
  <div class="bar">
    <div class="brand" onclick="go(null)">Big<b>StatX</b></div>
    <nav class="tabbar" aria-label="Ana bölümler">
      <button class="tabbtn on" data-tab="genel" onclick="go(null)">Genel Bakış</button>
      <button class="tabbtn" data-tab="filtre" onclick="goFilter()">Filtreleme</button>
    </nav>
    <div class="searchwrap">
      <svg class="searchicon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      <input class="search" id="q" placeholder="Oyuncu ara…  (Saliba, Haaland, Donnarumma…)" autocomplete="off" role="combobox" aria-expanded="false" aria-autocomplete="list" aria-controls="res"/>
      <button class="searchclear" id="qclear" type="button" aria-label="Aramayı temizle">×</button>
      <div class="results" id="res" style="display:none" role="listbox"></div>
    </div>
  </div>
</header>
<main id="app"></main>

<script id="data" type="application/json">__DATA__</script>
<script>
const BUILD="__BUILD__";
let DB=null, BYID={}, GROUPS=[], NAMEIDX=[], TEAMS=[];
const BUCK_TR={GK:"Kaleci",CB:"Stoper",RB:"Sa\u011f Bek",LB:"Sol Bek",DM:"Defansif Orta",CM:"Merkez Orta",AM:"Ofansif Orta",RW:"Sa\u011f Kanat",LW:"Sol Kanat",ST:"Forvet"};
// pozisyon-grubu renk kodu \u2014 futbola \u00f6zg\u00fc k\u00fc\u00e7\u00fck bir detay: kaleci/defans/orta saha/forvet
// her yerde ayn\u0131 renk dilini ta\u015f\u0131s\u0131n (bkz. engine.py POS_GROUP ile ayn\u0131 gruplama)
const POS_GROUP={GK:'gk',CB:'def',LB:'def',RB:'def',DM:'mid',CM:'mid',AM:'mid',LW:'fwd',RW:'fwd',ST:'fwd'};
function posGroupColor(b){ return 'var(--pg-'+(POS_GROUP[b]||'mid')+')'; }

function norm(s){return (s||"").toLocaleLowerCase("tr").normalize("NFD").replace(/[\u0300-\u036f]/g,"");}
function leagueShort(l){return (l||"").split("(")[0].trim();}
// LİG KADEME rozeti: motorda hesaplanan göreli kalite kademesi (bkz. bigstatx_engine.py
// LİG KALİTE KADEMESİ) — ham katsayı sayısı DEĞİL, "bu seviyedeki rakiplerin ortalaması"
// tarzı bir kademe etiketi. Küçük örneklemli ligde meta.leagues[].tier yoktur -> rozet basılmaz.
function leagueTierBadge(leagueName){
  const rec=(DB.meta.leagues||[]).find(x=>x.name===leagueName);
  if(!rec || !rec.tier) return '';
  return ' <span class="ligtier" title="Bu lig, '+esc(rec.tier)+' kategorisindeki liglere benzer bir ortalama kaliteye sahip.">'+esc(rec.tier)+'</span>';
}
function fmtVal(v){ if(v==null||v==="")return "—"; if(typeof v==="number"){ if(v>=1e6)return "€"+(v/1e6).toFixed(1).replace(".0","")+"M"; if(v>=1e3)return "€"+Math.round(v/1e3)+"K"; return "€"+v;} return v;}
// cimri vurgu: yalnız gerçekten yüksek (≥85) değerler vurgu rengi alır — orta bant nötr
// metin rengi (--tx/--mut), kırmızı burada kullanılmaz (CA düşük olmak "hata" değil, sadece
// düşük profil — kırmızı yalnız gerçek uyarılarda: kadro açığı, "geliştirilecek" percentile vb.)
function scoreColor(n){ if(n==null)return "var(--mut)"; if(n>=85)return "var(--live)"; if(n>=50)return "var(--tx)"; return "var(--mut)";}

function buildIndex(){
  BYID={}; const gmap={};
  DB.players.forEach(p=>{ BYID[p.id]=p;
    const key=norm(p.name)+"|"+norm(p.team);
    (gmap[key]=gmap[key]||{name:p.name,alt:p.alt,team:p.team,league:p.league,age:p.age,buckets:{}}).buckets[p.bucket]=p;
  });
  GROUPS=Object.values(gmap);
  NAMEIDX=GROUPS.map(g=>({g,key:norm(g.name)+" "+norm(g.alt||"")+" "+norm(g.team)}));
  const tset={}; DB.players.forEach(p=>{ if(p.team){ (tset[p.team]=tset[p.team]||new Set()).add(p.name); } });
  TEAMS=Object.entries(tset).map(([t,s])=>({t,c:s.size,key:norm(t)}));
}

/* ---------- search ---------- */
const q=document.getElementById('q'), res=document.getElementById('res'), qclear=document.getElementById('qclear');
let RESITEMS=[], RESIDX=-1;
// eşleşen alt-diziyi <mark> ile vurgular — norm() sadece küçük harf + aksan-soyma yaptığı için
// (uzunluk korunur) orijinal string üzerinde doğrudan indeks eşlemesi güvenli
function highlightMatch(s,qn){
  if(!qn) return esc(s);
  const ns=norm(s), i=ns.indexOf(qn);
  if(i<0) return esc(s);
  return esc(s.slice(0,i))+'<mark>'+esc(s.slice(i,i+qn.length))+'</mark>'+esc(s.slice(i+qn.length));
}
function closeRes(){ res.style.display='none'; q.setAttribute('aria-expanded','false'); RESITEMS=[]; RESIDX=-1; }
function markActive(){ RESITEMS.forEach((el,i)=>el.classList.toggle('active',i===RESIDX)); if(RESIDX>=0) RESITEMS[RESIDX].scrollIntoView({block:'nearest'}); }
function renderResults(v){
  const hits=NAMEIDX.filter(x=>x.key.includes(v)).slice(0,40)
    .map(x=>x.g).sort((a,b)=>topOv(b)-topOv(a)).slice(0,10);
  const thits=TEAMS.filter(x=>x.key.includes(v)).sort((a,b)=>b.c-a.c).slice(0,4);
  if(!hits.length && !thits.length){
    res.innerHTML='<div class="resempty">"'+esc(q.value.trim())+'" için sonuç yok</div>';
    res.style.display='block'; q.setAttribute('aria-expanded','true'); RESITEMS=[]; RESIDX=-1; return;
  }
  res.innerHTML=
   (thits.length?'<div class="ressec">Takımlar</div>'+thits.map(x=>
     '<div class="res" role="option" onclick="goTeam('+JSON.stringify(x.t).replace(/"/g,"&quot;")+')"><div style="flex:1;min-width:0"><div class="nm">'+highlightMatch(x.t,v)+'</div><div class="sub">'+x.c+' oyuncu</div></div><span class="tag" style="color:var(--live)">KADRO</span></div>'
   ).join(''):'')+
   (hits.length?'<div class="ressec">Oyuncular</div>'+hits.map(g=>{
     const e=defaultEntry(g), ov=topOv(g);
     return '<div class="res" role="option" onclick="openGroup('+GROUPS.indexOf(g)+')"><span class="pgdot" style="background:'+posGroupColor(e.bucket)+'"></span><div style="flex:1;min-width:0"><div class="nm">'+highlightMatch(g.name,v)+'</div><div class="sub">'+esc(g.team)+' · '+esc(leagueShort(g.league))+'</div></div><span class="resca" style="color:'+scoreColor(ov)+'">'+(ov||'—')+'</span></div>';
   }).join(''):'');
  res.style.display='block'; q.setAttribute('aria-expanded','true');
  RESITEMS=[...res.querySelectorAll('.res')]; RESIDX=-1;
}
q.addEventListener('input',()=>{
  qclear.style.display=q.value?'flex':'none';
  const v=norm(q.value).trim();
  if(v.length<2){closeRes();return;}
  renderResults(v);
});
q.addEventListener('keydown',e=>{
  if(res.style.display==='none') return;
  if(e.key==='ArrowDown'){ if(!RESITEMS.length)return; e.preventDefault(); RESIDX=(RESIDX+1)%RESITEMS.length; markActive(); }
  else if(e.key==='ArrowUp'){ if(!RESITEMS.length)return; e.preventDefault(); RESIDX=(RESIDX-1+RESITEMS.length)%RESITEMS.length; markActive(); }
  else if(e.key==='Enter'){ if(RESIDX>=0&&RESITEMS[RESIDX]){ e.preventDefault(); RESITEMS[RESIDX].click(); } }
  else if(e.key==='Escape'){ closeRes(); q.blur(); }
});
qclear.addEventListener('click',()=>{ q.value=''; qclear.style.display='none'; closeRes(); q.focus(); });
document.addEventListener('click',e=>{ if(!e.target.closest('.searchwrap')) closeRes(); });
function topOv(g){return Math.max(...Object.values(g.buckets).map(p=>p.overall||0));}
// oyuncunun ANA pozisyonuna (FC_En İyi -> best) karşılık gelen kova entry'si; yoksa en yüksek CA
function defaultEntry(g){
  const ents=Object.values(g.buckets);
  const best=(ents.find(p=>p.best)||{}).best;
  if(best && g.buckets[best]) return g.buckets[best];
  // best bir kovaya eşlenmiyorsa ilk pos[0]'a bak
  for(const p of ents){ if(p.pos&&p.pos[0]&&g.buckets[p.pos[0]]) return g.buckets[p.pos[0]]; }
  return ents.sort((a,b)=>(b.overall||0)-(a.overall||0))[0];
}
function openGroup(i){ res.style.display='none'; q.value=''; go(defaultEntry(GROUPS[i]).id); }
function esc(s){return (s||"").replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
// klavye erişimi: <article tabindex="0" onclick=...> gibi native-olmayan tıklanabilirler
// Enter/Boşluk'ta da tetiklensin (bkz. .lcard/.fcard/.fcard2/.tcard)
function kb(e){ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); e.currentTarget.click(); } }
// radar eksen etiketleri: kelime sınırında kes (mümkünse), orta-kelimede kesmekten kaçın —
// "Hava Topu K…" yerine "Hava Topu…"
function wordTrunc(s,max){
  if(s.length<=max) return s;
  const cut=s.slice(0,max), sp=cut.lastIndexOf(' ');
  return (sp>max*0.4 ? cut.slice(0,sp) : cut)+'…';
}
// imza animasyon 3/3: büyük CA rakamı 0'dan hedefe sayarak belirir — numSpan() işaretlenmiş
// span'i yazar (data-target), animateCanums() sayfa render edildikten sonra hepsini tetikler.
function numSpan(v,color){ return v==null?'<span class="canum" style="color:'+color+'">—</span>':'<span class="canum" data-target="'+v+'" style="color:'+color+'">0</span>'; }
function animateCanums(){
  const reduce=window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('.canum[data-target]').forEach(el=>{
    const target=+el.dataset.target; if(isNaN(target)) return;
    if(reduce){ el.textContent=target; return; }
    const t0=performance.now(), dur=750;
    function step(now){
      const t=Math.min(1,(now-t0)/dur), eased=1-Math.pow(1-t,3);
      el.textContent=Math.round(target*eased);
      if(t<1) requestAnimationFrame(step); else el.textContent=target;
    }
    requestAnimationFrame(step);
  });
}

/* ---------- routing ---------- */
function setActiveTab(name){ document.querySelectorAll('.tabbtn').forEach(b=>b.classList.toggle('on', b.dataset.tab===name)); }
function go(id){ res.style.display='none'; q.value=''; history.pushState({id},""); setActiveTab('genel'); render(id); window.scrollTo(0,0); }
function goTeam(t){ res.style.display='none'; q.value=''; history.pushState({team:t},""); setActiveTab('genel'); window.scrollTo(0,0); renderSquad(t); }
function goLeague(L){ res.style.display='none'; q.value=''; history.pushState({league:L},""); setActiveTab('genel'); window.scrollTo(0,0); renderLeague(L); }
function goCompare(){ res.style.display='none'; q.value=''; history.pushState({compare:1},""); setActiveTab('genel'); window.scrollTo(0,0); renderComparePage(); }
function goFilter(){ res.style.display='none'; q.value=''; history.pushState({filtre:1},""); setActiveTab('filtre'); window.scrollTo(0,0); renderFilterPage(); }
function navBack(){ if(history.state && (history.state.id||history.state.team||history.state.league)) history.back(); else { history.pushState({},""); setActiveTab('genel'); render(null); window.scrollTo(0,0);} }
window.onpopstate=e=>{ const s=e.state||{}; res.style.display='none';
  if(s.filtre){ setActiveTab('filtre'); renderFilterPage(); window.scrollTo(0,0); return; }
  setActiveTab('genel');
  if(s.allpos){ renderAllPositions(s.allpos); window.scrollTo(0,0); return; }
  s.team?renderSquad(s.team):(s.league?renderLeague(s.league):(s.compare?renderComparePage():render(s.id))); window.scrollTo(0,0); };
function render(id){ id ? renderProfile(id) : renderLanding(); }
function renderLeague(L){
  const rec=(DB.meta.leagues||[]).find(x=>x.name===L); const teams=rec?rec.teams:[];
  const cntS={}; DB.players.forEach(p=>{ if(p.team){ (cntS[p.team]=cntS[p.team]||new Set()).add(p.name); } });
  const cnt={}; for(const t in cntS) cnt[t]=cntS[t].size;
  document.getElementById('app').innerHTML=
    '<a class="back" onclick="navBack()">← geri</a>'+
    '<div class="phead"><div class="pid"><h2>'+esc(L)+'</h2><div class="pmeta">'+teams.length+' takım · birini seç → otomatik 11 + bölge analizi</div></div></div>'+
    '<div class="fgrid" style="margin-top:18px">'+(teams.length?teams.map(t=>{ const c=cnt[t]||0; const tr=(DB.meta.team_ratings||{})[t];
      return '<article class="tcard" tabindex="0" onkeydown="kb(event)" onclick="goTeam('+JSON.stringify(t).replace(/"/g,"&quot;")+')"><div><div class="tn">'+esc(t)+'</div><div class="ts">'+(c?c+' oyuncu (veri yüklü)':'tam veride')+'</div></div>'+(tr?'<span class="trbadge" style="background:'+scoreColor(tr.rating)+'" title="'+(tr.partial?'kısmi kadro ('+tr.squad+' oyuncu)':'takım reytingi')+'">'+(tr.partial?'~':'')+tr.rating+'</span>':'<span style="color:var(--live);font-family:var(--mono);font-size:18px">→</span>')+'</article>';
    }).join(''):'<div class="empty">Bu lig için takım bulunamadı.</div>')+'</div>';
}

/* ---------- landing ---------- */
// hero'daki dekoratif radar motifi: gerçek bir oyuncuya bağlı değil, ürünün imza
// görselleştirmesini (bkz. radarSVG) büyütülmüş halde önizleyen sabit bir illüstrasyon
function heroRadarSVG(){
  const N=8,R=176,cx=210,cy=210,fr=[.82,.55,.7,.92,.42,.78,.6,.88];
  const pt=(i,r)=>{const a=-Math.PI/2+i*(2*Math.PI/N);return [cx+r*Math.cos(a),cy+r*Math.sin(a)];};
  let rings=''; [.33,.66,1].forEach(f=>{let q=[];for(let i=0;i<N;i++){const[x,y]=pt(i,R*f);q.push(x.toFixed(1)+','+y.toFixed(1));} rings+='<polygon points="'+q.join(' ')+'" fill="none" stroke="rgba(255,255,255,.07)" stroke-width="1"/>';});
  let axes=''; for(let i=0;i<N;i++){const[x,y]=pt(i,R); axes+='<line x1="'+cx+'" y1="'+cy+'" x2="'+x.toFixed(1)+'" y2="'+y.toFixed(1)+'" stroke="rgba(255,255,255,.06)" stroke-width="1"/>';}
  let q=[]; for(let i=0;i<N;i++){const[x,y]=pt(i,R*fr[i]); q.push(x.toFixed(1)+','+y.toFixed(1));}
  const poly='<polygon points="'+q.join(' ')+'" fill="var(--live)" fill-opacity=".16" stroke="var(--live)" stroke-width="2" pathLength="1" class="radardraw" style="animation-delay:.5s"/>';
  return '<svg viewBox="0 0 420 420" aria-hidden="true">'+rings+axes+poly+'</svg>';
}
function renderLanding(){
  const _seen={}; const _pool=[];
  [...DB.players].sort((a,b)=>(b.overall||0)-(a.overall||0)).forEach(p=>{
    if((p.minutes||0)<900) return;
    const k=norm(p.name)+"|"+norm(p.team);
    if(_seen[k]) return; _seen[k]=1; _pool.push(p);   // oyuncu başına en yüksek overall entry'si
  });
  const featured=_pool.slice(0,12);
  const mq=(DB.meta.marquee||[]).filter(t=>TEAMS.some(x=>x.t===t));
  const teamList=(mq.length?mq:TEAMS.sort((a,b)=>b.c-a.c).slice(0,12).map(x=>x.t)).slice(0,12);
  document.getElementById('app').innerHTML=
   '<section class="dashhero"><div class="dhrow">'+
     '<div class="dhcontent">'+
       '<div class="dheye">Scouting Terminali</div>'+
       '<h1 class="dhh1">Big<span class="x">StatX</span></h1>'+
       '<p class="dhsub">Ligler genelinde radar profili, rol uyumu ve kadro mühendisliği — tek terminalde, gerçek maç verisiyle.</p>'+
       '<div class="dhcta"><button class="dhbtn pri" onclick="document.getElementById(\'q\').focus();window.scrollTo({top:0,behavior:\'smooth\'})">Oyuncu ara <span>→</span></button>'+
       '<button class="dhbtn" onclick="document.getElementById(\'ligler\').scrollIntoView({behavior:\'smooth\'})">Ligleri gözat</button>'+
       '<button class="dhbtn" onclick="goCompare()">Karşılaştırma <span>⇄</span></button></div>'+
     '</div>'+
     '<div class="dhradar">'+heroRadarSVG()+'</div>'+
   '</div>'+
     '<div class="dhstats">'+
       '<div class="dhst"><div class="n">'+DB.meta.total_entries.toLocaleString("tr")+'</div><div class="l">oyuncu girişi</div></div>'+
       '<div class="dhst"><div class="n">'+TEAMS.length+'</div><div class="l">takım</div></div>'+
       '<div class="dhst"><div class="n">'+(DB.meta.leagues||[]).length+'</div><div class="l">lig</div></div>'+
       '<div class="dhst"><div class="n">'+POS10_ORDER.length+'</div><div class="l">pozisyon</div></div>'+
     '</div></section>'+
   '<div class="feat-h" id="ligler">Ligler — gözat</div>'+
   '<div class="lgrid">'+(DB.meta.leagues||[]).map(x=>
     '<article class="lcard" tabindex="0" onkeydown="kb(event)" onclick="goLeague('+JSON.stringify(x.name).replace(/"/g,"&quot;")+')"><div class="ln2">'+esc(x.name)+'</div><div class="ls">'+x.teams.length+' takım</div></article>'
   ).join('')+'</div>'+
   '<div class="feat-h" style="margin-top:28px">Kadro Mühendisliği — bir takım seç</div>'+
   '<div class="fgrid">'+teamList.map(t=>{const c=(TEAMS.find(x=>x.t===t)||{}).c||0;
     return '<article class="tcard" tabindex="0" onkeydown="kb(event)" onclick="goTeam('+JSON.stringify(t).replace(/"/g,"&quot;")+')"><div><div class="tn">'+esc(t)+'</div><div class="ts">'+c+' oyuncu · otomatik 11</div></div><span style="color:var(--live);font-family:var(--mono);font-size:18px">→</span></article>';
   }).join('')+'</div>'+
   '<div class="feat-h" style="margin-top:28px">Öne çıkan oyuncular</div>'+
   '<div class="fgrid">'+featured.map(p=>
     '<article class="fcard" tabindex="0" onkeydown="kb(event)" onclick="go(\''+p.id+'\')"><span class="ov" style="color:'+scoreColor(p.overall)+'">'+(p.overall??'—')+'</span>'+
     '<div class="nm">'+esc(p.name)+'</div><div class="sub">'+esc(p.team)+' · '+p.bucket+'</div></article>').join('')+'</div>';
}

/* ---------- profile ---------- */
// oyuncunun oynadığı tüm pozisyon-girişlerini (bucket) CA'ya göre sıralı döner — hem tek-pozisyon
// profil sekmesinde hem "Tüm Pozisyonlar" birleşik görünümünde kullanılır
function groupBuckets(p){
  const key=norm(p.name)+"|"+norm(p.team);
  const grp=GROUPS.find(g=>norm(g.name)+"|"+norm(g.team)===key)||{buckets:{[p.bucket]:p}};
  const buckets=Object.keys(grp.buckets);
  const bestB=(Object.values(grp.buckets).find(x=>x.best)||{}).best;
  const ordered=buckets.slice().sort((x,y)=>{
    if(x===bestB)return -1; if(y===bestB)return 1;
    return (grp.buckets[y].overall||0)-(grp.buckets[x].overall||0);
  });
  return {grp,buckets,bestB,ordered};
}
function renderProfile(id){
  const p=BYID[id]; if(!p){document.getElementById('app').innerHTML='<div class="empty">Oyuncu bu veri setinde yok.</div>';return;}
  const {grp,buckets,bestB,ordered}=groupBuckets(p);
  const tabs=buckets.length>1 ? '<div class="ptabs">'+ordered.map(b=>'<button class="ptab '+(b===p.bucket?'on':'')+'" style="--pgc:'+posGroupColor(b)+'" onclick="go(\''+grp.buckets[b].id+'\')">'+b+' · '+BUCK_TR[b]+(b===bestB?' ★':'')+'</button>').join('')+
    '<button class="ptab allpos" onclick="goAllPos(\''+id+'\')">⊞ Tüm Pozisyonlar</button></div>' : '';

  document.getElementById('app').innerHTML=
    '<a class="back" onclick="navBack()">← geri</a>'+
    '<div class="phead"><div class="pid"><h2>'+esc(p.name)+'</h2>'+
      '<div class="pmeta"><b>'+tlink(p.team)+'</b> · '+esc(leagueShort(p.league))+leagueTierBadge(p.league)+' · '+p.bucket+' ('+BUCK_TR[p.bucket]+')</div>'+
      '<div class="chips">'+
        (p.pa!=null?chip('BSX Potansiyel',p.pa):'')+chip('En iyi mevki',(p.pos&&p.pos[0])?p.pos[0]:p.bucket)+chip('Yaş',p.age!=null?(Math.round(p.age)+(p.dob?' ('+fmtDob(p.dob)+')':'')):'—')+chip('Dk',p.minutes!=null?Math.round(p.minutes).toLocaleString("tr"):'—')+
        chip('Ayak',p.foot||'—')+chip('Değer',p.value_eur!=null?fmtMoney(p.value_eur):(p.value||'—'))+chip('Net maaş',p.wage_eur!=null?(fmtMoney(p.wage_eur)+'/yıl'):'—')+chip('Sözleşme',p.contract||'—')+
        (p.veff!=null&&p.veff>=75?'<span class="chip vchip" title="Pozisyonunda fiyatına göre en verimli %'+(100-p.veff)+' dilimde"><span class="k">DEĞER</span><span class="v">↑ %'+p.veff+' verimli</span></span>':'')+
      '</div></div>'+
      '<div class="score">'+
        (function(){
          const young = p.age!=null && p.age<23 && p.pa!=null && p.pa>(p.overall||0)+6;
          if(young){
            // genç yetenek: mevcut BSX Skoru düşük olabilir, potansiyeli öne çıkar
            return '<div class="n">'+numSpan(p.overall,scoreColor(p.pa))+'<span class="toPA"> → '+p.pa+'</span></div>'+
              '<div class="lab">BSX Skoru → BSX Potansiyel · 0-100</div>'+
              '<div class="lab2" style="color:var(--live)">gelişim potansiyeli yüksek</div>'+
              (p.pct!=null?'<div class="lab2">'+p.bucket+' sırası: <b>%'+p.pct+'</b></div>':'');
          }
          return '<div class="n">'+numSpan(p.overall,scoreColor(p.overall))+'</div><div class="lab">BSX Skoru · 0-100</div>'+(p.pct!=null?'<div class="lab2">'+p.bucket+' sırası: <b>%'+p.pct+'</b></div>':'');
        })()+
      '</div>'+
    '</div>'+tabs+
    '<div class="cols3 section sec-b" style="margin-top:38px">'+
      '<div><div class="panel-h">Statistiksel Profil — Radar</div><div id="radarbox">'+radarBlock(p)+'</div></div>'+
      '<div><div class="panel-h">En Benzer Oyuncular</div><div id="simlist"></div></div>'+
      '<div><div class="panel-h">Rol Uyumu — 32 Rol Sözlüğü</div><div id="rolbox" class="scrollpanel"></div></div>'+
    '</div>'+
    '<div class="section sec-a"><div class="panel-h">Oyun Modeli Uyumu</div><div class="mfit"><div id="mranks"></div><div id="mdetail"></div></div></div>'+
    '<div class="section sec-b" id="futurewrap"><div class="panel-h">Gelecekte Benzeyebileceği — Genç Profil Eşleşmesi</div><div id="futurelist"></div></div>'+
    '<div class="section sec-a" id="prospwrap"><div class="panel-h">Gelecekte Ona Benzeyebilecek Gençler</div><div id="prosplist"></div></div>'+
    '<div class="section sec-b"><div class="panel-h">Benzerlik Explorer — Tüm Adaylar</div><div id="expctrl"></div><div id="exlist"></div></div>';
  CUR=id; EXP={sort:'sim',ageMax:'',league:'',foot:'',cMax:'',wMax:''}; MODSEL=null; CMP=[id]; CMPBASE=id; RADD=[];
  SIMLVL=0; renderSim(p,5); renderRoles(p); renderModels(p); renderFuture(p); renderProsp(p); renderExplorer(p); animateCanums();
}
/* ---------- TÜM POZİSYONLAR: oyuncunun tüm bucket-girişlerini tek görünümde karşılaştır ---------- */
// pozisyondan bağımsız, tüm bucket'larda aynı isimlerle gelen ~12 ortak attribute (DB.meta.attr_order
// alt-kümesi) — mini-radar'ı üst üste bindirmek için ortak eksen seti gerekiyor, 28'in tamamı
// (attr_order) okunaksız olurdu.
const ALLPOS_ATTRS=['Hız','Hızlanma','Güç','Dayanıklılık','Çeviklik','İlk Kontrol','Pas','Vizyon','Top Kapma','Bitiricilik','Topsuz Alan','Karar Alma'];
function goAllPos(id){ history.pushState({allpos:id},""); setActiveTab('genel'); window.scrollTo(0,0); renderAllPositions(id); }
function renderAllPositions(id){
  const p0=BYID[id]; if(!p0){document.getElementById('app').innerHTML='<div class="empty">Oyuncu bu veri setinde yok.</div>';return;}
  const {grp,ordered,bestB}=groupBuckets(p0);
  const ord=DB.meta.attr_order||[];
  const axes=ALLPOS_ATTRS.filter(a=>ord.includes(a));
  const rows=ordered.map((b,i)=>{
    const q=grp.buckets[b];
    const bestRol=q.ROL&&q.ROL._en_iyi;
    const rolTxt=bestRol?(ROLAD[bestRol]||bestRol)+' · %'+((q.ROL[bestRol]||{}).uyum??'—'):'—';
    return {b,q,color:CMPCOL[i%CMPCOL.length],rolTxt};
  });
  const tableRows=rows.map(r=>'<tr'+(r.b===p0.bucket?' class="cur"':'')+'>'+
    '<td><span class="posdot" style="background:'+r.color+'"></span>'+r.b+' · '+BUCK_TR[r.b]+(r.b===bestB?' ★':'')+'</td>'+
    '<td class="num" style="color:'+scoreColor(r.q.overall)+'">'+(r.q.overall??'—')+'</td>'+
    '<td class="num">'+(r.q.pct!=null?'%'+r.q.pct:'—')+'</td>'+
    '<td>'+esc(r.rolTxt)+'</td>'+
    '<td><button class="swapb" onclick="go(\''+r.q.id+'\')">profili aç →</button></td>'+
    '</tr>').join('');
  const series=rows.map(r=>{
    const apArr=r.q.ap||[];
    return {name:r.b, color:r.color, pcts:axes.map(a=>{const idx=ord.indexOf(a); return idx>=0?apArr[idx]:null;})};
  });
  document.getElementById('app').innerHTML=
    '<a class="back" onclick="navBack()">← geri</a>'+
    '<div class="phead"><div class="pid"><h2>'+esc(p0.name)+'</h2>'+
      '<div class="pmeta"><b>'+tlink(p0.team)+'</b> · '+esc(leagueShort(p0.league))+' · <span style="color:var(--live)">Tüm Pozisyonlar ('+ordered.length+')</span></div>'+
    '</div></div>'+
    '<div class="section" style="margin-top:0;padding-top:0;border-top:none">'+
      '<table class="allpostbl"><thead><tr><th>Pozisyon</th><th class="num">BSX Skoru</th><th class="num">Kova sırası</th><th>En iyi rol</th><th></th></tr></thead><tbody>'+tableRows+'</tbody></table>'+
    '</div>'+
    '<div class="section"><div class="panel-h">Pozisyonlar Arası Profil Karşılaştırması</div>'+
      '<div class="cmpradar">'+radarMulti(axes.map(a=>BS_LABEL[a]||a),series)+'</div>'+
      '<div class="radleg">'+rows.map(r=>'<span class="lg"><i class="d" style="background:'+r.color+'"></i>'+r.b+'</span>').join('')+'</div>'+
      '<div class="rnote">Eksenler oyuncunun kova-içi percentile\'ı — aynı ham yetenek, farklı pozisyon havuzunda farklı sıraya denk gelebilir.</div>'+
    '</div>';
}
function chip(k,v){return '<span class="chip"><span class="k">'+k+'</span><span class="v">'+esc(String(v))+'</span></span>';}
function tlink(team){ if(!team) return '—'; return '<span class="tlink" data-t="'+esc(team)+'" onclick="event.stopPropagation();goTeam(this.dataset.t)">'+esc(team)+'</span>'; }

const ROLAD={"KL_GK":"Klasik Kaleci","CIZGI":"Çizgi Kalecisi","SW":"Sweeper Kaleci","KL_CB":"Klasik Stoper","BPD":"Topla Oynayan Stoper","KEN":"Kenar Stoper","CAK":"Çakılı Stoper","KL_FB":"Klasik Bek","STOP":"Stoperleşen Bek","WB":"Kanat Bek","IWB":"İçe Kat Eden Bek","DM_KL":"Defansif Orta Saha","DLP":"Derin Oyun Kurucu","ANCHOR":"Alan Kaplayan OS","DIN":"Dinamik Oyun Kurucu","SAVAS":"Savaşçı Orta Saha","CM_KL":"Merkez Orta Saha","B2B":"Box-to-Box","MEZ":"Mezzala","AM_KL":"Ofansif Orta Saha","AP":"Ofansif Oyun Kurucu","SHA":"Gizli Forvet","TRE":"Serbest Oyuncu","W_KL":"Klasik Kanat","IF":"Kanat Forvet","IW":"İç Kanat Oyuncusu","WM":"Çalışkan Kanat","9":"9 Numara","F9":"Sahte 9","DLF":"Yardımcı Forvet","POA":"Fırsatçı Forvet","TF":"Pivot Forvet"};
function renderRoles(p){
  const box=document.getElementById('rolbox'); if(!box)return;
  const R=p.ROL;
  if(!R){ box.innerHTML='<div class="empty">Bu oyuncu için rol skoru yok (veri kapsamı yetersiz).</div>'; return; }
  const keys=Object.keys(R).filter(k=>!k.startsWith('_'));
  keys.sort((a,b)=>(R[b].uyum||0)-(R[a].uyum||0));
  const rows=keys.map(k=>{
    const r=R[k]; const parent=(k==='9');
    const nm=ROLAD[k]||k;
    const uy=parent?null:r.uyum;
    const bar=uy!=null?'<div class="rolbar"><i style="width:'+uy+'%"></i></div>':'<div class="rolbar par">ebeveyn rol — Sıralama esas</div>';
    const tag=(k===R._en_iyi)?' <span class="rolbest">EN İYİ</span>':'';
    const eb=(parent&&R._ebeveyn_etiket)?' <span class="roltend">eğilim: '+(ROLAD[R._ebeveyn_etiket]||R._ebeveyn_etiket)+'</span>':'';
    return '<div class="rolrow"><div class="rolnm">'+nm+tag+eb+'</div>'+bar+
      '<div class="rolv">'+(uy!=null?('%'+uy):'—')+'</div>'+
      '<div class="rolv" title="Rol-özel BSX Skoru">'+(r.ca!=null?r.ca:'—')+'</div>'+
      '<div class="rolv" title="Sıralama skoru">'+(r.sira!=null?r.sira:'—')+'</div></div>';
  }).join('');
  box.innerHTML='<div class="rolhead"><span></span><span></span><span>Uyum</span><span>BSX_rol</span><span>Sıra</span></div>'+rows+
    '<div class="rnote" style="margin-top:10px">Uyum% = rol kimliği (havuz medyanı 50). BSX_rol = o roldeki BSX Skoru seviyesi. Sıra = "rolün en iyisi" skoru (seviye × şekil kapısı).</div>';
}
function fmtDob(s){ if(!s)return''; const m=String(s).match(/(\d{4})-(\d{2})-(\d{2})/); return m?m[3]+'.'+m[2]+'.'+m[1]:''; }
function fmtP90(v){ if(v==null||v==="") return "—"; v=+v; const a=Math.abs(v); if(a<10) return v.toFixed(2); if(a<100) return v.toFixed(1); return Math.round(v).toString(); }
let RADD=[];   // kullanıcının eklediği metrik anahtarları (max 3)
function axFrac(val,mn,mx,inv){ if(val==null||mn==null||mx==null)return 0; const r=mx-mn; if(r<=1e-9)return val>0?1:0; let fr=(val-mn)/r; if(inv)fr=1-fr; return Math.max(0,Math.min(1,fr)); }
let RADMODE='p90';   // 'p90' = 90 dk başına, 'mac' = maç başına, 'tot' = toplam (sezon)
function setRadMode(m){ RADMODE=m; const box=document.getElementById('radarbox'); if(box&&window.RADP)box.innerHTML=radarBlock(window.RADP); }
// rv değerleri PER-90. modlar: p90=v, toplam=v*dk/90, maç başına=toplam/maç
function radMult(p){
  const mins=p.minutes||0, mac=p.matches||0;
  if(RADMODE==='tot') return mins/90;
  if(RADMODE==='mac') return mac>0 ? (mins/90)/mac : 0;   // (toplam)/maç = v*(dk/90)/maç
  return 1;                                                // per90
}
function radConv(val,p){ if(val==null)return val; return val*radMult(p); }
function radarBlock(p){
  window.RADP=p;
  const b=p.bucket, L=p.league;
  const avg=(((DB.meta.avg||{})[b]||{})[L])||{rv:{},mx:{},mn:{}};
  const invset=new Set(((DB.meta.buckets[b]||{}).inv)||[]);
  const K=radMult(p);   // eksen min/max da aynı çarpanla ölçeklenir
  let ents=Object.keys(p.radar).map(name=>{
    const val=radConv((p.rv||{})[name],p), mx=(avg.mx||{})[name]*K, mn=(avg.mn||{})[name]*K, inv=invset.has(name);
    const aval=(avg.rv||{})[name]!=null?(avg.rv||{})[name]*K:null;
    return {name, raw:val, pf:axFrac(val,mn,mx,inv), af:axFrac(aval,mn,mx,inv), aval, rank:(p.rank||{})[name],
            pct:(p.radar||{})[name], pctL:(p.radarL||{})[name], added:false};
  });
  const xsc=(((DB.meta.xscale||{})[b]||{})[L])||{};
  RADD.forEach(key=>{ const sc=xsc[key]; const val=radConv((p.xm||{})[key],p); const lab=(DB.meta.xcat||{})[key]||key;
    if(sc){ ents.push({name:lab, raw:val, pf:axFrac(val,sc[0]*K,sc[1]*K,false), af:axFrac(sc[2]*K,sc[0]*K,sc[1]*K,false), aval:sc[2]*K, rank:null, added:true, key}); } });
  // eklenebilir metrik seçenekleri (radar dışı)
  const cat=DB.meta.xcat||{};
  const opts=Object.keys(cat).filter(k=>!RADD.includes(k)).sort((x,y)=>cat[x].localeCompare(cat[y],'tr'))
    .map(k=>'<option value="'+k+'">'+esc(cat[k])+'</option>').join('');
  const addCtl = RADD.length<3
    ? '<div class="radadd"><select id="radmsel"><option value="">+ metrik ekle…</option>'+opts+'</select><button onclick="addRadarMetric()">ekle</button></div>'
    : '<div class="radadd"><span style="color:var(--faint);font-size:12px">maks. 3 ek metrik</span></div>';
  const chipsAdded = RADD.map(k=>'<span class="rmchip">'+esc(cat[k]||k)+' <b onclick="removeRadarMetric(\''+k+'\')">✕</b></span>').join('');
  const macDis = (p.matches||0)>0 ? '' : ' disabled title="maç sayısı yok"';
  const modeSw='<div class="radmode">'+
    '<button class="rmb '+(RADMODE==='p90'?'on':'')+'" onclick="setRadMode(\'p90\')">90 dk başına</button>'+
    '<button class="rmb '+(RADMODE==='mac'?'on':'')+'"'+macDis+' onclick="setRadMode(\'mac\')">Maç başına</button>'+
    '<button class="rmb '+(RADMODE==='tot'?'on':'')+'" onclick="setRadMode(\'tot\')">Toplam</button></div>';
  const mins='<div class="radmins">Oynanan süre: <b>'+(p.minutes!=null?Math.round(p.minutes).toLocaleString('tr')+' dk':'—')+'</b>'+
    (p.matches!=null?' <span style="color:var(--faint)">· '+Math.round(p.matches)+' maç ('+(p.minutes&&p.matches?Math.round(p.minutes/p.matches):'—')+' dk/maç)</span>':'')+'</div>';
  const modeLbl = RADMODE==='tot'?'sezon toplamı':(RADMODE==='mac'?'maç başına':'90 dk başına');
  const head='<div class="radhead"><div class="radttl">'+esc(leagueShort(L))+' · '+b+' · '+modeLbl+' · eksen tepesi = ligde en yüksek</div>'+mins+'</div>'+modeSw;
  const leg='<div class="radleg"><span class="lg"><i class="d dp"></i>Oyuncu</span><span class="lg"><i class="d da"></i>Lig ort. (pozisyon)</span></div>';
  const tbl='<div class="axisval avg4"><div class="k" style="color:var(--mut)">Metrik</div><div class="v" style="color:var(--rad-p)">Oyuncu</div><div class="v" style="color:var(--rad-a)">Lig ort.</div><div class="v" style="color:var(--mut)">Poz%/Lig%</div>'+
    ents.map(e=>'<div class="k">'+esc(e.name)+(e.added?' <span style="color:var(--faint)">+</span>':'')+'</div><div class="v" style="color:var(--rad-p)">'+fmtP90(e.raw)+(e.rank?' <span class="vp">('+e.rank[0]+'/'+e.rank[1]+')</span>':'')+'</div><div class="v" style="color:var(--rad-a)">'+fmtP90(e.aval)+'</div><div class="v" style="color:var(--mut);font-size:11px">'+(e.pct!=null?e.pct:'—')+'<span style="color:var(--faint)"> / </span>'+(e.pctL!=null?e.pctL:'—')+'</div>').join('')+'</div>';
  return head+'<div class="radar-wrap">'+radarSVG(ents)+'</div>'+leg+
    (chipsAdded?'<div class="rmchips">'+chipsAdded+'</div>':'')+addCtl+
    '<div id="radarval" class="radarval">Eksene dokun → değer ve lig sırası</div>'+
    '<div class="rnote">Yeşil = oyuncu, altın = kendi ligindeki pozisyon ortalaması. '+
    (RADMODE==='tot'?'Toplam: per90 × oynanan 90&#39;lık dilim.':(RADMODE==='mac'?'Maç başına: sezon toplamı ÷ oynanan maç sayısı.':'90 dk başına: her 90 dakikaya normalize.'))+' Poz%/Lig% moddan bağımsızdır.</div>'+
    tbl;
}
function addRadarMetric(){ const sel=document.getElementById('radmsel'); if(!sel||!sel.value)return; if(RADD.length>=3)return; if(!RADD.includes(sel.value))RADD.push(sel.value); const box=document.getElementById('radarbox'); if(box&&window.RADP)box.innerHTML=radarBlock(window.RADP); }
function removeRadarMetric(k){ RADD=RADD.filter(x=>x!==k); const box=document.getElementById('radarbox'); if(box&&window.RADP)box.innerHTML=radarBlock(window.RADP); }
function radarSVG(ents){
  window.RADENTS=ents;
  // cx/cy/R viewBox kenarına göre: etiket yarıçapı (R+18) ile kenar arasında ~85px marj
  // bırakılıyor ki kısaltılmış eksen adları (bkz. wordTrunc) komşu etiketlerle çakışmasın/taşmasın.
  const N=ents.length, cx=220, cy=200, R=115;
  const ang=i=>(-Math.PI/2)+i*2*Math.PI/N;
  const pt=(i,r)=>[cx+Math.cos(ang(i))*r, cy+Math.sin(ang(i))*r];
  const defs='<defs><radialGradient id="radbg" cx="50%" cy="46%" r="68%"><stop offset="0%" stop-color="#171B22"/><stop offset="60%" stop-color="#12151A"/><stop offset="100%" stop-color="#0D0F12"/></radialGradient></defs>';
  let outer=[]; for(let i=0;i<N;i++) outer.push(pt(i,R).map(n=>n.toFixed(1)).join(','));
  let bg='<polygon points="'+outer.join(' ')+'" fill="url(#radbg)" stroke="rgba(255,255,255,.10)" stroke-width="1"/>';
  let rings=''; [.25,.5,.75].forEach(f=>{ let q=[]; for(let i=0;i<N;i++)q.push(pt(i,R*f).map(n=>n.toFixed(1)).join(',')); rings+='<polygon points="'+q.join(' ')+'" fill="none" stroke="rgba(255,255,255,.06)" stroke-width="1"/>'; });
  let axes=''; for(let i=0;i<N;i++){ const [x,y]=pt(i,R); axes+='<line x1="'+cx+'" y1="'+cy+'" x2="'+x.toFixed(1)+'" y2="'+y.toFixed(1)+'" stroke="rgba(255,255,255,.05)" stroke-width="1"/>'; }
  // "taktik tahtası" kalitesinde imza an: veri poligonu, hero'daki çizgi-animasyonuyla aynı
  // teknikle (pathLength=1 + stroke-dashoffset) sıfırdan çizilir; oyuncu çizgisi lig ortalamasından
  // biraz gecikmeli gelir ki göz önce bağlamı (lig ort.), sonra öne çıkanı (oyuncu) görsün.
  function poly(key,fill,stroke,delay){ let q=[]; for(let i=0;i<N;i++){const fr=ents[i][key]||0; q.push(pt(i,R*fr).map(n=>n.toFixed(1)).join(','));} return '<polygon points="'+q.join(' ')+'" fill="'+fill+'" stroke="'+stroke+'" stroke-width="1.8" stroke-linejoin="round" pathLength="1" class="radardraw" style="animation-delay:'+delay+'s"/>'; }
  let polys=poly('af','rgba(217,164,65,.08)','var(--rad-a)',0)+poly('pf','rgba(124,147,184,.16)','var(--rad-p)',.35);
  let dots='',vlab='',names='',hit='';
  for(let i=0;i<N;i++){
    const a=ang(i); const anc=Math.abs(Math.cos(a))<.3?'middle':(Math.cos(a)>0?'start':'end');
    const [lx,ly]=pt(i,R+18); const full=ents[i].name; const short=wordTrunc(full,16);
    names+='<text x="'+lx.toFixed(1)+'" y="'+(ly+3).toFixed(1)+'" fill="rgba(231,233,236,.68)" font-size="9" text-anchor="'+anc+'" font-family="var(--ui)" style="cursor:pointer" onclick="radarTap('+i+')"><title>'+esc(full)+'</title>'+esc(short)+(ents[i].added?' +':'')+'</text>';
    hit+='<circle cx="'+lx.toFixed(1)+'" cy="'+ly.toFixed(1)+'" r="15" fill="transparent" style="cursor:pointer" onclick="radarTap('+i+')"/>';
    const af=ents[i].af||0; const [ax,ay]=pt(i,R*af); dots+='<circle cx="'+ax.toFixed(1)+'" cy="'+ay.toFixed(1)+'" r="2.3" fill="var(--rad-a)"/>';
    const pf=ents[i].pf||0; const [px,py]=pt(i,R*pf); dots+='<circle cx="'+px.toFixed(1)+'" cy="'+py.toFixed(1)+'" r="2.7" fill="var(--rad-p)" style="cursor:pointer" onclick="radarTap('+i+')"/>';
    const [tx,ty]=pt(i,R*pf+11); vlab+='<text x="'+tx.toFixed(1)+'" y="'+(ty+3).toFixed(1)+'" fill="rgba(231,233,236,.92)" font-size="8.2" text-anchor="middle" font-family="var(--mono)">'+fmtP90(ents[i].raw)+'</text>';
  }
  return '<svg class="radar" viewBox="0 0 440 400">'+defs+bg+rings+axes+polys+dots+vlab+names+hit+'</svg>';
}
function radarTap(i){ const e=(window.RADENTS||[])[i]; if(!e)return; const el=document.getElementById('radarval'); if(!el)return;
  el.innerHTML='<b style="color:var(--rad-p)">'+esc(e.name)+'</b>: '+fmtP90(e.raw)+' <span style="color:var(--mut)">p90</span>'+(e.rank?' · ligde <b>'+e.rank[0]+'/'+e.rank[1]+'</b>':'')+' · lig ort '+fmtP90(e.aval)+(e.pct!=null?' · poz-içi <b>%'+e.pct+'</b>':'')+(e.pctL!=null?' · lig-içi <b>%'+e.pctL+'</b>':''); }

let SIMLVL=0;  // 0 = tümü, aksi halde |ΔCA|<=SIMLVL filtresi
function setSimLvl(v){ SIMLVL=v; renderSim(BYID[CUR], SIM_LIMIT||5); }
let SIM_LIMIT=5;
function renderSim(p,limit){
  SIM_LIMIT=limit;
  const box=document.getElementById('simlist');
  let sims=(p.similar||[]).filter(s=>BYID[s.id]);
  if(SIMLVL>0) sims=sims.filter(s=>Math.abs(s.dca||0)<=SIMLVL);
  const ctrl='<div class="simlvl">Seviye filtresi: '+
    [['Tümü',0],['±5',5],['±10',10],['±15',15]].map(([lbl,v])=>
      '<button class="lvlb '+(SIMLVL===v?'on':'')+'" onclick="setSimLvl('+v+')">'+lbl+'</button>').join('')+'</div>';
  const shown=sims.slice(0,limit).map((s,i)=>{ const q=BYID[s.id];
    const dca=s.dca||0; const dcaTxt=dca===0?'=':(dca>0?'+'+dca:''+dca);
    return '<div class="sim" onclick="go(\''+s.id+'\')"><div class="srank num">'+(i+1)+'</div>'+
      '<div class="sinfo"><div class="snm">'+esc(q.name)+'</div><div class="ssub">'+tlink(q.team)+' · '+esc(leagueShort(q.league))+'</div></div>'+
      '<div class="sov" style="color:'+scoreColor(q.overall)+'" title="BSX Skoru farkı '+dcaTxt+'">'+(q.overall??'—')+'<span class="dca">'+dcaTxt+'</span></div></div>';
  }).join('');
  box.innerHTML = ctrl + (shown || '<div class="empty">Bu seviye aralığında benzer oyuncu yok.</div>');
  if(sims.length>limit) box.innerHTML+='<button class="morebtn" onclick="renderSim(BYID[\''+p.id+'\'],'+sims.length+')">Daha fazla göster ('+(sims.length-limit)+')</button>';
}

/* ---------- B: gelecekte benzeyebileceği ---------- */
let CUR=null, EXP={sort:'sim',ageMax:'',league:'',foot:'',cMax:'',wMax:''};
function cands(p){ return (p.similar||[]).map(s=>({s,q:BYID[s.id]})).filter(x=>x.q); }

/* Rol uyumu rozeti: aday, HEDEFİN en iyi rolünde kaç uyum alıyor?
   >=70 uyumlu · 40-69 kısmen · <40 rol profili çok farklı (uyarı). */
function rolFitBadge(s, p){
  if(s==null || s.ru==null) return '';
  const tgt=(p.ROL&&p.ROL._en_iyi)?(ROLAD[p.ROL._en_iyi]||p.ROL._en_iyi):null;
  const own=s.rk?(ROLAD[s.rk]||s.rk):null;
  if(!tgt) return '';
  if(s.ru>=70) return '<div class="rfit ok">rol uyumu %'+s.ru+' · '+esc(tgt)+'</div>';
  if(s.ru>=40) return '<div class="rfit mid">rol uyumu %'+s.ru+' · kısmen '+esc(tgt)+
    (own?' <span class="ro">(asıl: '+esc(own)+')</span>':'')+'</div>';
  return '<div class="rfit bad">rol profili çok farklı — %'+s.ru+' '+esc(tgt)+
    (own?' <span class="ro">(asıl: '+esc(own)+')</span>':'')+'</div>';
}
function renderFuture(p){
  const box=document.getElementById('futurelist');
  const wrap=document.getElementById('futurewrap');
  const c=(p.future||[]).map(s=>({s,q:BYID[s.id]})).filter(x=>x.q)
    .sort((a,b)=>((b.s.ru??50)>=40)-((a.s.ru??50)>=40));
  const isWK=(p.age!=null && p.age<23);
  // wonderkid değilse bölümü tümden gizle
  if(wrap){ wrap.style.display = (isWK && c.length) ? '' : 'none'; }
  if(!isWK || !c.length){ box.innerHTML=''; return; }
  box.innerHTML='<div class="futnote">Bu genç oyuncunun <b>bugünkü öne çıkan özellik profiline</b> göre, aynı mevkide, ondan ileri seviyede ve boyca uyumlu örnekler. Gelişirse bu tip oyunculara benzeyebilir:</div>'+
    '<div class="frow">'+c.map(x=>{
    const q=x.q;
    return '<article class="fcard2" tabindex="0" onkeydown="kb(event)" onclick="go(\''+q.id+'\')"><div class="top"><span class="devbadge">'+(q.age!=null?Math.round(q.age)+' yaş':'—')+'</span><span style="font-family:var(--kit);font-size:18px;color:'+scoreColor(q.overall)+'">'+(q.overall??'—')+'</span></div>'+
      '<div class="nm">'+esc(q.name)+'</div><div class="sub">'+tlink(q.team)+' · '+esc(leagueShort(q.league))+'</div>'+
      '<div class="mini">profil benzerliği %'+x.s.sim.toFixed(0)+'</div>'+rolFitBadge(x.s,p)+'</article>';
  }).join('')+'</div>';
}

/* ---------- B2: gelecekte ona benzeyebilecek gençler (tersine, yaş>=26) ---------- */
function renderProsp(p){
  const box=document.getElementById('prosplist');
  const wrap=document.getElementById('prospwrap');
  const c=(p.prosp||[]).map(s=>({s,q:BYID[s.id]})).filter(x=>x.q)
    .sort((a,b)=>((b.s.ru??50)>=40)-((a.s.ru??50)>=40));
  const isEst=(p.age!=null && p.age>=26);
  if(wrap){ wrap.style.display=(isEst && c.length)?'':'none'; }
  if(!isEst || !c.length){ box.innerHTML=''; return; }
  box.innerHTML='<div class="futnote">Bu oyuncunun <b>öne çıkan özellik profiline</b> benzeyen, aynı mevkide ve henüz bu seviyeye ulaşmamış genç adaylar. Gelişirlerse ona benzeyebilirler:</div>'+
    '<div class="frow">'+c.map(x=>{
    const q=x.q;
    return '<article class="fcard2" tabindex="0" onkeydown="kb(event)" onclick="go(\''+q.id+'\')"><div class="top"><span class="devbadge">'+(q.age!=null?Math.round(q.age)+' yaş':'—')+'</span><span style="font-family:var(--kit);font-size:18px;color:'+scoreColor(q.overall)+'">'+(q.overall??'—')+'</span></div>'+
      '<div class="nm">'+esc(q.name)+'</div><div class="sub">'+tlink(q.team)+' · '+esc(leagueShort(q.league))+'</div>'+
      '<div class="mini">profil benzerliği %'+x.s.sim.toFixed(0)+'</div>'+rolFitBadge(x.s,p)+'</article>';
  }).join('')+'</div>';
}
function renderExplorer(p){
  const cs=cands(p);
  const ligs=[...new Set(cs.map(x=>leagueShort(x.q.league)).filter(Boolean))].sort();
  const foots=[...new Set(cs.map(x=>x.q.foot).filter(Boolean))].sort();
  const opt=(arr,sel)=>'<option value="">Tümü</option>'+arr.map(v=>'<option '+(v===sel?'selected':'')+'>'+esc(v)+'</option>').join('');
  document.getElementById('expctrl').innerHTML=
   '<div class="filters">'+
    '<div class="fld"><label>Sırala</label><select onchange="EXP.sort=this.value;listExp()">'+
      ['sim|Benzerlik','ov|FM Skoru','age|Yaş (genç)','val|Değer','wage|Maaş (düşük)','contract|Sözleşme (yakın)'].map(o=>{const[v,t]=o.split("|");return '<option value="'+v+'" '+(EXP.sort===v?'selected':'')+'>'+t+'</option>';}).join('')+'</select></div>'+
    '<div class="fld"><label>Yaş ≤</label><input type="number" min="15" max="45" placeholder="—" value="'+EXP.ageMax+'" oninput="EXP.ageMax=this.value;listExp()"></div>'+
    '<div class="fld"><label>Sözleşme bitiş ≤</label><input type="number" min="2026" max="2035" placeholder="≥2026" value="'+EXP.cMax+'" oninput="EXP.cMax=this.value;listExp()"></div>'+
    '<div class="fld"><label>Net maaş ≤ (€M/yıl)</label><input type="number" min="0" step="0.5" placeholder="—" value="'+EXP.wMax+'" oninput="EXP.wMax=this.value;listExp()"></div>'+
    '<div class="fld"><label>Lig</label><select onchange="EXP.league=this.value;listExp()">'+opt(ligs,EXP.league)+'</select></div>'+
    (foots.length?'<div class="fld"><label>Ayak</label><select onchange="EXP.foot=this.value;listExp()">'+opt(foots,EXP.foot)+'</select></div>':'')+
    '<button class="rst" onclick="EXP={sort:\'sim\',ageMax:\'\',league:\'\',foot:\'\',cMax:\'\',wMax:\'\'};renderExplorer(BYID[CUR])">sıfırla</button>'+
   '</div>';
  listExp();
}
function fmtMoney(v){ if(v==null)return '—'; if(v>=1e6)return '€'+(v/1e6).toFixed(v>=1e7?0:1).replace('.0','')+'M'; if(v>=1e3)return '€'+Math.round(v/1e3)+'K'; return '€'+v; }
function listExp(){
  const p=BYID[CUR]; let c=cands(p);
  if(EXP.ageMax) c=c.filter(x=>x.q.age!=null && x.q.age<=+EXP.ageMax);
  if(EXP.cMax) c=c.filter(x=>x.q.cyear!=null && x.q.cyear<=+EXP.cMax);
  if(EXP.wMax) c=c.filter(x=>x.q.wage_eur!=null && x.q.wage_eur<=+EXP.wMax*1e6);
  if(EXP.league) c=c.filter(x=>leagueShort(x.q.league)===EXP.league);
  if(EXP.foot) c=c.filter(x=>x.q.foot===EXP.foot);
  const nz=(v)=>v==null?-Infinity:v, hi=(v)=>v==null?Infinity:v;
  if(EXP.sort==='sim') c.sort((a,b)=>b.s.sim-a.s.sim);
  else if(EXP.sort==='ov') c.sort((a,b)=>nz(b.q.overall)-nz(a.q.overall));
  else if(EXP.sort==='age') c.sort((a,b)=>hi(a.q.age)-hi(b.q.age));
  else if(EXP.sort==='val') c.sort((a,b)=>nz(b.q.value_eur)-nz(a.q.value_eur));
  else if(EXP.sort==='wage') c.sort((a,b)=>hi(a.q.wage_eur)-hi(b.q.wage_eur));
  else if(EXP.sort==='contract') c.sort((a,b)=>hi(a.q.cyear)-hi(b.q.cyear));
  c=c.slice(0,30);
  const box=document.getElementById('exlist');
  if(!c.length){ box.innerHTML='<div class="empty">Filtreye uyan aday yok — gevşet.</div>'; return; }
  box.innerHTML='<div class="excount num">'+c.length+' aday gösteriliyor</div>'+c.map((x,i)=>{
    const q=x.q;
    return '<div class="exrow" onclick="go(\''+q.id+'\')">'+
      '<div class="srank num">'+(i+1)+'</div>'+
      '<div class="exinfo"><div class="snm">'+esc(q.name)+'</div><div class="ssub">'+tlink(q.team)+' · '+esc(leagueShort(q.league))+' · söz '+(q.cyear??'—')+' · '+fmtMoney(q.wage_eur)+'/yıl</div></div>'+
      '<div class="exage">'+(q.age!=null?Math.round(q.age):'—')+'</div>'+
      '<div class="exval">'+fmtMoney(q.value_eur)+'</div>'+
      '<div class="exsim"><div class="sbar"><i style="width:'+x.s.sim.toFixed(0)+'%"></i></div><div class="spct">%'+x.s.sim.toFixed(1)+'</div></div>'+
      '<div class="exov" style="color:'+scoreColor(q.overall)+'">'+(q.overall??'—')+'</div></div>';
  }).join('');
}

/* ---------- MODÜL 2: Kadro Mühendisliği (sol/sağ granular) ---------- */
// slot = [label, elig[], x, y]
const FORMATIONS={
 '4-2-3-1':[['KL',['GK'],.5,.93],['SLB',['LB'],.11,.72],['SLMB',['CB'],.34,.78],['S\u011eMB',['CB'],.66,.78],['S\u011eB',['RB'],.89,.72],
   ['SDO',['DM','CM'],.37,.56],['S\u011eDO',['DM','CM'],.63,.56],['SLO',['LW'],.15,.36],['MOO',['AM'],.5,.40],['S\u011eO',['RW'],.85,.36],['SNT',['ST'],.5,.15]],
 '4-3-3':[['KL',['GK'],.5,.93],['SLB',['LB'],.11,.72],['SLMB',['CB'],.34,.78],['S\u011eMB',['CB'],.66,.78],['S\u011eB',['RB'],.89,.72],
   ['MDO',['DM'],.5,.58],['SLMO',['CM','AM'],.30,.45],['S\u011eMO',['CM','AM'],.70,.45],['SLK',['LW'],.15,.24],['SNT',['ST'],.5,.13],['S\u011eK',['RW'],.85,.24]],
 '4-4-2':[['KL',['GK'],.5,.93],['SLB',['LB'],.11,.72],['SLMB',['CB'],.34,.78],['S\u011eMB',['CB'],.66,.78],['S\u011eB',['RB'],.89,.72],
   ['SLO',['LW'],.13,.46],['SDO',['CM','DM'],.37,.50],['S\u011eDO',['CM','DM'],.63,.50],['S\u011eO',['RW'],.87,.46],['SLST',['ST'],.37,.16],['S\u011eS',['ST'],.63,.16]],
 '3-5-2':[['KL',['GK'],.5,.93],['SLMB',['CB'],.28,.79],['STP',['CB'],.5,.82],['S\u011eMB',['CB'],.72,.79],['SLB',['LB','LW'],.10,.50],['S\u011eB',['RB','RW'],.90,.50],
   ['SDO',['DM','CM'],.32,.50],['MO',['CM','AM'],.5,.40],['S\u011eDO',['DM','CM'],.68,.50],['SLST',['ST'],.38,.15],['S\u011eS',['ST'],.62,.15]],
};
const CPOS2B={'KL':'GK','STP':'CB','S\u011eMB':'CB','SLMB':'CB','MB':'CB','S\u011eB':'RB','S\u011eKB':'RB','SLB':'LB','SLKB':'LB',
 'MDO':'DM','SDO':'DM','S\u011eDO':'DM','MO':'CM','SLMO':'CM','S\u011eMO':'CM','MOO':'AM','SLOO':'AM','S\u011eOO':'AM',
 'S\u011eO':'RW','S\u011eK':'RW','SLO':'LW','SLK':'LW','SNT':'ST','S\u011eS':'ST','SLST':'ST','SLF':'ST','S\u011eF':'ST','OF':'ST'};
let SQ=null;
const lastN=n=>(n||'').split(' ').slice(-1)[0];

function teamModel(t){
  const byN={};
  DB.players.filter(p=>p.team===t).forEach(p=>{
    const g=byN[p.name]||(byN[p.name]={name:p.name,pos:(p.pos||[]).slice(),ca:p.ca,ov:p.overall||0,bestId:p.id,bucket:p.bucket,cpos:p.cpos,best:p.best,kit:p.kit,ids:{}});
    g.ids[p.bucket]=p.id;   // her pozisyon kovası için o oyuncunun entry id'si
    if((p.overall||0)>=g.ov){g.ov=p.overall||0;g.bestId=p.id;g.pos=(p.pos||[]).slice();g.bucket=p.bucket;g.cpos=p.cpos;g.best=p.best;g.kit=p.kit;}  // en iyi mevki sırası
    if(p.ca!=null)g.ca=p.ca;
  });
  return Object.values(byN);
}
// slotun kova(lar)ına en uygun entry id'si: önce slot koduna denk gelen kova, yoksa bestId
function slotEntryId(p,slotElig,slotCode){
  const b=CPOS2B[slotCode];
  if(b && p.ids && p.ids[b]) return p.ids[b];
  for(const el of (slotElig||[])){ if(p.ids && p.ids[el]) return p.ids[el]; }
  return p.bestId;
}
function eligible(p,elig){ return (p.pos||[]).some(x=>elig.includes(x)); }
function assignXI(players,form){
  const slots=FORMATIONS[form], used=new Set(), xi={};
  const byCA=[...players].sort((a,b)=>(b.ca||0)-(a.ca||0));
  const put=(i,p)=>{ const sid=slotEntryId(p,slots[i][1],slots[i][0]); xi[i]={name:p.name,id:sid,ca:p.ca,ov:p.ov,kit:p.kit}; used.add(p.name); };
  // Pass 0: FC_Club position birebir slot koduyla (kul\u00fcb\u00fcn ger\u00e7ek dizili\u015fi)
  slots.forEach((s,i)=>{ const c=byCA.find(p=>!used.has(p.name)&&p.cpos===s[0]); if(c)put(i,c); });
  // Pass 0b: FC_Club position kova e\u015fle\u015fmesi (tarafl\u0131/detayl\u0131 kodlar CPOS2B ile kovaya iner)
  slots.forEach((s,i)=>{ if(xi[i])return; const c=byCA.find(p=>!used.has(p.name)&&CPOS2B[p.cpos]&&s[1].includes(CPOS2B[p.cpos])); if(c)put(i,c); });
  // Pass 1: veri-a\u00e7\u0131k pozisyon s\u0131ras\u0131 (FC_En \u0130yi -> FM s\u0131ras\u0131); veride yazmayan pozisyona atama yap\u0131lmaz
  byCA.forEach(p=>{
    if(used.has(p.name))return;
    for(const pos of (p.pos||[])){
      let placed=false;
      for(let i=0;i<slots.length;i++){
        if(xi[i]) continue;
        if(slots[i][1].includes(pos)){ put(i,p); placed=true; break; }
      }
      if(placed) break;
    }
  });
  // Pass 2: h\u00e2l\u00e2 bo\u015f slotlar\u0131 en iyi uygun oyuncuyla doldur (yine yaln\u0131z veri-a\u00e7\u0131k pozisyonlar)
  slots.forEach((s,i)=>{
    if(xi[i]) return;
    const c=byCA.find(p=>!used.has(p.name)&&eligible(p,s[1]));
    if(c) put(i,c);
  });
  // yedek: slot ba\u015f\u0131na kalan en iyi uygun
  const backup={};
  slots.forEach((s,i)=>{ const c=byCA.find(p=>!used.has(p.name)&&eligible(p,s[1])); if(c){backup[i]={name:c.name,id:slotEntryId(c,s[1],s[0]),ca:c.ca,ov:c.ov};used.add(c.name);} });
  const bench=byCA.filter(p=>!used.has(p.name)).slice(0,16).map(p=>({name:p.name,id:p.bestId,ca:p.ca,ov:p.ov,pos:p.pos,bucket:p.bucket,kit:p.kit}));
  return {xi,backup,bench};
}
function renderSquad(t){ SQ={team:t,form:'4-2-3-1',players:teamModel(t),sel:null,move:{},heat:false}; const r=assignXI(SQ.players,SQ.form); SQ.xi=r.xi; SQ.backup=r.backup; SQ.bench=r.bench; squadView(); }
function setForm(f){ SQ.form=f; SQ.move={}; const r=assignXI(SQ.players,SQ.form); SQ.xi=r.xi; SQ.backup=r.backup; SQ.bench=r.bench; SQ.sel=null; squadView(); }
function effPos(i){ const s=FORMATIONS[SQ.form][i]; const m=(SQ.move||{})[i]; return m?[m[0],m[1]]:[s[2],s[3]]; }
function toggleHeat(){ if(SQ)SQ.heat=!SQ.heat; squadView(); }
function _zP(){ const slots=FORMATIONS[SQ.form],P=[]; slots.forEach((s,i)=>{ if(SQ.xi[i])P.push(effPos(i)); }); return P; }
function _infl(cx,cy,P){ const AY=0.654,s2=0.0144; let t=0; for(const p of P){ const dx=cx-p[0],dy=(cy-p[1])*AY; t+=Math.exp(-(dx*dx+dy*dy)/s2); } return t; }
function zoneHeat(){
  const P=_zP(),C=6,R=8; let h='';
  for(let j=0;j<R;j++)for(let i=0;i<C;i++){ const I=_infl((i+.5)/C,(j+.5)/R,P);
    const st=I>=0.7?'zg':(I>=0.30?'zy':(I>=0.12?'zr':'zn'));
    h+='<div class="zcell '+st+'" style="left:'+(i/C*100).toFixed(2)+'%;top:'+(j/R*100).toFixed(2)+'%;width:'+(100/C).toFixed(3)+'%;height:'+(100/R).toFixed(3)+'%"></div>'; }
  return '<div class="zheat">'+h+'</div>';
}
function zoneWarn(){
  const P=_zP(); if(P.length<6) return '';
  const col=['Sol kanat','Merkez','Sağ kanat'], band=['ileri uç','ön orta saha','orta saha','arka bölge','derin bölge','kaleci'];
  const out=[];
  for(let zj=1;zj<=4;zj++){              // ileri uç(0) ve kaleci(5) hattı banner dışı
    for(let zi=0;zi<3;zi++){
      let s=0,n=0;
      for(let fj=0;fj<3;fj++)for(let fi=0;fi<2;fi++){ s+=_infl((zi*2+fi+.5)/6,(zj*3+fj+.5)/18,P); n++; }
      const I=s/n, thr=(zi===1?0.55:0.30);   // merkez sütun daha sıkı (boş kalmamalı)
      if(I<thr) out.push(col[zi]+' · '+band[zj]);
    }
  }
  if(!out.length) return '';
  return '<div class="zonewarn"><div class="zwh">⚠ ÇOK SIKINTILI BÖLGE — bu bölgeden sorumlu oyuncu yok</div><div class="zwl">'+out.map(z=>'<span>'+z+'</span>').join('')+'</div></div>';
}
function dragStart(e,src){ window.DRAG=src; if(e.dataTransfer){e.dataTransfer.effectAllowed='move';e.dataTransfer.setData('text','x');} }
function allowDrop(e){ e.preventDefault(); }
function dropSlot(e,to){ e.preventDefault(); e.stopPropagation(); const s=window.DRAG; window.DRAG=null; if(!s)return;
  if(s.t==='s'){ if(s.i===to)return; const a=SQ.xi[s.i], b=SQ.xi[to]; if(!a)return; SQ.xi[to]=a; if(b)SQ.xi[s.i]=b; else delete SQ.xi[s.i]; }
  else if(s.t==='b'){ const bp=SQ.bench[s.i]; if(!bp)return; const out=SQ.xi[to];
    SQ.xi[to]={name:bp.name,id:bp.id,ca:bp.ca,ov:bp.ov}; SQ.bench.splice(s.i,1);
    if(out){ const pl=SQ.players.find(p=>p.name===out.name)||{pos:[],bucket:null}; SQ.bench.unshift({name:out.name,id:out.id,ca:out.ca,ov:out.ov,pos:pl.pos,bucket:pl.bucket}); } }
  squadView();
}
function dropPitch(e){ e.preventDefault(); const s=window.DRAG; window.DRAG=null; if(!s||s.t!=='s')return;
  const pit=document.getElementById('pitch'); if(!pit)return; const rc=pit.getBoundingClientRect();
  let x=(e.clientX-rc.left)/rc.width, y=(e.clientY-rc.top)/rc.height;
  x=Math.max(0.04,Math.min(0.96,x)); y=Math.max(0.06,Math.min(0.96,y));
  SQ.move[s.i]=[x,y]; squadView();
}
function dropBench(e){ e.preventDefault(); const s=window.DRAG; window.DRAG=null; if(!s||s.t!=='s')return; const out=SQ.xi[s.i]; if(!out)return;
  const pl=SQ.players.find(p=>p.name===out.name)||{pos:[],bucket:null}; SQ.bench.unshift({name:out.name,id:out.id,ca:out.ca,ov:out.ov,pos:pl.pos,bucket:pl.bucket}); delete SQ.xi[s.i]; squadView(); }
function squadView(){
  const slots=FORMATIONS[SQ.form]; let chips='';
  slots.forEach((s,i)=>{ const st=SQ.xi[i], bu=SQ.backup[i]; const xy=effPos(i);
    chips+='<div class="pchip '+(st?'':'empty')+(SQ.sel==i?' sel':'')+((SQ.move||{})[i]?' moved':'')+'" draggable="'+(st?'true':'false')+'" ondragstart="dragStart(event,{t:\'s\',i:'+i+'})" ondragover="allowDrop(event)" ondrop="dropSlot(event,'+i+')" style="left:'+(xy[0]*100)+'%;top:'+(xy[1]*100)+'%" onclick="openSlot('+i+')">'+
      '<div class="plabel">'+s[0]+'</div>'+
      '<div class="dwrap"><div class="disc">'+(st?(st.kit!=null?st.kit:esc(lastN(st.name).slice(0,2).toUpperCase())):'+')+'</div>'+
      (st?'<div class="rbadge" style="background:'+scoreColor(st.ov)+'">'+(st.ca??'—')+'</div>':'')+'</div>'+
      '<div class="nm">'+(st?esc(lastN(st.name)):'<span class=pos>'+s[1][0]+'</span>')+'</div>'+
      (bu?'<div class="bk">'+esc(lastN(bu.name))+' · '+(bu.ca??'—')+'</div>':'')+'</div>';
  });
  // kategorize dikey yedek (GK -> ST)
  const BORD=['GK','CB','RB','LB','DM','CM','AM','RW','LW','ST'], BLBL={GK:'Kaleciler',CB:'Stoperler',RB:'Sa\u011f Bekler',LB:'Sol Bekler',DM:'Defansif Orta',CM:'Merkez Orta',AM:'Ofansif Orta',RW:'Sa\u011f Kanat',LW:'Sol Kanat',ST:'Forvetler'};
  const byB={}; SQ.bench.forEach((p,idx)=>{ (byB[p.bucket]=byB[p.bucket]||[]).push({p,idx}); });
  const benchH = BORD.filter(b=>byB[b]&&byB[b].length).map(b=>
    '<div class="bcat"><div class="bcath">'+BLBL[b]+'</div>'+byB[b].map(o=>
      '<div class="brow" draggable="true" ondragstart="dragStart(event,{t:\'b\',i:'+o.idx+'})" onclick="go(\''+o.p.id+'\')"><div class="bn">'+esc(o.p.name)+'</div><div class="bs2">'+(o.p.pos||[]).join('/')+' · BSX Skoru <b style="color:'+scoreColor(o.p.ov)+'">'+(o.p.ca??'—')+'</b></div></div>'
    ).join('')+'</div>'
  ).join('') || '<div class="empty">yedek yok</div>';

  document.getElementById('app').innerHTML=
   '<a class="back" onclick="navBack()">← geri</a>'+
   '<div class="phead" style="padding-bottom:16px"><div class="pid"><h2>'+esc(SQ.team)+'</h2>'+
     '<div class="pmeta">otomatik ilk 11 · FC kulüp dizilişi esas · '+SQ.players.length+' oyuncu · rozet = BSX Skoru, disk = forma no</div></div>'+
     (function(){ const tr=(DB.meta.team_ratings||{})[SQ.team]; return tr?'<div class="score"><div class="n" style="color:'+scoreColor(tr.rating)+'">'+(tr.partial?'~':'')+tr.rating+'</div><div class="lab">Takım Reytingi</div><div class="lab2">'+(tr.partial?'kısmi kadro ('+tr.squad+')':'en iyi 11 + derinlik')+'</div></div>':''; })()+
   '</div>'+
   '<div class="fsel" style="margin-bottom:14px">'+Object.keys(FORMATIONS).map(f=>'<button class="fbtn '+(f===SQ.form?'on':'')+'" onclick="setForm(\''+f+'\')">'+f+'</button>').join('')+
     '</div>'+
   '<div class="squad"><div><div class="pitch" id="pitch" ondragover="allowDrop(event)" ondrop="dropPitch(event)">'+
     '<div class="ln mid"></div><div class="ln circ"></div><div class="ln boxT"></div><div class="ln boxB"></div>'+chips+'</div></div>'+
   '<div><div class="panel-h">Yedek Kulübesi <span style="color:var(--faint);font-weight:400;font-size:12px">(buraya bırak → 11\'den çıkar)</span></div>'+
     '<div class="benchcol" ondragover="allowDrop(event)" ondrop="dropBench(event)">'+benchH+'</div>'+
     '<div class="panel-h" style="margin-top:22px">Nasıl çalışır</div><div style="color:var(--mut);font-size:13px;line-height:1.6">11, önce <b>FC kulüp dizilişine</b> (FC_Club position) göre kurulur; boş kalan slotlara oyuncular veri-açık pozisyonlarına göre yerleşir. Sahada bir oyuncuyu başka oyuncunun üstüne sürükle → <b>yer değişir</b>; boş bir alana sürükle → o <b>pozisyon oraya taşınır</b> (ör. merkez orta sahayı yukarı çek). Yedeği sahaya, sahadakini kulübeye sürükleyebilirsin. Slota dokun → alternatifler + transfer önerileri.</div></div></div>'+
   squadGapHTML();
}
/* ---- KADRO AÇIĞI + UNDERVALUED TRANSFER ÖNERİLERİ ---- */
function squadGapHTML(){
  const tr=(DB.meta.team_ratings||{})[SQ.team];
  if(!tr||!tr.gaps||!tr.gaps.length) return '';
  const onTeam=new Set(SQ.players.map(p=>p.name));
  const cards=tr.gaps.map(g=>{
    // bu pozisyonda takımda olmayan, değer-verimli (undervalued) adaylar
    const cands=DB.players.filter(p=>p.best===g.pos && !p.nofm && !onTeam.has(p.name) && p.veff!=null && (p.overall||0)>=(g.ca||45))
      .sort((a,b)=>(b.veff-a.veff)||((b.overall||0)-(a.overall||0))).slice(0,4);
    const sevTxt = g.sev==='eksik'?'<span style="color:var(--neg)">EKSİK pozisyon</span>':'<span style="color:var(--neu)">zayıf (en iyi BSX Skoru '+g.ca+')</span>';
    const rows = cands.map(c=>'<div class="gapc" onclick="go(\''+c.id+'\')"><div><div class="gnm">'+esc(c.name)+'</div><div class="gsub">'+tlink(c.team)+' · '+esc(leagueShort(c.league))+' · '+(c.value_eur!=null?fmtMoney(c.value_eur):'—')+'</div></div>'+
      '<div style="text-align:right"><div style="font-family:var(--kit);font-size:17px;color:'+scoreColor(c.overall)+'">'+(c.overall??'—')+'</div><div class="gveff">↑%'+c.veff+' verimli</div></div></div>').join('')||'<div style="color:var(--faint);font-size:12px;padding:6px 0">uygun aday bulunamadı</div>';
    return '<div class="gapcard" data-sev="'+esc(g.sev)+'"><div class="gaphd"><b>'+(BUCK_TR[g.pos]||g.pos)+'</b> · '+sevTxt+'</div>'+rows+'</div>';
  }).join('');
  return '<div class="section"><div class="panel-h">Kadro Açığı & Değer-Verimli Transfer Önerileri</div>'+
    '<div style="color:var(--mut);font-size:12.5px;margin-bottom:12px">Takımın en zayıf/eksik pozisyonları ve o pozisyonda fiyatına göre en verimli (undervalued) adaylar.</div>'+
    '<div class="gapgrid">'+cards+'</div></div>';
}
function openSlot(i){ SQ.sel=i; squadView(); drawSlot(i); }
function goFromDraw(id){ const o=document.getElementById('ovl'); if(o)o.remove(); SQ.sel=null; go(id); }
function closeDraw(){ SQ.sel=null; const o=document.getElementById('ovl'); if(o)o.remove(); squadView(); }
function drawSlot(i){
  const slot=FORMATIONS[SQ.form][i], elig=slot[1], st=SQ.xi[i], e=st?BYID[st.id]:null;
  const alts=SQ.players.filter(p=>eligible(p,elig)&&(!st||p.name!==st.name)).sort((a,b)=>(b.ca||0)-(a.ca||0)).slice(0,10);
  const altH=alts.length?alts.map(p=>'<div class="altrow"><div class="ai"><div class="an">'+esc(p.name)+'</div><div class="as">'+p.pos.join('/')+' · BSX Skoru '+(p.ca??'—')+'</div></div><div class="av" style="color:'+scoreColor(p.ov)+'">'+(p.ca??'—')+'</div><button class="swapb" onclick="swapIn('+JSON.stringify(p.name).replace(/"/g,"&quot;")+')">geç</button></div>').join(''):'<div class="empty">bu pozisyonda kadroda başka oyuncu yok</div>';
  let upH='<div class="empty">oyuncu seçili değil</div>';
  if(e){ const ups=(e.similar||[]).map(s=>BYID[s.id]?{q:BYID[s.id],sim:s.sim}:null).filter(Boolean)
          .filter(x=>x.q.team!==SQ.team).slice(0,6);
    upH=ups.length?ups.map(x=>{
      const dca=(x.q.ca!=null&&e.ca!=null)?(x.q.ca-e.ca):null;
      const badge=dca==null?'<span style="color:var(--mut)">—</span>':(dca>0?'<span style="color:var(--pos)">+'+dca+'</span>':(dca<0?'<span style="color:var(--mut)">'+dca+'</span>':'<span style="color:var(--focus)">=</span>'));
      return '<div class="altrow" style="cursor:pointer" onclick="goFromDraw(\''+x.q.id+'\')"><div class="ai"><div class="an">'+esc(x.q.name)+'</div><div class="as">'+tlink(x.q.team)+' · '+esc(leagueShort(x.q.league))+' · %'+x.sim.toFixed(0)+' benzer · BSX Skoru '+(x.q.ca??'—')+'</div></div><div class="av">'+badge+'</div></div>';
    }).join(''):'<div class="empty">benzer aday bulunamadı</div>'; }
  const head=e?('<h3>'+esc(e.name)+'</h3><div class="pmeta">'+slot[0]+' · BSX Skoru <b style="color:'+scoreColor(e.overall)+'">'+(e.ca??'—')+'</b></div>'):('<h3>Boş slot</h3><div class="pmeta">'+slot[0]+' — uygun: '+elig.join('/')+'</div>');
  const prof=e?'<a class="drlink" onclick="goFromDraw(\''+e.id+'\')">Profili & radarı aç →</a>':'';
  document.body.insertAdjacentHTML('beforeend','<div class="ovl" id="ovl" onclick="if(event.target.id===\'ovl\')closeDraw()"><aside class="draw" aria-label="Slot detayı"><button class="drclose" onclick="closeDraw()">✕</button>'+head+prof+
    '<div class="drsec"><div class="panel-h">Transfer Hedefi Değerlendir ('+slot[0]+')</div>'+
      '<input id="tgtq" class="tgtinput" placeholder="Oyuncu ara (ana ya da tam isim)..." oninput="tgtSearch('+i+')" autocomplete="off">'+
      '<div id="tgtres" class="tgtres"></div><div id="tgteval"></div></div>'+
    '<div class="drsec"><div class="panel-h">Pozisyon Alternatifleri ('+slot[0]+')</div>'+altH+'</div>'+
    '<div class="drsec"><div class="panel-h">Benzer Oyuncular / Transfer Önerileri</div>'+upH+'</div></aside></div>');
}
// slot için transfer hedefi arama (ana + tam isim eşleşir)
function tgtSearch(i){
  const v=norm(document.getElementById('tgtq').value); const box=document.getElementById('tgtres');
  document.getElementById('tgteval').innerHTML='';
  if(v.length<2){ box.innerHTML=''; return; }
  const hits=NAMEIDX.filter(x=>x.key.includes(v)).slice(0,6);
  box.innerHTML=hits.map(x=>{ const g=x.g, p=defaultEntry(g);
    return '<div class="tgtrow" onclick="tgtEval('+i+',\''+p.id+'\')"><span>'+esc(g.name)+'</span><span class="tgtm">'+esc(g.team)+' · BSX Skoru '+(p.ca??'—')+'</span></div>';
  }).join('')||'<div class="empty">eşleşme yok</div>';
}
// seçilen hedefi slota göre değerlendir: pozisyon uygunluğu + kalite + maaş
function tgtEval(i,id){
  const slot=FORMATIONS[SQ.form][i], elig=slot[1], p=BYID[id], st=SQ.xi[i], cur=st?BYID[st.id]:null;
  document.getElementById('tgtres').innerHTML=''; document.getElementById('tgtq').value=p.name;
  // 1) POZİSYON UYGUNLUĞU (ana mevki şart)
  const posOk = (p.best && elig.includes(p.best)) || (p.pos||[]).some(x=>elig.includes(x));
  const posPrimary = p.best && elig.includes(p.best);
  // 2) KALİTE: slottaki mevcut oyuncuya göre BSX Skoru farkı
  const dca=(cur&&p.ca!=null&&cur.ca!=null)?(p.ca-cur.ca):null;
  // 3) MAAŞ: kadro maaş bağlamı (medyan XI maaşı)
  const xiWages=Object.values(SQ.xi).map(s=>BYID[s.id]).filter(q=>q&&q.wage_eur!=null).map(q=>q.wage_eur).sort((a,b)=>a-b);
  const medW=xiWages.length?xiWages[Math.floor(xiWages.length/2)]:null;
  const topW=xiWages.length?xiWages[xiWages.length-1]:null;
  let verdicts=[];
  // pozisyon kararı
  if(!posOk) verdicts.push(['kötü','Pozisyon uyumsuz','Bu oyuncunun oynayabildiği mevkiler ('+(p.pos||[]).join('/')+') bu slota ('+elig.join('/')+') uymuyor.']);
  else if(!posPrimary) verdicts.push(['orta','Yan mevki','Ana mevkisi '+(p.best||'?')+'; bu slotu ikincil pozisyonu olarak oynar.']);
  else verdicts.push(['iyi','Pozisyon ideal','Ana mevkisi ('+p.best+') tam bu slot.']);
  // kalite kararı
  if(dca!=null){
    if(dca>=3) verdicts.push(['iyi','Kalite yükseltir','Mevcut oyuncudan +'+dca+' BSX Skoru daha iyi.']);
    else if(dca<=-4) verdicts.push(['kötü','Kalite düşürür','Mevcut oyuncudan '+dca+' BSX Skoru daha düşük — gerileme.']);
    else verdicts.push(['orta','Benzer kalite','Mevcut oyuncuyla yakın seviye ('+(dca>=0?'+':'')+dca+' BSX Skoru).']);
  }
  // maaş kararı
  if(p.wage_eur!=null && medW!=null){
    if(p.wage_eur > topW*1.15) verdicts.push(['kötü','Maaş çok yüksek','İstediği maaş ('+fmtMoney(p.wage_eur)+'/yıl) kadronun en yüksek maaşını (%15+) aşıyor — maaş yapısını bozar.']);
    else if(p.wage_eur > medW*1.6) verdicts.push(['orta','Maaş üst bant','Maaşı ('+fmtMoney(p.wage_eur)+'/yıl) kadro medyanının belirgin üstünde.']);
    else verdicts.push(['iyi','Maaş uyumlu','Maaşı ('+fmtMoney(p.wage_eur)+'/yıl) kadro yapısına oturur.']);
  } else verdicts.push(['orta','Maaş bilinmiyor','Bu oyuncunun maaş verisi yok.']);
  // genel skor
  const score=verdicts.reduce((a,[v])=>a+(v==='iyi'?1:v==='kötü'?-1:0),0);
  const overall=score>=2?['iyi','İYİ TRANSFER']:score<=-1?['kötü','RİSKLİ TRANSFER']:['orta','TARTIŞMALI'];
  const vc={iyi:'var(--pos)','kötü':'var(--neg)',orta:'var(--focus)'};
  document.getElementById('tgteval').innerHTML=
    '<div class="tgthead" style="border-color:'+vc[overall[0]]+'"><b style="color:'+vc[overall[0]]+'">'+overall[1]+'</b> — '+esc(p.name)+' · BSX Skoru '+(p.ca??'—')+(p.pa!=null?' · BSX Potansiyel '+p.pa:'')+'</div>'+
    verdicts.map(([v,t,d])=>'<div class="tgtv"><span class="tgtvb" style="background:'+vc[v]+'">'+(v==='iyi'?'✓':v==='kötü'?'✕':'!')+'</span><div><b>'+t+'</b><div class="tgtvd">'+d+'</div></div></div>').join('')+
    '<a class="drlink" onclick="goFromDraw(\''+p.id+'\')">Profili aç →</a>';
}
function swapIn(name){
  const i=SQ.sel, pl=SQ.players.find(p=>p.name===name); if(!pl)return;
  const incoming={name:pl.name,id:pl.bestId,ca:pl.ca,ov:pl.ov}, out=SQ.xi[i];
  let from=null; for(const k in SQ.xi){ if(SQ.xi[k]&&SQ.xi[k].name===name){from=k;break;} }
  SQ.xi[i]=incoming;
  if(from!==null && +from!==i){ if(out)SQ.xi[from]=out; else delete SQ.xi[from]; }
  else { SQ.bench=SQ.bench.filter(x=>x.name!==name); if(out)SQ.bench.unshift({name:out.name,id:out.id,ca:out.ca,ov:out.ov,pos:(SQ.players.find(p=>p.name===out.name)||{pos:[]}).pos}); }
  const o=document.getElementById('ovl'); if(o)o.remove(); squadView(); drawSlot(i);
}

/* ---------- D: oyun modeli uyumu ---------- */
let MODSEL=null;
function fitColor(n){ if(n==null)return "var(--mut)"; if(n>=75)return "var(--pos)"; if(n>=45)return "var(--tx)"; return "var(--mut)"; }
function teamDominant(team){
  const ps=DB.players.filter(x=>x.team===team && x.fit); if(!ps.length)return null;
  const ks=Object.keys(DB.meta.models), sum={}; ks.forEach(k=>sum[k]=0);
  ps.forEach(x=>ks.forEach(k=>sum[k]+=(x.fit[k]||0)));
  return ks.sort((a,b)=>sum[b]-sum[a])[0];
}
function renderModels(p){
  if(!p.fit || !DB.meta.models){ document.getElementById('mranks').innerHTML='<div class="empty">Model verisi yok.</div>'; return; }
  const M=DB.meta.models;
  const ranked=Object.keys(p.fit).sort((a,b)=>p.fit[b]-p.fit[a]);
  // bu oyuncu için hiç model-uyum verisi yoksa (ör. bazı kaleciler) — çökme yerine boş durum
  if(!ranked.length){ document.getElementById('mranks').innerHTML='<div class="empty">Model verisi yok.</div>'; document.getElementById('mdetail').innerHTML=''; return; }
  if(MODSEL===null || !ranked.includes(MODSEL)) MODSEL=ranked[0];
  document.getElementById('mranks').innerHTML=ranked.map(k=>{
    const v=p.fit[k];
    return '<div class="mrow '+(k===MODSEL?'on':'')+'" onclick="MODSEL=\''+k+'\';renderModels(BYID[CUR])"><div class="mname">'+esc(M[k].name)+'</div>'+
      '<div class="mbarwrap"><div class="mbar"><i style="width:'+v+'%;background:'+fitColor(v)+'"></i></div></div>'+
      '<div class="mpct" style="color:'+fitColor(v)+'">%'+v+'</div></div>';
  }).join('');
  // detay
  const ord=DB.meta.attr_order||[];
  const attrs=Object.keys(M[MODSEL].attrs).map(a=>({a,pct:(p.ap&&ord.indexOf(a)>=0)?p.ap[ord.indexOf(a)]:null})).filter(x=>x.pct!=null);
  attrs.sort((a,b)=>b.pct-a.pct);
  // MUTLAK eşik kullan — göreceli sıralama (kendi içindeki en düşük 3'ü) tek başına yeterli
  // değil: %90+ olan bir oyuncunun "en düşük"ü bile mutlak olarak güçlü olabilir (bkz. Mbappé
  // örneği). scoreColor/fitColor'daki mutlak-eşik deseniyle tutarlı: yalnız gerçekten yüksek
  // (≥60) "güçlü", gerçekten düşük (<40) "geliştirilecek" sayılır; ikisi de boşsa bölüm gizlenir.
  const STRONG_T=60, WEAK_T=40;
  const strong=attrs.filter(x=>x.pct>=STRONG_T).slice(0,3);
  const weak=attrs.filter(x=>x.pct<WEAK_T).slice(-3).reverse();
  const dom=teamDominant(p.team); const tsf=dom?p.fit[dom]:null;
  document.getElementById('mdetail').innerHTML=
    '<aside class="mdet" aria-label="Oyun modeli detayı"><div class="dh">'+esc(M[MODSEL].name)+'</div>'+
    '<div class="df" style="color:'+fitColor(p.fit[MODSEL])+'">%'+p.fit[MODSEL]+'</div>'+
    '<div style="color:var(--mut);font-size:12.5px">bu sisteme uyum ('+p.bucket+' kovası içinde)</div>'+
    (strong.length?'<div class="swlabel">✓ Güçlü yönler</div>'+strong.map(x=>'<span class="swchip swpos">'+esc(BS_LABEL[x.a]||x.a)+' <b>%'+x.pct+'</b></span>').join(''):'')+
    (weak.length?'<div class="swlabel">✗ Geliştirilecek</div>'+weak.map(x=>'<span class="swchip swneg">'+esc(BS_LABEL[x.a]||x.a)+' <b>%'+x.pct+'</b></span>').join(''):'')+
    (dom?'<div class="tsf">Takım sistemi uyumu — <b>'+esc(p.team)+'</b> ağırlıklı <b>'+esc(M[dom].name)+'</b> oynuyor; bu oyuncunun o sisteme uyumu <b style="color:'+fitColor(tsf)+'">%'+tsf+'</b>.</div>':'')+
    '</aside>';
}

/* ---------- KARŞILAŞTIRMA (maks 5) ---------- */
let CMP=[], CMPBASE=null; const CMPCOL=['#7C93B8','#D9A441','#5B8AA6','#A88FCC','#C4776A'];
function radarMulti(names, series){
  // bkz. radarSVG: aynı marj-yetersizliği düzeltmesi (kenara ~85px boşluk)
  const N=names.length, cx=220, cy=200, R=122;
  const ang=i=>(-Math.PI/2)+i*2*Math.PI/N, pt=(i,r)=>[cx+Math.cos(ang(i))*r, cy+Math.sin(ang(i))*r];
  let g='';
  [.25,.5,.75,1].forEach(f=>{let p=[];for(let i=0;i<N;i++)p.push(pt(i,R*f).map(n=>n.toFixed(1)).join(','));g+='<polygon points="'+p.join(' ')+'" fill="none" stroke="var(--chalk)"/>';});
  for(let i=0;i<N;i++){const a=pt(i,R);g+='<line x1="'+cx+'" y1="'+cy+'" x2="'+a[0].toFixed(1)+'" y2="'+a[1].toFixed(1)+'" stroke="var(--chalk)"/>';
    const l=pt(i,R+18),an=ang(i),anc=Math.abs(Math.cos(an))<.3?'middle':(Math.cos(an)>0?'start':'end');
    const f=names[i],sh=wordTrunc(f,16);
    g+='<text x="'+l[0].toFixed(1)+'" y="'+(l[1]+3).toFixed(1)+'" fill="var(--mut)" font-size="9" text-anchor="'+anc+'"><title>'+esc(f)+'</title>'+esc(sh)+'</text>';}
  series.forEach((s,si)=>{let p=[];for(let i=0;i<N;i++){const v=s.pcts[i]==null?0:s.pcts[i];p.push(pt(i,R*v/100).map(n=>n.toFixed(1)).join(','));}
    g+='<polygon points="'+p.join(' ')+'" fill="'+s.color+'24" stroke="'+s.color+'" stroke-width="2" stroke-linejoin="round" pathLength="1" class="radardraw" style="animation-delay:'+(si*.12)+'s"/>';
    for(let i=0;i<N;i++){const v=s.pcts[i];if(v==null)continue;const a=pt(i,R*v/100);g+='<circle cx="'+a[0].toFixed(1)+'" cy="'+a[1].toFixed(1)+'" r="2.6" fill="'+s.color+'"/>';}});
  return '<svg class="radar" viewBox="0 0 440 400">'+g+'</svg>';
}
function renderComparePage(){
  // bağımsız karşılaştırma sekmesi: önce oyuncu seç, sonra aynı pozisyondan ekle
  const app=document.getElementById('app');
  app.innerHTML='<div class="backrow"><button class="backbtn" onclick="navBack()">← geri</button></div>'+
    '<div class="phead"><div class="pid"><h2>Karşılaştırma</h2>'+
      '<div class="pmeta">Bir oyuncu seç, sonra aynı pozisyondan en fazla 5 oyuncuyu kıyasla — istatistik, radar ve birbirlerine benzerlik oranı</div></div></div>'+
    (CMPBASE&&BYID[CMPBASE]
      ? '<div class="section"><button class="backbtn" style="margin-bottom:14px" onclick="cmpReset()">↺ farklı oyuncuyla başla</button><div id="comparebox"></div></div>'
      : '<div class="section"><div class="cmpsearch"><input id="cmpseed" placeholder="Karşılaştırmaya başlamak için oyuncu ara…" oninput="cmpSeedSearch(this.value)" autocomplete="off"><div id="cmpseedres" class="cmpres"></div></div>'+
        '<div class="empty">Henüz oyuncu seçilmedi. Yukarıdan bir oyuncu arayıp seç.</div></div>');
  if(CMPBASE&&BYID[CMPBASE]) renderCompare();
}
function cmpSeedSearch(qy){
  const box=document.getElementById('cmpseedres'); if(!box)return;
  const s=norm(qy||'').trim();
  if(s.length<2){ box.innerHTML=''; return; }
  const hits=NAMEIDX.filter(x=>x.key.includes(s)).slice(0,8).sort((a,b)=>topOv(b.g)-topOv(a.g));
  box.innerHTML=hits.map(x=>{ const g=x.g, p=defaultEntry(g), ov=topOv(g);
    return '<div class="cmpresit" onclick="cmpSeedPick(\''+p.id+'\')"><span class="pgdot" style="background:'+posGroupColor(p.bucket)+'"></span><div style="flex:1;min-width:0"><div class="nm">'+highlightMatch(g.name,s)+'</div><div class="cmpresm">'+esc(g.team)+' · '+esc(leagueShort(g.league))+'</div></div><span class="resca" style="color:'+scoreColor(ov)+'">'+(ov??'—')+'</span></div>';
  }).join('')||'<div class="cmpresno">eşleşme yok</div>';
}
function cmpSeedPick(id){ if(!BYID[id])return; CMPBASE=id; CMP=[id]; renderComparePage(); }
function cmpReset(){ CMPBASE=null; CMP=[]; renderComparePage(); }
function renderCompare(){
  const box=document.getElementById('comparebox'); if(!box)return;
  if(!CMPBASE||!BYID[CMPBASE]) CMPBASE=CUR;
  const base=BYID[CMPBASE]; if(!base)return;
  // mevki seçici: bu oyuncunun tüm mevki kayıtları (bek oynarken / cm oynarken ...)
  const ent=DB.players.filter(x=>x.name===base.name && x.team===base.team);
  const byBucket={}; ent.forEach(x=>{ if(!byBucket[x.bucket]||(x.overall||0)>(byBucket[x.bucket].overall||0)) byBucket[x.bucket]=x; });
  const bks=Object.keys(byBucket);
  const posSel = bks.length>1
    ? '<div class="cmppos"><span class="cmpposl">Mevki:</span>'+bks.map(b=>'<button class="ptab '+(b===base.bucket?'on':'')+'" style="--pgc:'+posGroupColor(b)+'" onclick="setCmpBase(\''+byBucket[b].id+'\')">'+b+' · '+BUCK_TR[b]+'</button>').join('')+'</div>'
    : '';
  const metrics=Object.keys(base.radar);
  const players=CMP.map(id=>BYID[id]).filter(Boolean);
  const colOf=id=>CMPCOL[CMP.indexOf(id)%CMPCOL.length];
  const series=players.map(p=>({color:colOf(p.id),pcts:metrics.map(m=>p.radar[m])}));
  const th='<th>Veriler (p90)</th>'+metrics.map(m=>'<th>'+esc(m)+'</th>').join('')+'<th>Dakika</th><th></th>';
  const rows=players.map(p=>{const c=colOf(p.id);const rv=p.rv||{};
    return '<tr><td class="pcell"><b style="color:'+c+'">'+esc(p.name)+'</b><div class="ps">'+tlink(p.team)+', '+(p.age!=null?Math.round(p.age):'—')+'</div></td>'+
      metrics.map(m=>'<td style="color:'+c+'">'+fmtP90(rv[m])+'</td>').join('')+
      '<td style="color:'+c+'">'+(p.minutes!=null?Math.round(p.minutes):'—')+'</td>'+
      '<td>'+(p.id!==CMPBASE?'<button class="xbtn" onclick="removeCmp(\''+p.id+'\')">✕</button>':'')+'</td></tr>';}).join('');
  const blocks=players.map(pl=>{ const c=colOf(pl.id);
    const cand=((pl.statsim)||[]).map(id=>BYID[id]).filter(Boolean).filter(q=>!CMP.includes(q.id)).slice(0,8);
    const chips=cand.length?cand.map(q=>'<button class="bvchip" onclick="addCmp(\''+q.id+'\')"'+(CMP.length>=5?' disabled':'')+'>'+esc(q.name)+'<span class="bvsub">'+esc(q.team)+' · '+(q.ca??'—')+'</span></button>').join(''):'<span class="cmpaddlbl">başka benzer yok</span>';
    return '<div class="bvgrp"><div class="bvglabel"><i class="bvdot" style="background:'+c+'"></i>'+esc(pl.name)+'\'e benzer</div><div class="bvrow">'+chips+'</div></div>';
  }).join('');
  // İKİLİ BENZERLİK MATRİSİ: seçili oyuncuların birbirine profil benzerliği (ap percentile üzerinden)
  let simMatrix='';
  if(players.length>=2){
    const hdr='<th></th>'+players.map(p=>'<th style="color:'+colOf(p.id)+'">'+esc(p.name.split(' ').slice(-1)[0])+'</th>').join('');
    const mrows=players.map(a=>{
      const cells=players.map(b=>{
        if(a.id===b.id) return '<td class="smx-self">—</td>';
        const s=pairSim(a,b);
        return '<td style="background:'+simHeat(s)+';color:'+(s>=55?'#0C0F14':'var(--tx)')+'">%'+Math.round(s)+'</td>';
      }).join('');
      return '<tr><td class="smx-name" style="color:'+colOf(a.id)+'">'+esc(a.name)+'</td>'+cells+'</tr>';
    }).join('');
    simMatrix='<div class="simmx"><div class="cmpsubh">Birbirlerine profil benzerliği</div>'+
      '<div class="cmptablewrap"><table class="cmptable smx"><thead><tr>'+hdr+'</tr></thead><tbody>'+mrows+'</tbody></table></div></div>';
  }
  box.innerHTML=
    posSel+
    '<div class="cmpsearch"><input id="cmpq" placeholder="Oyuncu ara ve ekle ('+(BUCK_TR[base.bucket]||'aynı pozisyon')+')…" oninput="cmpSearch(this.value)"'+(CMP.length>=5?' disabled':'')+'><div id="cmpres" class="cmpres"></div></div>'+
    '<div class="cmptablewrap"><table class="cmptable"><thead><tr>'+th+'</tr></thead><tbody>'+rows+'</tbody></table></div>'+
    simMatrix+
    '<div class="cmpradar">'+radarMulti(metrics,series)+'</div>'+
    '<div class="bvbar"><div class="bvlabel">İstatistiksel benzer — listedeki her oyuncu için'+(CMP.length>=5?'  ·  maks. 5 oyuncu (kaldır → ekle)':'')+'</div>'+blocks+'</div>';
}
function setCmpBase(id){ if(!BYID[id])return; CMPBASE=id; CMP=[id]; renderCompare(); }
// iki oyuncunun profil benzerliği (motorun Rol-İmza mantığı: şekil %50 + spike %50)
function pairSim(a,b){
  const A=a.ap, B=b.ap;
  if(!A||!B||A.length!==B.length||!A.length) return 0;
  const n=A.length;
  // şekil: merkezlenmiş percentile kosinüsü (negatif -> 0)
  let ma=0,mb=0; for(let i=0;i<n;i++){ma+=A[i];mb+=B[i];} ma/=n; mb/=n;
  let dot=0,na=0,nb=0;
  for(let i=0;i<n;i++){ const x=A[i]-ma, y=B[i]-mb; dot+=x*y; na+=x*x; nb+=y*y; }
  const shape=Math.max(0, dot/(Math.sqrt(na*nb)+1e-6))*100;
  // spike: >=70 imza örtüşmesi (üstel), kosinüs
  let sdot=0,sa=0,sb=0;
  for(let i=0;i<n;i++){
    const pa=Math.pow(Math.max(0,(A[i]-70)/30),2), pb=Math.pow(Math.max(0,(B[i]-70)/30),2);
    sdot+=pa*pb; sa+=pa*pa; sb+=pb*pb;
  }
  const spike=(sa>0&&sb>0)?Math.max(0,Math.min(1,sdot/(Math.sqrt(sa*sb)+1e-6)))*100:0;
  return 0.5*shape+0.5*spike;
}
// benzerlik -> ısı rengi (düşük=koyu, yüksek=canlı yeşil)
function simHeat(s){ const t=Math.max(0,Math.min(100,s))/100; const a=0.10+0.55*t;
  return 'rgba(124,147,184,'+a.toFixed(2)+')'; }
function cmpSearch(qy){
  const box=document.getElementById('cmpres'); if(!box)return; const base=BYID[CMPBASE]; if(!base)return;
  const s=norm(qy||'').trim();
  if(s.length<2){ box.innerHTML=''; return; }
  const res=DB.players.filter(p=>p.bucket===base.bucket && !CMP.includes(p.id) && (norm(p.name)+' '+norm(p.alt||'')).includes(s))
    .sort((a,b)=>(b.overall||0)-(a.overall||0)).slice(0,8);
  box.innerHTML=res.length?res.map(p=>'<div class="cmpresit" onclick="addCmp(\''+p.id+'\')"><span class="pgdot" style="background:'+posGroupColor(p.bucket)+'"></span><div style="flex:1;min-width:0"><div class="nm">'+highlightMatch(p.name,s)+'</div><div class="cmpresm">'+esc(p.team)+' · '+esc(leagueShort(p.league))+'</div></div><span class="resca" style="color:'+scoreColor(p.overall)+'">'+(p.overall??'—')+'</span></div>').join(''):'<div class="cmpresno">eşleşme yok (aynı pozisyonda)</div>';
}
function toggleCmp(id){ if(id===CMPBASE)return; if(CMP.includes(id))CMP=CMP.filter(x=>x!==id); else if(CMP.length<5)CMP.push(id); renderCompare(); }
function addCmp(id){ if(CMP.length<5 && !CMP.includes(id)) CMP.push(id); renderCompare(); }
function removeCmp(id){ if(id!==CMPBASE) CMP=CMP.filter(x=>x!==id); renderCompare(); }

/* ============================================================================
   FİLTRELEME SEKMESİ — "Genel Bakış"tan bağımsız, kendi state'i ve render'ı.
   Mevcut render()/renderProfile()/renderSquad()/renderLeague()/renderComparePage()
   fonksiyonlarına dokunmaz; yalnız paylaşılan DB'yi okur, sonuç satırına
   tıklayınca mevcut go(id) route'uyla profile geçer.
   ============================================================================ */
function jsonAttr(s){ return JSON.stringify(s).replace(/"/g,'&quot;'); }
const POS10_ORDER=['GK','CB','LB','RB','DM','CM','AM','LW','RW','ST'];
let FILTER_STATE={ bucket:'ST', filters:[], combine:'and' };
let FLT_SORT={ type:'ca', idx:null, dir:-1 };   // sonuç tablosu sıralama durumu
let ROLES_BY_BUCKET={};
let PICKER_CAT='radar';
const GENERAL_FIELDS={
  age:  {label:'Yaş', type:'numeric', dmin:14, dmax:42, get:p=>p.age},
  ca:   {label:'BSX Skoru', type:'numeric', dmin:0, dmax:100, get:p=>p.ca},
  // BSX Potansiyel (eski PA) — BSX Skoru ile aynı desen: yeniden adlandırılmış ama
  // kademesiz ham sayı (0-100), min/max sayı kutusuyla filtrelenir.
  pa:   {label:'BSX Potansiyel', type:'numeric', dmin:0, dmax:100, get:p=>p.pa},
  cyear:{label:'Sözleşme Yılı', type:'numeric', dmin:new Date().getFullYear(), dmax:new Date().getFullYear()+8, get:p=>p.cyear},
  league:{label:'Lig', type:'select', get:p=>p.league, options:()=>(DB.meta.leagues||[]).map(x=>x.name).sort()},
  team: {label:'Takım', type:'select', get:p=>p.team, options:()=>TEAMS.map(x=>x.t).sort()},
  foot: {label:'Ayak', type:'select', get:p=>p.foot, options:()=>['Sol ayaklı','Sağ ayaklı','Çift ayaklı']},
  // dizi-değerli alan: oyuncunun oynayabildiği TÜM pozisyonlar (birincil değil) — "RB de
  // oynayabilen ama asıl CB olanlar" gibi sorgular için VE/VEYA modu anlamlı olan tek alan.
  pos:  {label:'Oynayabildiği Pozisyonlar', type:'select-multi-value', get:p=>p.pos||[], options:()=>POS10_ORDER},
};

/* ---- saf filtre mantığı: render/DOM'dan tamamen bağımsız, tek başına test edilebilir ---- */
// 'radar' grubu artık İSTATİSTİK kategorisi: ham StatsLook/QSL per-90 değerleri (p.xm),
// yalnız radar grafiğine seçilmiş ~11 metrik değil, motorun okuduğu TÜM sütunlar (meta.xcat).
// __cm__ önekli field id'ler kullanıcı tanımlı özel metriklerdir (bkz. CUSTOM_METRICS).
function fieldValue(p, filt){
  if(filt.group==='radar'){
    if(filt.field.indexOf('__cm__')===0){
      const cm=CUSTOM_METRICS.find(x=>x.id===filt.field);
      return cm ? customMetricValue(p,cm) : null;
    }
    return (p.xm||{})[filt.field];
  }
  if(filt.group==='bs') return (p.bs||{})[filt.field];
  if(filt.group==='rol'){ const blk=(p.ROL||{})[filt.field]; return blk?blk.uyum:null; }
  if(filt.group==='genel'){ const d=GENERAL_FIELDS[filt.field]; return d?d.get(p):null; }
  return null;
}
// ATTRIBUTE (bs) EKSEN İSİMLERİ: 48 eksenin ham/dahili adı (motor tarafında BS_ sütun
// adı, ör. "Top Kapma") yerine KAPASİTE-vurgulu kullanıcı-yüzü ismi — "ne kadar iyi
// yapabiliyor" (kapasite) ile StatsLook'un "kaç kere yaptı" (gerçekleşen performans)
// ayrımı isimde görünür kalsın diye. Anahtar HER ZAMAN ham eksen adı (p.bs[...],
// DB.meta.bs_tiers[...] hep bu anahtarla çalışır) — yalnız GÖSTERİM metni değişir.
// Bu harita üç yerde kullanılır: (1) Filtreleme > Attribute kategorisi, (2) "Oyun
// Modeli Uyumu" güçlü/geliştirilecek chip'leri (bkz. renderModels), (3) "Tüm
// Pozisyonlar" karşılaştırma mini-radarı (bkz. renderAllPositions/ALLPOS_ATTRS).
// Bilinçli olarak DEĞİŞTİRİLMEYEN eksenler (ham istatistik isimleriyle çakışma riski
// yüzünden): Top Kapma, Hava Topları, Kafa Vuruşu, Yumruklama.
const BS_LABEL={
  'Hız':'Hız', 'Hızlanma':'Çabukluk', 'Güç':'Güç', 'Çeviklik':'Çeviklik', 'Denge':'Denge',
  'Dayanıklılık':'Kondisyon', 'Zıplama':'Zıplama', 'Dripling':'Dripling', 'Pas':'Pas',
  'İlk Kontrol':'İlk Kontrol', 'Bitiricilik':'Bitiricilik', 'Kafa Vuruşu':'Kafa Vuruşu',
  'Orta Yapma':'Orta Açma Yeteneği', 'Uzaktan Şut':'Uzaktan Şut', 'Teknik':'Teknik Kapasite',
  'FC_Zayıf Ayak':'Zayıf Ayak', 'Markaj':'Markaj Yeteneği',
  'Mevki Alma':'Pozisyon Alma Yeteneği (Savunma)', 'Topsuz Alan':'Pozisyon Alma Yeteneği (Hücum)',
  'Birebir':'Birebir Hakimiyeti', 'Vizyon':'Oyun Görüşü', 'Özel Yetenek':'Beceri Repertuvarı',
  'Soğukkanlılık':'Soğukkanlılık', 'Konsantrasyon':'Odaklanma', 'Agresiflik':'Saldırganlık',
  'Çalışkanlık':'Saha İçi Efor', 'İşbirliği':'Takım Oyunu Anlayışı', 'Cesaret':'Mücadele Direnci',
  'Kararlılık':'Mental Güç', 'Liderlik':'Liderlik', 'Refleksler':'Refleks Yeteneği',
  'Elle Kontrol':'Top Tutuş Yeteneği', 'Hava Topları':'Hava Topları',
  'Bölge Hakimiyeti':'Ceza Sahası Hakimiyeti', 'İletişim':'Savunma Organizasyon Yeteneği',
  'Degaj':'Ayakla Oyun Kurma Yeteneği', 'Elle Oyun Başlatma':'Elle Dağıtım Yeteneği',
  'Yumruklama':'Yumruklama', 'Top Kapma':'Top Kapma', 'Karar Alma':'Karar Verme Yeteneği',
  'Önsezi':'Sezgi', 'Vücut Zindeliği':'Atletizm', 'Ani Çıkış Eğilimi':'Çıkış Zamanlaması',
  'Eksantriklik':'Eksantriklik', 'FC_Patlayıcılık':'Patlayıcılık', 'FC_Top Kesmeler':'Top Kesme',
  'FC_Uzun Adım':'Uzun Adım', 'FC_Şut Gücü':'Şut Gücü',
};
// ATTRIBUTE (bs) KADEMELERİ: her eksenin motorda (natural_breaks, bkz.
// bigstatx_engine.py) hesaplanmış KENDİ 5 kesim noktası — sabit bir aralık
// DEĞİL, DB.meta.bs_tiers[eksen]'den okunur; eksenden eksene farklı çıkar
// (ör. Hız ile Teknik aynı sayı aralığına denk gelmez, kasıtlı).
const BS_TIER_LABELS=['Çok Kötü','Kötü','Ortalama','İyi','Çok İyi','Elit'];
function bsTierCuts(field){ return (DB.meta.bs_tiers||{})[field]||[]; }
// v'nin bu eksende hangi kademeye (0-5) düştüğünü bulur (cuts artan sırada,
// üst-uçtan itibaren üstünde/eşit olduğu ilk sınırın index'i + 1).
function bsTierIndex(field, v){
  if(v==null || isNaN(v)) return null;
  const cuts=bsTierCuts(field); let idx=0;
  for(const c of cuts){ if(v>=c) idx++; else break; }
  return idx;
}
function bsTierLabel(field, v){
  const idx=bsTierIndex(field, v);
  return idx==null ? '—' : (BS_TIER_LABELS[idx]||'—');
}
// (Potansiyel artık kademesiz — bkz. GENERAL_FIELDS.pa — BSX Potansiyel BSX Skoru ile
// birebir aynı ham-sayı yolunu kullanır, bu fonksiyondan geçer.)
// Ham {min,max} aralığını olduğu gibi kullanır (radar/rol/genel-numerik alanlar — BSX
// Skoru ve BSX Potansiyel dahil). bs (Attribute) artık İKİ UÇLU KADEME ARALIĞI ile
// çalışır (minTier/maxTier, 0-5) — bu, matchesFilter içinde doğrudan bsTierIndex ile
// karşılaştırılır, bu fonksiyonun ham sayısal {min,max} yoluna hiç girmez (kademe
// sınırındaki ondalık kesim noktasıyla ham değer arasında "dahil/hariç" belirsizliği
// olmasın diye — bkz. matchesFilter).
function resolveNumericRange(filt){
  return {min:filt.min, max:filt.max};
}
// select-tipi filtrede birden çok değer seçilince mod belirler: 'or' (herhangi biri,
// varsayılan) ya da 'and' (hepsi birden — yalnız dizi-değerli alanlarda anlamlı, ör.
// hem RB hem LB oynayabilsin; skaler alanda (lig gibi) 'and' + 2 değer hep boş sonuç verir,
// bu matematiksel olarak doğru ve kullanıcı seçimidir, ayrıca engellenmez).
function matchesFilter(p, filt){
  if(filt.type==='select' || filt.type==='select-multi-value'){
    if(!filt.values || !filt.values.length) return true;
    const v=fieldValue(p,filt);
    const owned = filt.type==='select-multi-value' ? (Array.isArray(v)?v:[]) : [v];
    return filt.mode==='and'
      ? filt.values.every(x=>owned.includes(x))
      : filt.values.some(x=>owned.includes(x));
  }
  // Attribute (bs) kademe ARALIĞI: değerin kendi kademe index'i (0-5) [minTier,maxTier]
  // içinde mi — doğrudan tam sayı karşılaştırması, ondalık kesim noktasına hiç bakmaz
  // (bkz. yukarıdaki not). Varsayılan minTier:0/maxTier:5 = tüm aralık. (Potansiyel artık
  // kademesiz — BSX Skoru ile aynı ham numerik yol üzerinden aşağıdaki genel dala düşer.)
  if(filt.type==='bs-tier'){
    const v=fieldValue(p,filt);
    if(v==null || isNaN(v)) return false;
    const idx = bsTierIndex(filt.field, v);
    if(idx==null) return false;
    const lo=filt.minTier??0, hi=filt.maxTier??(BS_TIER_LABELS.length-1);
    return idx>=lo && idx<=hi;
  }
  const v=fieldValue(p,filt);
  if(v==null || (typeof v==='number' && isNaN(v))) return false;
  const {min,max}=resolveNumericRange(filt);
  if(min!=null && min!=='' && v<min) return false;
  if(max!=null && max!=='' && v>max) return false;
  return true;
}
// combine: filtre SATIRLARININ birbiriyle ilişkisi — 'and' (hepsi, varsayılan) ya da
// 'or' (herhangi biri yeter). Filtre satırı yoksa her zaman true (filtresiz = tüm havuz).
function matchesFilters(p, filters, combine){
  if(!filters.length) return true;
  return (combine==='or') ? filters.some(f=>matchesFilter(p,f)) : filters.every(f=>matchesFilter(p,f));
}

/* ---- İSTATİSTİK: özel metrik (iki ham StatsLook alanı arasında türetilmiş değer) ---- */
let CUSTOM_METRICS=[];   // {id:'__cm__N', label, aField, bField, op}
let CM_SEQ=0;
let CM_FORM_OPEN=false;
const CM_OPS={
  diff: {sym:'−', label:'Fark (A − B)',   calc:(a,b)=>(a==null||b==null)?null:a-b},
  ratio:{sym:'/', label:'Oran (A / B)',   calc:(a,b)=>(a==null||b==null||b===0)?null:a/b},
  sum:  {sym:'+', label:'Toplam (A + B)', calc:(a,b)=>(a==null||b==null)?null:a+b},
};
function customMetricValue(p, cm){
  const a=(p.xm||{})[cm.aField], b=(p.xm||{})[cm.bField];
  return CM_OPS[cm.op].calc(a,b);
}
function round1(v){ return Math.round(v*10)/10; }
// bir alanın seçili pozisyondaki gerçek değer aralığı — yeni filtre eklenirken min/max
// varsayılanı bunlardan gelir (ham StatsLook sütunları 0-100 değil, ör. "Toplam Pas" 90'a,
// "Gol Sayısı" 1.5'e kadar çıkabilir — sabit bir ölçek yok, gerçek veriden okunmalı).
function fieldRange(field){
  const b=FILTER_STATE.bucket;
  const isCm=field.indexOf('__cm__')===0;
  const cm=isCm?CUSTOM_METRICS.find(x=>x.id===field):null;
  let mn=Infinity, mx=-Infinity;
  DB.players.forEach(p=>{
    if(b!=='ALL' && p.bucket!==b) return;
    const v = isCm ? (cm?customMetricValue(p,cm):null) : (p.xm||{})[field];
    if(v!=null && !isNaN(v)){ if(v<mn) mn=v; if(v>mx) mx=v; }
  });
  if(mn===Infinity) return {min:isCm?-10:0, max:isCm?10:100};
  return {min:round1(mn), max:round1(mx)};
}

/* ---- alan kayıt defteri: seçili pozisyona göre uygun alan listesi ---- */
// b==='ALL' → "Hepsi" modu: tek pozisyona sınırlamaz, tüm bucket-girişleri havuza dahil olur
function rolesForBucket(b){
  if(ROLES_BY_BUCKET[b]) return ROLES_BY_BUCKET[b];
  const set=new Set();
  DB.players.forEach(p=>{ if((b==='ALL'||p.bucket===b) && p.ROL) Object.keys(p.ROL).forEach(k=>{ if(k[0]!=='_') set.add(k); }); });
  return ROLES_BY_BUCKET[b]=[...set];
}
let STATCOLS_BY_BUCKET={};
// meta.xcat motorun okuduğu TÜM ham StatsLook/QSL sütunlarını listeler (pozisyondan bağımsız,
// tek düz sözlük). Bir pozisyon için anlamlı olanları süzmek üzere: o kova içindeki
// oyuncuların en az %10'unda dolu (non-null) olan sütunlar tutulur — ör. kaleciler için
// "Gol Sayısı"/"Şut İsabet %" gibi saha-oyuncusu istatistikleri elenir (kapsam ~%1),
// "Toplam Pas"/"Uzun Toplar" gibi kaleciye de uygun olanlar kalır (kapsam ~%95+).
function statColsForBucket(b){
  if(STATCOLS_BY_BUCKET[b]) return STATCOLS_BY_BUCKET[b];
  const cat=DB.meta.xcat||{};
  const keys=Object.keys(cat);
  const counts=Object.fromEntries(keys.map(k=>[k,0]));
  let n=0;
  DB.players.forEach(p=>{
    if(b!=='ALL' && p.bucket!==b) return;
    n++;
    const xm=p.xm||{};
    for(const k of keys){ if(xm[k]!=null) counts[k]++; }
  });
  const cols = n ? keys.filter(k=>counts[k]/n>=0.10) : keys.slice();
  cols.sort((x,y)=>(cat[x]||x).localeCompare(cat[y]||y,'tr'));
  return STATCOLS_BY_BUCKET[b]=cols;
}
function fieldsForCategory(cat){
  const b=FILTER_STATE.bucket;
  if(cat==='radar'){
    const xc=DB.meta.xcat||{};
    const base=statColsForBucket(b).map(k=>({field:k,label:xc[k]||k,sub:'İstatistik · ham (per-90)'}));
    const custom=CUSTOM_METRICS.map(cm=>({field:cm.id,label:'★ '+cm.label,sub:'Özel Metrik'}));
    return base.concat(custom);
  }
  if(cat==='bs'){
    // "Hepsi" modunda kaleci+saha oyuncusu karışık olduğu için iki eksen kümesinin birleşimi
    const axes = b==='ALL' ? [...new Set([...(DB.meta.bs_axes_gk||[]),...(DB.meta.bs_axes_field||[])])]
      : (b==='GK'?DB.meta.bs_axes_gk:DB.meta.bs_axes_field)||[];
    return axes.map(a=>({field:a,label:BS_LABEL[a]||a,sub:'Attribute · 6 kademe'}));
  }
  if(cat==='rol'){
    return rolesForBucket(b).map(kod=>({field:kod,label:((DB.meta.rol_registry||{})[kod]||{}).ad||kod,sub:'Rol Uyum %'}));
  }
  if(cat==='genel'){
    return Object.entries(GENERAL_FIELDS).map(([k,d])=>({field:k,label:d.label,sub:d.type==='numeric'?'Sayısal':'Seçim'}));
  }
  return [];
}

/* ---- render ---- */
function renderFilterPage(){
  app.innerHTML=
    '<div class="fltwrap">'+
      '<div class="fltbuckets" id="fltbuckets"></div>'+
      '<div class="fltbar"><button class="fltaddbtn" onclick="toggleFieldPicker()">+ Alan Ekle</button>'+
        '<div class="fltcombine" id="fltcombine"></div>'+
        '<div class="fltcount" id="fltcount"></div></div>'+
      '<div id="fieldpicker" style="display:none"></div>'+
      '<div class="fltrows" id="fltrows"></div>'+
      '<div class="fltresults" id="fltresults"></div>'+
    '</div>';
  renderBucketPills(); renderCombineToggle(); renderFilterRows(); renderFilterResults();
}
function renderCombineToggle(){
  const el=document.getElementById('fltcombine'); if(!el) return;
  el.innerHTML='<span class="ccword">Filtreler:</span>'+
    '<button class="ccbtn'+(FILTER_STATE.combine==='and'?' on':'')+'" onclick="setCombine(\'and\')">VE (hepsi)</button>'+
    '<button class="ccbtn'+(FILTER_STATE.combine==='or'?' on':'')+'" onclick="setCombine(\'or\')">VEYA (herhangi biri)</button>';
}
function renderBucketPills(){
  const el=document.getElementById('fltbuckets'); if(!el) return;
  // "Hepsi": hiçbir pozisyona sınırlamaz — 10 kovanın tamamı tek havuzda (bir oyuncu
  // oynadığı her pozisyon için ayrı satır olarak görünür, bkz. renderFilterResults'taki
  // "Poz" sütunu). Diğer pillerden ayırt edilsin diye pozisyon-grubu rengi almıyor.
  el.innerHTML='<button class="fltpill allbucket'+(FILTER_STATE.bucket==='ALL'?' on':'')+'" onclick="setFilterBucket(\'ALL\')">⊞ Hepsi</button>'+
    POS10_ORDER.map(b=>'<button class="fltpill'+(b===FILTER_STATE.bucket?' on':'')+'" style="--pgc:'+posGroupColor(b)+'" onclick="setFilterBucket('+jsonAttr(b)+')">'+b+' · '+(BUCK_TR[b]||b)+'</button>').join('');
}
function setFilterBucket(b){
  if(b===FILTER_STATE.bucket) return;
  FILTER_STATE.bucket=b;
  FILTER_STATE.filters=FILTER_STATE.filters.filter(f=> f.group==='genel' || fieldsForCategory(f.group).some(x=>x.field===f.field));
  FLT_SORT={type:'ca',idx:null,dir:-1};   // eski sıralama sütunu (indeks) artık geçersiz olabilir
  closeFieldPicker(); renderBucketPills(); renderFilterRows(); renderFilterResults();
}
function toggleFieldPicker(){
  const el=document.getElementById('fieldpicker'); if(!el) return;
  if(el.style.display==='none'){ el.style.display='block'; renderFieldPicker(); } else el.style.display='none';
}
function closeFieldPicker(){ const el=document.getElementById('fieldpicker'); if(el) el.style.display='none'; }
function setPickerCat(c){ PICKER_CAT=c; renderFieldPicker(); }
function toggleCmBuilder(){ CM_FORM_OPEN=!CM_FORM_OPEN; renderFieldPicker(); }
function renderCmBuilderHtml(){
  const cols=statColsForBucket(FILTER_STATE.bucket), xc=DB.meta.xcat||{};
  const optHtml=cols.map(k=>'<option value="'+esc(k)+'">'+esc(xc[k]||k)+'</option>').join('');
  let html='<div class="cmbox"><button class="cmtogglebtn" onclick="toggleCmBuilder()">'+(CM_FORM_OPEN?'✕ Kapat':'+ Özel Metrik Oluştur')+'</button>';
  if(CM_FORM_OPEN){
    html+='<div class="cmform">'+
      '<select id="cmA" class="fltsel">'+optHtml+'</select>'+
      '<select id="cmOp" class="fltsel">'+Object.entries(CM_OPS).map(([k,o])=>'<option value="'+k+'">'+o.label+'</option>').join('')+'</select>'+
      '<select id="cmB" class="fltsel">'+optHtml+'</select>'+
      '<input id="cmLabel" class="fltnumtext" type="text" placeholder="Etiket (opsiyonel)"/>'+
      '<button class="cmcreatebtn" onclick="createCustomMetric()">Oluştur</button>'+
      '</div>';
  }
  return html+'</div>';
}
function createCustomMetric(){
  const aField=document.getElementById('cmA').value, bField=document.getElementById('cmB').value,
        op=document.getElementById('cmOp').value, lbl=(document.getElementById('cmLabel').value||'').trim();
  if(!aField || !bField || aField===bField) return;
  const xc=DB.meta.xcat||{};
  const label = lbl || ((xc[aField]||aField)+' '+CM_OPS[op].sym+' '+(xc[bField]||bField));
  CUSTOM_METRICS.push({id:'__cm__'+(CM_SEQ++), label, aField, bField, op});
  CM_FORM_OPEN=false;
  renderFieldPicker();
}
function deleteCustomMetric(id){
  CUSTOM_METRICS=CUSTOM_METRICS.filter(x=>x.id!==id);
  // aynı FLT_SORT indeks-kayması düzeltmesi (bkz. removeFilter) — özel metrik aktif bir
  // filtre satırıysa ve ondan SONRAKİ bir sütuna göre sıralanıyorsa indeks kaymalı,
  // TAM o sütunsa sıfırlanmalı; ilgisiz bir sütuna göre sıralanıyorsa hiç dokunulmamalı.
  const ri=FILTER_STATE.filters.findIndex(f=>f.field===id);
  if(ri!==-1){
    FILTER_STATE.filters.splice(ri,1);
    if(FLT_SORT.type==='filter'){
      if(FLT_SORT.idx===ri) FLT_SORT={type:'ca',idx:null,dir:-1};
      else if(FLT_SORT.idx>ri) FLT_SORT.idx--;
    }
  }
  renderFieldPicker(); renderFilterRows(); renderFilterResults();
}
function renderFieldPicker(){
  const el=document.getElementById('fieldpicker'); if(!el || el.style.display==='none') return;
  const cats=[['radar','İstatistik'],['bs','Attribute'],['rol','Rol Uyum'],['genel','Genel']];
  // her kategori butonunda kaç alan olduğu görünsün — "boş görünüyor" hissini önler
  const counts=Object.fromEntries(cats.map(([k])=>[k, fieldsForCategory(k).length]));
  const items=fieldsForCategory(PICKER_CAT).filter(x=>!FILTER_STATE.filters.some(f=>f.group===PICKER_CAT && f.field===x.field));
  const builder = PICKER_CAT==='radar' ? renderCmBuilderHtml() : '';
  el.innerHTML='<div class="fpchead">Kategori seçin, sonra listeden alan ekleyin</div>'+
    '<div class="fpcats">'+cats.map(([k,l])=>'<button class="fpcat'+(k===PICKER_CAT?' on':'')+'" onclick="setPickerCat('+jsonAttr(k)+')">'+l+'<span class="n">'+counts[k]+'</span></button>').join('')+'</div>'+
    builder+
    '<div class="fplist">'+(items.length?items.map(x=>{
      const isCustom=x.field.indexOf('__cm__')===0;
      const del=isCustom?'<span class="fpdel" onclick="event.stopPropagation();deleteCustomMetric('+jsonAttr(x.field)+')">🗑</span>':'';
      return '<div class="fpitemwrap"><button class="fpitem" onclick="addFilter('+jsonAttr(PICKER_CAT)+','+jsonAttr(x.field)+')"><span>'+esc(x.label)+'</span><span class="sub">'+esc(x.sub)+'</span></button>'+del+'</div>';
    }).join(''):'<div class="fltempty">'+(counts[PICKER_CAT]===0?'bu pozisyon için uygun alan yok':'tüm alanlar zaten eklendi')+'</div>')+'</div>';
}
function addFilter(group, field){
  const meta=fieldsForCategory(group).find(x=>x.field===field);
  if(!meta) return;
  let filt;
  const gtype = group==='genel' ? GENERAL_FIELDS[field].type : null;
  if(gtype==='select' || gtype==='select-multi-value'){
    filt={group,field,label:meta.label,type:gtype,values:[],mode:'or'};
  } else if(group==='genel'){
    const d=GENERAL_FIELDS[field];
    filt={group,field,label:meta.label,type:'numeric',min:d.dmin,max:d.dmax};
  } else if(group==='radar'){
    const r=fieldRange(field);
    filt={group,field,label:meta.label,type:'numeric',min:r.min,max:r.max};
  } else if(group==='bs'){
    filt={group,field,label:meta.label,type:'bs-tier',minTier:0,maxTier:BS_TIER_LABELS.length-1};
  } else {
    filt={group,field,label:meta.label,type:'numeric',min:0,max:100};
  }
  FILTER_STATE.filters.push(filt);
  closeFieldPicker(); renderFilterRows(); renderFilterResults();
}
// BUG DÜZELTMESİ: filtre silinince FLT_SORT.idx yalnız TAM eşitlikte sıfırlanıyordu —
// ör. 3 filtre varken filtre sütunu #2'ye göre sırala, sonra filtre #0'ı sil: kalan
// filtreler kayar (eski #1->#0, eski #2->#1) ama FLT_SORT.idx hâlâ 2'de kalıyordu ->
// artık dizide olmayan bir indekse işaret ediyor, sıralama sessizce bozuluyordu (ok
// işareti kayboluyor, sıra ham CA'ya değil "undefined" karşılaştırmasına dönüyordu).
// Şimdi: silinen tam o sütünse sıfırla, silinenden SONRAKİ bir sütünse indeksi kaydır.
function removeFilter(i){
  FILTER_STATE.filters.splice(i,1);
  if(FLT_SORT.type==='filter'){
    if(FLT_SORT.idx===i) FLT_SORT={type:'ca',idx:null,dir:-1};
    else if(FLT_SORT.idx>i) FLT_SORT.idx--;
  }
  renderFilterRows(); renderFilterResults();
}
function updateFilterNum(i,which,val){ FILTER_STATE.filters[i][which]=(val===''?null:parseFloat(val)); renderFilterResults(); }
// Attribute KADEME ARALIĞI: which='minTier'|'maxTier'. Kullanıcı alt sınırı
// üst sınırın üstüne (ya da tam tersi) çekerse öteki ucu da beraber sürükler — ters/boş
// bir aralık sessizce oluşmasın. Aralık değiştiğinde öteki select'in görünen değeri de
// değişebileceğinden (bu sürüklenme durumunda) satırlar TAMAMEN yeniden render edilir.
function updateFilterTierRange(i, which, val){
  const f=FILTER_STATE.filters[i];
  f[which]=parseInt(val,10)||0;
  if(f.minTier>f.maxTier){
    if(which==='minTier') f.maxTier=f.minTier; else f.minTier=f.maxTier;
  }
  renderFilterRows(); renderFilterResults();
}
function toggleFilterChip(i,val){ const f=FILTER_STATE.filters[i]; f.values=f.values.includes(val)?f.values.filter(x=>x!==val):[...f.values,val]; renderFilterRows(); renderFilterResults(); }
function updateFilterSelect(i,sel){ FILTER_STATE.filters[i].values=[...sel.selectedOptions].map(o=>o.value); renderFilterResults(); }
function setFilterMode(i,m){ FILTER_STATE.filters[i].mode=m; renderFilterRows(); renderFilterResults(); }
function setCombine(m){ FILTER_STATE.combine=m; renderCombineToggle(); renderFilterResults(); }
function renderFilterRows(){
  const el=document.getElementById('fltrows'); if(!el) return;
  if(!FILTER_STATE.filters.length){ el.innerHTML='<div class="fltempty">Henüz filtre eklenmedi — "+ Alan Ekle" ile başlayın.</div>'; return; }
  const grpLbl={radar:'İSTAT',bs:'ATTR',rol:'ROL',genel:'GENEL'};
  el.innerHTML=FILTER_STATE.filters.map((f,i)=>{
    let ctrl;
    if(f.type==='bs-tier'){
      // Attribute kademe ARALIĞI: iki dropdown (alt kademe – üst kademe), sayı kutusu
      // yok, ham 0-100 değeri kullanıcıya hiçbir yerde gösterilmiyor. Eksene özel kesim
      // noktası kullanır (bsTierCuts(field)) — bkz. BS_LABEL için ayrı isim haritası.
      const cuts = bsTierCuts(f.field);
      const optHtml=(sel, isMax)=>BS_TIER_LABELS.map((lbl,idx)=>{
        const bound = isMax ? (idx<cuts.length?' title="< '+cuts[idx]+'"':'') : (idx>=1?' title="≥ '+cuts[idx-1]+'"':'');
        return '<option value="'+idx+'"'+(sel===idx?' selected':'')+bound+'>'+esc(lbl)+'</option>';
      }).join('');
      ctrl='<select class="fltsel" onchange="updateFilterTierRange('+i+',\'minTier\',this.value)">'+optHtml(f.minTier,false)+'</select>'+
           '<span style="color:var(--faint)">–</span>'+
           '<select class="fltsel" onchange="updateFilterTierRange('+i+',\'maxTier\',this.value)">'+optHtml(f.maxTier,true)+'</select>';
    } else if(f.type==='numeric'){
      ctrl='<input class="fltnum" type="number" value="'+(f.min??'')+'" onchange="updateFilterNum('+i+',\'min\',this.value)"/>'+
           '<span style="color:var(--faint)">–</span>'+
           '<input class="fltnum" type="number" value="'+(f.max??'')+'" onchange="updateFilterNum('+i+',\'max\',this.value)"/>';
    } else {
      const opts=(GENERAL_FIELDS[f.field].options?GENERAL_FIELDS[f.field].options():[]);
      if(opts.length<=10){
        ctrl='<div class="fltchips">'+opts.map(o=>'<button class="fltchip'+(f.values.includes(o)?' on':'')+'" onclick="toggleFilterChip('+i+','+jsonAttr(o)+')">'+esc(o)+'</button>').join('')+'</div>';
      } else {
        ctrl='<select class="fltsel" multiple size="5" onchange="updateFilterSelect('+i+',this)">'+opts.map(o=>'<option value="'+esc(o)+'"'+(f.values.includes(o)?' selected':'')+'>'+esc(o)+'</option>').join('')+'</select>';
      }
      // VE/VEYA: seçili değerler birbiriyle nasıl birleşsin (yalnız 2+ değerde anlamlı,
      // ama tutarlılık için her zaman gösterilir)
      ctrl+='<span class="rowcombine"><button class="ccmini'+(f.mode!=='and'?' on':'')+'" onclick="setFilterMode('+i+',\'or\')">VEYA</button>'+
            '<button class="ccmini'+(f.mode==='and'?' on':'')+'" onclick="setFilterMode('+i+',\'and\')">VE</button></span>';
    }
    return '<div class="fltrow"><span class="fgrp">'+(grpLbl[f.group]||f.group)+'</span><span class="fname">'+esc(f.label)+'</span>'+ctrl+'<span class="fltrm" onclick="removeFilter('+i+')">×</span></div>';
  }).join('');
}
// sonuç tablosu sıralama: CA ve eklenen her filtre sütunu tıklanınca aktif olur, tekrar
// tıklayınca yön değişir. Değeri olmayan (null) satırlar her zaman en sona düşer.
function sortAccessor(p){
  if(FLT_SORT.type==='ca') return p.ca;
  const f=FILTER_STATE.filters[FLT_SORT.idx];
  return f ? fieldValue(p,f) : null;
}
function cmpVal(va,vc){
  if(typeof va==='number' && typeof vc==='number') return va-vc;
  return String(va).localeCompare(String(vc),'tr');
}
function setSort(type, idx){
  if(FLT_SORT.type===type && FLT_SORT.idx===idx) FLT_SORT.dir=-FLT_SORT.dir;
  else FLT_SORT={type,idx,dir:-1};
  renderFilterResults();
}
function sortArrow(type, idx){
  if(FLT_SORT.type!==type || FLT_SORT.idx!==idx) return '';
  return FLT_SORT.dir===1 ? ' ▲' : ' ▼';
}
// sonuç tablosu hücresi: fieldValue null/sayı/metin döndürebildiği gibi 'pos' gibi
// dizi-değerli alanlarda dizi de döndürür (bkz. GENERAL_FIELDS.pos) — hepsini kapsar.
// f verilirse ve Attribute (bs) sütunuysa ham 0-100 sayısı yerine kademe etiketi
// gösterir (tutarlılık: filtre girişinde de artık ham sayı yok, bkz. bs-tier).
function fmtCellVal(v, f){
  if(f && f.group==='bs') return bsTierLabel(f.field, v);
  if(v==null) return '—';
  if(Array.isArray(v)) return v.length ? esc(v.join(', ')) : '—';
  if(typeof v==='number') return Math.round(v*10)/10;
  return esc(v);
}
// "Hepsi" modunda aynı oyuncu birden çok kova-girişiyle (LW/RW/ST gibi, her biri motorun
// veri modelinde GERÇEKTEN ayrı bir kayıt — bkz. id="{rowid}_{bucket}") filtreyi ayrı ayrı
// geçebilir. Bu, veri tekrarı DEĞİL (oyuncunun her pozisyonda kendi radar/rol-uyum değeri
// var, o yüzden ayrı kayıt gerekiyor) — ama TABLOYA yazdırmadan önce tekilleştirilmeli ki
// farklı oyuncularmış gibi görünmesin. rowid (id'nin "_bucket" öncesi kısmı) tekillik
// anahtarı; birden çok geçen giriş varsa oyuncunun BİRİNCİL pozisyonuna (p.best) ait giriş
// varsa o temsilci seçilir, yoksa en yüksek CA'lı giriş (CA zaten pozisyondan bağımsız aynı
// değer, ama garanti olsun diye).
function dedupeHitsByPlayer(hits){
  const byRow=new Map();
  for(const p of hits){
    const rowid=p.id.slice(0,p.id.lastIndexOf('_'));
    const cur=byRow.get(rowid);
    if(!cur){ byRow.set(rowid,p); continue; }
    const curIsBest=cur.bucket===cur.best, pIsBest=p.bucket===p.best;
    if(pIsBest && !curIsBest) byRow.set(rowid,p);
    else if(pIsBest===curIsBest && (p.overall||0)>(cur.overall||0)) byRow.set(rowid,p);
  }
  return [...byRow.values()];
}
// "POZ" hücresi: birincil pozisyon (p.best, kalın) + varsa diğer oynayabildiği pozisyonlar
// (p.pos'tan birincil çıkarılmış, küçük/ikincil) — ör. "LW · +RW, ST"
function posCellHtml(p){
  const primary=p.best||p.bucket;
  const others=(p.pos||[]).filter(x=>x!==primary);
  return '<span class="posdot" style="background:'+posGroupColor(primary)+'"></span><b>'+primary+'</b>'+
    (others.length?'<span class="possec"> · +'+others.join(', ')+'</span>':'');
}
function renderFilterResults(){
  const el=document.getElementById('fltresults'); if(!el) return;
  const cnt=document.getElementById('fltcount');
  const b=FILTER_STATE.bucket;
  const isAll=b==='ALL';
  const pool=isAll ? DB.players : DB.players.filter(p=>p.bucket===b);
  const poolCount=isAll ? new Set(pool.map(p=>p.id.slice(0,p.id.lastIndexOf('_')))).size : pool.length;
  let hits=pool.filter(p=>matchesFilters(p,FILTER_STATE.filters,FILTER_STATE.combine));
  if(isAll) hits=dedupeHitsByPlayer(hits);
  hits.sort((a,c)=>{
    const va=sortAccessor(a), vc=sortAccessor(c);
    if(va==null && vc==null) return 0;
    if(va==null) return 1;
    if(vc==null) return -1;
    return cmpVal(va,vc)*FLT_SORT.dir;
  });
  if(cnt) cnt.textContent=hits.length.toLocaleString('tr')+' / '+poolCount.toLocaleString('tr')+' oyuncu';
  // extraCols artık TÜM aktif filtreleri sütun olarak gösterir (eskiden ilk 3'le
  // sınırlıydı) — temel sütunlar (Oyuncu/Takım/Lig/Yaş/CA) sticky, metrik
  // sütunları yatay scroll ile görünür; çok filtre eklenince tablo daralmak yerine kayar.
  const LIMIT=200, shown=hits.slice(0,LIMIT), extraCols=FILTER_STATE.filters;
  if(!shown.length){ el.innerHTML='<div class="fltempty">Bu kriterlere uyan oyuncu yok.</div>'; return; }
  el.innerHTML='<table class="flttable"><thead><tr>'+
    '<th class="stk stk1">Oyuncu</th><th class="stk stk2">Takım</th><th class="stk stk3">Lig</th><th class="stk stk4">Yaş</th>'+
    '<th class="stk stk5 srt" onclick="setSort(\'ca\',null)">BSX Skoru'+sortArrow('ca',null)+'</th>'+
    (isAll?'<th>Poz</th>':'')+
    extraCols.map((f,i)=>'<th class="srt" onclick="setSort(\'filter\','+i+')">'+esc(f.label)+sortArrow('filter',i)+'</th>').join('')+
    '</tr></thead><tbody>'+
    shown.map(p=>'<tr class="pr" onclick="go('+jsonAttr(p.id)+')">'+
      '<td class="stk stk1 nm" title="'+esc(p.name)+'">'+esc(p.name)+'</td>'+
      '<td class="stk stk2" title="'+esc(p.team||'')+'">'+esc(p.team||'—')+'</td>'+
      '<td class="stk stk3" title="'+esc(leagueShort(p.league))+'">'+esc(leagueShort(p.league))+'</td>'+
      '<td class="stk stk4">'+(p.age??'—')+'</td>'+
      '<td class="stk stk5" style="color:'+scoreColor(p.ca)+'">'+(p.ca??'—')+'</td>'+
      (isAll?'<td>'+posCellHtml(p)+'</td>':'')+
      extraCols.map(f=>'<td>'+fmtCellVal(fieldValue(p,f),f)+'</td>').join('')+
    '</tr>').join('')+'</tbody></table>'+
    (hits.length>LIMIT?'<div class="fltmore">'+(hits.length-LIMIT)+' sonuç daha — daraltmak için filtre ekleyin.</div>':'');
}

/* ---------- boot: tam veri varsa fetch et, yoksa gömülü ---------- */
function boot(data){ DB=data; buildIndex(); const s=history.state||{};
  if(s.filtre){ setActiveTab('filtre'); renderFilterPage(); return; }
  s.team?renderSquad(s.team):render(s.id); }
fetch('./paralaks_data.json').then(r=>{if(!r.ok)throw 0;return r.json()})
  .then(d=>boot(d))
  .catch(()=>boot(JSON.parse(document.getElementById('data').textContent)));
</script>
</body>
</html>"""

html = TPL.replace("__DATA__", DATA).replace("__BUILD__", BUILD)
OUT_PATH.write_text(html, encoding='utf-8')
print(f"OK -> {OUT_PATH} ({OUT_PATH.stat().st_size / (1024*1024):.1f} MB)")
