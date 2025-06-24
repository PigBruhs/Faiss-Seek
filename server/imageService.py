import sys
import os
import threading
import queue
from PIL import Image
from pathlib import Path
import shutil
import time

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.index_base import build_index_base
from utils.index_search import search_topn
from utils.feature_extraction import feature_extractor
from utils.crawler import crawler
from tqdm import tqdm
import json

class ImageService:
    def __init__(self):
        self.fe = feature_extractor()
        # <<< 已修改: 任务队列在服务初始化时创建，确保单一实例
        self.task_queue = queue.Queue()
        self.url_to_filename_map = {}

    # <<< 已修改: 此方法逻辑已大幅简化和修正
    def download_images(self, url, name, max_imgs=128):
        """
        启动爬虫下载图片。此方法现在只负责创建和启动爬虫，不干涉其内部线程管理。
        """
        try:
            print(f"[下载服务] 开始处理URL: {url}, 目标库: {name}, 最大图片数: {max_imgs}")
            
            # <<< 关键修正: 创建爬虫实例时，将 self.task_queue 传递进去
            # 这样爬虫的下载线程才能和这里的索引线程通信
            crawl_instance = crawler(
                url=url, 
                name=name, 
                max_images=max_imgs, 
                task_queue=self.task_queue
            )
            
            crawl_instance.crawl_page()
            
            print(f"[下载服务] 爬取和下载过程结束。最终下载数量: {crawl_instance.downloaded_image_count}")
            
            # 任务结束后，保存URL映射
            crawl_instance.save_image()
            self.url_to_filename_map = crawl_instance.decoder()

        except Exception as e:
            print(f"[下载服务] 处理下载任务时发生严重错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # <<< 关键修正: 无论成功与否，都要向索引线程发送'None'信号，以确保它能正常退出
            print("[下载服务] 发送任务结束信号给索引线程。")
            self.task_queue.put(None)

    def index_images(self, name):
        """此方法逻辑正确，无需修改，它会等待来自下载线程的通知。"""
        # ... (此部分代码无需改动) ...
        base_image_folder = Path(f"../crawled_images/{name}")
        while True:
            try:
                batch_num = self.task_queue.get(timeout=600) # 加个超时避免永久阻塞
            except queue.Empty:
                print("[索引] 长时间未收到新任务，自动退出。")
                break

            if batch_num is None:
                print("[索引] 收到结束信号，索引线程准备退出。")
                self.task_queue.task_done()
                break

            print(f"[索引] 收到任务，开始处理批次 {batch_num}...")
            batch_folder = base_image_folder / f"batch{batch_num}"
            index_folder = Path(f"../index_base/url/{name}")
            index_folder.mkdir(parents=True, exist_ok=True)

            if not batch_folder.exists():
                print(f"[警告] 索引失败：找不到批次文件夹 {batch_folder}")
                self.task_queue.task_done()
                continue

            for model in ["resnet50", "vgg16", "vit16"]:
                print(f"[索引] 使用模型 {model} 为批次 {batch_num} 创建索引...")
                build_index_base(
                    input_folder=str(batch_folder),
                    index_folder=str(index_folder / model),
                    fe=self.fe,
                    model=model
                )
            
            print(f"[索引] 批次 {batch_num} 处理完成，删除临时图片文件。")
            try:
                shutil.rmtree(batch_folder)
            except OSError as e:
                print(f"[错误] 删除文件夹 {batch_folder} 失败: {e}")
                
            self.task_queue.task_done()
        
        print("[索引] 索引线程已成功退出。")

    # <<< 已修改: 简化线程启动逻辑
    def reconstruct_index_base(self, name=None, path_or_url=None, max_imgs=4096):
        try:
            if not (path_or_url and (path_or_url.startswith("http://") or path_or_url.startswith("https://"))):
                return {"success": False, "message": "无效的URL，请输入以http://或https://开头的网址"}

            print("[服务] 准备启动下载和索引双线程...")
            # 创建下载和索引的线程
            download_thread = threading.Thread(target=self.download_images, args=(path_or_url, name, max_imgs))
            index_thread = threading.Thread(target=self.index_images, args=(name,))

            # 同时启动，它们将通过 self.task_queue 进行协作
            download_thread.start()
            index_thread.start()

            # 等待两个线程都执行完毕
            download_thread.join()
            print("[服务] 下载线程已结束。")
            index_thread.join()
            print("[服务] 索引线程已结束。")
            
            print("[服务] 所有任务已完成。")
            
            # ... (后续的成功/失败返回逻辑保持不变) ...
            index_folder = Path(f"../index_base/url/{name}")
            if not index_folder.exists():
                return {"success": True, "message": f"{name} 索引库重建完成，但未生成任何索引文件（可能未爬取到图片）。", "index_count": 0}
                
            index_counts = [len(list((index_folder / model).glob("*.index"))) for model in ["resnet50", "vgg16", "vit16"]]
            
            if len(set(index_counts)) > 1:
                print(f"[警告] 三个模型文件夹下的索引数量不一致: {index_counts}")
            
            index_count = index_counts[0] if index_counts else 0

            return {"success": True, "message": f"{name} 索引库重建成功", "index_count": index_count}

        except Exception as e:
            print(f"索引库重建失败: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"{name} 索引库重建失败: {str(e)}", "index_count": -1}

    # ... (destroy_index_base 和 img_search 方法无需修改) ...
    def destroy_index_base(self,name=None):
        try:
            local_index_folder = Path(f"../index_base/local/{name}")
            if local_index_folder.exists() and local_index_folder.is_dir():
                shutil.rmtree(local_index_folder)
                local_data_folder = Path(f"../data/local/{name}")
                if local_data_folder.exists() and local_data_folder.is_dir():
                    shutil.rmtree(local_data_folder)
                return {"success": True, "message": f"{name} 索引库删除成功"}


            url_index_folder = Path(f"../index_base/url/{name}")
            if url_index_folder.exists() and url_index_folder.is_dir():
                shutil.rmtree(url_index_folder)

            return {"success": True, "message": f"{name} 索引库删除成功"}


        except Exception as e:
            print(f"索引库删除失败: {e}")
            return {"success": False, "message": f"{name} 索引库删除失败"}


    def img_search(self, img=None,img_path=None,model="vgg16", top_n=5, mode="local", name=None):
        try:
            if hasattr(img, 'stream'):
                img = Image.open(img.stream)

            topn = search_topn(image_path=img_path, image=img,model=model, top_n=top_n, fe=self.fe, mode=mode, name=name)

            if not isinstance(topn, list):
                return { "success": False, "message": "图片匹配失败，返回结果格式不正确" }

            results = []
            for item in topn:
                if isinstance(item, tuple) and len(item) == 2:
                    name, score = item
                    results.append({"name": name, "score": score})
                else:
                    print(f"跳过无效的匹配结果: {item}")

            return { "success": True, "message": "图片匹配成功", "result": results }
        except Exception as e:
            print(f"图片匹配失败，错误详情: {e}")
            return { "success": False, "message": f"图片匹配失败，{e}" }


if __name__ == "__main__":
    service = ImageService()
    # 找一个相对传统的、静态图片多的网站进行测试
    # 注意：很多网站如 wallhaven.cc, pexels.com 都有很强的反爬机制，用requests基本无法成功
    # 我们可以试试 unsplash，但成功率也不能保证
    result = service.reconstruct_index_base(
        name="test_unsplash", 
        path_or_url="https://unsplash.com/t/wallpapers", 
        max_imgs=20 # 测试时建议用小一点的数值
    )
    print(json.dumps(result, indent=2))
