import os


import faiss
import sys
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.feature_extraction import feature_extractor

def build_index_base(input_folder: str, index_folder: str, model = "vgg16", fe=None) -> bool:
    # 清理并创建索引输出目录
    if os.path.isdir(index_folder):
        shutil.rmtree(index_folder)
    os.makedirs(index_folder, exist_ok=True)

    success = True
    exts = ('.jpg', '.jpeg', '.png', '.bmp')

    for fname in os.listdir(input_folder):
        if not fname.lower().endswith(exts):
            continue
        path = os.path.join(input_folder, fname)
        try:

            feat = fe.extract(image_path=path, model=model)

            faiss.write_index(feat, os.path.join(index_folder, f"{fname}.index"))
        except Exception as e:
            print(f"Failed to process {fname}: {e}")
            success = False

    return success

def load_index_base(index_folder: str) -> dict[str, faiss.IndexFlatIP]:
    indices = {}
    if not os.path.isdir(index_folder):
        print(f"Index folder {index_folder} does not exist.")
        return indices
    for fn in os.listdir(index_folder):
        if fn.endswith('.index'):
            name, _ = os.path.splitext(fn)
            idx_path = os.path.join(index_folder, fn)
            idx = faiss.read_index(idx_path)
            indices[name] = idx
    return indices

if __name__ == "__main__":
    input_folder = "../data/base"
    index_folder = "../index_base"
    success = build_index_base(input_folder, index_folder,model="vgg16")
    print("All indices built successfully." if success else "Some indices failed to build.")