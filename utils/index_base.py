import os
import faiss
from portrait_extraction import resnet50_feature_extractor
from typing import Dict

# 批量读取文件夹中图片，提取特征并为每张图片创建并保存 Faiss 索引
def build_and_save_indices(input_folder: str, index_folder: str):
    """
    批量处理 input_folder 下的所有图片文件，提取 ResNet50 特征，创建 IndexFlatIP 索引并保存到 index_folder。
    """
    os.makedirs(index_folder, exist_ok=True)
    for filename in os.listdir(input_folder):
        if filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
            image_path = os.path.join(input_folder, filename)
            feat = resnet50_feature_extractor(image_path)
            index = feat
            base, _ = os.path.splitext(filename)
            index_path = os.path.join(index_folder, f"{base}.index")
            faiss.write_index(index, index_path)

# 从磁盘加载所有 .index 文件，返回图片名到 Faiss 索引的映射
def load_indices(index_folder: str) -> Dict[str, faiss.IndexFlatIP]:
    """
    扫描 index_folder 下所有 .index 文件，加载为 Faiss 索引，并以文件名(不含扩展)为 key 返回。
    """
    indices: Dict[str, faiss.IndexFlatIP] = {}
    for file in os.listdir(index_folder):
        if file.lower().endswith(".index"):
            name, _ = os.path.splitext(file)
            path = os.path.join(index_folder, file)
            indices[name] = faiss.read_index(path)
    return indices

if __name__ == "__main__":
    # 测试代码
    input_folder = "../data/base"
    index_folder = "../index_base"
    build_and_save_indices(input_folder, index_folder)
    indices = load_indices(index_folder)
    for name, index in indices.items():
        print(f"Loaded index for {name}: {index.ntotal} vectors")

    from index_similarity import compute_index_similarity
    features = resnet50_feature_extractor("../data/search/002_anchor_image_0001.jpg")
    similarities = []
    for name, index in indices.items():
        compute_index_similarity(features, index)
        similarities.append((name, compute_index_similarity(features, index)))

    similarities.sort(key=lambda x: x[1], reverse=True)
    print(f"相似度排序：{similarities}")

