from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re, requests, os, threading, time, hashlib

app = Flask(__name__)

# ========== 配置区域 ==========
IMAGE_SAVE_DIR = 'image'
MAX_IMAGES = 100
ENABLE_DOWNLOAD = True
SCROLL_PAUSE = 3
PAGE_WAIT = 10
MAX_DEPTH = 2
MIN_SIZE = 2 * 1024
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
}
# =============================

def clean_image_url(url: str) -> str:
    """
    清理图片 URL，删除无效后缀
    """
    url = url.split('?', 1)[0]  # 去掉 URL 参数
    url = re.sub(r'(_fw\d+|_thumb|_small)', '', url)  # 删除 fw320、thumb 等后缀
    return url

def fetch_and_parse(url: str) -> str:
    """
    使用 Playwright 加载页面并自动滚动，提取页面中的图片资源（包括 <img> 和 <canvas[data-src]>）
    """
    with sync_playwright() as p:
        # 启动 Chromium 浏览器（非无头模式方便调试）
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            ignore_https_errors=True,
            user_agent=HEADERS["User-Agent"]
        )
        page = context.new_page()

        try:
            # 加载目标页面，等待网络空闲状态
            page.goto(url, timeout=PAGE_WAIT * 1000)
            page.wait_for_load_state('networkidle')
            print(f"[√] 页面加载完成：{url}")
        except PlaywrightTimeout:
            print(f"[×] 页面加载超时：{url}，继续尝试爬取")

        # 获取页面中 <img> 和 <canvas[data-src]> 总数量
        def get_img_count():
            return page.eval_on_selector_all("img, canvas[data-src]", "els => els.length")

        last_count = 0               # 上次图片数量
        stable_scrolls = 0           # 连续未增长计数
        max_scrolls = 30             # 最多滚动次数
        img_urls = set()             # 当前页收集的图片 URL

        for i in range(max_scrolls):
            # 向下滚动页面以触发懒加载
            page.evaluate("window.scrollBy(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE)

            # 统计图片数量
            new_count = get_img_count()
            num_canvas = page.eval_on_selector_all("canvas[data-src]", "els => els.length")
            print(f"[→] 滚动{i+1}次，图片数: {new_count}（其中 canvas: {num_canvas}）")

            # 使用 BeautifulSoup 提取图片链接（<img> 和 <canvas[data-src]>）
            soup = BeautifulSoup(page.content(), 'html.parser')
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                if src:
                    img_urls.add(urljoin(url, src))
            for canvas in soup.find_all('canvas', {'data-src': True}):
                src = canvas.get('data-src')
                if src:
                    img_urls.add(urljoin(url, src))

            # 检查图片是否有增长
            if new_count > last_count:
                stable_scrolls = 0
            else:
                stable_scrolls += 1

            last_count = new_count

            # 每滚动 4 次下载当前页面图片（避免过多重复请求）
            if i > 0 and i % 4 == 0:
                print(f"[→] 暂停滚动，开始下载当前页面的图片")
                download_images(list(img_urls), url)
                img_urls.clear()

            # 如果连续 3 次滚动无新增资源，则停止滚动
            if stable_scrolls >= 3:
                print("[✓] 页面稳定，停止滚动")
                break

        # 最后再等待几秒，确保懒加载资源完成
        time.sleep(5)
        html = page.content()
        browser.close()
        return html

def extract_urls(base_url: str, html: str):
    """
    提取图片 URL 和子页面链接，包括动态加载的缩略图和 <canvas> 元素中的图片
    """
    soup = BeautifulSoup(html, 'html.parser')
    img_urls, page_links = set(), set()
    parsed_base = urlparse(base_url)

    # 提取图片 URL
    for img in soup.find_all('img'):
        src = img.get('src') or img.get('data-src') or img.get('data-original')
        if src:
            cleaned_src = clean_image_url(urljoin(base_url, src))
            img_urls.add(cleaned_src)

    # 提取 <canvas> 元素中的图片 URL
    for canvas in soup.find_all('canvas', {'data-src': True}):
        src = canvas.get('data-src')
        if src:
            cleaned_src = clean_image_url(urljoin(base_url, src))
            img_urls.add(cleaned_src)

    # 提取子页面链接
    for a in soup.find_all('a', href=True):
        href = urljoin(base_url, a['href'])
        if urlparse(href).netloc == parsed_base.netloc:
            page_links.add(href.split('#')[0])

    return list(img_urls), list(page_links)

def download_images(urls: list, base_url: str):
    domain = urlparse(base_url).netloc.replace('.', '_')
    target_dir = os.path.join(IMAGE_SAVE_DIR, domain)
    os.makedirs(target_dir, exist_ok=True)

    for raw in urls:
        url = clean_image_url(raw)
        if url.startswith('data:image'):  # 跳过 base64 图片
            print(f'[×] 跳过 base64 图片: {url}')
            continue

        # 使用 URL 的 MD5 作为文件名，防止重名
        name = hashlib.md5(url.encode('utf-8')).hexdigest()
        ext = os.path.splitext(url)[1]
        if not ext or len(ext) > 5:
            ext = '.jpg'  # 默认扩展名
        path = os.path.join(target_dir, f'{name}{ext}')

        if os.path.exists(path):
            print(f'[✓] 文件已存在，跳过下载: {path}')
            continue

        try:
            # 发起 GET 请求时添加更完整的头部
            resp = requests.get(url, headers={
                **HEADERS,
                'Referer': base_url,
                'Accept': 'image/*,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'keep-alive'
            }, timeout=15, stream=True)

            # 若返回状态码不为 200，跳过
            if resp.status_code != 200:
                print(f'[×] 返回状态码异常 {resp.status_code}: {url}')
                continue

            content_type = resp.headers.get('Content-Type', '')
            if not content_type.startswith('image'):
                # 输出部分返回内容以便调试
                sample = resp.content[:200].decode('utf-8', errors='ignore')
                print(f'[×] 跳过非图片资源: {url} Content-Type: {content_type} 返回示例: {sample[:100]}')
                continue

            # 保存图片到本地
            with open(path, 'wb') as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)

            print(f'[√] 下载成功: {path}')
        except Exception as e:
            print(f'[×] 下载失败: {url} 原因: {e}')

            
@app.route('/fetch-images', methods=['GET'])
def fetch_images():
    target = request.args.get('url')
    if not target:
        return jsonify({'error': '请提供 url 参数'}), 400

    queue = [(target, 0)]
    visited, all_imgs = set(), []

    while queue and len(all_imgs) < MAX_IMAGES:
        url, depth = queue.pop(0)
        if url in visited or depth > MAX_DEPTH:
            continue
        visited.add(url)

        try:
            html = fetch_and_parse(url)
        except Exception as e:
            print(f'[×] 访问失败 {url}: {e}')
            continue

        # 提取图片和子页面链接
        imgs, links = extract_urls(url, html)

        # 下载当前页面的图片
        for img in imgs:
            cleaned = clean_image_url(img)
            if cleaned not in all_imgs:
                all_imgs.append(cleaned)
                if len(all_imgs) >= MAX_IMAGES:
                    break

        if ENABLE_DOWNLOAD and imgs:
            print(f"[→] 开始下载当前页面的图片: {url}")
            download_images(imgs, url)

        # 添加子页面链接到队列
        for link in links:
            if link not in visited:
                queue.append((link, depth + 1))

    result = all_imgs[:MAX_IMAGES]
    return jsonify({
        'total_found': len(all_imgs),
        'returned': len(result),
        'image_urls': result,
        'download_dir': os.path.join(IMAGE_SAVE_DIR, urlparse(target).netloc.replace('.', '_'))
                         if ENABLE_DOWNLOAD else None
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)