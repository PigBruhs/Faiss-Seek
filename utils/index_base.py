# FS/utils/index_base.py

import hashlib
from tqdm import tqdm
import os
import tempfile
from typing import Dict, List, Tuple

import faiss
import sys
import shutil

import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.portrait_extraction import resnet50_feature_extractor, vit_b_16_feature_extractor

def build_index_base(input_folder: str, index_folder: str) -> bool:
    # 清理并创建索引输出目录
    local_dir = os.path.join(index_folder, 'local')
    if os.path.isdir(local_dir):
        shutil.rmtree(local_dir)
    os.makedirs(local_dir, exist_ok=True)

    success = True
    exts = ('.jpg', '.jpeg', '.png', '.bmp')

    for fname in tqdm(os.listdir(input_folder), desc='Building indices'):
        if not fname.lower().endswith(exts):
            continue
        path = os.path.join(input_folder, fname)
        try:
            # 提取特征并转为 (1, d) 的 float32 数组
            feat = vit_b_16_feature_extractor(image_path=path)
            faiss.write_index(feat, os.path.join(local_dir, f"{fname}.index"))
        except Exception as e:
            print(f"Failed to process {fname}: {e}")
            success = False

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
    input_folder = "../data/base"
    index_folder = "../index_base"
    success = build_index_base(input_folder, index_folder)
    print("All indices built successfully." if success else "Some indices failed to build.")