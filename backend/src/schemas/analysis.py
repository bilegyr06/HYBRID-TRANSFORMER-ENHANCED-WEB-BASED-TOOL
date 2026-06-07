"""Pydantic schemas for unified analysis results.

These schemas support an additive migration path:
- keep the existing /process endpoint intact
- expose a separate /analysis/results endpoint for richer analysis payloads
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


AnalysisMode = Literal["overall", "individual"]


class AnalysisRequest(BaseModel):
    mode: AnalysisMode = Field(
        default="overall",
        description="Analysis mode: overall uses global TextRank, individual uses per-document analysis.",
    )
    filenames: List[str] = Field(
        default_factory=list,
        description="Optional file names to analyze from the upload directory.",
    )
    documents: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional document mapping of doc_id to text.",
    )
    compute_rouge: bool = Field(
        default=True,
        description="Whether to compute self-ROUGE for the generated summaries.",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Soft cap for individual extractive sentences included in the response.",
    )
    coverage_target: float = Field(
        default=0.35,
        ge=0.1,
        le=0.9,
        description="Coverage target for global TextRank in overall mode.",
    )


class AnalysisDocumentResult(BaseModel):
    filename: str
    original_text: str = ""
    extractive: Dict[str, object]
    abstractive_summary: str
    key_themes: List[str] = Field(default_factory=list)
    metrics: Optional[Dict[str, float]] = None
    error: Optional[str] = None


class AnalysisResponse(BaseModel):
    status: str
    mode: AnalysisMode
    processed_files: int
    results: List[AnalysisDocumentResult]
    overall_synthesis: Optional[str] = None
    synthesis: Optional[Dict[str, object]] = None
    synthesis_message: Optional[str] = None
