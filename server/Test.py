import requests
from bs4 import BeautifulSoup
import re
import time

# 常量定义
BASE_IMAGE_URL = "https://pixnio.com/free-images/"
START_URL = "https://pixnio.com/zh/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

# 数据结构
image_urls = set()
visited_urls = set()
max_pages = 10
page_count = 0

def crawl_page(url):
    global page_count

    if page_count >= max_pages or url in visited_urls:
        return

    try:
        print(f"[{page_count+1}/{max_pages}] 正在爬取: {url}")
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return

        visited_urls.add(url)
        page_count += 1

        soup = BeautifulSoup(response.text, 'html.parser')

        # 提取图片链接
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and src.startswith(BASE_IMAGE_URL):
                image_urls.add(src)

        # 提取下一个页面链接，继续递归（深度优先）
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith("https://pixnio.com/zh/") and "?" not in href and href not in visited_urls:
                crawl_page(href)

    except Exception as e:
        print(f"错误访问: {url}\n错误信息: {e}")

# 启动爬虫
crawl_page(START_URL)
# 保存结果
# 保存结果（只保存文件名部分）
save_path = r"e:/软件实训开发/答而多图图/data/pixnio_image_urls.txt"
with open(save_path, "w", encoding="utf-8") as f:
    for url in sorted(image_urls):
        filename = url.split("/")[-1]
        f.write(filename + "\n")


print(f"\n✅ 共爬取页面数: {page_count}，图片链接数: {len(image_urls)}")
print("📄 链接已保存至 pixnio_image_urls.txt")