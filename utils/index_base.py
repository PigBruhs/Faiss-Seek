import os
import faiss
import sys
import shutil

# 假设其他模块路径正确
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.feature_extraction import feature_extractor

def build_index_base(input_folder: str, index_folder: str, model="vgg16", fe=None) -> bool:
    """
    为指定文件夹中的图片创建或追加FAISS索引。

    <<< 核心修改: 移除了 shutil.rmtree(index_folder) 以支持追加索引 >>>
    现在此函数不会删除已有的索引，而是在现有基础上添加新的索引文件。
    """
    # 确保索引输出目录存在，如果不存在则创建
    os.makedirs(index_folder, exist_ok=True)

    success = True
    exts = ('.jpg', '.jpeg', '.png', '.bmp', '.webp') # 增加了对 .webp 的支持

    # 检查输入文件夹是否存在
    if not os.path.isdir(input_folder):
        print(f"[错误] 输入文件夹不存在: {input_folder}")
        return False

    image_files = [fname for fname in os.listdir(input_folder) if fname.lower().endswith(exts)]
    
    if not image_files:
        print(f"[信息] 输入文件夹 {input_folder} 中没有找到需要处理的图片。")
        return True # 认为这是一个成功的操作，因为没有失败

    print(f"[信息] 在 {input_folder} 中找到 {len(image_files)} 张图片，开始创建索引...")

    for fname in image_files:
        path = os.path.join(input_folder, fname)
        index_path = os.path.join(index_folder, f"{os.path.splitext(fname)[0]}.index")
        
        # <<< 优化: 如果索引已存在，则跳过，避免重复工作
        if os.path.exists(index_path):
            # print(f"[跳过] 索引文件已存在: {index_path}")
            continue

        try:
            feat = fe.extract(image_path=path, model=model)
            if feat is None:
                print(f"[警告] 未能从图片中提取特征: {fname}")
                continue

            # 直接写入索引，因为我们是按文件处理，不会有冲突
            faiss.write_index(feat, index_path)
        except Exception as e:
            # 提供更详细的错误日志
            print(f"[严重错误] 处理文件 {fname} 失败: {e}")
            import traceback
            traceback.print_exc()
            success = False

    return success

def load_index_base(index_folder: str) -> dict[str, faiss.IndexFlatIP]:
    """
    从文件夹加载所有FAISS索引。此函数无需修改。
    """
    indices = {}
    if not os.path.isdir(index_folder):
        print(f"Index folder {index_folder} does not exist.")
        return indices
    
    for fn in os.listdir(index_folder):
        if fn.endswith('.index'):
            # 使用 os.path.splitext 来正确处理可能包含点的文件名
            name, _ = os.path.splitext(fn)
            idx_path = os.path.join(index_folder, fn)
            try:
                idx = faiss.read_index(idx_path)
                indices[name] = idx
            except Exception as e:
                print(f"加载索引文件 {fn} 失败: {e}")
                
    return indices

if __name__ == "__main__":
    # 这是一个测试用的主程序入口
    # 确保测试文件夹和路径正确
    # 例如:
    # input_folder = "../crawled_images/test_unsplash/batch0"
    # index_folder = "../index_base/url/test_unsplash/vgg16"
    
    print("这是一个库文件，请通过 ImageService 来调用它。")

