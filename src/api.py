import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(__file__))

from ai_engine import extract_search_intent, generate_sales_response
from logic import load_catalog, load_catalog_from_db, search_products
from recommender import build_association_rules, get_recommendations, evaluate_recommender
from semantic_search import SemanticIndex

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global state — loaded once at startup
_catalog: pd.DataFrame = pd.DataFrame()
_rules: pd.DataFrame = pd.DataFrame()
_semantic_index: SemanticIndex = SemanticIndex()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _catalog, _rules, _semantic_index

    _catalog = (
        load_catalog_from_db()
        if os.getenv("USE_DB", "false").lower() == "true"
        else load_catalog()
    )
    logger.info("Catalog loaded: %d products", len(_catalog))

    _rules = build_association_rules()
    logger.info("Rules ready: %d rules", len(_rules))

    if not _catalog.empty:
        logger.info("Building semantic index...")
        _semantic_index.build(_catalog)
        logger.info("Semantic index ready")

    yield


app = FastAPI(title="CartMind API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RecommendRequest(BaseModel):
    product_name: str
    top_n: int = 3


class SearchRequest(BaseModel):
    query: str
    client_id: Optional[str] = None
    use_semantic: bool = True   # set False to fall back to keyword-only search


class RecommendationItem(BaseModel):
    product: str
    confidence: str
    lift: float
    reason: str


class RecommendResponse(BaseModel):
    product_name: str
    recommendations: list[RecommendationItem]


class SearchResponse(BaseModel):
    intent: dict
    results: list[dict]
    ai_pitch: Optional[str]
    search_mode: str   # "semantic" | "keyword"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "catalog_size": len(_catalog),
        "rules_loaded": not _rules.empty,
        "semantic_index_ready": _semantic_index.is_ready,
    }


@app.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    if _rules.empty:
        return RecommendResponse(
            product_name=req.product_name, recommendations=[]
        )
    recs = get_recommendations(req.product_name, _rules, top_n=req.top_n)
    return RecommendResponse(product_name=req.product_name, recommendations=recs)


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    if _catalog.empty:
        raise HTTPException(status_code=503, detail="Catalog not loaded")

    # 1. Extract structured intent (category filter + price) from Gemini
    intent = extract_search_intent(req.query)

    # 2. Search — semantic first, keyword fallback
    results_df = pd.DataFrame()
    search_mode = "keyword"

    if req.use_semantic and _semantic_index.is_ready:
        results_df = _semantic_search_with_filters(req.query, intent)
        if not results_df.empty:
            search_mode = "semantic"

    if results_df.empty:
        results_df = search_products(intent, _catalog)

    if results_df.empty:
        return SearchResponse(
            intent=intent, results=[], ai_pitch=None, search_mode=search_mode
        )

    top = results_df.iloc[0]
    pitch = generate_sales_response(top, req.query)
    results = results_df.fillna("").to_dict(orient="records")

    return SearchResponse(
        intent=intent, results=results, ai_pitch=pitch, search_mode=search_mode
    )


@app.get("/evaluate")
def evaluate(k: int = 3):
    """
    Evaluate the recommender with a temporal train/test split.
    Returns Precision@K and Hit Rate@K.
    """
    return evaluate_recommender(_rules, k=k)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _semantic_search_with_filters(
    query: str, intent: dict, top_k: int = 10
) -> pd.DataFrame:
    """
    Run semantic search then apply hard filters (category, price) from Gemini intent.
    Returns top 5 after filtering.
    """
    results = _semantic_index.search(query, top_k=top_k)
    if results.empty:
        return results

    # Apply category filter if Gemini detected one
    category = intent.get("category")
    if category and category in _catalog["category"].unique():
        filtered = results[results["category"] == category]
        if not filtered.empty:
            results = filtered

    # Apply price filter
    max_price = intent.get("max_price")
    if max_price:
        try:
            price_filtered = results[results["price"] <= float(max_price)]
            if not price_filtered.empty:
                results = price_filtered
        except (ValueError, TypeError):
            pass

    return results.head(5)
