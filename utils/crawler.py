import os
import requests
from bs4 import BeautifulSoup
import random
import json
import threading
from urllib.parse import urlparse, urljoin
from queue import Queue, Empty
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import re

# <<< 新增: 导入Selenium相关模块
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# <<< 核心修改: 导入webdriver-manager，用于自动管理ChromeDriver
from webdriver_manager.chrome import ChromeDriverManager

# --- 常量和设置 ---
# 更新HEADERS，使用更真实的浏览器头部
HEADERS = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }
]

try:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    PROJECT_ROOT = os.path.abspath("..")

class crawler:
    """
    一个高效、多线程的爬虫，用于查找和下载网站上的图片。
    它现在使用Selenium来处理JavaScript动态渲染的网站。
    """
    # <<< 核心修改: 增加 max_crawl_depth 参数
    def __init__(self, url, name, max_images=1024, crawl_threads=1, download_threads=8, task_queue=None, max_crawl_depth=3):
        """
        初始化爬虫。

        Args:
            url (str): 起始URL。
            name (str): 会话名称。
            max_images (int): 最大图片数。
            crawl_threads (int): 爬取线程数。由于Selenium资源消耗大且为避免竞争，强烈建议设为1。
            download_threads (int): 下载线程数。
            task_queue (queue.Queue, optional): 用于通知批处理完成的任务队列。
            max_crawl_depth (int): 最大爬取深度，防止无限递归。
        """
        self.name = name
        self.max_images = max_images
        self.root_domain = urlparse(url).netloc
        self.url_queue = Queue()
        # <<< 关键修正: 初始化 image_queue 属性 >>>
        self.image_queue = Queue()
        # <<< 修改: 队列现在存储 (URL, 深度) 元组
        self.url_queue.put((url, 0))
        self.visited_urls = set([url])
        self.queued_image_urls = set()
        self.downloaded_image_map = []
        self.downloaded_image_count = 0
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.crawl_threads_count = crawl_threads
        self.download_threads_count = download_threads
        self.max_crawl_depth = max_crawl_depth
        
        # <<< 新增: 定义要忽略的URL关键词 >>>
        self.IGNORED_PATTERNS = {
            'login', 'register', 'signin', 'signup', 'policy', 'privacy',
            'about', 'contact', 'faq', 'terms', 'support', 'jobs'
        }
        
        self.task_queue = task_queue
        self.signaled_batches = set()

        self.crawled_images_dir = os.path.join(PROJECT_ROOT, "crawled_images", self.name)
        self.mapping_folder = os.path.join(PROJECT_ROOT, "index_base", "url", self.name)
        os.makedirs(self.crawled_images_dir, exist_ok=True)
        os.makedirs(self.mapping_folder, exist_ok=True)
        self._active_crawl_threads = 0

        self.host_failure_counts = {}
        self.failure_lock = threading.Lock()
        self.MAX_HOST_FAILURES = 5

    def _create_robust_session(self):
        session = requests.Session()
        retry_strategy = Retry(total=2, status_forcelist=[429, 500, 502, 503, 504], backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        session.headers.update(random.choice(HEADERS))
        return session

    def _crawl_worker(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(f'user-agent={random.choice(HEADERS)["User-Agent"]}')
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

        driver = None
        try:
            print(f"[Selenium] 线程 {threading.current_thread().name} 正在准备WebDriver...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print(f"[Selenium] 线程 {threading.current_thread().name} 的WebDriver初始化成功。")
        except Exception as e:
            print(f"[严重错误] WebDriver初始化失败: {e}")
            return

        with self.lock:
            self._active_crawl_threads += 1

        print(f"[爬虫线程-{threading.current_thread().name}] 已启动 (使用Selenium)。活跃线程数: {self._active_crawl_threads}")

        while not self.stop_event.is_set():
            try:
                # <<< 修改: 获取URL和其对应的深度
                current_url, current_depth = self.url_queue.get(timeout=5)
            except Empty:
                if self.url_queue.empty(): break
                else: continue

            if self.downloaded_image_count >= self.max_images:
                self.stop_event.set()
                self.url_queue.task_done()
                break

            print(f"[爬虫线程-{threading.current_thread().name}] 正在爬取 (深度 {current_depth}): {current_url} ...")

            try:
                driver.get(current_url)
                
                print("[滚动] 开始模拟向下滚动页面...")
                scroll_count = 0
                max_scrolls = 10
                last_height = driver.execute_script("return document.body.scrollHeight")

                while scroll_count < max_scrolls:
                    with self.lock:
                        if len(self.queued_image_urls) >= self.max_images:
                            print("[滚动] 已找到足够数量的图片，停止滚动。")
                            break
                    
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    scroll_count += 1
                    print(f"[滚动] 完成第 {scroll_count}/{max_scrolls} 次滚动。")
                    
                    time.sleep(3)
                    
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        print("[滚动] 页面高度未变，已到达底部。")
                        break
                    last_height = new_height

                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                print(f"[调试] 页面 '{soup.title.string if soup.title else '无标题'}' 的内容长度为 {len(page_source)} 字符。")

                img_count = 0
                for img in soup.find_all('img'):
                    src = img.get('src') or img.get('data-src')
                    if not src or src.startswith('data:image'): continue
                    
                    img_url = urljoin(current_url, src)

                    if any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                        with self.lock:
                            if len(self.queued_image_urls) < self.max_images and img_url not in self.queued_image_urls:
                                self.queued_image_urls.add(img_url)
                                self.image_queue.put(img_url)
                                img_count += 1
                
                print(f"[发现] 从 {current_url} (滚动后) 找到 {img_count} 张新图片。图片队列大小: {self.image_queue.qsize()}")

                # <<< 核心修改: 只有在未达到最大深度时，才继续添加新链接 >>>
                if current_depth < self.max_crawl_depth:
                    link_count = 0
                    for a_tag in soup.find_all('a', href=True):
                        next_url = a_tag.get('href')
                        if not next_url: continue

                        # <<< 新增: URL过滤逻辑 >>>
                        if any(pattern in next_url.lower() for pattern in self.IGNORED_PATTERNS):
                            continue # 如果URL包含黑名单关键词，则跳过

                        next_url = urljoin(current_url, next_url).split('#')[0].split('?')[0]
                        
                        if urlparse(next_url).netloc == self.root_domain and next_url.startswith('http'):
                            with self.lock:
                                if next_url not in self.visited_urls:
                                    self.visited_urls.add(next_url)
                                    # <<< 修改: 将新URL和增加后的深度一起放入队列
                                    self.url_queue.put((next_url, current_depth + 1))
                                    link_count += 1
                    
                    print(f"[发现] 从 {current_url} 找到 {link_count} 个新链接 (下一深度: {current_depth + 1})。URL队列大小: {self.url_queue.qsize()}")
                else:
                    print(f"[信息] 已达到最大爬取深度({self.max_crawl_depth})，不再从此页面添加新链接。")


            except Exception as e:
                print(f"[严重错误] 处理页面 {current_url} 时发生未知错误: {e}")
            finally:
                self.url_queue.task_done()
        
        if driver:
            driver.quit()
        
        with self.lock:
            self._active_crawl_threads -= 1
        
        print(f"[爬虫线程-{threading.current_thread().name}] 已退出。剩余活跃爬虫线程: {self._active_crawl_threads}")

    def _download_worker(self):
        session = self._create_robust_session()
        while not self.stop_event.is_set():
            try:
                url = self.image_queue.get(timeout=3)
            except Empty:
                if self._active_crawl_threads == 0 and self.url_queue.empty() and self.image_queue.empty():
                    break
                continue

            hostname = urlparse(url).netloc
            with self.failure_lock:
                failure_count = self.host_failure_counts.get(hostname, 0)
            
            if failure_count >= self.MAX_HOST_FAILURES:
                print(f"[熔断] 主机 {hostname} 连续失败次数过多，暂时跳过该主机的下载任务: {url}")
                self.image_queue.task_done()
                continue

            with self.lock:
                if self.downloaded_image_count >= self.max_images:
                    self.image_queue.task_done()
                    self.stop_event.set()
                    continue

            try:
                resp = session.get(url, timeout=10)
                resp.raise_for_status()

                with self.failure_lock:
                    if self.host_failure_counts.get(hostname, 0) > 0:
                         self.host_failure_counts[hostname] = 0

                content_type = resp.headers.get('Content-Type', '').split(';')[0]
                ext_map = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/gif': '.gif', 'image/bmp': '.bmp', 'image/webp': '.webp'}
                file_extension = os.path.splitext(urlparse(url).path)[-1].lower()
                if file_extension not in ext_map.values():
                    file_extension = ext_map.get(content_type)
                
                if not file_extension:
                    print(f"[跳过] 无法确定图片类型: {url} (Content-Type: {content_type})")
                    self.image_queue.task_done()
                    continue

                with self.lock:
                    if self.downloaded_image_count < self.max_images:
                        self.downloaded_image_count += 1
                        current_count = self.downloaded_image_count
                        
                        current_batch_num = (current_count - 1) // 128
                        target_folder = os.path.join(self.crawled_images_dir, f"batch{current_batch_num}")
                        os.makedirs(target_folder, exist_ok=True)
                        
                        image_idx_str = f"img_{current_count:04d}"
                        filename = f"{image_idx_str}{file_extension}"
                        path = os.path.join(target_folder, filename)

                        with open(path, 'wb') as f: f.write(resp.content)
                        
                        self.downloaded_image_map.append((image_idx_str, url))
                        print(f"[下载成功] [{current_count}/{self.max_images}] -> {path}")

                        is_batch_full = (current_count % 128 == 0)
                        is_last_image = (current_count == self.max_images)
                        
                        if self.task_queue and (is_batch_full or is_last_image) and current_batch_num not in self.signaled_batches:
                            print(f"[通知] 批次 {current_batch_num} 已准备好，通知索引线程...")
                            self.task_queue.put(current_batch_num)
                            self.signaled_batches.add(current_batch_num)
                    else:
                        self.stop_event.set()

            except requests.RequestException as e:
                print(f"[下载失败] URL: {url}, 原因: {e}")
                with self.failure_lock:
                    self.host_failure_counts[hostname] = self.host_failure_counts.get(hostname, 0) + 1
                    print(f"[熔断计数] 主机 {hostname} 连续失败 {self.host_failure_counts[hostname]} 次。")
            except Exception as e:
                print(f"[严重错误] 下载时发生未知错误: {url}, 原因: {e}")
            finally:
                self.image_queue.task_done()
        
        print(f"[下载线程-{threading.current_thread().name}] 已退出。")

    def crawl_page(self):
        print(f"[启动] 启动 {self.crawl_threads_count} 个爬取线程和 {self.download_threads_count} 个下载线程。")
        threads = []
        for i in range(self.crawl_threads_count):
            t = threading.Thread(target=self._crawl_worker, name=f"Crawl-{i+1}")
            t.start()
            threads.append(t)
        
        for i in range(self.download_threads_count):
            t = threading.Thread(target=self._download_worker, name=f"Download-{i+1}")
            t.start()
            threads.append(t)

        while not self.stop_event.is_set():
            time.sleep(2)
            
            if self.downloaded_image_count >= self.max_images:
                print("[监控] 已达到目标图片数量，准备停止所有任务。")
                self.stop_event.set()
                break

            if self._active_crawl_threads == 0 and self.url_queue.empty():
                print("[监控] 所有爬取任务完成，URL队列已空。等待剩余图片下载...")
                self.image_queue.join() 
                print("[监控] 所有图片已下载完成。")
                self.stop_event.set()
                break
        
        print("[收尾] 等待所有线程安全退出...")
        for t in threads:
            t.join()
        
        print("[完成] 所有爬虫和下载线程均已成功停止。")

    def save_image(self):
        mapping_file = os.path.join(self.mapping_folder, "url_mapping.json")
        url_mapping = {}
        if os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    url_mapping = json.load(f)
            except json.JSONDecodeError: pass
        
        for idx, url in self.downloaded_image_map:
            url_mapping[idx] = url
        
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(url_mapping, f, ensure_ascii=False, indent=2)
        
        print(f"URL 映射文件已更新/保存至: {mapping_file}")

    def decoder(self):
        mapping_file = os.path.join(self.mapping_folder, "url_mapping.json")
        if os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError: return {}
        return {}
