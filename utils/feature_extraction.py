import io
import faiss
import numpy as np
import torch
import torchvision.transforms as transforms
from PIL import Image
from torchvision.models import resnet50, vit_b_16, vgg16

class feature_extractor:
    """
    一个高效的特征提取器，采用懒加载策略来管理GPU显存。
    """
    def __init__(self):
        self.max_dim = 1024
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"特征提取器正在使用设备: {self.device}")

        # <<< 核心修改: 不在初始化时加载模型 >>>
        # 只存储模型配置，实现懒加载
        self.models = {
            "resnet50": None,
            "vgg16": None,
            "vit16": None,
        }
        self.model_configs = {
            "resnet50": {'path': '../pretrained/resnet50-0676ba61.pth', 'loader': resnet50},
            "vgg16": {'path': '../pretrained/vgg16-397923af.pth', 'loader': vgg16},
            "vit16": {'path': '../pretrained/imagenet21k+imagenet2012_ViT-B_16-224.pth', 'loader': vit_b_16}
        }
        self.current_model_name = None

    def _load_model(self, model_name: str):
        """
        按需加载模型到GPU，并卸载其他模型以释放显存。
        """
        # 如果请求的模型已经加载，则无需任何操作
        if self.current_model_name == model_name:
            return

        # 如果有其他模型已加载，先卸载它
        if self.current_model_name is not None and self.models[self.current_model_name] is not None:
            print(f"卸载旧模型 '{self.current_model_name}' 以释放显存...")
            del self.models[self.current_model_name]
            self.models[self.current_model_name] = None
            if self.device.type == 'cuda':
                torch.cuda.empty_cache()

        # 加载新模型
        print(f"模型 '{model_name}' 未加载，现在开始加载到 {self.device}...")
        config = self.model_configs[model_name]
        model = config['loader'](weights=None)
        checkpoint = torch.load(config['path'], map_location=self.device)

        # 针对不同模型和权重文件结构进行处理
        if model_name == 'vit16':
            model_dict = model.state_dict()
            if 'state_dict' in checkpoint: checkpoint = checkpoint['state_dict']
            pretrained_dict = {k: v for k, v in checkpoint.items() if k in model_dict and not k.startswith('heads.')}
            model_dict.update(pretrained_dict)
            model.load_state_dict(model_dict, strict=False)
            model.heads = torch.nn.Identity() # 替换分类头以获取特征
        else:
            model.load_state_dict(checkpoint)

        model.to(self.device)
        model.eval()
        
        # 保存新加载的模型
        self.models[model_name] = model
        self.current_model_name = model_name
        print(f"模型 '{model_name}' 加载成功。")


    def _extract_resnet50(self, img, model):
        preprocess = transforms.Compose([
            transforms.Lambda(lambda x: x.convert('RGB')),
            transforms.Resize((224, 224), interpolation=transforms.InterpolationMode.LANCZOS),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        input_tensor = preprocess(img).unsqueeze(0).to(self.device)
        feature_extractor = torch.nn.Sequential(*list(model.children())[:-1])
        with torch.no_grad():
            features = feature_extractor(input_tensor)
        return features.view(features.size(0), -1)

    def _extract_vgg16(self, img, model):
        preprocess = transforms.Compose([
            transforms.Lambda(lambda x: x.convert('RGB')),
            transforms.Resize((224, 224), interpolation=transforms.InterpolationMode.LANCZOS),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        input_tensor = preprocess(img).unsqueeze(0).to(self.device)
        features_extractor = model.features
        with torch.no_grad():
            features = features_extractor(input_tensor)
        pooled = model.avgpool(features)
        return pooled.view(pooled.size(0), -1)

    def _extract_vit16(self, img, model):
        preprocess = transforms.Compose([
            transforms.Lambda(lambda x: x.convert('RGB')),
            transforms.Resize((224, 224), interpolation=transforms.InterpolationMode.LANCZOS),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        input_tensor = preprocess(img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            features = model(input_tensor)
        return features

    def extract(self, model="vgg16", image_path=None, image=None):
        if image is not None:
            if isinstance(image, bytes):
                img = Image.open(io.BytesIO(image))
            else:
                img = image
        elif image_path is not None:
            try:
                img = Image.open(image_path)
            except Exception as e:
                print(f"无法打开图片文件: {image_path}, 错误: {e}")
                return None
        else:
            raise ValueError("必须提供 image_path 或 image 参数")
            
        if img is None: return None

        # 1. 按需加载模型
        self._load_model(model)
        model_instance = self.models[model]

        # 2. 根据模型名称调用对应的提取器
        extractor_fn = getattr(self, f'_extract_{model.replace("16", "16")}', None) # 处理vit16的命名
        if model == "resnet50": extractor_fn = self._extract_resnet50
        elif model == "vgg16": extractor_fn = self._extract_vgg16
        elif model == "vit16": extractor_fn = self._extract_vit16
        else: raise ValueError(f"未知模型类型: {model}")

        features = extractor_fn(img, model_instance)
        
        # 3. 构建并返回Faiss索引
        feats = features.cpu().numpy().astype('float32')
        faiss.normalize_L2(feats)
        index = faiss.IndexFlatIP(feats.shape[1])
        index.add(feats)

        return index

