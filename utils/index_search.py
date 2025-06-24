import os
import faiss
import numpy as np
import sys
import json
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.index_base import load_index_base
from utils.feature_extraction import feature_extractor

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'#这里似乎是因为我电脑上跑着两个pytorch导致它报的不安全。实际情况应该不会用到


def decoder_ring(pname, results):
    """
    将搜索结果中的图片编号转换为原始URL

    参数:
        pname: 项目名称
        results: 搜索结果列表，格式为[(文件名, 相似度分数),...]
    返回:
        解码后的结果列表，同样格式
    """
    decoded_results = []
    for item in results:
        # 确保item是(name, score)格式的元组
        if isinstance(item, tuple) and len(item) == 2:
            name, score = item

            # 判断是否为URL编号格式
            if isinstance(name, str) and name.startswith("url_") and "." in name:
                try:
                    # 提取编号
                    image_idx = name.split("_")[1].split(".")[0]
                    
                    # 使用项目根目录作为基准
                    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    index_base_path = os.path.join(PROJECT_ROOT, "index_base", "url", pname)
                    mapping_file = os.path.join(index_base_path, "url_mapping.json")

                    if os.path.exists(mapping_file):
                        with open(mapping_file, 'r', encoding='utf-8') as f:
                            url_mapping = json.load(f)
                            if image_idx in url_mapping:
                                name = url_mapping[image_idx]
                except Exception as e:
                    print(f"解码URL失败: {e}")

            # 添加解码后的结果，保持元组格式
            decoded_results.append((name, score))
        else:
            print(f"跳过无效结果项: {item}")

    return decoded_results


def search_topn(
        image_path: str = None,
        image=None,
        top_n: int = 5,
        model="vgg16",
        fe=None,
        mode="local",
        name=None
) -> list[tuple[str, float]]:
    """
    在索引库中检索与给定图片最相似的前 top_n 个结果。

    参数：
      image_path: 本地图片路径，可选
      image: 内存中图片（PIL Image 或 bytes），优先
      top_n: 返回的最相似结果数
    返回：
      List[(URL或文件名, 相似度)]
    """
    try:

        # 加载索引库
        if mode == "local":
            index_path = f"../index_base/local/{model}"
        elif mode == "url":
            index_path = f"../index_base/url/{name}/{model}"
        else:
            raise ValueError("Unsupported mode. Use 'local' or 'url'.")
        print(f"加载索引路径: {index_path}")
        index_base = load_index_base(index_path)

        if not index_base:
            print("索引库为空，无法进行搜索")
            return []

        # 提取查询向量
        if not image_path and not image:
            raise ValueError("必须提供 image_path 或 image 参数")
        query_img = fe.extract(image_path=image_path, image=image, model=model)
        query_vec = query_img.reconstruct_n(0, 1).astype(np.float32)

        if query_vec is None or query_vec.shape[0] == 0:
            raise ValueError("查询向量为空，无法进行搜索")
        faiss.normalize_L2(query_vec)

        # 合并底库所有向量并记录名称顺序
        names, feats = [], []
        for fname, idx in index_base.items():
            nt = idx.ntotal
            if nt == 0:
                continue
            vecs = idx.reconstruct_n(0, nt).astype(np.float32)
            faiss.normalize_L2(vecs)
            for v in vecs:
                names.append(fname)
                feats.append(v)

        if not feats:
            print("底库向量为空，无法进行搜索")
            return []

        features = np.stack(feats, axis=0)
        d = features.shape[1]
        flat = faiss.IndexFlatIP(d)
        flat.add(features)

        # 搜索并映射回名称或URL
        distances, indices = flat.search(query_vec, top_n)
        results = []
        for idx, score in zip(indices[0], distances[0]):
            if idx < len(names):
                file_name = names[idx]
                results.append((file_name, float(score)))
        decoded_results = decoder_ring(name, results)
        return decoded_results
    except Exception as e:
        print(f"搜索失败，错误详情: {e}")
        return []



if __name__ == "__main__":
    fe = feature_extractor()
    test_image = "../data/search/002_anchor_image_0001.jpg"
    from PIL import Image

    results = search_topn(image=Image.open(test_image), model="vgg16", fe=fe, top_n=5, mode="url",name="test_index")
    print(results)







