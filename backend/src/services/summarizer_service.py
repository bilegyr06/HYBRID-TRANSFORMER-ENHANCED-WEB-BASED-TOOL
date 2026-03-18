from transformers import pipeline
from typing import List, Dict
import torch

class SummarizerService:
    """Abstractive summarization using BART (zero-shot first, LoRA later)."""
    
    def __init__(self, model_name: str = "sshleifer/distilbart-cnn-12-6"):
        # Use distilbart for speed + lower VRAM
        device = 0 if torch.cuda.is_available() else -1  # 0 = GPU, -1 = CPU
        self.summarizer = pipeline(
            "summarization",
            model=model_name,
            device=device,
            dtype=torch.float16 if device == 0 else None
        )
    
    def generate_summary(self, key_sentences: List[Dict], max_length: int = 200) -> str:
        """Generate abstractive summary from ranked sentences."""
        if not key_sentences:
            return "No key content available for summarization."
        
        # Combine top sentences with a guiding prompt
        combined_text = " ".join([s["sentence"] for s in key_sentences])
        prompt = (
            "Summarize the following key insights from multiple academic papers "
            "in a coherent, concise paragraph focusing on main themes and findings:\n\n"
            + combined_text
        )
        
        # Truncate if too long (BART max ~1024 tokens)
        if len(prompt) > 3000:
            prompt = prompt[:3000] + "..."
        
        try:
            summary = self.summarizer(
                prompt,
                max_length=max_length,
                min_length=50,
                do_sample=False,          # deterministic for defence consistency
                num_beams=4,
                early_stopping=True
            )[0]['summary_text']
            return summary.strip()
        except Exception as e:
            return f"Summarization failed: {str(e)}"