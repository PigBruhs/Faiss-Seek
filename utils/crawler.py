import os
import time
import random
import base64
from collections import deque
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Optional Selenium for dynamic content loading
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

HEADERS = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64)..."},
    # ... 更多UA 省略
]

class Crawler:
    """
    爬虫类，用于爬取指定网站的图片链接并下载图片。
    支持静态和动态加载、滚动、load-more点击以及基本反反爬手段。
    添加丰富的调试输出，方便观察爬取进度。
    """

    def __init__(self, url, name, max_images=1024, use_selenium=False, proxy_list=None):
        self.name = name
        self.image_urls = set()
        self.visited_urls = set()
        self.url_queue = deque([url])
        self.max_images = max_images
        self.current_batch = 0
        self.proxy_list = proxy_list or []
        
        os.makedirs(f"../crawled_images/{self.name}", exist_ok=True)
        self.use_selenium = use_selenium and SELENIUM_AVAILABLE
        if self.use_selenium:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument(f"--user-agent={random.choice(HEADERS)['User-Agent']}")
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 10)

    def filename_hash(self,input_str):
        """
        将输入字符串转换为可作为Windows文件名的可逆哈希值

        参数:
            input_str: 要转换的字符串
        返回:
            可用作Windows文件名的可逆哈希字符串
        """
        # 将输入转换为bytes
        if isinstance(input_str, str):
            input_bytes = input_str.encode('utf-8')
        else:
            input_bytes = input_str

        # 使用Base64编码
        encoded = base64.b64encode(input_bytes).decode('ascii')

        # 替换Windows文件名不允许的字符
        filename_safe = encoded.replace('/', '-').replace('+', '_').replace('=', '@')

        # 添加前缀
        return f"base64_{filename_safe}"

    def _random_headers(self):
        return random.choice(HEADERS)

    def _random_proxy(self):
        return random.choice(self.proxy_list) if self.proxy_list else None

    def _delay(self):
        time.sleep(random.uniform(1, 3))  # 随机延迟

    def _scroll_and_load(self):
        body = self.driver.find_element(By.TAG_NAME, 'body')
        for _ in range(5):
            ActionChains(self.driver).send_keys("\ue00f").perform()
            time.sleep(1)
        try:
            load_more = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'更多') or contains(text(),'Load More')]") ))
            load_more.click()
            time.sleep(2)
        except Exception:
            pass

    def crawl_page(self):
        """
        广度优先爬取页面，收集图片链接。
        添加调试输出：当前 URL、已抓取图片数、队列长度。
        """
        print(f"[启动爬虫] 初始 URL: {self.url_queue[0]}, 最大图片: {self.max_images}")
        while self.url_queue and len(self.image_urls) < self.max_images:
            current_url = self.url_queue.popleft()
            print(f"[处理] URL: {current_url}")
            print(f"    已访问: {len(self.visited_urls)}, 队列: {len(self.url_queue)}, 图片收集: {len(self.image_urls)}")
            if current_url in self.visited_urls:
                print("    跳过，已访问过")
                continue
            self.visited_urls.add(current_url)

            try:
                if self.use_selenium:
                    self.driver.get(current_url)
                    self._delay()
                    self._scroll_and_load()
                    html = self.driver.page_source
                else:
                    session = requests.Session()
                    headers = self._random_headers()
                    proxy = self._random_proxy()
                    print(f"    请求头: {headers['User-Agent']}, 代理: {proxy}")
                    resp = session.get(current_url, headers=headers, proxies={'http': proxy, 'https': proxy} if proxy else None, timeout=10)
                    if resp.status_code != 200:
                        print(f"    请求失败，状态码 {resp.status_code}")
                        continue
                    html = resp.text

                soup = BeautifulSoup(html, 'html.parser')

                for img in soup.find_all('img'):
                    src = img.get('src')
                    if not src:
                        continue
                    img_url = urljoin(current_url, src)
                    if img_url.startswith('http') and 'logo' not in img_url:
                        if img_url not in self.image_urls:
                            self.image_urls.add(img_url)
                            print(f"    新图片 [{len(self.image_urls)}]: {img_url}")
                        if len(self.image_urls) >= self.max_images:
                            break

                for a_tag in soup.find_all('a', href=True):
                    next_url = urljoin(current_url, a_tag['href'])
                    if next_url.startswith('http') and next_url not in self.visited_urls:
                        self.url_queue.append(next_url)
                self._delay()

            except Exception as e:
                print(f"爬取失败 {current_url}: {e}")

        if self.use_selenium:
            self.driver.quit()
        print(f"[结束] 共抓取图片 {len(self.image_urls)}，访问网页 {len(self.visited_urls)}")

    def save_image(self):
        """
        下载图片到指定文件夹，每次128张后断点续传。
        添加下载日志。
        """
        target_folder = f"../crawled_images/{self.name}/batch{self.current_batch}"
        os.makedirs(target_folder, exist_ok=True)
        downloaded = len(os.listdir(target_folder))
        print(f"[保存] 批次 {self.current_batch}, 已下载 {downloaded}/{len(self.image_urls)}")

        for idx, url in enumerate(list(self.image_urls)[downloaded:], start=downloaded+1):
            if idx > downloaded and (idx-1) % 128 == 0 and idx-1 != downloaded:
                self.current_batch += 1
                print(f"达到128张，切换到批次 {self.current_batch}")
                break
            try:
                resp = requests.get(url, headers=self._random_headers(), timeout=10)
                if resp.status_code == 200:
                    fn = self.filename_hash(url)
                    ext = os.path.splitext(urlparse(url).path)[-1]
                    if ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                        print(f"跳过非图片资源: {url}")
                        continue
                    path = os.path.join(target_folder, fn + ext)
                    with open(path, 'wb') as f:
                        f.write(resp.content)
                    print(f"保存 [{idx}/{len(self.image_urls)}]: {path}")
                else:
                    print(f"下载失败 {resp.status_code}: {url}")
            except Exception as e:
                print(f"错误下载 {url}: {e}")
        print(f"[保存结束] 批次 {self.current_batch}, 下载完成 {len(os.listdir(target_folder))}张图片")

if __name__ == "__main__":
    url = "https://www.hippopx.com"  # 替换为你要爬取的目标网站
    name = "example_crawl"
    crawler_instance = Crawler(url, name, max_images=8)

    # 爬取页面
    crawler_instance.crawl_page()

    crawler_instance.save_image()

    print(f"爬取完成，共下载 {len(crawler_instance.image_urls)} 张图片。")


