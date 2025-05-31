# Faiss-Seek/utils/crawler.py

import os
import time

import requests
from bs4 import BeautifulSoup

BASE_IMAGE_URL = "http://hbimg.huaban.com/"
START_URL = "https://miankoutupian.com/image/search/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

def crawl_page(url: str, max_pages: int = 12) -> set:
    """
    深度优先爬取页面，返回所有符合 BASE_IMAGE_URL 的图片链接，
    page_count、image_urls、visited_urls 在闭包中唯一。
    """
    image_urls = set()
    visited_urls = set()
    page_count = 0

    def _crawl(u: str):
        nonlocal page_count
        if page_count >= max_pages or u in visited_urls:
            return
        try:
            visited_urls.add(u)
            page_count += 1
            print(f"[{page_count}/{max_pages}] 正在爬取: {u}")
            resp = requests.get(u, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                return

            soup = BeautifulSoup(resp.text, 'html.parser')
            # 提取图片链接
            for img in soup.find_all('img'):
                src = img.get('src')
                if src and src.startswith(BASE_IMAGE_URL):
                    image_urls.add(src)
            # 递归页链接
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith(START_URL) and '?' not in href:
                    _crawl(href)
            time.sleep(0.1)
        except Exception as e:
            print(f"错误访问: {u}\n{e}")

    _crawl(url)
    return image_urls

def save_images(image_urls, target_folder):
    os.makedirs(target_folder, exist_ok=True)
    for idx, url in enumerate(image_urls, 1):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                ext = os.path.splitext(url)[1] or '.jpg'
                filename = f"img_{idx:03d}{ext}"
                path = os.path.join(target_folder, filename)
                with open(path, 'wb') as f:
                    f.write(resp.content)
                print(f"[{idx}/{len(image_urls)}] 保存: {path}")
            else:
                print(f"下载失败 ({resp.status_code}): {url}")
        except Exception as e:
            print(f"错误下载: {url} -> {e}")

if __name__ == "__main__":
    urls = crawl_page(START_URL, max_pages=12)
    print(f"共抓取到 {len(urls)} 张图片，开始下载…")
    save_images(urls, "../crawled_images")
    print("下载完成。")
