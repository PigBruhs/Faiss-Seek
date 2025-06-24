import os
import requests
from bs4 import BeautifulSoup
import random
import base64
from urllib.parse import urlparse, urljoin
from collections import deque
import json


HEADERS = [
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"},
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36"},
        {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0"},
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/537.75.14"},
        {"User-Agent": "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)"},
        {"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11"},
        {"User-Agent": "Opera/9.25 (Windows NT 5.1; U; en)"},
        {
            "User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)"},
        {"User-Agent": "Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)"},
        {
            "User-Agent": "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12"},
        {"User-Agent": "Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9"},
        {
            "User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Ubuntu/11.04 Chromium/16.0.912.77 Chrome/16.0.912.77 Safari/535.7"},
        {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:10.0) Gecko/20100101 Firefox/10.0"}
]

class crawler:
    """
    爬虫类，用于爬取指定网站的图片链接并下载图片。
    """

    def __init__(self,url,name,max_images=1024):
        self.name = name
        self.image_urls = set()  # 存储爬取到的图片链接
        self.visited_urls = set()  # 存储已访问的页面链接
        self.url_queue = deque([url])
        self.max_images = max_images
        self.current_batch=0
        os.makedirs(f"../crawled_images/{self.name}",exist_ok=True)  # 确保目录存在

    def generate_filename_from_url(self, url):
            """
            将URL编码为文件名

            参数:
                url: 图片URL地址
            返回:
                编码后的文件名
            """
            # 将URL转换为bytes
            url_bytes = url.encode('utf-8')

            # Base64编码
            base64_str = base64.b64encode(url_bytes).decode('utf-8')

            # 替换Base64中的特殊字符，使其文件名友好
            base64_str = base64_str.replace('/', '-').replace('+', '_').replace('=', '@')

            # 添加前缀
            return f"base64_{base64_str}"


    def crawl_page(self):

        while self.url_queue and len(self.image_urls) < self.max_images:
            current_url = self.url_queue.popleft()
            if current_url in self.visited_urls:
                continue

            try:
                resp = requests.get(current_url, headers=random.choice(HEADERS), timeout=10)
                if resp.status_code != 200:
                    print(f"无法访问 {current_url}，状态码: {resp.status_code}")
                    continue

                soup = BeautifulSoup(resp.text, 'html.parser')
                self.visited_urls.add(current_url)

                # 提取图片链接
                for img in soup.find_all('img'):
                    src = img.get('src')
                    if src:
                        # 处理相对URL
                        img_url = urljoin(current_url, src)
                        if (img_url.startswith('http') or img_url.startswith('https')) and "logo" not in img_url:
                            self.image_urls.add(img_url)
                            print(f"[{len(self.image_urls)}/{self.max_images}] 发现图片: {img_url}")
                        if len(self.image_urls) >= self.max_images:
                            break

                # 提取页面内的所有链接并加入队列进行递归爬取
                for a_tag in soup.find_all('a', href=True):
                    next_url = urljoin(current_url, a_tag['href'])
                    if next_url.startswith('http') or next_url.startswith('https'):
                        self.url_queue.append(next_url)

            except Exception as e:
                print(f"爬取失败: {e}")

    def save_image(self):
        """
        下载图片到指定文件夹，使用编号命名文件，并维护URL映射文件。
        每次下载128张后结束，支持断点续传。
        """
        target_folder = f"../crawled_images/{self.name}/batch{self.current_batch}"
        mf_folder = f"../index_base/url/{self.name}/"
        os.makedirs(target_folder, exist_ok=True)
        os.makedirs(mf_folder, exist_ok=True)

        # 映射文件路径
        mapping_file = os.path.join(mf_folder, "url_mapping.json")

        # 加载现有的URL映射（如果存在）
        url_mapping = {}
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r', encoding='utf-8') as f:
                url_mapping = json.load(f)

        # 计算当前编号起点
        current_idx = len(url_mapping)

        # 统计已下载图片数
        downloaded_count = len([f for f in os.listdir(target_folder)
                                if f.startswith('url_') and f.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp'))])

        for idx, url in enumerate(list(self.image_urls)[downloaded_count:], 1):
            if downloaded_count >= 128 or downloaded_count >= self.max_images:
                print(f"暂停下载")
                self.current_batch += 1
                break

            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    # 检查文件类型
                    file_extension = os.path.splitext(urlparse(url).path)[-1]
                    if file_extension not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                        continue

                    # 使用编号命名文件
                    image_idx = current_idx + downloaded_count
                    filename = f"url_{image_idx}{file_extension}"
                    path = os.path.join(target_folder, filename)

                    # 保存图片
                    with open(path, 'wb') as f:
                        f.write(resp.content)

                    # 更新URL映射
                    url_mapping[str(image_idx)] = url

                    # 定期保存映射文件
                    if downloaded_count % 10 == 0:
                        with open(mapping_file, 'w', encoding='utf-8') as f:
                            json.dump(url_mapping, f, ensure_ascii=False, indent=2)

                    downloaded_count += 1
                    print(f"[{downloaded_count}/{len(self.image_urls)}] 保存: {path}")
                else:
                    print(f"下载失败 ({resp.status_code}): {url}")
            except Exception as e:
                print(f"错误下载: {url} -> {e}")

        # 最终保存映射文件
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(url_mapping, f, ensure_ascii=False, indent=2)






if __name__ == "__main__":
    url = "https://www.hippopx.com"  # 替换为你要爬取的目标网站
    name = "example_crawl"
    crawler_instance = crawler(url, name, max_images=129)

    # 爬取页面
    crawler_instance.crawl_page()

    crawler_instance.save_image()

    print(f"爬取完成，共下载 {len(crawler_instance.image_urls)} 张图片。")
