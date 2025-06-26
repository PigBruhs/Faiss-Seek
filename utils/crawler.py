import os
import requests
from bs4 import BeautifulSoup
import random
import json
import threading
from urllib.parse import urlparse, urljoin
# <<< 核心修正: 同时导入 PriorityQueue 和 Queue >>>
from queue import PriorityQueue, Queue, Empty
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# --- 常量和设置 ---
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
    def __init__(self, url, name, max_images=1024, crawl_threads=1, download_threads=4, task_queue=None, max_crawl_depth=2):
        self.name = name
        self.max_images = max_images
        self.root_domain = urlparse(url).netloc
        # 使用优先队列处理URL，确保高价值页面被优先访问
        self.url_queue = PriorityQueue()
        self.url_queue.put((0, 0, url)) # (优先级, 深度, URL)
        # 使用标准队列处理图片URL
        self.image_queue = Queue()
        
        self.visited_urls = set([url])
        self.queued_image_urls = set()
        self.downloaded_image_map = []
        self.downloaded_image_count = 0
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.crawl_threads_count = crawl_threads
        self.download_threads_count = download_threads
        self.max_crawl_depth = max_crawl_depth
        
        # URL关键词黑名单，避免爬取无用页面
        self.IGNORED_PATTERNS = {
            'login', 'register', 'signin', 'signup', 'policy', 'privacy',
            'about', 'contact', 'faq', 'terms', 'support', 'jobs', 'profile',
            'password', 'account', 'upload', 'cart', 'checkout', 'forum',
            '/ar/', '/de/', '/es/', '/fr/', '/it/', '/ja/', '/ko/', '/pt/', 
            '/ru/', '/zh/', '/pl/', '/nl/', '/sv/', '/tr/', '/cs/', '/da/',
            '/fi/', '/hu/', '/no/', '/ro/', '/sk/', '/th/',
            '/blog/', '/news/', '/article/'
        }
        # 高优先级URL关键词
        self.PRIORITY_PATTERNS = {'photo', 'image', 'gallery', 'album', 'media'}
        
        self.task_queue = task_queue
        self.signaled_batches = set()
        self.crawled_images_dir = os.path.join(PROJECT_ROOT, "crawled_images", self.name)
        self.mapping_folder = os.path.join(PROJECT_ROOT, "index_base", "url", self.name)
        os.makedirs(self.crawled_images_dir, exist_ok=True)
        os.makedirs(self.mapping_folder, exist_ok=True)
        self._active_crawl_threads = 0

        # 熔断机制属性
        self.host_failure_counts = {}
        self.failure_lock = threading.Lock()
        self.MAX_HOST_FAILURES = 5

        # 爬虫空闲超时机制属性
        self.last_image_found_time = time.time()
        self.CRAWL_IDLE_TIMEOUT = 60 # 秒

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
                priority, current_depth, current_url = self.url_queue.get(timeout=5)
            except Empty:
                if time.time() - self.last_image_found_time > self.CRAWL_IDLE_TIMEOUT:
                    print(f"[超时] 爬虫已空闲超过 {self.CRAWL_IDLE_TIMEOUT} 秒，可能已完成或陷入困境，准备退出。")
                    self.stop_event.set()
                if self.url_queue.empty(): break
                else: continue
            
            if self.downloaded_image_count >= self.max_images:
                self.stop_event.set()
                self.url_queue.task_done()
                break

            print(f"[爬虫线程-{threading.current_thread().name}] 正在爬取 (深度 {current_depth}, 优先级 {priority}): {current_url} ...")

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
                    time.sleep(3)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        print("[滚动] 页面高度未变，已到达底部。")
                        break
                    last_height = new_height

                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')

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
                                self.last_image_found_time = time.time()
                
                print(f"[发现] 从 {current_url} (滚动后) 找到 {img_count} 张新图片。图片队列大小: {self.image_queue.qsize()}")

                if current_depth < self.max_crawl_depth:
                    link_count = 0
                    for a_tag in soup.find_all('a', href=True):
                        next_url_raw = a_tag.get('href')
                        if not next_url_raw: continue
                        
                        if any(pattern in next_url_raw.lower() for pattern in self.IGNORED_PATTERNS):
                            continue

                        next_url = urljoin(current_url, next_url_raw).split('#')[0].split('?')[0]
                        
                        # <<< 最终修复: 智能分拣URL，防止图片URL进入爬取队列 >>>
                        is_image_link = any(ext in next_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif'])

                        if is_image_link:
                            # 如果是图片链接，直接放入下载队列
                            with self.lock:
                                if len(self.queued_image_urls) < self.max_images and next_url not in self.queued_image_urls:
                                    self.queued_image_urls.add(next_url)
                                    self.image_queue.put(next_url)
                        elif urlparse(next_url).netloc == self.root_domain and next_url.startswith('http'):
                             # 如果是普通网页链接，才放入爬取队列
                            with self.lock:
                                if next_url not in self.visited_urls:
                                    self.visited_urls.add(next_url)
                                    priority = 0 if any(p in next_url.lower() for p in self.PRIORITY_PATTERNS) else 1
                                    self.url_queue.put((priority, current_depth + 1, next_url))
                                    link_count += 1
                    
                    print(f"[发现] 从 {current_url} 找到 {link_count} 个新链接。URL队列大小: {self.url_queue.qsize()}")
                else:
                    print(f"[信息] 已达到最大爬取深度({self.max_crawl_depth})，不再从此页面添加新链接。")

            except Exception as e:
                print(f"[严重错误] 处理页面 {current_url} 时发生未知错误: {e}")
            finally:
                self.url_queue.task_done()
        
        if driver: driver.quit()
        with self.lock: self._active_crawl_threads -= 1
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
                            self.task_queue.put(current_batch_num)
                            self.signaled_batches.add(current_batch_num)
                    else:
                        self.stop_event.set()

            except requests.RequestException as e:
                print(f"[下载失败] URL: {url}, 原因: {e}")
                with self.failure_lock:
                    self.host_failure_counts[hostname] = self.host_failure_counts.get(hostname, 0) + 1
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
        
        with self.lock:
            try:
                if os.path.exists(mapping_file):
                    with open(mapping_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if content:
                            url_mapping = json.loads(content)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[警告] 读取现有映射文件失败: {e}。将创建一个新的映射文件。")
                url_mapping = {}

            for idx, url in self.downloaded_image_map:
                url_mapping[idx] = url
            
            try:
                with open(mapping_file, 'w', encoding='utf-8') as f:
                    json.dump(url_mapping, f, ensure_ascii=False, indent=4)
                print(f"URL 映射文件已成功更新/保存至: {mapping_file}")
            except IOError as e:
                print(f"[严重错误] 写入URL映射文件失败: {e}")

    def decoder(self):
        mapping_file = os.path.join(self.mapping_folder, "url_mapping.json")
        if os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError: return {}
        return {}
