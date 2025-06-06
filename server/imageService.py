import sys
import os
import threading
import queue
from PIL import Image
from pathlib import Path
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.index_base import build_index_base
from utils.index_search import searcher
from utils.feature_extraction import feature_extractor
from utils.crawler import crawler
from flask import Flask, request, jsonify
from tqdm import tqdm

class ImageService:
    def __init__(self):
        self.fe = feature_extractor()
        self.searcher = searcher()
        self.task_queue = queue.Queue()
        self.url_to_filename_map = {}

    def download_images(self, url, name, max_imgs=128):
        base_image_folder = Path(f"../crawled_images/{name}")  # 注意拼写是crawled_images
        base_image_folder.mkdir(parents=True, exist_ok=True)
        crawl = crawler(url,name,max_imgs)
        crawl.crawl_page()

        total_batches = (max_imgs + 127) // 128
        for batch_num in tqdm(range(total_batches)):
            crawl.save_image()
            self.url_to_filename_map=crawl.decoder()

            # 通知索引线程处理新批次
            self.task_queue.put(batch_num)
            self.task_queue.put(None)




    def index_images(self, name):
        base_image_folder = Path(f"../crawled_images/{name}")  # 修正拼写：crawled_images
        while True:
            # 阻塞等待直到收到新任务
            batch_num = self.task_queue.get()

            # 检查终止信号
            if batch_num is None:
                self.task_queue.task_done()
                break

            batch_folder = base_image_folder / f"batch_{batch_num}"
            index_folder = Path(f"../index_base/url/{name}")
            index_folder.mkdir(parents=True, exist_ok=True)

            for model in ["resnet50", "vgg16", "vit16"]:
                build_index_base(
                    input_folder=str(batch_folder),
                    index_folder=str(index_folder / model),
                    fe=self.fe,
                    model=model
                )

            shutil.rmtree(batch_folder)
            self.task_queue.task_done()

    def reconstruct_index_base(self, name=None,path_or_url=None, max_imgs=32767):
        try:
            # 创建并启动线程
            if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
                is_url = True
            elif os.path.isabs(path_or_url):
                is_url = False
            else:
                raise ValueError("输入既不是有效的 URL，也不是绝对路径")
            if is_url:
                download_thread = threading.Thread(target=self.download_images, args=(path_or_url, name, max_imgs))
                index_thread = threading.Thread(target=self.index_images, args=(name,))

                # 先启动下载线程
                download_thread.start()
                # 稍等确保下载线程先运行
                threading.Event().wait(0.1)
                # 再启动索引线程
                index_thread.start()

                # 等待线程完成
                download_thread.join()
                index_thread.join()

            else:
                # 如果是本地路径，直接构建索引
                index_folder = Path(f"../index_base/local/{name}")
                index_folder.mkdir(parents=True, exist_ok=True)
                base_image_folder = Path(f"../data/local/{name}")
                base_image_folder.mkdir(parents=True, exist_ok=True)

                source_folder = Path(path_or_url)
                if not source_folder.exists() or not source_folder.is_dir():
                    raise FileNotFoundError("指定的本地路径不存在或不是文件夹")

                for file in source_folder.iterdir():
                    if file.is_file() and file.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                        shutil.copy(file, base_image_folder)

                for model in ["resnet50", "vgg16", "vit16"]:
                    build_index_base(
                        input_folder=str(base_image_folder),
                        index_folder=str(index_folder / model),
                        fe=self.fe,
                        model=model
                    )

            return {"success": True, "message": f"{name} 索引库重建成功"}
        except Exception as e:
            print(f"索引库重建失败: {e}")
            return {"success": False, "message": f"{name} 索引库重建失败"}

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


    def img_search(self,img,model="vgg16",top_n=5,mode="local",name=None):
        try:
            img = Image.open(img.stream).convert('RGB')
            topn = searcher.search_topn(image = img, model=model, top_n=top_n, fe=self.fe,mode=mode, name=name)
        except Exception as e:
            print("图片匹配失败")
            result = {"success": False, "message": f"图片匹配失败，{e}"}
            return result

        results = [{"name": name,"score": score} for (name,score) in topn]

        return {
        "success": True,
        "message": "图片匹配成功",
        "result": results
        }
    def decoder_ring(self,results):
        res = []
        for name,score in results:
            filename = self.url_to_filename_map.get(name)
            res.append((filename,score))
        return res



if __name__ == "__main__":
    service = ImageService()

    # 测试索引重建

    result = service.reconstruct_index_base(name="test_index", path_or_url="https://www.hippopx.com", max_imgs=384)
    print(result)


    # 测试图片搜索
    from PIL import Image
    test_image = Image.open("../data/search/002_anchor_image_0001.jpg")
    search_result = service.img_search(test_image, model="vgg16", top_n=5, mode="url", name="test_index")
    print(search_result)





        