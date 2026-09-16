#!/usr/bin/env python3
"""
GTÜ Duyuru Takip Botu
Gebze Teknik Üniversitesi Genel ve Siber Güvenlik MYO duyurularını takip eder,
yeni duyuru tespit ettiğinde Telegram üzerinden bildirim gönderir.
"""

import html
import json
import logging
import os
import re
import sys
import time
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

# Takip edilecek sayfalar
PAGES = [
    {
        "name": "GTÜ Genel Duyurular",
        "url": "https://www.gtu.edu.tr/kategori/9/0/display.aspx",
    },
    {
        "name": "GTÜ Siber Güvenlik MYO",
        "url": "https://www.gtu.edu.tr/kategori/4302/0/display.aspx",
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
    """
    Kayıtlı duyuruları diskten yükler.
    Dosya yoksa ilk çalıştırma (first run) olduğunu bildirir.
    """
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
    """
    Verilen GTÜ duyuru sayfasını indirir ve duyuruları ayıklar.
    Döndürülen liste en yeni duyurudan en eskiye doğrudur.
    """
    logger.info(f"Sayfa taranıyor: {page_url}")
    try:
        response = requests.get(page_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Sayfa indirilirken hata ({page_url}): {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    announcements = []

    # GTÜ duyuru listesi yapısı: <ul class="... list-disc ..."><li class="hover:underline"><a href="...">Başlık</a></li></ul>
    # Hem sınıf bazlı hem de genel fallback ile duyuru linkleri aranır:
    links = soup.select("ul.list-disc li a")
    if not links:
        # Fallback 1: BeautifulSoup ile li içindeki a etiketleri
        links = soup.select("li.hover\\:underline a") or soup.select("li a")

    if not links:
        # Fallback 2: Regex ile HTML üzerinden doğrudan arama
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


def send_telegram_message(token: str, chat_id: str, text: str) -> bool:
    """Telegram Bot API üzerinden HTML formatında mesaj gönderir."""
    if not token or not chat_id:
        logger.warning("Telegram Bot Token veya Chat ID tanımlanmadığı için mesaj gönderilemedi.")
        return False

    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    try:
        res = requests.post(api_url, json=payload, timeout=15)
        if res.status_code == 200:
            return True
        else:
            logger.error(f"Telegram API Hatası ({res.status_code}): {res.text}")
            return False
    except requests.RequestException as e:
        logger.error(f"Telegram mesajı gönderilemedi: {e}")
        return False


def main():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    seen_data, is_first_run = load_seen_announcements()
    total_new_announcements = 0
    updated_seen_data = dict(seen_data)

    if is_first_run:
        logger.info("İlk çalıştırma tespit edildi. Mevcut duyurular kaydediliyor (spam engelleme modu)...")

    for page in PAGES:
        page_name = page["name"]
        page_url = page["url"]

        current_items = fetch_announcements(page_url)
        if not current_items:
            continue

        seen_urls = set(seen_data.get(page_url, []))

        if is_first_run:
            # İlk çalıştırmada tüm mevcut duyuruları hafızaya al
            updated_seen_data[page_url] = [item["url"] for item in current_items]
            continue

        # Yeni duyuruları bul (mevcut sayfada olup hafızada olmayanlar)
        # Kronolojik sıra için sondan başa (eskiden yeniye) doğru gönderilir
        new_items = [item for item in current_items if item["url"] not in seen_urls]

        if new_items:
            logger.info(f"'{page_name}' için {len(new_items)} YENİ duyuru bulundu!")
            # Yeni duyuruları kullanıcının doğru sırada görmesi için eskiden yeniye ters çevir
            for item in reversed(new_items):
                safe_title = html.escape(item["title"])
                safe_name = html.escape(page_name)
                msg = (
                    f"📢 <b>{safe_name}</b>\n\n"
                    f"📌 <b>{safe_title}</b>\n\n"
                    f"🔗 <a href=\"{item['url']}\">Duyuruyu Görüntüle</a>"
                )

                logger.info(f"Bildirim gönderiliyor: {item['title']} -> {item['url']}")
                send_telegram_message(bot_token, chat_id, msg)
                total_new_announcements += 1
                time.sleep(1)  # Telegram rate limit aşımını önlemek için bekleme

            # Güncel URL listesini kaydet
            all_page_urls = list(dict.fromkeys([item["url"] for item in current_items] + list(seen_urls)))
            updated_seen_data[page_url] = all_page_urls
        else:
            logger.info(f"'{page_name}' için yeni duyuru yok.")

    if is_first_run:
        save_seen_announcements(updated_seen_data)
        logger.info("İlk tarama tamamlandı. Telegram'a kurulum bilgi mesajı iletiliyor.")
        welcome_msg = (
            "🤖 <b>GTÜ Duyuru Botu Aktif Edildi!</b>\n\n"
            "✅ Sistem başarıyla kuruldu ve takip başlatıldı.\n\n"
            "📋 <b>Takip Edilen Sayfalar:</b>\n"
            "• GTÜ Genel Duyurular\n"
            "• GTÜ Siber Güvenlik MYO\n\n"
            "<i>Yeni bir duyuru yayınlandığında anında buradan bilgilendirileceksiniz.</i>"
        )
        send_telegram_message(bot_token, chat_id, welcome_msg)
    elif total_new_announcements > 0:
        save_seen_announcements(updated_seen_data)
        logger.info(f"Toplam {total_new_announcements} yeni duyuru için bildirim gönderildi ve kaydedildi.")
    else:
        logger.info("Herhangi bir yeni duyuru bulunamadı. İşlem tamamlandı.")


if __name__ == "__main__":
    main()
