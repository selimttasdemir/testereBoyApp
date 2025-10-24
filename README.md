# Kesim Kayıt Uygulaması

Bu küçük masaüstü uygulama, kesilen mamüllerin boylarını SQLite ile kaydeder, yeni eklenen kayıtları 24 saat boyunca görsel olarak vurgular (yanıp söner) ve kayıtları Excel veya PDF olarak dışa aktarır.

Gereksinimler
- Python 3.8+
- Bağımlılıklar: requirements.txt içindekiler (pandas, openpyxl, reportlab)

Kurulum
1. Sanal bir ortam oluşturun ve aktif edin (önerilir):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Bağımlılıkları yükleyin:

```bash
pip install -r requirements.txt
```

Çalıştırma

```bash
python app.py
```

Windows .exe oluşturma (paketleme)

- Bu depo içinde `build_exe.sh` adında yardımcı bir betik ekledim. Sisteminizde `pyinstaller` kuruluysa şu şekilde paketleyebilirsiniz:

```bash
# sanal ortam aktif ise
pip install pyinstaller
chmod +x build_exe.sh
./build_exe.sh
```

- Betik `--onedir` (tek klasör) modunda derleme yapar. Bu, `dist/testereBoyApp/` içinde çalıştırılabilir bir klasör oluşturur. Mevcut `data.db` dosyanız (eğer proje kökünde bulunuyorsa) otomatik olarak bu klasöre kopyalanır — böylece veriler korunur ve uygulama çalıştırıldığında değişiklikler korunur.

Not: Tek dosya (`--onefile`) modu kullanılsaydı, dahil edilen `data.db` geçici bir klasöre açılır ve uygulama tarafından yapılan değişiklikler kalıcı olmazdı. Bu nedenle kalıcı veri için `--onedir` kullanılması önerilir.

Kullanım
- "Boy (mm)" alanına sayısal değeri girin.
- "Tampon" seçeneğinden "Sabit" veya "Hareketli" seçin.
- "Ekle" butonuna basarak kayıt oluşturun.
- Yeni eklenen satırlar 24 saat boyunca sarı renkte yanıp söner.
- "Excel olarak dışa aktar" ve "PDF olarak dışa aktar" ile tüm kayıtları dosyaya kaydedebilirsiniz. Oluşturulan dosya isimleri tarih-saat içerir.

Notlar
- Veritabanı dosyası `data.db` olarak uygulama dizininde oluşturulur.
- Bu bir başlangıç uygulamasıdır; ihtiyaç varsa filtreleme, tarih aralığı seçimi, yazdırma düzeni gibi geliştirmeler eklenebilir.
