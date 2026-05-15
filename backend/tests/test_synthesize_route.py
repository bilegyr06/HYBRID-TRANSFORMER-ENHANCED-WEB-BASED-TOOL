"""Focused endpoint test for POST /api/synthesize/multi-document.

Exercises:
- default synthesis
- regenerate with top-k truncation
- export to Markdown
- authenticated save to the project library database
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_current_user_optional
from src.api import routes as api_routes
from src.core.database import Base
from src.main import app
from src.models.review import SavedReview
from src.models.user import User


class FakeSummarizer:
    def __init__(self) -> None:
        self.calls: list[list[dict[str, Any]]] = []

    def synthesize_from_extractive_sentences(self, extractive_sentences, target_length=250, min_length=150, max_length=300):
        self.calls.append(list(extractive_sentences))
        return {
            "abstractive_summary": "Models agree that transformers improve cross-paper synthesis while keeping traceability.",
            "key_themes": [
                "Transformer-based summarization",
                "Cross-document traceability",
                "Computational efficiency",
                "Faithfulness and provenance",
            ],
            "provenance": [
                {
                    "index": 0,
                    "text": item.get("text") or item.get("sentence"),
                    "doc_id": item.get("doc_id"),
                    "sentence_id": item.get("sentence_id"),
                    "score": item.get("score", 0.0),
                }
                for item in extractive_sentences
            ],
            "theme_support_counts": {"Transformer-based summarization": len(extractive_sentences)},
            "representative_quotes": {
                "Transformer-based summarization": {
                    "index": 0,
                    "text": extractive_sentences[0].get("text") if extractive_sentences else "",
                    "doc_id": extractive_sentences[0].get("doc_id") if extractive_sentences else None,
                    "sentence_id": extractive_sentences[0].get("sentence_id") if extractive_sentences else None,
                    "score": extractive_sentences[0].get("score", 0.0) if extractive_sentences else 0.0,
                }
            },
            "metadata": {
                "documents_represented": sorted({item.get("doc_id") for item in extractive_sentences if item.get("doc_id")}),
                "faithfulness_score": 0.81,
                "avg_input_score": 0.77,
            },
        }


def main() -> int:
    print("=" * 80)
    print("POST /api/synthesize/multi-document endpoint test")
    print("=" * 80)

    original_summarizer = api_routes.summarizer
    original_data_dir = api_routes.settings.DATA_DIR

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        db_path = tmp_path / "test_reviews.db"
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)

        setup_db = TestingSessionLocal()
        try:
            user = User(email="tester@example.com", hashed_password="hashed", full_name="Test User")
            setup_db.add(user)
            setup_db.commit()
            setup_db.refresh(user)
        finally:
            setup_db.close()

        def override_get_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        def override_current_user(db: Any = Depends(override_get_db)):
            return db.query(User).filter(User.email == "tester@example.com").first()

        fake_summarizer = FakeSummarizer()
        api_routes.summarizer = fake_summarizer
        api_routes.settings.DATA_DIR = tmp_path / "data"
        api_routes.settings.DATA_DIR.mkdir(parents=True, exist_ok=True)

        app.dependency_overrides[api_routes.get_db] = override_get_db
        app.dependency_overrides[get_current_user_optional] = override_current_user

        client = TestClient(app)
        payload = {
            "extractive_sentences": [
                {"text": "Transformers improve summarization quality.", "doc_id": "paper_1", "sentence_id": 0, "score": 0.95},
                {"text": "Provenance helps users trace claims to sources.", "doc_id": "paper_2", "sentence_id": 1, "score": 0.91},
                {"text": "Regeneration can use a smaller subset of top-ranked sentences.", "doc_id": "paper_3", "sentence_id": 2, "score": 0.88},
            ],
            "title": "Synthesis test review",
        }

        try:
            # Default synthesis
            response = client.post("/api/synthesize/multi-document", json={**payload, "action": "synthesize"})
            assert response.status_code == 200, response.text
            body = response.json()
            assert body["status"] == "success"
            assert "abstractive_summary" in body["data"]
            assert len(fake_summarizer.calls[-1]) == 3
            print("✓ default synthesis passed")

            # Regenerate with top-k truncation
            response = client.post(
                "/api/synthesize/multi-document",
                json={**payload, "action": "regenerate", "regen_k": 2},
            )
            assert response.status_code == 200, response.text
            assert len(fake_summarizer.calls[-1]) == 2
            print("✓ regenerate truncation passed")

            # Export to Markdown
            response = client.post(
                "/api/synthesize/multi-document",
                json={**payload, "action": "export", "export_format": "md"},
            )
            assert response.status_code == 200, response.text
            export_message = response.json()["message"]
            assert "Exported to" in export_message
            exported_path = Path(export_message.split("Exported to ", 1)[1])
            assert exported_path.exists()
            assert exported_path.suffix == ".md"
            print("✓ markdown export passed")

            # Authenticated save to DB
            response = client.post(
                "/api/synthesize/multi-document",
                json={**payload, "action": "save", "title": "Saved synthesis"},
            )
            assert response.status_code == 200, response.text
            saved = response.json()["data"]["saved_review"]
            assert saved["title"] == "Saved synthesis"

            check_db = TestingSessionLocal()
            try:
                reviews = check_db.query(SavedReview).all()
            finally:
                check_db.close()

            assert len(reviews) == 1
            print("✓ authenticated save passed")

            print("\nAll endpoint checks passed.")
            return 0
        finally:
            client.close()
            app.dependency_overrides.clear()
            api_routes.summarizer = original_summarizer
            api_routes.settings.DATA_DIR = original_data_dir
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())