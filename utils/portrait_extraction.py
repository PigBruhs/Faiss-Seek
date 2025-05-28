import torch
import torchvision.transforms as transforms
from torchvision.models import resnet50,vit_b_16
from PIL import Image
import numpy as np
import faiss
import io


def resnet50_feature_extractor(image_path=None, image=None,max_dim=1024):
    """ResNet-50特征提取函数
    参数：
        image_path: 输入图片路径
        image: 输入图片对象(内存中的
        max_dim: 最大限制尺寸
    返回：
        faiss的归一化向量
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
    if image is not None:
        if isinstance(image, bytes):
            img = Image.open(io.BytesIO(image))
        else:
            img = image
    elif image_path is not None:
        img = Image.open(image_path)
    else:
        raise ValueError("必须提供 image_path 或 image 参数")
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

    # GPU加速
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    feature_extractor = feature_extractor.to(device)
    input_tensor = input_tensor.to(device)

    # 特征提取
    with torch.no_grad():
        features = feature_extractor(input_tensor)

    features = features.squeeze().cpu().numpy()  # 降维至(2048,)
    features = np.expand_dims(features, axis=0)  # Faiss需要二维输入

    # L2归一化（提升相似度计算效果）
    faiss.normalize_L2(features)
    index = faiss.IndexFlatIP(2048)
    index.add(features)

    return index


def vit_b_16_feature_extractor(image_path=None, image=None, max_dim=1024):
    # 1. 预处理
    preprocess = transforms.Compose([
        transforms.Lambda(lambda img: img.convert('RGB')),
        transforms.Lambda(lambda img: img.resize(
            (max_dim, int(img.size[1] * max_dim / img.size[0]))
            if img.size[0] < img.size[1] else
            (int(img.size[0] * max_dim / img.size[1]), max_dim),
            Image.LANCZOS)),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])
    if image is not None:
        img = Image.open(io.BytesIO(image)) if isinstance(image, bytes) else image
    elif image_path is not None:
        img = Image.open(image_path)
    else:
        raise ValueError("必须提供 image_path 或 image 参数")
    input_tensor = preprocess(img).unsqueeze(0)

    # 2. 加载模型权重
    model = vit_b_16(weights=None)
    checkpoint = torch.load("../pretrained/imagenet21k+imagenet2012_ViT-B_16-224.pth", map_location='cpu')
    state_dict = checkpoint.get('state_dict', checkpoint)
    model.load_state_dict(state_dict, strict=False)
    model.eval()

    # 3. 手动执行 forward_features
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    input_tensor = input_tensor.to(device)
    with torch.no_grad():
        # 直接用已预处理的 input_tensor，保证通道数为 3
        x = input_tensor
        x = model.conv_proj(x)  # 输出 (B, C, H, W)
        B, C, H, W = x.shape
        x = x.flatten(2).transpose(1, 2)  # (B, N, C)
        cls_token = model.class_token.expand(B, -1, -1)
        x = torch.cat((cls_token, x), dim=1)  # (B, N+1, C)
        x = x + model.encoder.pos_embedding
        x = model.encoder.dropout(x)
        for block in model.encoder.layers:
            x = block(x)
        x = model.encoder.ln(x)
        features = x[:, 0]  # 取 [CLS] token

    # 4. 构建 Faiss 索引
    feats = features.cpu().numpy().astype('float32')
    faiss.normalize_L2(feats)
    index = faiss.IndexFlatIP(feats.shape[1])
    index.add(feats)

    return index


# 使用示例 ---------------------------------------------------
if __name__ == "__main__":
    features = vit_b_16_feature_extractor("../data/search/002_anchor_image_0001.jpg")
    print(features)


