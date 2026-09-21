#!/usr/bin/env python3
"""
GTÜ Duyuru Takip Botu (E-posta & Telegram Destekli)
Gebze Teknik Üniversitesi Genel, Siber Güvenlik MYO ve Şehir ve Bölge Planlama
duyurularını takip eder, yeni duyuru tespit ettiğinde ilgili kişilerin e-posta adreslerine
bildirim gönderir.
"""

import html
import json
import logging
import os
import re
import smtplib
import sys
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Takip edilecek sayfalar ve alıcı e-posta adresleri
PAGES = [
    {
        "name": "GTÜ Genel Duyurular",
        "url": "https://www.gtu.edu.tr/kategori/9/0/display.aspx",
        "recipients": [
            "beratgl2004@gmail.com",
            "zeynepulubas112@gmail.com",
        ],
    },
    {
        "name": "GTÜ Siber Güvenlik MYO",
        "url": "https://www.gtu.edu.tr/kategori/4302/0/display.aspx",
        "recipients": [
            "beratgl2004@gmail.com",
        ],
    },
    {
        "name": "GTÜ Şehir ve Bölge Planlama",
        "url": "https://www.gtu.edu.tr/kategori/755/0/display.aspx",
        "recipients": [
            "zeynepulubas112@gmail.com",
        ],
    },
]

BASE_URL = "https://www.gtu.edu.tr"
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seen_announcements.json")

# HTTP İstek Başlıkları
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}


def load_seen_announcements() -> Tuple[Dict[str, List[str]], bool]:
    """Kayıtlı duyuruları diskten yükler."""
    if not os.path.exists(DATA_FILE):
        return {}, True

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data, False
    except Exception as e:
        logger.error(f"Geçmiş duyuru dosyası okunurken hata oluştu: {e}")
        return {}, False


def save_seen_announcements(data: Dict[str, List[str]]) -> None:
    """Güncel duyuru listesini JSON dosyasına yazar."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Duyuru geçmişi '{DATA_FILE}' dosyasına kaydedildi.")
    except Exception as e:
        logger.error(f"Duyuru geçmişi kaydedilirken hata: {e}")


def fetch_announcements(page_url: str) -> List[Dict[str, str]]:
    """Verilen GTÜ duyuru sayfasını indirir ve duyuruları ayıklar."""
    logger.info(f"Sayfa taranıyor: {page_url}")
    try:
        response = requests.get(page_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Sayfa indirilirken hata ({page_url}): {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    announcements = []

    # GTÜ duyuru listesi yapısı: ul.list-disc li a
    links = soup.select("ul.list-disc li a")
    if not links:
        links = soup.select("li.hover\\:underline a") or soup.select("li a")

    if not links:
        pattern = re.compile(
            r'<li[^>]*class="[^"]*hover:underline[^"]*"[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            re.DOTALL | re.IGNORECASE,
        )
        for href, raw_title in pattern.findall(response.text):
            clean_title = re.sub(r'<[^>]+>', '', raw_title).strip()
            clean_href = href.strip()
            if clean_title and clean_href:
                announcements.append({
                    "title": clean_title,
                    "url": urljoin(BASE_URL, clean_href),
                })
        if announcements:
            logger.info(f"{page_url} adresinde regex ile {len(announcements)} adet duyuru bulundu.")
            return announcements

    for a in links:
        title = a.get_text(strip=True)
        raw_href = a.get("href", "").strip()

        if not title or not raw_href:
            continue

        full_url = urljoin(BASE_URL, raw_href)
        announcements.append({
            "title": title,
            "url": full_url,
        })

    logger.info(f"{page_url} adresinde {len(announcements)} adet duyuru bulundu.")
    return announcements


def send_email(smtp_user: str, smtp_pass: str, recipients: List[str], subject: str, html_body: str) -> bool:
    """Gmail SMTP üzerinden şık HTML e-posta gönderir."""
    if not smtp_user or not smtp_pass or not recipients:
        logger.warning(f"E-posta bilgileri veya alıcı eksik. Alıcılar: {recipients}")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"GTÜ Duyuru Takipçisi <{smtp_user}>"
    msg["To"] = ", ".join(recipients)

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Önce SSL (Port 465), gerekirse TLS (Port 587) dener
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, recipients, msg.as_string())
        logger.info(f"E-posta başarıyla gönderildi: {recipients} -> {subject}")
        return True
    except Exception as e_ssl:
        logger.warning(f"SSL (465) ile gönderilemedi ({e_ssl}), TLS (587) deneniyor...")
        try:
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, recipients, msg.as_string())
            logger.info(f"E-posta TLS (587) ile başarıyla gönderildi: {recipients} -> {subject}")
            return True
        except Exception as e_tls:
            logger.error(f"E-posta gönderim hatası: {e_tls}")
            return False


def build_announcement_email_html(page_name: str, title: str, url: str) -> str:
    """Yeni duyuru için modern ve duyarlı HTML e-posta şablonu."""
    safe_page = html.escape(page_name)
    safe_title = html.escape(title)
    safe_url = html.escape(url)

    return f"""\
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{safe_title}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: #f3f4f6;
      margin: 0;
      padding: 24px;
      color: #1f2937;
    }}
    .email-card {{
      max-width: 580px;
      margin: 0 auto;
      background: #ffffff;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
      border: 1px solid #e5e7eb;
    }}
    .header {{
      background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
      color: #ffffff;
      padding: 22px 28px;
    }}
    .header h1 {{
      margin: 0;
      font-size: 18px;
      font-weight: 700;
    }}
    .content {{
      padding: 28px;
    }}
    .tag {{
      display: inline-block;
      background-color: #dbeafe;
      color: #1e40af;
      font-size: 12px;
      font-weight: 700;
      padding: 4px 12px;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 16px;
    }}
    .announcement-title {{
      font-size: 17px;
      font-weight: 700;
      line-height: 1.5;
      color: #111827;
      margin: 0 0 24px 0;
    }}
    .btn {{
      display: inline-block;
      background-color: #dc2626;
      color: #ffffff !important;
      text-decoration: none;
      font-weight: 600;
      font-size: 14px;
      padding: 12px 24px;
      border-radius: 8px;
    }}
    .footer {{
      background-color: #f9fafb;
      padding: 16px 28px;
      font-size: 12px;
      color: #6b7280;
      border-top: 1px solid #f3f4f6;
      text-align: center;
    }}
  </style>
</head>
<body>
  <div class="email-card">
    <div class="header">
      <h1>🎓 Gebze Teknik Üniversitesi Duyuru Takibi</h1>
    </div>
    <div class="content">
      <div class="tag">{safe_page}</div>
      <div class="announcement-title">{safe_title}</div>
      <div>
        <a href="{safe_url}" class="btn" target="_blank">Duyuruyu Görüntüle &rarr;</a>
      </div>
    </div>
    <div class="footer">
      Bu bildirim GTÜ Duyuru Otomasyonu tarafından otomatik olarak gönderilmiştir.
    </div>
  </div>
</body>
</html>
"""


def build_welcome_email_html(page_name: str) -> str:
    """Yeni bir sayfa takibe eklendiğinde gönderilen teyit e-postası."""
    safe_page = html.escape(page_name)
    return f"""\
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <title>GTÜ Duyuru Takibi Aktif Edildi</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f3f4f6; padding: 24px; color: #1f2937; }}
    .email-card {{ max-width: 580px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e5e7eb; }}
    .header {{ background: #1e3a8a; color: #ffffff; padding: 22px; text-align: center; }}
    .header h2 {{ margin: 0; font-size: 18px; }}
    .content {{ padding: 28px; line-height: 1.6; }}
    .footer {{ background: #f9fafb; padding: 16px; font-size: 12px; color: #6b7280; text-align: center; border-top: 1px solid #f3f4f6; }}
  </style>
</head>
<body>
  <div class="email-card">
    <div class="header">
      <h2>🎉 GTÜ Duyuru Takibi Aktif Edildi!</h2>
    </div>
    <div class="content">
      <p>Merhaba,</p>
      <p><b>{safe_page}</b> sayfası için e-posta bildirim sisteminiz başarıyla devreye alındı.</p>
      <p>Okul web sitesinde bu kategoriye yeni bir duyuru eklendiğinde doğrudan bu adrese bilgilendirme e-postası iletilecektir.</p>
    </div>
    <div class="footer">
      GTÜ Duyuru Otomasyon Sistemi
    </div>
  </div>
</body>
</html>
"""


def send_telegram_message(token: str, chat_id: str, text: str) -> bool:
    """Telegram yapılandırılmışsa bildirim atar."""
    if not token or not chat_id:
        return False
    try:
        res = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=15,
        )
        return res.status_code == 200
    except Exception as e:
        logger.error(f"Telegram mesaj hatası: {e}")
        return False


def main():
    smtp_user = os.getenv("GMAIL_USER") or os.getenv("SMTP_EMAIL", "").strip()
    smtp_pass = os.getenv("GMAIL_APP_PASSWORD") or os.getenv("SMTP_PASSWORD", "").strip()
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    tg_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    seen_data, _ = load_seen_announcements()
    total_new_announcements = 0
    updated_seen_data = dict(seen_data)

    for page in PAGES:
        page_name = page["name"]
        page_url = page["url"]
        recipients = page["recipients"]

        current_items = fetch_announcements(page_url)
        if not current_items:
            continue

        # Eğer bu sayfa ilk kez taranıyorsa (örn: yeni eklenen Şehir ve Bölge Planlama):
        if page_url not in seen_data:
            logger.info(f"'{page_name}' ilk kez taranıyor. Mevcut duyurular kaydediliyor (anti-spam)...")
            updated_seen_data[page_url] = [item["url"] for item in current_items]
            # Sadece hoş geldiniz / aktif edildi maili gönder
            welcome_subject = f"✅ GTÜ {page_name} Duyuru Takibi Başlatıldı"
            welcome_html = build_welcome_email_html(page_name)
            send_email(smtp_user, smtp_pass, recipients, welcome_subject, welcome_html)
            continue

        seen_urls = set(seen_data.get(page_url, []))
        new_items = [item for item in current_items if item["url"] not in seen_urls]

        if new_items:
            logger.info(f"'{page_name}' için {len(new_items)} YENİ duyuru bulundu!")
            # Eski tarihliden yeniye doğru gönder
            for item in reversed(new_items):
                subject = f"📢 [GTÜ] {page_name}: {item['title']}"
                html_body = build_announcement_email_html(page_name, item["title"], item["url"])

                # E-posta bildirimi gönder
                send_email(smtp_user, smtp_pass, recipients, subject, html_body)

                # Eğer Telegram bilgisi varsa ve alıcılar arasında beratgl2004@gmail.com varsa Telegram'a da at
                if tg_token and tg_chat_id and "beratgl2004@gmail.com" in recipients:
                    tg_msg = (
                        f"📢 <b>{html.escape(page_name)}</b>\n\n"
                        f"📌 <b>{html.escape(item['title'])}</b>\n\n"
                        f"🔗 <a href=\"{item['url']}\">Duyuruyu Görüntüle</a>"
                    )
                    send_telegram_message(tg_token, tg_chat_id, tg_msg)

                total_new_announcements += 1
                time.sleep(1)

            all_page_urls = list(dict.fromkeys([item["url"] for item in current_items] + list(seen_urls)))
            updated_seen_data[page_url] = all_page_urls
        else:
            logger.info(f"'{page_name}' için yeni duyuru yok.")

    if updated_seen_data != seen_data:
        save_seen_announcements(updated_seen_data)
        logger.info(f"İşlem tamamlandı, veriler güncellendi (Yeni duyuru: {total_new_announcements}).")
    else:
        logger.info("Herhangi bir değişiklik olmadı.")


if __name__ == "__main__":
    main()
