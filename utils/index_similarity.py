import faiss
# 计算两个特征数组的相似度
def compute_index_similarity(index1: faiss.IndexFlatIP, index2: faiss.IndexFlatIP) -> float:
    """
    计算两个 Faiss 索引的相似度（双向平均 Top-1 内积）。
    参数：
        index1, index2: faiss.IndexFlatIP，已添加需比较的特征
    返回：
        float 类型相似度，范围 [-1, 1]
    """
    # 检查索引维度和数量
    nt1, d1 = index1.ntotal, index1.d
    nt2, d2 = index2.ntotal, index2.d
    if d1 != d2:
        raise ValueError("两个索引的特征维度不一致")
    if nt1 == 0 or nt2 == 0:
        return 0.0
    # 从索引中重构所有向量
    xb1 = index1.reconstruct_n(0, nt1)
    xb2 = index2.reconstruct_n(0, nt2)
    # L2 归一化
    faiss.normalize_L2(xb1)
    faiss.normalize_L2(xb2)
    # 构建临时内积索引
    idx1 = faiss.IndexFlatIP(d1)
    idx2 = faiss.IndexFlatIP(d1)
    idx1.add(xb1)
    idx2.add(xb2)
    # 双向 Top-1 搜索并平均
    D12, _ = idx2.search(xb1, 1)
    D21, _ = idx1.search(xb2, 1)
    return float((D12.mean() + D21.mean()) / 2)

if __name__ == "__main__":
    import portrait_extraction

    index_1 = faiss.IndexFlatIP(2048)
    index_2 = faiss.IndexFlatIP(2048)
    index_3 = faiss.IndexFlatIP(2048)

    index_1.add(portrait_extraction.resnet50_feature_extractor("../data/search/002_anchor_image_0001.jpg"))
    index_2.add(portrait_extraction.resnet50_feature_extractor("../data/base/002_anchor_image_0002.jpg"))
    index_3.add(portrait_extraction.resnet50_feature_extractor("../data/base/2012_000166.jpg"))

    print(compute_index_similarity(index_1, index_2))
    print(compute_index_similarity(index_1, index_3))
