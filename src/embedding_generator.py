import numpy as np

class Embedder:
    """Sentence embeddings with an offline-safe lexical fallback."""
    def __init__(self, model_name: str):
        self.backend = "sentence-transformers"
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
        except Exception:
            self.backend = "token-vector-fallback"
            self.model = None

    def fit_transform(self, texts):
        if self.backend == "sentence-transformers":
            return self.model.encode(list(texts), normalize_embeddings=True, show_progress_bar=False)
        # Dependency-free bag-of-tokens fallback: useful for demo execution in
        # restricted environments; install requirements for semantic embeddings.
        tokenised = [str(t).split() for t in texts]
        vocabulary = {token for text in tokenised for token in text}
        index = {token: i for i, token in enumerate(sorted(vocabulary))}
        matrix = np.zeros((len(tokenised), len(index)))
        for row, text in enumerate(tokenised):
            for token in text:
                matrix[row, index[token]] += 1
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        return matrix / np.maximum(norms, 1e-12)
