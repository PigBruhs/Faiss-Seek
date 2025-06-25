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


def decoder_ring(pname: str, results: list[tuple]) -> list[tuple]:
    """
    将搜索结果中的图片编号(如 'img_0085') 转换为其原始URL。

    <<< 核心修改: 修正了URL的解码逻辑 >>>

    Args:
        pname (str): 项目名称 (例如 'pixnio')。
        results (list): 搜索结果列表，格式为 [('img_0085', 0.54), ...]。

    Returns:
        list: 解码后的结果列表，格式为 [('http://...', 0.54), ...]。
    """
    # 构造一次映射文件的路径，避免在循环中重复构造
    try:
        # 使用 Pathlib 提高路径操作的健壮性
        PROJECT_ROOT = Path(__file__).resolve().parents[1]
        mapping_file = PROJECT_ROOT / "index_base" / "url" / pname / "url_mapping.json"

        if not mapping_file.exists():
            print(f"[警告] 找不到URL映射文件，将返回原始文件名: {mapping_file}")
            return results
        
        with open(mapping_file, 'r', encoding='utf-8') as f:
            url_mapping = json.load(f)
            
    except Exception as e:
        print(f"[严重错误] 加载URL映射文件失败: {e}")
        # 如果加载失败，直接返回原始文件名，避免程序崩溃
        return results

    decoded_results = []
    for item in results:
        if isinstance(item, tuple) and len(item) == 2:
            name, score = item # name 是 'img_xxxx'

            # <<< 核心修改: 使用 .get() 方法安全地查找URL >>>
            # 如果 name (例如 'img_0085') 在映射表中，则替换为对应的URL。
            # 如果不在 (例如这是一个本地文件名)，则保持原样。
            decoded_name = url_mapping.get(name, name)
            
            decoded_results.append((decoded_name, score))
        else:
            print(f"跳过无效的结果项: {item}")
            
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







