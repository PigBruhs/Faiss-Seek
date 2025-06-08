import os
import faiss
import numpy as np
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.index_base import load_index_base
from utils.feature_extraction import feature_extractor

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'#这里似乎是因为我电脑上跑着两个pytorch导致它报的不安全。实际情况应该不会用到

class searcher:
    """
    用于检索图片的类，初始化时加载索引文件夹。
    """

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
        在 index_base（名称->单向量索引）中，检索与给定图片最相似的前 top_n 个结果。

        参数：
          index_base: Dict[name, faiss.IndexFlatIP]
          image_path: 本地图片路径，可选
          image: 内存中图片（PIL Image 或 bytes），优先
          top_n: 返回的最相似结果数
        返回：
          List[(名称, 相似度)]
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
            for name, idx in index_base.items():
                nt = idx.ntotal
                if nt == 0:
                    continue
                vecs = idx.reconstruct_n(0, nt).astype(np.float32)
                faiss.normalize_L2(vecs)
                for v in vecs:
                    names.append(name)
                    feats.append(v)

            if not feats:
                print("底库向量为空，无法进行搜索")
                return []

            features = np.stack(feats, axis=0)
            d = features.shape[1]
            flat = faiss.IndexFlatIP(d)
            flat.add(features)

            # 搜索并映射回名称
            distances, indices = flat.search(query_vec, top_n)
            results = []
            for idx, score in zip(indices[0], distances[0]):
                if idx < len(names):
                    results.append((names[idx], float(score)))
                else:
                    print(f"跳过无效的索引: {idx}")
            return results
        except Exception as e:
            print(f"搜索失败，错误详情: {e}")
            return []


"""
if __name__ == "__main__":
    # 测试用例
    from utils.feature_extraction import feature_extractor
    test_image = "../data/search/002_anchor_image_0001.jpg"
    from PIL import Image
    fe = feature_extractor()
    results = searcher.search_topn(image=Image.open(test_image), model="vgg16", fe=fe, top_n=5, mode="url", name="test_index")
    print(results)
"""






