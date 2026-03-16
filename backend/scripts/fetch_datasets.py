import arxiv
import json
from pathlib import Path
from tqdm import tqdm
import time

def fetch_arxiv_abstracts(
    max_results: int = 2000,
    query: str = "AI OR NLP OR 'machine learning' OR 'computer science' OR summarization OR transformer"
) -> None:
    """Fetch STEM abstracts from arXiv and save as JSONL."""
    
    client = arxiv.Client(
        page_size=100,          # faster fetching
        delay_seconds=3,        # be nice to arXiv servers
        num_retries=3
    )
    
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
        sort_order=arxiv.SortOrder.Descending
    )
    
    data = []
    print(f"🔍 Fetching up to {max_results} abstracts...")
    
    for result in tqdm(client.results(search), total=max_results):
        data.append({
            "title": result.title,
            "abstract": result.summary,
            "doi": result.doi or "",
            "published": str(result.published.date()),
            "categories": result.categories
        })
        
        # Small safety pause every 100 papers
        if len(data) % 100 == 0:
            time.sleep(1)
    
    # Save
    output_dir = Path("backend/data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "arxiv_stem_abstracts.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    print(f"✅ Success! Saved {len(data)} abstracts to {output_path}")

if __name__ == "__main__":
    fetch_arxiv_abstracts(max_results=1500)   # start with 1500 (safe & fast)