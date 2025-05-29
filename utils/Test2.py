import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.index_base import build_index_base

# 定义输入和索引文件夹路径
input_folder = "E:/软件实训开发/答而多图图/data/base"
index_folder = "E:/软件实训开发/答而多图图/index_base"

# 调用 build_index_base 函数
success = build_index_base(input_folder, index_folder)

# 检查结果
if success:
    print("All indices built successfully.")
else:
    print("Some indices failed to build.")