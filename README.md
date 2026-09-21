# 🎓 GTÜ Duyuru Takip & Telegram Bildirim Botu

Gebze Teknik Üniversitesi **Genel Duyurular** ve **Siber Güvenlik Meslek Yüksekokulu Duyuruları** sayfalarını 30 dakikada bir otomatik olarak kontrol eden, yeni bir duyuru yayınlandığında Telegram üzerinden anında bildirim gönderen **%100 ücretsiz, sunucusuz (serverless) ve 7/24 çalışan** otomasyon sistemi.

---

## 📌 Özellikler

- ⏱ **7/24 Dakik Takip:** cron-job.org + GitHub Actions mimarisi ile sıfır gecikmeli kontrol.
- 🔔 **Anlık Telegram Bildirimi:** Sayfa adı, duyuru başlığı ve doğrudan duyuru bağlantısı.
- 🛡 **Anti-Spam Koruması:** Bot ilk kez çalıştığında geçmişteki yüzlerce eski duyuruyu göndermez; mevcut duyuruları hafızaya alır ve sadece sistemin kurulduğunu bildiren tek bir mesaj gönderir. Sonrasında yalnızca yeni eklenen duyuruları iletir.
- 💾 **Kendi Kendini Yöneten Durum:** Ek veritabanı veya sunucu gerektirmez; `seen_announcements.json` dosyası GitHub Actions tarafından otomatik olarak güncellenir.

---

## 🚀 Adım Adım Kurulum Rehberi (5 Dakika)

Bu sistemi kendi Telegram hesabınız için kurmak isterseniz aşağıdaki adımları sırayla takip etmeniz yeterlidir:

### 1. Bu Repoyu Alın (Fork veya Kendi Reponuzu Açın)
- Bu sayfanın sağ üstünde yer alan **Fork** butonuna basarak projeyi kendi GitHub hesabınıza kopyalayın (veya dosyaları kendi oluşturduğunuz yeni bir repoya yükleyin).

---

### 2. Telegram Botunuzu Kurun ve Bilgilerinizi Alın

#### A. Bot Token Alma:
1. Telegram'da **[@BotFather](https://t.me/BotFather)** botunu açın ve `/start` deyin.
2. `/newbot` komutunu gönderin.
3. Botunuz için bir isim ve kullanıcı adı belirleyin (Örn: `AliGtuDuyuruBot`).
4. BotFather'ın verdiği **HTTP API Token**'ı kopyalayın (Örn: `7123456789:AAHfk...`).
5. **ÖNEMLİ:** Yeni kurduğunuz botun sayfasına gidip **Başlat (Start)** butonuna mutlaka basın *(Botun size mesaj atabilmesi için bu şarttır)*.

#### B. Telegram Chat ID Öğrenme:
1. Telegram'da **[@userinfobot](https://t.me/userinfobot)** botuna gidin ve `/start` yazın.
2. Botun size söylediği `Id` numarasını (Örn: `123456789`) kopyalayın.

---

### 3. GitHub Reponuzun Ayarlarını Yapın

#### A. Gizli Anahtarları (Secrets) Ekleyin:
1. GitHub reponuzda **Settings** > **Secrets and variables** > **Actions** sekmesine gidin.
2. **New repository secret** butonuna tıklayarak şu 2 anahtarı ekleyin:
   - **`TELEGRAM_BOT_TOKEN`**: BotFather'dan aldığınız token.
   - **`TELEGRAM_CHAT_ID`**: userinfobot'tan aldığınız numerik ID.

#### B. Repoya Yazma İzni Verin:
1. Reponuzda **Settings** > **Actions** > **General** sayfasına gidin.
2. Sayfanın en altındaki **Workflow permissions** bölümünü bulun.
3. **Read and write permissions** seçeneğini işaretleyip **Save** deyin.

---

### 4. GitHub Erişim Anahtarı (Personal Access Token) Alın

cron-job.org'un reponuzu tetikleyebilmesi için bir GitHub erişim token'ına ihtiyacı vardır:
1. GitHub'da sağ üstteki profil fotoğrafınıza tıklayıp **Settings**'e gidin.
2. Sol menünün en altındaki **Developer settings** > **Personal access tokens** > **Tokens (classic)** bölümünü açın.
3. **Generate new token (classic)** butonuna tıklayın:
   - **Note:** `CronJob Trigger` yazabilirsiniz.
   - **Expiration:** No expiration veya 90 days seçin.
   - **Scopes:** Hem **`repo`** hem de **`workflow`** kutucuklarını mutlaka işaretleyin.
4. En alttan yeşil **Generate token** butonuna basın ve çıkan `ghp_...` anahtarını kopyalayın.

---

### 5. 7/24 Kesintisiz Zamanlayıcıyı Kurun (cron-job.org)

GitHub'ın dahili zamanlayıcısının gecikmelerine takılmamak ve 30 dakikada bir tam vaktinde çalışması için:

1. **[cron-job.org](https://cron-job.org)** sitesine ücretsiz kayıt olun.
2. **Cronjobs** > **Create Cronjob** butonuna tıklayın:
   - **Title:** `GTÜ Duyuru Takip Botu`
   - **URL:** *(Kullanıcı adınızı ve repo adınızı yazın)*:
     ```text
     https://api.github.com/repos/KULLANICI_ADINIZ/REPO_ADINIZ/actions/workflows/tracker.yml/dispatches
     ```
   - **Schedule:** `Every 30 minutes` (Her 30 dakikada bir).
3. **Advanced** (Gelişmiş) bölümünü açın:
   - **Request Method:** `POST`
   - **Request Headers (Başlıklar):** Yanlarındaki **"+" (Ekle)** butonuna basarak şu 3 başlığı ekleyin:
     | Header Adı (Key) | Değeri (Value) |
     | :--- | :--- |
     | `Authorization` | `Bearer ghp_BURAYA_GITHUB_TOKENINIZ` |
     | `Accept` | `application/vnd.github+json` |
     | `User-Agent` | `GTU-Bot` |
     *(Not: `Bearer` kelimesi ile `ghp_` arasında 1 boşluk olmalıdır).*
   - **Request Body (Gövde):**
     ```json
     {"ref": "main"}
     ```
4. **Test Run** butonuna tıklayın; `204 No Content` cevabını gördükten sonra **Save** (Kaydet) deyin.

---

## 🎉 Tebrikler!

Tüm kurulum tamamlandı!
- Birkaç saniye içinde Telegram botunuzdan **"GTÜ Duyuru Botu Aktif Edildi!"** mesajı gelecektir.
- Sistem artık tamamen bulutta, 7/24, sıfır maliyetle çalışmaya devam edecek ve GTÜ'den yeni bir duyuru geldiği an doğrudan cebinize iletilecektir.
