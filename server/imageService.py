import sys
import os
import threading
import queue
from PIL import Image
from pathlib import Path
import shutil
import time

# 假设其他模块路径正确
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
        self.task_queue = queue.Queue()
        self.url_to_filename_map = {}

    def download_images(self, url, name, max_imgs=20000):
        """
        启动爬虫下载图片。此方法现在只负责创建和启动爬虫，不干涉其内部线程管理。
        """
        try:
            print(f"[下载服务] 开始处理URL: {url}, 目标库: {name}, 最大图片数: {max_imgs}")
            
            crawl_instance = crawler(
                url=url, 
                name=name, 
                max_images=max_imgs, 
                task_queue=self.task_queue
            )
            
            crawl_instance.crawl_page()
            
            print(f"[下载服务] 爬取和下载过程结束。最终下载数量: {crawl_instance.downloaded_image_count}")
            
            crawl_instance.save_image()
            self.url_to_filename_map = crawl_instance.decoder()

        except Exception as e:
            print(f"[下载服务] 处理下载任务时发生严重错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("[下载服务] 发送任务结束信号给索引线程。")
            self.task_queue.put(None)

    def index_images(self, name):
        """
        <<< 核心重构: 优化索引流程，避免重复加载模型 >>>
        该方法现在会先收集所有待处理的批次，然后按模型对所有批次进行统一处理。
        """
        base_image_folder = Path(f"../crawled_images/{name}")
        
        # 阶段一：收集所有准备就绪的批次任务
        ready_batch_folders = []
        print("[索引服务] 等待下载线程发送批次任务...")
        while True:
            try:
                # 阻塞式获取任务，直到收到None信号
                batch_num = self.task_queue.get()
                
                if batch_num is None:
                    print("[索引服务] 收到下载结束信号，开始集中处理所有批次。")
                    self.task_queue.task_done()
                    break
                
                print(f"[索引服务] 收到批次 {batch_num} 准备就绪的信号。")
                batch_folder = base_image_folder / f"batch{batch_num}"
                if batch_folder.exists():
                    ready_batch_folders.append(batch_folder)
                else:
                    print(f"[警告] 收到批次 {batch_num} 信号，但文件夹不存在: {batch_folder}")
                self.task_queue.task_done()

            except queue.Empty:
                # 在阻塞模式下理论上不会发生，但作为安全保障
                print("[索引服务] 任务队列意外为空，退出监听。")
                break
        
        # 阶段二：按模型为所有批次建立索引
        index_folder = Path(f"../index_base/url/{name}")
        index_folder.mkdir(parents=True, exist_ok=True)

        if not ready_batch_folders:
            print("[索引服务] 没有需要处理的批次，索引任务结束。")
            return

        for model in ["resnet50", "vgg16", "vit16"]:
            print(f"--- 开始为模型 '{model}' 处理所有批次 ---")
            for batch_folder in ready_batch_folders:
                print(f"[索引] 使用模型 '{model}' 处理文件夹: {batch_folder.name}")
                build_index_base(
                    input_folder=str(batch_folder),
                    index_folder=str(index_folder / model),
                    fe=self.fe,
                    model=model
                )
        
        # 阶段三：统一清理所有处理过的批次文件夹
        print("[清理] 所有索引任务已完成，开始删除临时图片文件夹...")
        for batch_folder in ready_batch_folders:
            try:
                if batch_folder.exists():
                    shutil.rmtree(batch_folder)
                    print(f"[清理] 已删除: {batch_folder}")
            except OSError as e:
                print(f"[清理错误] 删除文件夹 {batch_folder} 失败: {e}")

        print("[索引] 索引线程已成功退出。")

    def reconstruct_index_base(self, name=None, path_or_url=None, max_imgs=4096):
        # ... (此部分逻辑无需修改，保持原样) ...
        is_url = path_or_url and (path_or_url.startswith("http://") or path_or_url.startswith("https://"))
        if not is_url and Path(path_or_url).exists():
            input_folder = str(path_or_url)
            index_folder = Path("../index_base/local")
            for model in ["resnet50", "vgg16", "vit16"]:
                build_index_base(
                    input_folder=input_folder,
                    index_folder=str(index_folder / model),
                    fe=self.fe,
                    model=model
                )
            index_counts = [len(list((index_folder / model).glob("*.index"))) for model in ["resnet50", "vgg16", "vit16"]]

            if len(set(index_counts)) > 1:
                print(f"[警告] 三个模型文件夹下的索引数量不一致: {index_counts}")

            index_count = index_counts[0] if index_counts else 0
            print(f"[服务] 本地图源更新完毕，索引数量: {index_count}")

            return {"success": True, "message": f"本地图源更新完毕", "index_count": index_count}
        elif is_url:
            try:
                print("[服务] 准备启动下载和索引双线程...")
                download_thread = threading.Thread(target=self.download_images, args=(path_or_url, name, max_imgs))
                index_thread = threading.Thread(target=self.index_images, args=(name,))

                download_thread.start()
                index_thread.start()

                download_thread.join()
                print("[服务] 下载线程已结束。")
                index_thread.join()
                print("[服务] 索引线程已结束。")

                print("[服务] 所有任务已完成。")

                index_folder = Path(f"../index_base/url/{name}")
                if not index_folder.exists():
                    return {"success": True, "message": f"{name} 索引库重建完成，但未生成任何索引文件（可能未爬取到图片）。",
                            "index_count": 0}

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
        return {
            "success": False,
            "message": f"提供的路径 '{path_or_url}' 不是有效的URL且在本地不存在",
            "index_count": -1
        }

    def destroy_index_base(self,name=None):
        # ... (此部分逻辑无需修改，保持原样) ...
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
        # ... (此部分逻辑无需修改，保持原样) ...
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
    result = service.reconstruct_index_base(
        name="test_unsplash", 
        path_or_url="https://unsplash.com/t/wallpapers", 
        max_imgs=20
    )
    print(json.dumps(result, indent=2))
