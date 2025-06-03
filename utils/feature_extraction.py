import io

import faiss
import numpy as np
import torch
import torchvision.transforms as transforms
from PIL import Image
from torchvision.models import resnet50, vit_b_16,vgg16

class feature_extractor:

    def __init__(self):
        self.max_dim = 1024
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # 加载 ResNet50
        self.resnet = resnet50(weights=None)
        resnet_checkpoint = torch.load('../pretrained/resnet50-0676ba61.pth', map_location=self.device)
        self.resnet.load_state_dict(resnet_checkpoint)
        self.resnet = self.resnet.to(self.device)

        # 加载 VGG16
        self.vgg = vgg16(weights=None)
        vgg_checkpoint = torch.load('../pretrained/vgg16-397923af.pth', map_location=self.device)
        self.vgg.load_state_dict(vgg_checkpoint)
        self.vgg = self.vgg.to(self.device)

        # 加载 ViT-B/16
        self.vit = vit_b_16(weights=None)
        vit_checkpoint = torch.load('../pretrained/imagenet21k+imagenet2012_ViT-B_16-224.pth', map_location=self.device)
        if 'state_dict' in vit_checkpoint:
            vit_checkpoint = vit_checkpoint['state_dict']
        self.vit.load_state_dict(vit_checkpoint, strict=False)
        self.vit = self.vit.to(self.device)


    def resnet50_feature_extractor(self,img):
        # 图像预处理流水线
        preprocess = transforms.Compose([
            transforms.Lambda(lambda img: img.convert('RGB')),  # 强制转RGB
            transforms.Lambda(lambda img: img.resize(  # 智能尺寸限制
                (self.max_dim, self.max_dim) if max(img.size) > self.max_dim else img.size,
                Image.LANCZOS)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

        input_tensor = preprocess(img).unsqueeze(0)  # 添加batch维度

        # 截断模型至全局平均池化层前
        feature_extractor = torch.nn.Sequential(
            *list(self.resnet.children())[:-2],  # 保留至layer4
            torch.nn.AdaptiveAvgPool2d(1)  # 动态适应任意尺寸
        )
        feature_extractor.eval()
        input_tensor = input_tensor.to(self.device)

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

    def vit_b_16_feature_extractor(self,img):
        # 1. 预处理
        preprocess = transforms.Compose([
            transforms.Lambda(lambda img: img.convert('RGB')),  # 强制转RGB
            transforms.Lambda(lambda img: img.resize(  # 智能尺寸限制
                (224, 224),
                Image.LANCZOS)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

        input_tensor = preprocess(img).unsqueeze(0)

        input_tensor = input_tensor.to(self.device)
        with torch.no_grad():
            # 直接用已预处理的 input_tensor，保证通道数为 3
            x = input_tensor
            x = self.vit.conv_proj(x)  # 输出 (B, C, H, W)
            B, C, H, W = x.shape
            x = x.flatten(2).transpose(1, 2)  # (B, N, C)
            cls_token = self.vit.class_token.expand(B, -1, -1)
            x = torch.cat((cls_token, x), dim=1)  # (B, N+1, C)
            x = x + self.vit.encoder.pos_embedding
            x = self.vit.encoder.dropout(x)
            for block in self.vit.encoder.layers:
                x = block(x)
            x = self.vit.encoder.ln(x)
            features = x[:, 0]  # 取 [CLS] token

        # 4. 构建 Faiss 索引
        feats = features.cpu().numpy().astype('float32')
        faiss.normalize_L2(feats)
        index = faiss.IndexFlatIP(feats.shape[1])
        index.add(feats)

        return index

    def vgg16_feature_extractor(self,img):

        # 图像预处理流水线
        preprocess = transforms.Compose([
            transforms.Lambda(lambda img: img.convert('RGB')),
            transforms.Lambda(lambda img: img.resize(
                (self.max_dim, self.max_dim) if max(img.size) > self.max_dim else img.size,
                Image.LANCZOS)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

        input_tensor = preprocess(img).unsqueeze(0)

        feature_extractor = torch.nn.Sequential(*list(self.vgg.features.children()))
        feature_extractor.eval()

        input_tensor = input_tensor.to(self.device)

        # 特征提取
        with torch.no_grad():
            features = feature_extractor(input_tensor)

        # 池化并转为二维数组
        pooled = torch.nn.functional.adaptive_avg_pool2d(features, 1)
        feats = pooled.squeeze().cpu().numpy()
        feats = np.expand_dims(feats, axis=0)

        # L2归一化并构建Faiss索引
        faiss.normalize_L2(feats)
        index = faiss.IndexFlatIP(feats.shape[1])
        index.add(feats)

        return index

    def extract(self,model="vgg16",image_path=None, image=None):
        if image is not None:
            if isinstance(image, bytes):
                img = Image.open(io.BytesIO(image))
            else:
                img = image
        elif image_path is not None:
                img = Image.open(image_path)
        else:
            raise ValueError("必须提供 image_path 或 image 参数")

        if model == "resnet50":
            return self.resnet50_feature_extractor(img)
        elif model == "vit16":
            return self.vit_b_16_feature_extractor(img)
        elif model == "vgg16":
            return self.vgg16_feature_extractor(img)
        else:
            raise ValueError(f"未知模型类型: {model}")





