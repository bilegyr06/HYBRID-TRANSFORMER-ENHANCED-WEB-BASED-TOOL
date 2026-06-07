from __future__ import annotations

import logging
import re
from typing import Dict, List

from src.core.config import settings
from src.schemas.analysis import AnalysisDocumentResult, AnalysisRequest, AnalysisResponse
from src.services.summarizer_service import SummarizerService
from src.services.text_rank_service_improved import TextRankService
from src.services.tfidf_service import get_theme_service
from src.utils.evaluation import compute_rouge_scores

logger = logging.getLogger(__name__)

_text_rank = TextRankService()
_summarizer = SummarizerService()
_theme_service = get_theme_service()


def _load_documents(request: AnalysisRequest) -> Dict[str, str]:
    if request.documents:
        return {doc_id: text for doc_id, text in request.documents.items() if text and text.strip()}

    documents: Dict[str, str] = {}
    for filename in request.filenames:
        file_path = settings.UPLOAD_DIR / filename
        if not file_path.exists() or file_path.suffix.lower() not in {".pdf", ".txt"}:
            continue

        if file_path.suffix.lower() == ".pdf":
            pdfplumber = __import__("pdfplumber")
            with pdfplumber.open(file_path) as pdf:
                documents[filename] = "\n".join(page.extract_text() or "" for page in pdf.pages)
        else:
            documents[filename] = file_path.read_text(encoding="utf-8", errors="ignore")

    return documents


def _cluster_themes_semantic(
    themes: List[str],
    extractive_sentences: List[Dict],
    max_clusters: int = 3,
) -> List[Dict]:
    """Cluster themes using semantic similarity and generate coherent cluster descriptions."""
    if not themes:
        return []
    
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        from sklearn.cluster import AgglomerativeClustering
        
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode(themes)
        
        n_clusters = min(max_clusters, len(themes))
        if n_clusters < 1:
            n_clusters = 1
        
        clusterer = AgglomerativeClustering(
            n_clusters=n_clusters,
            linkage="ward",
            metric="euclidean"
        )
        cluster_labels = clusterer.fit_predict(embeddings)
        
        clusters_dict = {}
        for idx, label in enumerate(cluster_labels):
            if label not in clusters_dict:
                clusters_dict[label] = []
            clusters_dict[label].append((idx, themes[idx]))
        
        result_clusters = []
        for cluster_id, theme_pairs in clusters_dict.items():
            theme_texts = [t for _, t in theme_pairs]
            primary_theme = theme_texts[0]
            title = primary_theme[:45] if len(primary_theme) > 45 else primary_theme
            description = " • ".join(theme_texts[:2])
            
            result_clusters.append({
                "title": title,
                "description": description,
                "themes": theme_texts,
            })
        
        return result_clusters
        
    except ImportError:
        logger.warning("sentence_transformers not available; using fallback clustering")
        return [{
            "title": themes[0][:45] if themes else "Key Themes",
            "description": " • ".join(themes[:2]) if len(themes) > 1 else themes[0],
            "themes": themes,
        }]
    except Exception as e:
        logger.error(f"Theme clustering failed: {e}")
        return [{
            "title": "Key Themes",
            "description": " • ".join(themes[:3]) if len(themes) >= 3 else " • ".join(themes),
            "themes": themes,
        }]


def _build_result(
    filename: str,
    text: str,
    top_k: int,
    compute_rouge: bool,
) -> AnalysisDocumentResult:
    key_sentences = _text_rank.extract_key_sentences(text)[:top_k]
    abstractive_summary = _summarizer.generate_summary(key_sentences)
    key_themes = _theme_service.extract_themes(abstractive_summary, num_themes=5) if abstractive_summary else []
    rouge_scores = (
        compute_rouge_scores(
            abstractive_summary,
            [sentence.get("sentence", "") for sentence in key_sentences],
            reference=text,
        )
        if compute_rouge
        else None
    )

    return AnalysisDocumentResult(
        filename=filename,
        original_text=text,
        extractive={"key_sentences": key_sentences, "total_extracted": len(key_sentences)},
        abstractive_summary=abstractive_summary,
        key_themes=key_themes,
        metrics=rouge_scores,
    )


def generate_analysis_results(request: AnalysisRequest) -> AnalysisResponse:
    documents = _load_documents(request)
    results: List[AnalysisDocumentResult] = []

    if not documents:
        return AnalysisResponse(
            status="success",
            mode=request.mode,
            processed_files=0,
            results=[],
            overall_synthesis=None,
            synthesis=None,
            synthesis_message="No valid documents found.",
        )

    if request.mode == "individual":
        for filename, text in documents.items():
            results.append(_build_result(filename, text, request.top_k, request.compute_rouge))

        return AnalysisResponse(
            status="success",
            mode=request.mode,
            processed_files=len(results),
            results=results,
        )

    # overall mode: keep per-document results for the UI, but add global synthesis
    for filename, text in documents.items():
        results.append(_build_result(filename, text, request.top_k, request.compute_rouge))

    try:
        collection_result = _text_rank.extract_key_sentences_from_collection(
            documents=documents,
            coverage_target=request.coverage_target,
        )
        extractive_sentences = collection_result.get("extractive_sentences", [])
        
        if not extractive_sentences:
            return AnalysisResponse(
                status="success",
                mode=request.mode,
                processed_files=len(results),
                results=results,
                overall_synthesis=None,
                synthesis=None,
                synthesis_message="No globally salient sentences found.",
            )
        
        synthesis_result = _summarizer.synthesize_from_extractive_sentences(extractive_sentences)
        sentence_strings = [s.get("sentence", "") if isinstance(s, dict) else s for s in extractive_sentences]
        concatenated_reference = "\n".join(documents.values())

        # Check synthesis quality and degrade to extractive if needed.
        quality_score = synthesis_result.get("quality_score", 0.8)
        has_hallucination = synthesis_result.get("has_hallucination", False)
        synthesis_degraded = bool(synthesis_result.get("synthesis_degraded", False))
        synthesis_summary = synthesis_result.get("abstractive_summary", "")
        
        # QUALITY DEGRADATION: If synthesis quality is too low or hallucination detected, fallback to extractive
        if quality_score < 0.5 or has_hallucination:
            logger.warning(
                f"Synthesis quality below threshold (score={quality_score:.2f}, hallucination={has_hallucination}). "
                f"Degrading to extractive-only summary."
            )
            # Fallback: Use concatenated extractive sentences as summary
            synthesis_summary = _summarizer._build_extractive_fallback_summary(sentence_strings[:10], max_words=220)
            synthesis_result["abstractive_summary"] = synthesis_summary
            synthesis_result["synthesis_degraded"] = True
            synthesis_degraded = True
            summary_tokens = set(re.findall(r"\w+", synthesis_summary.lower()))
            input_tokens = set(re.findall(r"\w+", " ".join(sentence_strings).lower()))
            metadata = synthesis_result.setdefault("metadata", {})
            metadata["word_count"] = len(synthesis_summary.split())
            metadata["char_count"] = len(synthesis_summary)
            metadata["faithfulness_score"] = round(
                len(summary_tokens.intersection(input_tokens)) / max(1, len(summary_tokens)),
                3,
            )

        # Recompute ROUGE against the final returned synthesis so metrics match the payload.
        overall_rouge = compute_rouge_scores(
            synthesis_summary,
            sentence_strings,
            reference=concatenated_reference,
        )
        
        # Semantic theme clustering (max 3 clusters)
        raw_themes = synthesis_result.get("key_themes", [])
        clustered_themes = _cluster_themes_semantic(raw_themes, extractive_sentences, max_clusters=3)
        
        # Enrich synthesis result
        synthesis_result["key_themes_clustered"] = clustered_themes
        synthesis_result["overall_rouge_scores"] = overall_rouge
        synthesis_result["synthesis_degraded"] = synthesis_degraded
        
        logger.info(
            f"Overall synthesis complete: {len(extractive_sentences)} extractive sentences, "
            f"{len(clustered_themes)} theme clusters, ROUGE-1={overall_rouge.get('reference_rouge1', overall_rouge.get('rouge1', 0))}, "
            f"quality_score={quality_score:.2f}, degraded={synthesis_degraded}"
        )
        
    except Exception as e:
        logger.error(f"Overall synthesis generation failed: {e}", exc_info=True)
        return AnalysisResponse(
            status="success",
            mode=request.mode,
            processed_files=len(results),
            results=results,
            overall_synthesis=None,
            synthesis=None,
            synthesis_message=f"Synthesis generation failed: {str(e)}",
        )

    return AnalysisResponse(
        status="success",
        mode=request.mode,
        processed_files=len(results),
        results=results,
        overall_synthesis=synthesis_result.get("abstractive_summary"),
        synthesis=synthesis_result,
    )
