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
from selenium.common.exceptions import WebDriverException

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
    def __init__(self, url, name, max_images=1024, crawl_threads=2, download_threads=4, task_queue=None): # <<< 修改: 建议减少爬虫线程数
        """
        初始化爬虫。

        Args:
            url (str): 起始URL。
            name (str): 会话名称。
            max_images (int): 最大图片数。
            crawl_threads (int): 爬取线程数。由于Selenium资源消耗较大，建议设为1或2。
            download_threads (int): 下载线程数。
            task_queue (queue.Queue, optional): 用于通知批处理完成的任务队列。
        """
        self.name = name
        self.max_images = max_images
        self.root_domain = urlparse(url).netloc
        self.url_queue = Queue()
        self.image_queue = Queue()
        self.url_queue.put(url)
        self.visited_urls = set([url])
        self.queued_image_urls = set()
        self.downloaded_image_map = []
        self.downloaded_image_count = 0
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.crawl_threads_count = crawl_threads
        self.download_threads_count = download_threads
        
        self.task_queue = task_queue
        self.signaled_batches = set()

        self.crawled_images_dir = os.path.join(PROJECT_ROOT, "crawled_images", self.name)
        self.mapping_folder = os.path.join(PROJECT_ROOT, "index_base", "url", self.name)
        os.makedirs(self.crawled_images_dir, exist_ok=True)
        os.makedirs(self.mapping_folder, exist_ok=True)
        self._active_crawl_threads = 0

    def _create_robust_session(self):
        # 此方法依然用于下载线程，效率更高
        session = requests.Session()
        retry_strategy = Retry(total=3, status_forcelist=[429, 500, 502, 503, 504], backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        session.headers.update(random.choice(HEADERS))
        return session

    def _crawl_worker(self):
        # <<< 核心修改: 使用Selenium代替requests来获取页面内容
        
        # --- Selenium WebDriver 设置 ---
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 无头模式，不在前台显示浏览器
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080") # 设置窗口大小以加载桌面版网页
        # 伪装成真实浏览器
        chrome_options.add_argument(f'user-agent={random.choice(HEADERS)["User-Agent"]}')
        
        driver = None
        try:
            # 使用PROJECT_ROOT构建chromedriver路径
            # 假设chromedriver.exe在项目根目录下
            driver_path = os.path.join(PROJECT_ROOT, "chromedriver.exe")
            
            # 如果在Linux/Mac系统，文件名可能不同
            if not os.path.exists(driver_path):
                driver_path = os.path.join(PROJECT_ROOT, "chromedriver")
            
            # 检查文件是否存在
            if not os.path.exists(driver_path):
                print(f"[错误] ChromeDriver 未找到。请将 chromedriver.exe 放置在项目根目录: {PROJECT_ROOT}")
                print(f"[提示] 当前查找路径: {driver_path}")
                print(f"[提示] 您可以从 https://chromedriver.chromium.org/ 下载 ChromeDriver")
                return  # 无法启动浏览器，此线程退出
            
            print(f"[信息] 使用 ChromeDriver 路径: {driver_path}")
            service = Service(executable_path=driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print(f"[Selenium] 线程 {threading.current_thread().name} 的WebDriver初始化成功。")
            
        except WebDriverException as e:
            print(f"[严重错误] WebDriver初始化失败: {e}")
            print(f"[提示] 请检查以下几点:")
            print(f"  1. ChromeDriver 是否已下载并放置在: {PROJECT_ROOT}")
            print(f"  2. ChromeDriver 版本是否与您的 Chrome 浏览器版本匹配")
            print(f"  3. ChromeDriver 是否有执行权限")
            return  # 无法启动浏览器，此线程退出
        
        with self.lock:
            self._active_crawl_threads += 1

        print(f"[爬虫线程-{threading.current_thread().name}] 已启动 (使用Selenium)。活跃线程数: {self._active_crawl_threads}")

        while not self.stop_event.is_set():
            try:
                current_url = self.url_queue.get(timeout=5)
            except Empty:
                if self.url_queue.empty(): break
                else: continue

            if self.downloaded_image_count >= self.max_images:
                self.stop_event.set()
                self.url_queue.task_done()
                break

            print(f"[爬虫线程-{threading.current_thread().name}] 正在爬取: {current_url} ...")

            try:
                # 使用Selenium加载页面
                driver.get(current_url)
                # 等待5-10秒，让JS有足够时间渲染页面。对于加载慢的网站，可能需要增加这个时间。
                time.sleep(7)
                
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                print(f"[调试] 页面 '{soup.title.string if soup.title else '无标题'}' 的内容长度为 {len(page_source)} 字符。")

                # --- 查找图片 (逻辑保持不变) ---
                img_count = 0
                for img in soup.find_all('img'):
                    src = img.get('src') or img.get('data-src')
                    if not src or src.startswith('data:image'): continue
                    
                    img_url = urljoin(current_url, src)

                    # 增加更宽松的图片URL判断
                    if any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                        with self.lock:
                            if len(self.queued_image_urls) < self.max_images and img_url not in self.queued_image_urls:
                                self.queued_image_urls.add(img_url)
                                self.image_queue.put(img_url)
                                img_count += 1
                
                print(f"[发现] 从 {current_url} 找到 {img_count} 张新图片。图片队列大小: {self.image_queue.qsize()}")

                # --- 查找链接 (逻辑保持不变) ---
                link_count = 0
                for a_tag in soup.find_all('a', href=True):
                    next_url = a_tag.get('href')
                    if not next_url: continue

                    next_url = urljoin(current_url, next_url).split('#')[0].split('?')[0]
                    
                    if urlparse(next_url).netloc == self.root_domain and next_url.startswith('http'):
                        with self.lock:
                            if next_url not in self.visited_urls:
                                self.visited_urls.add(next_url)
                                self.url_queue.put(next_url)
                                link_count += 1
                
                print(f"[发现] 从 {current_url} 找到 {link_count} 个新链接。URL队列大小: {self.url_queue.qsize()}")

            except Exception as e:
                print(f"[严重错误] 处理页面 {current_url} 时发生未知错误: {e}")
            finally:
                self.url_queue.task_done()
        
        if driver:
            driver.quit() # 关闭浏览器，释放资源
        
        with self.lock:
            self._active_crawl_threads -= 1
        
        print(f"[爬虫线程-{threading.current_thread().name}] 已退出。剩余活跃爬虫线程: {self._active_crawl_threads}")

    def _download_worker(self):
        # 下载线程保持不变，继续使用requests，效率更高
        session = self._create_robust_session()
        while not self.stop_event.is_set():
            try:
                url = self.image_queue.get(timeout=3)
            except Empty:
                if self._active_crawl_threads == 0 and self.url_queue.empty() and self.image_queue.empty():
                    break
                continue

            with self.lock:
                if self.downloaded_image_count >= self.max_images:
                    self.image_queue.task_done()
                    self.stop_event.set()
                    continue

            try:
                resp = session.get(url, timeout=20)
                resp.raise_for_status()
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
