import sys,os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SearchWorker:
    """
    初始化时加载索引文件夹
    run 方法根据输入的 (image, model) 调用检索函数并返回结果
    """

    def __init__(self, index_folder: str):
        from utils.index_base import load_index_base
        self.index_base = load_index_base(index_folder)

    def run(self, image = None, image_path = None, model="vgg16"):
        from utils.index_search import search_topn
        return search_topn(
            index_base=self.index_base,
            image=image,
            image_path=image_path,
            top_n=5,
            model=model
        )

if __name__ == "__main__":
    worker = SearchWorker(index_folder="../index_base/local")
    # 测试用例
    from utils.portrait_extraction import resnet50_feature_extractor
    test_image ="../data/search/002_anchor_image_0001.jpg"
    results = worker.run(image_path=test_image, model="vgg16")
    print(results)
