from flask import Flask, request, jsonify,g
from flask_cors import CORS
import sys
import os
from werkzeug.utils import secure_filename

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.index_base import load_index_base
from utils.index_search import search_topn
from flask import Flask, request, jsonify

class ImageService:
    def imageMatch(self,file):
        return ImageMatch(file)


imageService=ImageService()

def ImageMatch(file):
    filename = secure_filename(file.filename)
    if '.' not in filename:
        filename += '.jpg'

    temp_dir = '../data/temp'
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    file_path = os.path.join(temp_dir, filename)
    file.save(file_path)

    if not os.path.exists(file_path):
        result={"success":False,"message":"文件保存失败"}
        return result

    try:
        indices = load_index_base('../index_base/local')  # 加载索引
        print("索引加载成功:", indices.keys())  # 打印加载的索引文件名
    except Exception as e:
        print("索引加载失败:", str(e))
        raise

    try:
        topn = search_topn(indices, image_path=file_path, top_n=5)  # 获取匹配结果
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        print("图片匹配失败")
        result={"success":False,"message":"图片匹配失败"}
        return result


    if os.path.exists(file_path):
        os.remove(file_path)

    base_url = request.host_url + "data/base/"
    results = [{"name": name, "url": base_url + name, "score": score} for name, score in topn]

    result={"success":True, "message":"图片接受成功", "result":results}
    return result

        