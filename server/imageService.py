import sys
import os
import threading
import queue
from PIL import Image
from pathlib import Path
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

    # <<< MODIFIED: 此方法逻辑已大幅简化
    def download_images(self, url, name, max_imgs=128):
        """
        该方法现在只负责创建并运行爬虫。
        爬虫自身将在完成批处理时通过task_queue进行通知。
        """
        # 在创建爬虫时，将自身的任务队列传递进去
        crawl = crawler(url, name, max_imgs, task_queue=self.task_queue)
        
        # crawl_page 现在会阻塞，直到所有爬取和下载工作完成
        crawl.crawl_page()
        
        # crawl_page 结束后，保存最终的URL映射文件
        crawl.save_image()

        # 所有下载任务已完成，向索引线程发送终止信号
        print("[通知] 所有下载任务完成，向索引线程发送终止信号。")
        self.task_queue.put(None)

    def index_images(self, name):
        """此方法无需修改，其逻辑已经是正确的事件驱动模型。"""
        base_image_folder = Path(f"../crawled_images/{name}")
        while True:
            # 阻塞等待直到收到新任务（批次号）
            batch_num = self.task_queue.get()

            # 检查终止信号
            if batch_num is None:
                self.task_queue.task_done()
                break

            print(f"[索引] 开始处理批次 {batch_num}...")
            batch_folder = base_image_folder / f"batch{batch_num}"
            index_folder = Path(f"../index_base/url/{name}")
            index_folder.mkdir(parents=True, exist_ok=True)

            if not batch_folder.exists():
                print(f"[警告] 索引失败：找不到批次文件夹 {batch_folder}")
                self.task_queue.task_done()
                continue

            for model in ["resnet50", "vgg16", "vit16"]:
                build_index_base(
                    input_folder=str(batch_folder),
                    index_folder=str(index_folder / model),
                    fe=self.fe,
                    model=model
                )
            
            # 索引完成后删除该批次的图片以节省空间
            print(f"[索引] 批次 {batch_num} 处理完成，删除临时图片文件。")
            shutil.rmtree(batch_folder)
            self.task_queue.task_done()
        
        print("[索引] 索引线程已退出。")


    # <<< MODIFIED: 简化线程启动逻辑
    def reconstruct_index_base(self, name=None,path_or_url=None, max_imgs=4096):
        try:
            if not (path_or_url.startswith("http://") or path_or_url.startswith("https://")):
                 # 此处省略了本地路径处理逻辑，因为它与问题无关
                raise ValueError("当前仅处理URL输入")

            # 创建并启动线程
            print("[服务] 启动下载和索引线程...")
            download_thread = threading.Thread(target=self.download_images, args=(path_or_url, name, max_imgs))
            index_thread = threading.Thread(target=self.index_images, args=(name,))

            # 同时启动两个线程，它们通过队列进行通信
            download_thread.start()
            index_thread.start()

            # 等待两个线程都完成
            download_thread.join()
            index_thread.join()
            print("[服务] 下载和索引线程均已完成。")
            
            # 检查最终结果
            index_folder = Path(f"../index_base/url/{name}")
            model_folders = [index_folder / model for model in ["resnet50", "vgg16", "vit16"]]
            index_counts = [len(list(folder.glob("*.index"))) for folder in model_folders if folder.exists()]

            if len(set(index_counts)) == 1 and index_counts:
                index_count = index_counts[0]
            else:
                # 即使列表为空或数量不一致，也进行计算
                index_count = sum(index_counts) if index_counts else 0
                if len(set(index_counts)) > 1:
                     print(f"[警告] 三个模型文件夹下的索引数量不一致: {index_counts}")


            return {
                "success": True,
                "message": f"{name} 索引库重建成功",
                "index_count": index_count
            }

        except Exception as e:
            print(f"索引库重建失败: {e}")
            return {"success": False, "message": f"{name} 索引库重建失败: {str(e)}", "index_count": -1}
    
    # 以下方法 destroy_index_base 和 img_search 无需修改
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

    # 测试索引重建

    result = service.reconstruct_index_base(name="test_index", path_or_url="https://www.hippopx.com", max_imgs=6)
    print(result)


    # 测试图片搜索
    from PIL import Image
    test_image = Image.open("../data/search/002_anchor_image_0001.jpg")
    search_result = service.img_search(test_image, model="vgg16", top_n=5, mode="url", name="test_index")
    print(search_result)
