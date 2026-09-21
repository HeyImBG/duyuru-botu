# 🎓 GTÜ Duyuru Takip & E-posta Bildirim Sistemi

Gebze Teknik Üniversitesi duyuru sayfalarını 30 dakikada bir otomatik olarak kontrol eden, yeni bir duyuru yayınlandığında ilgili öğrencilerin e-posta adreslerine anında bildirim gönderen **%100 ücretsiz, sunucusuz (serverless) ve 7/24 çalışan** otomasyon sistemi.

---

## 📌 Özellikler ve Takip Edilen Bölümler

Bu sistem şu anda GTÜ bünyesindeki 3 farklı duyuru sayfasını takip edip kişiye özel olarak yönlendirmektedir:

| Takip Edilen Sayfa | Kategori | Alıcı E-postalar |
| :--- | :--- | :--- |
| **GTÜ Genel Duyurular** | Üniversite Geneli | `beratgl2004@gmail.com`, `zeynepulubas112@gmail.com` |
| **Siber Güvenlik MYO** | Bölüm / Fakülte | `beratgl2004@gmail.com` |
| **Şehir ve Bölge Planlama** | Bölüm / Fakülte | `zeynepulubas112@gmail.com` |

- 📬 **Kişiye Özel Bildirim:** Herkes sadece kendisini ilgilendiren duyuruların e-postasını alır.
- 📱 **Mobil Uyumlu Şık E-postalar:** Doğrudan duyuruya yönlendiren buton ve etiket içeren modern HTML tasarımı.
- 🛡 **Anti-Spam Koruması:** Yeni bir sayfa veya kullanıcı eklendiğinde geçmişteki yüzlerce eski duyuru maile boca edilmez; sadece sistemin başladığını bildiren tek bir hoş geldiniz maili gönderilir, ardından yalnızca **yeni** duyurular iletilir.
- ⏱ **7/24 Kesintisiz Takip:** `cron-job.org` + `GitHub Actions` altyapısıyla bilgisayarınız kapalıyken bile arka planda tıkır tıkır çalışır.

---

## 🚀 Adım Adım Kurulum Rehberi (Kendi Bölümünüz İçin Kurun)

Arkadaşlarınız veya başka bölümdeki öğrenciler bu projeyi kendi bölümleri ve e-postaları için kurmak isterse aşağıdaki adımları takip edebilir:

### 1. Bu Repoyu Forklayın
- Sayfanın sağ üst köşesinde bulunan **Fork** butonuna tıklayarak bu repoyu kendi GitHub hesabınıza kopyalayın.

---

### 2. Kendi Bölümünüzü ve E-postanızı Ayarlayın
[`tracker.py`](tracker.py) dosyasındaki `PAGES` listesini kendi bölümünüze göre düzenleyin:

```python
PAGES = [
    {
        "name": "GTÜ Genel Duyurular",
        "url": "https://www.gtu.edu.tr/kategori/9/0/display.aspx",
        "recipients": ["kendi_mailiniz@gmail.com"],
    },
    {
        "name": "Kendi Bölümünüzün Adı",
        "url": "https://www.gtu.edu.tr/kategori/XXXX/0/display.aspx",
        "recipients": ["kendi_mailiniz@gmail.com", "arkadasinizin_maili@gmail.com"],
    },
]
```

---

### 3. Google Uygulama Şifresi (App Password) Alın

Gmail'in bot üzerinden otomatik mail gönderebilmesi için 16 haneli bir uygulama şifresi gerekir:

1. [myaccount.google.com/security](https://myaccount.google.com/security) adresine gidin.
2. Hesabınızda **2 Adımlı Doğrulama**'nın açık olduğundan emin olun.
3. [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) sayfasına gidin *(veya arama kutusuna "Uygulama şifreleri" yazın)*.
4. Uygulama adına `GTU Duyuru Botu` yazıp **Oluştur** deyin.
5. Verilen **16 haneli kodu** (Örn: `abcd efgh ijkl mnop`) kopyalayın.

---

### 4. GitHub Reponuzun Ayarlarını Yapın

#### A. Gizli Anahtarları (Secrets) Ekleyin:
1. GitHub reponuzda **Settings** > **Secrets and variables** > **Actions** bölümüne gidin.
2. **New repository secret** butonuna tıklayarak şu 2 anahtarı ekleyin:
   - **`GMAIL_USER`**: Gönderici Gmail adresiniz (örn: `adiniz@gmail.com`).
   - **`GMAIL_APP_PASSWORD`**: Az önce aldığınız 16 haneli Google şifresi.

#### B. Repoya Yazma İzni Verin:
1. **Settings** > **Actions** > **General** sayfasına gidin.
2. Sayfanın altındaki **Workflow permissions** kısmından **Read and write permissions** seçeneğini işaretleyip **Save** butonuna basın.

---

### 5. 7/24 Zamanlayıcıyı Kurun (cron-job.org)

Sistemin her 30 dakikada bir otomatik çalışması için:

1. **[cron-job.org](https://cron-job.org)** sitesine ücretsiz üye olun.
2. **Cronjobs** > **Create Cronjob** butonuna tıklayın:
   - **Title:** `GTÜ Duyuru Takipçisi`
   - **URL:** 
     ```text
     https://api.github.com/repos/KULLANICI_ADINIZ/REPO_ADINIZ/actions/workflows/tracker.yml/dispatches
     ```
   - **Schedule:** `Every 30 minutes`
3. **Advanced** (Gelişmiş) bölümüne tıklayın:
   - **Request Method:** `POST`
   - **Request Headers:**
     | Key | Value |
     | :--- | :--- |
     | `Authorization` | `Bearer GITHUB_PERSONAL_ACCESS_TOKENINIZ` |
     | `Accept` | `application/vnd.github+json` |
     | `User-Agent` | `GTU-Bot` |
   - **Request Body:**
     ```json
     {"ref": "main"}
     ```
4. **Test Run** butonuna basın, `204 No Content` gördükten sonra **Save** diyerek kaydedin.

---

## 🎉 Tebrikler!
Artık sistem tamamen bulutta 7/24 çalışır. GTÜ'de veya bölümünüzde yeni bir duyuru yayınlandığı an hem sizin hem de arkadaşlarınızın gelen kutusuna şık bir bildirim e-postası düşecektir!
