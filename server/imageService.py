from flask import Flask, request, jsonify,g
from flask_cors import CORS
import sys
import os
from werkzeug.utils import secure_filename

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.index_base import build_index_base,load_index_base
from utils.index_search import searcher
from utils.feature_extraction import feature_extractor
from flask import Flask, request, jsonify

class ImageService:
    def __init__(self):
        self.fe = feature_extractor()
        build_index_base(input_folder="../data/base",index_folder= "../index_base/local/resnet50",fe=self.fe,model="resnet50")
        build_index_base(input_folder="../data/base",index_folder= "../index_base/local/vit16",fe=self.fe,model="vit16")
        build_index_base(input_folder="../data/base",index_folder= "../index_base/local/vgg16",fe=self.fe,model="vgg16")
        self.searcher = searcher()


    def img_search(self,img,model="vgg16",top_n=5):
        return searcher.search_topn(img, model=model, top_n=top_n, fe=self.fe)

if __name__=="__main__":
    # 测试 ImageService 类
    image_service = ImageService()
    test_image_path = "../data/search/002_anchor_image_0001.jpg"
    results = image_service.img_search(test_image_path, model="vit16", top_n=5)
    print(results)


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
        topn = imageService.img_search(file_path, model="vgg16", top_n=5)
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



        