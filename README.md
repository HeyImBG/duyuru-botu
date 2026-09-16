# 🎓 GTÜ Duyuru Takip & Telegram Bildirim Botu

Gebze Teknik Üniversitesi **Genel Duyurular** ve **Siber Güvenlik Meslek Yüksekokulu Duyuruları** sayfalarını 30 dakikada bir otomatik olarak kontrol eden, yeni bir duyuru yayınlandığında Telegram üzerinden anında bildirim gönderen **%100 ücretsiz, sunucusuz (serverless) ve 7/24 çalışan** otomasyon sistemi.

---

## 📌 Özellikler

- ⏱ **7/24 Otomatik Takip:** GitHub Actions ile her 30 dakikada bir kontrol (`cron: '*/17,47 * * * *'`).
- 🔔 **Anlık Telegram Bildirimi:** Sayfa adı, duyuru başlığı ve doğrudan duyuru bağlantısı.
- 🛡 **Anti-Spam Koruması:** Bot ilk kez çalıştığında geçmişteki onlarca eski duyuruyu göndermez; mevcut duyuruları hafızaya alıp yalnızca botun başladığını bildiren tek bir mesaj gönderir. Sonrasında yalnızca yeni eklenen duyurular bildirilir.
- 💾 **Kendi Kendini Yöneten Durum:** Ek veritabanı gerektirmez; `seen_announcements.json` dosyası GitHub Actions tarafından otomatik olarak repoya güncellenir (`git push`).

---

## 🚀 Kurulum Adımları (5 Dakika)

### 1. Telegram Botu Oluşturma
1. Telegram uygulamasında [@BotFather](https://t.me/BotFather) botunu bulun ve başlatın.
2. `/newbot` komutunu gönderin.
3. Botunuz için bir isim ve kullanıcı adı belirleyin (Örn: `GtuDuyuruBot` / `gtu_duyuru_bot`).
4. BotFather size bir **HTTP API Token** verecektir (Örn: `7123456789:AAHfk...`). Bu token'ı bir yere not edin.
5. Yeni oluşturduğunuz botun sohbetine gidin ve **Başlat (Start)** butonuna basın. *(Önemli: Botun size mesaj atabilmesi için en az bir kez başlatmış olmanız gerekir)*.

### 2. Telegram Chat ID'nizi Öğrenme
1. Telegram'da [@userinfobot](https://t.me/userinfobot) botuna gidin ve `/start` yazın.
2. Botun size döndürdüğü `Id` numarasını (Örn: `123456789`) not edin.

---

### 3. GitHub Deposu (Repository) Ayarları

#### A. Gizli Anahtarları (Secrets) Ekleyin:
1. GitHub'da bu projeyi yüklediğiniz repoya gidin.
2. **Settings** (Ayarlar) > **Secrets and variables** > **Actions** sekmesine tıklayın.
3. **New repository secret** butonuna tıklayarak şu 2 anahtarı ekleyin:
   - **`TELEGRAM_BOT_TOKEN`**: BotFather'dan aldığınız token.
   - **`TELEGRAM_CHAT_ID`**: `@userinfobot`'tan aldığınız chat ID numarası.

#### B. Workflow Yazma İznini Aktif Edin:
Actions botunun son görülen duyuruları repoya kaydedebilmesi için bu izin zorunludur:
1. Reponuzda **Settings** > **Actions** > **General** bölümüne gidin.
2. Sayfayı aşağı kaydırıp **Workflow permissions** başlığını bulun.
3. **Read and write permissions** seçeneğini işaretleyin.
4. **Save** (Kaydet) butonuna tıklayın.

---

## 🧪 İlk Test (Manuel Çalıştırma)

GitHub'a kodları pushladıktan sonra sistemin çalıştığını doğrulamak için:
1. GitHub reponuzda üst menüden **Actions** sekmesine gidin.
2. Sol taraftan **GTÜ Duyuru Kontrolü** iş akışını seçin.
3. Sağdaki **Run workflow** butonuna tıklayın.
4. Birkaç saniye içinde Telegram botunuzdan:
   > 🤖 **GTÜ Duyuru Botu Aktif Edildi!**
   >
   > ✅ Sistem başarıyla kuruldu ve takip başlatıldı...
   şeklinde bir teyit mesajı alacaksınız.

Artık sistem her 30 dakikada bir otomatik çalışacak ve okulunuzdan yeni bir duyuru geldiğinde cebinize bildirim atacaktır!

---

## 💻 Bilgisayarınızda Yerel Olarak Çalıştırmak İsterseniz

```bash
# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Ortam değişkenlerini ayarlayın ve çalıştırın
export TELEGRAM_BOT_TOKEN="bot_tokeniniz"
export TELEGRAM_CHAT_ID="chat_id_niz"
python tracker.py
```
