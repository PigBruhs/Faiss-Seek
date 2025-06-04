import os
import requests
from bs4 import BeautifulSoup
import random

HEADERS = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/537.75.14"},
    {"User-Agent": "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)"},
    {"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11"},
    {"User-Agent": "Opera/9.25 (Windows NT 5.1; U; en)"},
    {"User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)"},
    {"User-Agent": "Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)"},
    {"User-Agent": "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12"},
    {"User-Agent": "Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9"},
    {"User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Ubuntu/11.04 Chromium/16.0.912.77 Chrome/16.0.912.77 Safari/535.7"},
    {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:10.0) Gecko/20100101 Firefox/10.0"}
]

def crawl_page(url, max_images=100):
    """
    爬取指定网站的图片链接。
    :param url: 网站 URL
    :param max_images: 最大图片数量
    :return: 图片链接集合
    """
    image_urls = set()
    try:
        resp = requests.get(url, headers=random.choice(HEADERS), timeout=10)
        if resp.status_code != 200:
            print(f"无法访问 {url}，状态码: {resp.status_code}")
            return image_urls

        soup = BeautifulSoup(resp.text, 'html.parser')
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and (src.startswith('http') or src.startswith('https')):
                image_urls.add(src)
            if len(image_urls) >= max_images:
                break
    except Exception as e:
        print(f"爬取失败: {e}")
    return image_urls

def save_image(image_urls, target_folder):
    """
    下载图片到指定文件夹。
    :param image_urls: 图片链接集合
    :param target_folder: 保存图片的文件夹路径
    """
    os.makedirs(target_folder, exist_ok=True)
    for idx, url in enumerate(image_urls, 1):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                url = url.split(':')[1].replace('/', '_')  # 替换斜杠以避免文件名问题
                if "logo" in url:
                    continue
                filename = f"{url}"  # 使用索引作为文件名
                path = os.path.join(target_folder, filename)
                with open(path, 'wb') as f:
                    f.write(resp.content)
                print(f"[{idx}/{len(image_urls)}] 保存: {path}")
            else:
                print(f"下载失败 ({resp.status_code}): {url}")
        except Exception as e:
            print(f"错误下载: {url} -> {e}")

if __name__ == "__main__":
    website_url = input("请输入要爬取的网页 URL: ")
    save_folder = input("请输入保存图片的文件夹路径: ")
    max_images = int(input("请输入最大图片数量: "))

    print("开始爬取图片链接...")
    image_links = crawl_page(website_url, max_images)
    print(f"共爬取到 {len(image_links)} 张图片，开始下载...")
    save_image(image_links, save_folder)
    print("图片下载完成。")