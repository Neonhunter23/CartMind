import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"  # 118MB, supports Spanish natively


def _product_text(row: pd.Series) -> str:
    """Concatenate product fields into a single string for embedding."""
    parts = [
        str(row.get("name", "")),
        str(row.get("category", "")),
        str(row.get("short_description", "")),
    ]
    return " ".join(p for p in parts if p and p != "nan").strip()


class SemanticIndex:
    """
    Builds a FAISS index over product embeddings for semantic similarity search.

    Usage:
        index = SemanticIndex()
        index.build(catalog_df)
        results_df = index.search("algo cómodo para ver la tele", top_k=5)
    """

    def __init__(self):
        self._model = None
        self._index = None
        self._catalog: pd.DataFrame = pd.DataFrame()

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading sentence-transformers model: %s", MODEL_NAME)
            self._model = SentenceTransformer(MODEL_NAME)
            logger.info("Model loaded")

    def build(self, catalog_df: pd.DataFrame) -> None:
        """Encode all products and build the FAISS index."""
        import faiss

        self._load_model()
        self._catalog = catalog_df.reset_index(drop=True)

        texts = [_product_text(row) for _, row in self._catalog.iterrows()]
        logger.info("Encoding %d products...", len(texts))

        embeddings = self._model.encode(
            texts,
            batch_size=64,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,   # cosine similarity via inner product
        ).astype("float32")

        dim = embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dim)  # inner product = cosine on L2-normalized vecs
        self._index.add(embeddings)
        logger.info("FAISS index built: %d vectors of dim %d", self._index.ntotal, dim)

    def search(self, query: str, top_k: int = 5, min_score: float = 0.25) -> pd.DataFrame:
        """
        Return the top_k most semantically similar products.

        min_score filters out results with low cosine similarity (0-1 scale).
        """
        if self._index is None or self._catalog.empty:
            return pd.DataFrame()

        self._load_model()

        q_vec = self._model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

        scores, indices = self._index.search(q_vec, top_k)
        scores, indices = scores[0], indices[0]

        rows = []
        for score, idx in zip(scores, indices):
            if score < min_score:
                continue
            row = self._catalog.iloc[idx].to_dict()
            row["_semantic_score"] = float(score)
            rows.append(row)

        if not rows:
            return pd.DataFrame()

        return pd.DataFrame(rows).reset_index(drop=True)

    @property
    def is_ready(self) -> bool:
        return self._index is not None and self._index.ntotal > 0
