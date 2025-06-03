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
        try:
            topn = searcher.search_topn(img, model=model, top_n=top_n, fe=self.fe)
        except Exception as e:
            print("图片匹配失败")
            result = {"success": False, "message": "图片匹配失败"}
            return result

        base_url = request.host_url + "data/base/"
        results = [{"name": name, "url": base_url + name, "score": score} for name, score in topn]

        result = {"success": True, "message": "图片接受成功", "result": results}
        return result







        