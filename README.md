# BigStatX

Oyuncu yetenek verisini gerçek maç istatistikleriyle birleştiren, açıklanabilir/
denetlenebilir futbol scouting ve kadro planlama platformu.

🔗 **Canlı demo:** https://barisocak.github.io/BigStatX/paralaks.html

## Ne yapıyor

- **32.435 oyuncu, 541 takım, 30 lig** — tek bir veri motorunda birleştirilmiş
- **48 birleşik attribute ekseni** — birden fazla veri kaynağının en güvenilir
  tarafını esas alan, kanıtla geçersiz kılınabilen bir harmanlama mantığıyla kurulmuş
- **32 rol tanımı** — her oyuncu için pozisyon-bazlı rol uyum skoru (Derin Oyun
  Kurucu, Mezzala, Sahte 9 gibi), gerçek attribute ağırlıklarına dayalı
- **Blok Uyumu** — iki/üç oyuncunun (stoper ikilisi, çift pivot, forvet ortaklığı
  gibi) birbirine göre uyumunu, 10 farklı oyun tarzına göre hesaplayan sistem
- **Gelişmiş filtreleme** — 59 ham istatistik + 48 attribute + rol uyumu + genel
  bilgi, hepsi kombinlenebilir (VE/VEYA), özel metrik oluşturma
- **Takım analizi** — otomatik ilk 11, kadro açığı tespiti, sistem uyumu
- **Lig kalite kademesi** — her lig kendi ortalama seviyesine göre otomatik sınıflandırılıyor

## Temel felsefe: yetenek–performans ilişkisi

Bir oyuncunun **yapabildiği** (kapasite/yetenek) ile **gerçekte yaptığı** (maç
istatistikleri) arasındaki ilişkiyi kurmak — bu ikisi arasındaki fark/örtüşme,
bir oyuncunun potansiyelini mi yoksa gerçek performansını mı yansıttığını ayırt
etmeyi sağlıyor. Sistemin en özgün katmanı burası.

## Kulüpler için

Sistemdeki ~600 takımlık geniş havuz sayesinde:

- **Altyapı değerlendirmesi** — genç oyuncular için düzenli, karşılaştırılabilir raporlar
- **Tek takım odaklı planlama** — kendi kadronuzun sistem uyumu, kadro açıkları,
  rol dağılımı tek ekranda; geniş havuzdan ihtiyaca uygun profil taraması
- **Sözleşme bazlı transfer stratejisi** — sözleşmesi biten oyuncuları erken tespit
- **30 ligin tamamına erişim** — büyük liglerin dışında kalan, keşfedilmemiş havuzlar
- **Veri kalitesiyle doğru orantılı derinlik** — proje şu an kısıtlı/genel veriyle
  geliştirildi; kulübe özel, daha zengin veri sağlandığında analiz derinliği ve
  isabet oranı doğrudan artacak şekilde tasarlandı

## Nasıl çalışıyor

```
Ham veri → veri motoru → tam veritabanı (JSON)
        ↓
demo alt-küme üretimi
        ↓
frontend derleyici → tek dosyalık site
```

Tek dosyalık frontend (vanilla JS/CSS, framework/npm bağımlılığı yok), motor
Python/pandas ile çalışıyor.

## Yol haritası

- Kulübe özel branding/tema desteği
- Çoklu sezon geçmişi ile oyuncu gelişim trendi
- Kullanıcı yetkilendirme (scout/teknik direktör/yönetici seviyeleri)
- Maç bazlı video/olay verisiyle entegrasyon
- Rakip takım analiz raporları
- İngilizce dil desteği
- Tüm lig/takımlara tam erişim (şu an demo, sınırlı alt-küme)

## Not

Bu demo, tam veritabanının küçük bir alt-kümesiyle çalışıyor. Ham veri
(`bigstatxdb_v8.xlsx`) ve tam veritabanı (`paralaks_data.json`, ~220 MB) bu
repoda yer almıyor — yalnız motor/derleyici kaynak kodu ve demo alt-küme
(`paralaks_demo.json`) burada.
