import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import torch
import torchvision.transforms as transforms
from torchvision.models import resnet50
from PIL import Image
import numpy as np
import faiss


def resnet50_feature_extractor(image_path, max_dim=1024):
    """ResNet-50特征提取函数
    参数：
        image_path: 输入图片路径
        max_dim: 最大限制尺寸（保持长宽比，防止显存溢出）
    返回：
        faiss兼容的归一化向量（numpy数组）
    """
    # 图像预处理流水线
    preprocess = transforms.Compose([
        transforms.Lambda(lambda img: img.convert('RGB')),  # 强制转RGB
        transforms.Lambda(lambda img: img.resize(  # 智能尺寸限制
            (max_dim, max_dim) if max(img.size) > max_dim else img.size,
            Image.LANCZOS)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])

    # 加载并预处理图像
    img = Image.open(image_path)
    input_tensor = preprocess(img).unsqueeze(0)  # 添加batch维度

    # 初始化模型（自动下载预训练权重）
    model = resnet50(weights=None)

    checkpoint_path = "../pretrained/resnet50-0676ba61.pth"
    state_dict = torch.load(checkpoint_path)
    model.load_state_dict(state_dict)

    # 截断模型至全局平均池化层前
    feature_extractor = torch.nn.Sequential(
        *list(model.children())[:-2],  # 保留至layer4
        torch.nn.AdaptiveAvgPool2d(1)  # 动态适应任意尺寸
    )
    feature_extractor.eval()

    # GPU加速（适配RTX 4080S）
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    feature_extractor = feature_extractor.to(device)
    input_tensor = input_tensor.to(device)

    # 特征提取
    with torch.no_grad():
        features = feature_extractor(input_tensor)

    # 转换为Faiss兼容格式
    features = features.squeeze().cpu().numpy()  # 降维至(2048,)
    features = np.expand_dims(features, axis=0)  # Faiss需要二维输入

    # L2归一化（提升相似度计算效果）
    faiss.normalize_L2(features)

    return features


# 使用示例 ---------------------------------------------------
if __name__ == "__main__":
    features = resnet50_feature_extractor("../data/search/002_anchor_image_0001.jpg")

    # 创建Faiss索引
    dimension = 2048  # ResNet-50特征维度
    index = faiss.IndexFlatIP(dimension)  # 内积索引（已归一化）

    # 添加特征到索引
    index.add(features)
    print("特征向量已存入Faiss索引，形状：", features.shape)
    print(features)

