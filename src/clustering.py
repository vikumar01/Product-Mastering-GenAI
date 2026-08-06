import pandas as pd

class UnionFind:
    def __init__(self, values): self.parent = {v: v for v in values}
    def find(self, v):
        if self.parent[v] != v: self.parent[v] = self.find(self.parent[v])
        return self.parent[v]
    def join(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b: self.parent[b] = a

def clusters(products: pd.DataFrame, pairs: pd.DataFrame) -> pd.DataFrame:
    uf = UnionFind(products.row_id)
    for pair in pairs[pairs.decision == "auto_merge"].itertuples(): uf.join(pair.left_row_id, pair.right_row_id)
    result = products.copy()
    result["cluster_key"] = result.row_id.map(uf.find)
    ordered = {key: f"P{n:05d}" for n, key in enumerate(sorted(result.cluster_key.unique()), 1)}
    result["canonical_id"] = result.cluster_key.map(ordered)
    return result.drop(columns="cluster_key")
