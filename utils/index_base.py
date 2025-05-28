# Faiss-Seek/utils/index_base.py

import os
import faiss
import hashlib
import tempfile
from typing import Dict, List, Tuple
from .portrait_extraction import resnet50_feature_extractor

def build_index_base(
    input_folder: str = None,
    index_folder: str = None,
    crawler_results: List[Tuple[str, bytes]] = None
) -> bool:
    url_dir = os.path.join(index_folder, 'url')
    local_dir = os.path.join(index_folder, 'local')
    os.makedirs(url_dir, exist_ok=True)
    os.makedirs(local_dir, exist_ok=True)
    success = True
    cache_dir = None

    try:
        if crawler_results:
            cache_dir = tempfile.mkdtemp()
            for url, img_bytes in crawler_results:
                key = hashlib.md5(url.encode('utf-8')).hexdigest()
                tmp_path = os.path.join(cache_dir, f"{key}.img")
                with open(tmp_path, 'wb') as f:
                    f.write(img_bytes)
                try:
                    feat = resnet50_feature_extractor(image=img_bytes)
                    d = feat.shape[1]
                    idx = faiss.IndexFlatIP(d)
                    idx.add(feat)
                    faiss.write_index(idx, os.path.join(url_dir, f"{key}.index"))
                    with open(os.path.join(url_dir, f"{key}.url"), 'w', encoding='utf-8') as f:
                        f.write(url)
                except Exception:
                    success = False
                finally:
                    os.remove(tmp_path)
        else:
            for filename in os.listdir(input_folder or ""):
                if not filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
                    continue
                try:
                    image_path = os.path.join(input_folder, filename)
                    feat = resnet50_feature_extractor(image_path=image_path)
                    d = feat.shape[1]
                    idx = faiss.IndexFlatIP(d)
                    idx.add(feat)
                    base, _ = os.path.splitext(filename)
                    faiss.write_index(idx, os.path.join(local_dir, f"{base}.index"))
                    with open(os.path.join(local_dir, f"{base}.url"), 'w', encoding='utf-8') as f:
                        f.write(base)
                except Exception:
                    success = False
    finally:
        if cache_dir and os.path.isdir(cache_dir):
            os.rmdir(cache_dir)

    return success

def load_index_base(index_folder: str) -> Dict[str, Dict[str, faiss.IndexFlatIP]]:
    indices: Dict[str, Dict[str, faiss.IndexFlatIP]] = {'local': {}, 'url': {}}
    for kind in ('local', 'url'):
        dir_path = os.path.join(index_folder, kind)
        if not os.path.isdir(dir_path):
            continue
        for fn in os.listdir(dir_path):
            if not fn.endswith(".index"):
                continue
            name, _ = os.path.splitext(fn)
            path = os.path.join(dir_path, fn)
            idx = faiss.read_index(path)
            url_file = os.path.join(dir_path, f"{name}.url")
            if os.path.isfile(url_file):
                with open(url_file, encoding='utf-8') as f:
                    key = f.read().strip()
            else:
                key = name
            indices[kind][key] = idx
    return indices


if __name__ == "__main__":
    # 测试代码
    input_folder = "../data/base"
    index_folder = "../index_base"
    success = build_index_base(input_folder, index_folder)
    if success:
        print("All indices built successfully.")
    else:
        print("Some indices failed to build.")
    indices = load_index_base(index_folder)
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
    


