# utils/crawler.py (完整替换)

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

# --- 常量和设置 ---
HEADERS = [
    {"User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"},
    {"User-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"},
    {"User-agent": "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:90.0) Gecko/20100101 Firefox/90.0"},
]

try:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    PROJECT_ROOT = os.path.abspath("..")

class crawler:
    """
    一个高效、多线程的爬虫，用于查找和下载网站上的图片。
    它可以接收一个任务队列，以便在完成批处理时通知其他线程。
    """
    # <<< MODIFIED: 新增 task_queue 参数
    def __init__(self, url, name, max_images=1024, crawl_threads=4, download_threads=8, task_queue=None):
        """
        初始化爬虫。

        Args:
            url (str): 起始URL。
            name (str): 会话名称。
            max_images (int): 最大图片数。
            crawl_threads (int): 爬取线程数。
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
        
        # <<< MODIFIED: 保存任务队列并添加一个集合来跟踪已通知的批次
        self.task_queue = task_queue
        self.signaled_batches = set()

        self.crawled_images_dir = os.path.join(PROJECT_ROOT, "crawled_images", self.name)
        self.mapping_folder = os.path.join(PROJECT_ROOT, "index_base", "url", self.name)
        os.makedirs(self.crawled_images_dir, exist_ok=True)
        os.makedirs(self.mapping_folder, exist_ok=True)
        self._active_crawl_threads = 0

    def _create_robust_session(self):
        session = requests.Session()
        retry_strategy = Retry(total=3, status_forcelist=[429, 500, 502, 503, 504], backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        return session

    def _crawl_worker(self):
        session = self._create_robust_session()
        with self.lock:
            self._active_crawl_threads += 1

        while not self.stop_event.is_set():
            try:
                current_url = self.url_queue.get(timeout=1)
            except Empty:
                break

            if len(self.queued_image_urls) >= self.max_images:
                self.stop_event.set()
                self.url_queue.task_done()
                break

            try:
                resp = session.get(current_url, headers=random.choice(HEADERS), timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, 'html.parser')

                for img in soup.find_all('img'):
                    src = img.get('src') or img.get('data-src')
                    if not src: continue
                    img_url = urljoin(current_url, src)
                    if not img_url.startswith('http') or "logo" in img_url or ".svg" in img_url: continue
                    with self.lock:
                        if len(self.queued_image_urls) < self.max_images and img_url not in self.queued_image_urls:
                            self.queued_image_urls.add(img_url)
                            self.image_queue.put(img_url)

                for a_tag in soup.find_all('a', href=True):
                    next_url = urljoin(current_url, a_tag['href']).split('#')[0]
                    if urlparse(next_url).netloc == self.root_domain and next_url.startswith('http'):
                        with self.lock:
                            if next_url not in self.visited_urls:
                                self.visited_urls.add(next_url)
                                self.url_queue.put(next_url)
            except requests.RequestException:
                pass
            except Exception:
                pass
            finally:
                self.url_queue.task_done()
        
        with self.lock:
            self._active_crawl_threads -= 1

    def _download_worker(self):
        session = self._create_robust_session()
        while not self.stop_event.is_set():
            try:
                url = self.image_queue.get(timeout=1)
            except Empty:
                if self._active_crawl_threads == 0 and self.url_queue.empty():
                    break
                continue

            with self.lock:
                if self.downloaded_image_count >= self.max_images:
                    self.image_queue.task_done()
                    continue

            try:
                resp = session.get(url, headers=random.choice(HEADERS), timeout=15)
                resp.raise_for_status()
                
                file_extension = os.path.splitext(urlparse(url).path)[-1].lower()
                if file_extension not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    content_type = resp.headers.get('Content-Type', '').split(';')[0]
                    ext_map = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/gif': '.gif', 'image/bmp': '.bmp'}
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
                        
                        mapping_path = os.path.join(self.mapping_folder, "url_mapping.json")
                        url_mapping = {}
                        if os.path.exists(mapping_path):
                           with open(mapping_path, 'r', encoding='utf-8') as f:
                               try: url_mapping = json.load(f)
                               except json.JSONDecodeError: pass

                        image_idx = len(url_mapping) + current_count
                        filename = f"url_{image_idx}{file_extension}"
                        path = os.path.join(target_folder, filename)

                        with open(path, 'wb') as f:
                            f.write(resp.content)
                        
                        self.downloaded_image_map.append((str(image_idx), url))
                        print(f"  [已保存] [{current_count}/{self.max_images}] -> {path}")

                        # <<< MODIFIED: 检查是否应发送批处理完成信号
                        # 当下载数是128的倍数时，或当下载了最后一张图片时，发出通知
                        should_signal = (current_count % 128 == 0) or (current_count == self.max_images)
                        if self.task_queue and should_signal and current_batch_num not in self.signaled_batches:
                            print(f"[通知] 批次 {current_batch_num} 已准备好，通知索引线程...")
                            self.task_queue.put(current_batch_num)
                            self.signaled_batches.add(current_batch_num)
                    else:
                        self.stop_event.set()

            except requests.RequestException:
                pass
            except Exception:
                pass
            finally:
                self.image_queue.task_done()

    def crawl_page(self):
        threads = []
        for _ in range(self.crawl_threads_count):
            t = threading.Thread(target=self._crawl_worker)
            t.start()
            threads.append(t)
        
        for _ in range(self.download_threads_count):
            t = threading.Thread(target=self._download_worker)
            t.start()
            threads.append(t)

        while not self.stop_event.is_set():
            time.sleep(1)
            if self.downloaded_image_count >= self.max_images:
                self.stop_event.set()

            if self._active_crawl_threads == 0 and self.url_queue.empty():
                self.image_queue.join() 
                self.stop_event.set()
        
        for t in threads:
            t.join()

    def save_image(self):
        mapping_file = os.path.join(self.mapping_folder, "url_mapping.json")
        url_mapping = {}
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r', encoding='utf-8') as f:
                try: url_mapping = json.load(f)
                except json.JSONDecodeError: pass
        
        for idx, url in self.downloaded_image_map:
            url_mapping[idx] = url
        
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(url_mapping, f, ensure_ascii=False, indent=2)
        
        print(f"URL 映射文件已保存至: {mapping_file}")

    def decoder(self):
        mapping_file = os.path.join(self.mapping_folder, "url_mapping.json")
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}