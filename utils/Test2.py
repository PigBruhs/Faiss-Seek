import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"工作目录已设置为: {os.getcwd()}")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.index_base import build_index_base

# 定义输入和索引文件夹路径
input_folder = "../data/base"
index_folder = "../index_base"

# 调用 build_index_base 函数
success = build_index_base(input_folder, index_folder)

# 检查结果
if success:
    print("All indices built successfully.")
else:
    print("Some indices failed to build.")