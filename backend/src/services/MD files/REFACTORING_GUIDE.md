"""
REFACTORING GUIDE: TextRank Enhancement with Research-Aware Biases

This document explains:
1. What was improved from the original implementation
2. How each bias component works mathematically
3. How to tune parameters for your use case
4. Comparison of old vs. new architecture
"""

# ==============================================================================
# PART 1: IMPROVEMENTS SUMMARY
# ==============================================================================

"""
KEY IMPROVEMENTS:

1. MATHEMATICAL RIGOR
   Original: Bias applied additively with arbitrary strength values
   Improved: Score = (1-β)*PageRank + β*Bias with normalized components
   Benefit: Principled weighted combination; β ∈ [0,1] controls influence

2. MODULARITY
   Original: Position bias and length bonus hardcoded; limited customization
   Improved: Enable/disable each bias component independently
   Benefit: Experiment with individual factors; revert to pure TextRank easily

3. GRAPH INTEGRITY
   Original: Unclear how biases interact with graph structure
   Improved: PageRank scores first (pure TextRank), then blend with bias
   Benefit: Preserves graph-based ranking logic; biases are priors only

4. STRUCTURAL AWARENESS
   Original: No IMRD (Introduction-Methods-Results-Discussion) support
   Improved: Keyword detection for research paper structure
   Benefit: Better captures academic paper conventions

5. HYPERPARAMETER TRANSPARENCY
   Original: Hard-coded strength values (0.2 for position, 0.05 for length)
   Improved: All parameters exposed with clear semantics
   Benefit: Easy to tune via configuration; scientific reproducibility

6. DIAGNOSTIC CAPABILITIES
   Original: No insight into how each component affects scoring
   Improved: get_bias_diagnostics() method returns component breakdown
   Benefit: Debug and understand model behavior

7. EVALUATION FRAMEWORK
   Original: No evaluation tools provided
   Improved: ROUGE metrics, comparison utilities, qualitative guide
   Benefit: Measure improvement against pure TextRank objectively


ORIGINAL ARCHITECTURE:
┌─────────────────┐
│   TF-IDF        │
│  + Similarity   │
└────────┬────────┘
         │
    ┌────▼────┐
    │ PageRank│
    └────┬────┘
         │
    ┌────▼────────────────────────┐
    │ Apply Position Bias          │
    │ Add: 0.2 * (1 - i/n)         │
    └────┬────────────────────────┘
         │
    ┌────▼────────────────────────┐
    │ Apply Length Bonus           │
    │ Add: 0.05 * (len/max_len)    │
    └────┬────────────────────────┘
         │
    ┌────▼────────────────┐
    │ Sort & Filter       │
    │ Redundancy Check    │
    └────┬────────────────┘
         │
    ┌────▼────────────────┐
    │ Output              │
    └─────────────────────┘

ISSUES:
- No principled way to combine biases
- Additive bias changes absolute PageRank values unpredictably
- Can't evaluate pure TextRank performance
- Position bias grows unboundedly

---

NEW ARCHITECTURE:
┌─────────────────┐
│   TF-IDF        │
│  + Similarity   │
└────────┬────────┘
         │
    ┌────▼────────────────────────────┐
    │ Build Graph & PageRank           │
    │ (Pure TextRank - Untouched)      │
    └────┬───────────────────────────┘
         │
    ┌────┴──────────────────────┐
    │ Compute Bias Components    │
    │                            │
    │  ├─ Position Bias          │
    │  │  exp(-decay * pos / n)   │
    │  │                          │
    │  ├─ Structural Bias         │
    │  │  keyword matching        │
    │  │                          │
    │  ├─ Keyword Bias            │
    │  │  mean TF-IDF score       │
    │  │                          │
    │  └─ Length Penalty          │
    │     Gaussian normalization  │
    │                            │
    ├─ Normalize components      │
    └────┬──────────────────────┘
         │
  ┌──────▼─────────────────────────┐
  │ Blend Scores                    │
  │ final = (1-β)*PR + β*Bias       │
  │ where β ∈ [0, 1]               │
  └──────┬──────────────────────────┘
         │
    ┌────▼─────────────────────┐
    │ Redundancy Filtering      │
    │ Greedy selection          │
    │ (with tunable threshold)  │
    └────┬────────────────────┘
         │
    ┌────▼────────────────────┐
    │ Sort by Original Order   │
    │ + Format Output          │
    └────┬────────────────────┘
         │
    ┌────▼───────────────────────────┐
    │ Return with Components          │
    │ (Optional diagnostics)          │
    └─────────────────────────────────┘

BENEFITS:
- Pure TextRank is untouched
- Biases act as a prior via β weight
- All components are controllable
- Can measure effect of each bias
"""

# ==============================================================================
# PART 2: MATHEMATICAL FORMULATION
# ==============================================================================

"""
CORE SCORING FORMULA:

    score[i] = (1 - β) × PageRank[i] + β × Bias[i]

where:
    - β ∈ [0, 1] is the overall bias weight
    - PageRank[i] is the pure TextRank score for sentence i
    - Bias[i] is the normalized combination of all bias components

BIAS VECTOR CONSTRUCTION:

    Bias[i] = (w₁ × B_pos[i] + w₂ × B_struct[i] + w₃ × B_kw[i]) / (w₁ + w₂ + w₃)
            × Penalty_length[i]

where:
    - w₁, w₂, w₃ are user-specified weights for position, structural, keyword biases
    - Each component is normalized to [0, 1] independently
    - Length penalty acts as a multiplicative gate


POSITION BIAS (B_pos):

    Motivation: Academic abstracts often place key information early and late
    
    Formula: B_pos[i] = max(
                exp(-λ × distance_from_start / n),
                exp(-λ × distance_from_end / n)
             )
             / max_value
    
    where:
        - λ = position_decay ∈ [0, 1] (controls decay rate)
        - n = total sentences
        - Function creates U-shape (higher at beginning and end)
        - Normalized to [0, 1]
    
    Parameters:
        - position_decay: Higher values (e.g., 0.5) = faster decay toward middle
                         Lower values (e.g., 0.1) = smoother bias
    
    Examples:
        abstract with 5 sentences:
        Sentence:  0     1     2     3     4
        Bias:      1.0   0.7   0.4   0.7   1.0   (with decay=0.3)
        
        Intuition: Opening sentence states objective, concluding sentence states
                   conclusion/significance → both get boosted


STRUCTURAL BIAS (B_struct):

    Motivation: Sentences with research-specific keywords carry more information
    
    Formula: B_struct[i] = min(1.0, keyword_matches[i] / (words_in_sentence[i] / 5))
             / max_value
    
    where:
        - keyword_matches counts overlaps with IMRD keywords
        - Normalized by sentence length (longer sentences get proportionally more matches)
        - Capped at 1.0 before normalization
        - Final normalization to [0, 1]
    
    Example keywords by section:
        Objective:   ['objective', 'purpose', 'aim', 'propose', 'novel']
        Method:      ['method', 'approach', 'algorithm', 'implement']
        Result:      ['result', 'finding', 'show', 'achieve', 'improvement']
        Conclusion:  ['conclusion', 'conclusion', 'significant', 'limitation']
    
    Examples:
        Sentence: "We propose a novel deep learning algorithm."
        Keywords matched: 'propose', 'novel', 'algorithm' (3 matches)
        Words: 7, Normalized: min(1.0, 3 / 1.4) = 1.0
        B_struct ≈ high
        
        Sentence: "The results are good."
        Keywords matched: 'results' (1 match, but weak)
        Words: 4, Normalized: 1 / 0.8 = capped at 1.0
        B_struct ≈ medium


KEYWORD BIAS (B_kw):

    Motivation: Domain importance = how central are the terms in the document?
    
    Formula: B_kw[i] = mean(TF-IDF[i]) / max(mean(TF-IDF[:]))
    
    where:
        - TF-IDF[i] = mean TF-IDF score across all terms in sentence i
        - Normalized to [0, 1]
    
    Intuition: High TF-IDF terms are specific to this document.
               Sentences with high-TF-IDF content are about document's main topics.
    
    Example:
        Sentence 1: "Deep learning is powerful." (generic terms) → low TF-IDF → low bias
        Sentence 2: "Transformer architecture with attention mechanism." (specific) → high TF-IDF → high bias


LENGTH PENALTY (P_length):

    Motivation: Avoid bias toward extremely short or long sentences
    
    Formula:
        P_length[i] = 0.1                          if words[i] < min_length
                    = exp(-0.1 × ((w[i]-m)/σ)²)  otherwise
    
    where:
        - min_length = minimum sentence length threshold (default: 5 words)
        - m = median sentence length
        - σ = standard deviation of sentence lengths
        - Squared values in Gaussian create symmetric penalty
    
    Examples with min_length=5:
        "Time flies." (2 words) → P_length = 0.1 (90% penalty)
        "This is a normal sentence." (5 words) → P_length ≈ 1.0 (no penalty)
        "This is a very long sentence that goes on and on..." (20+ words) → P_length ≈ mild penalty


REDUDANCY FILTERING:

    Greedy algorithm selects top-k sentences while maintaining diversity
    
    Algorithm:
        1. Sort sentences by blended score (highest first)
        2. Initialize: selected = [], selected_indices = []
        3. For each candidate in sorted order:
           a. If len(selected) >= k: STOP
           b. If candidate is first: SELECT candidate
           c. Else: For each previously selected sentence:
              - Compute cosine_similarity(TF-IDF[candidate], TF-IDF[selected])
              - If similarity >= threshold (default: 0.75): SKIP candidate (too similar)
           d. If not similar to any selected: SELECT candidate
    
    Effect: Ensures extracted sentences don't repeat the same information
"""

# ==============================================================================
# PART 3: PARAMETER TUNING
# ==============================================================================

"""
SCENARIO 1: Pure TextRank (Research Baseline)
────────────────────────────────────────────

Purpose: Validate pure algorithm performance before adding biases

Configuration:
    bias_weight = 0.0
    use_position_bias = False
    use_structural_bias = False
    use_keyword_bias = False

Code:
    service = TextRankServiceImproved(
        top_k=5,
        bias_weight=0.0,
        use_position_bias=False,
        use_structural_bias=False,
        use_keyword_bias=False
    )


SCENARIO 2: Light Bias (Conservative Enhancement)
──────────────────────────────────────────────────

Purpose: Subtle improvement while staying close to pure TextRank

Configuration:
    bias_weight = 0.1           # 10% bias, 90% PageRank
    use_position_bias = True
    use_structural_bias = False # Disabled; too aggressive
    use_keyword_bias = False
    position_decay = 0.3        # Moderate decay

Code:
    service = TextRankServiceImproved(
        bias_weight=0.1,
        use_position_bias=True,
        use_structural_bias=False,
        use_keyword_bias=False,
        position_decay=0.3
    )

Result: TextRank output slightly boosted for opening/closing sentences
Use when: You trust PageRank but want mild positional adjustment


SCENARIO 3: Moderate Bias (Balanced Approach)
──────────────────────────────────────────────

Purpose: Moderate improvement with awareness of paper structure

Configuration:
    bias_weight = 0.2           # 20% bias, 80% PageRank
    use_position_bias = True
    use_structural_bias = True
    use_keyword_bias = True
    position_weight = 0.35
    structural_weight = 0.35
    keyword_weight = 0.30
    position_decay = 0.25       # Slightly slower decay

Code:
    service = TextRankServiceImproved(
        bias_weight=0.2,
        use_position_bias=True,
        use_structural_bias=True,
        use_keyword_bias=True,
        position_weight=0.35,
        structural_weight=0.35,
        keyword_weight=0.30,
        position_decay=0.25
    )

Result: Balanced combination of all factors
Use when: You want to exploit paper structure but don't over-rely on it


SCENARIO 4: Heavy Bias (Maximum Structure Awareness)
────────────────────────────────────────────────────

Purpose: Heavily incorporate academic paper conventions

Configuration:
    bias_weight = 0.35          # 35% bias, 65% PageRank
    use_position_bias = True
    use_structural_bias = True
    use_keyword_bias = True
    position_weight = 0.3
    structural_weight = 0.5     # Highest weight to structure
    keyword_weight = 0.2
    position_decay = 0.5        # Rapid decay to center
    use_length_penalty = True

Code:
    service = TextRankServiceImproved(
        bias_weight=0.35,
        position_weight=0.3,
        structural_weight=0.5,
        keyword_weight=0.2,
        position_decay=0.5,
        use_length_penalty=True
    )

Result: Strongly favors sentences with IMRD keywords
Use when: Keywords are very indicative in your domain


TUNING STRATEGY:
───────────────

1. Start with Pure TextRank (bias_weight=0)
   - Establish baseline
   - Run evaluation to get ROUGE scores
   
2. Try Light Bias (bias_weight=0.1, position only)
   - See if position bias helps
   - Check ROUGE improvement
   
3. Add Components One at a Time
   - Test with structural_bias enabled
   - Test with keyword_bias enabled
   - Use get_bias_diagnostics() to see effect
   
4. Compare Results
   - Use TextRankComparator.compare_extractions()
   - Look for ROUGE improvement
   - Verify sentences are more meaningful (qualitative check)
   
5. Fine-tune Weights
   - Adjust position_weight, structural_weight, keyword_weight
   - Use GridSearchCV-like approach if time permits
   
6. Monitor for Over-Fitting
   - Don't increase bias_weight beyond 0.35
   - Ensure results still make sense visually
   - Check that PageRank structure is still evident (via diagnostics)
"""

# ==============================================================================
# PART 4: USAGE EXAMPLES
# ==============================================================================

"""
EXAMPLE 1: Compare Pure vs. Biased
──────────────────────────────────

from src.services.text_rank_service_improved import TextRankServiceImproved
from src.services.evaluation_framework import TextRankComparator, ROUGEEvaluator

# Create two instances
textrank_pure = TextRankServiceImproved(bias_weight=0.0)
textrank_biased = TextRankServiceImproved(bias_weight=0.2)

# Sample abstract
abstract = '''
Deep learning has revolutionized computer vision. We propose a novel attention mechanism
that improves transformer performance. Our method uses sparse attention to reduce computation.
We tested on ImageNet and CIFAR-100 datasets. Results show 5% improvement over BERT baseline.
The approach is especially effective for long sequences. In conclusion, sparse attention is
a promising direction for future work.
'''

# Extract summaries
pure_summary = textrank_pure.extract_key_sentences(abstract)
biased_summary = textrank_biased.extract_key_sentences(abstract)

print("PURE TEXTRANK:")
for item in pure_summary:
    print(f"  [{item['rank']}] {item['sentence'][:70]}... (score: {item['score']})")

print("\\nBIASED TEXTRANK:")
for item in biased_summary:
    print(f"  [{item['rank']}] {item['sentence'][:70]}... (score: {item['score']})")

# Compare
comparison = TextRankComparator.compare_extractions(abstract, textrank_pure, textrank_biased)
print(f"\\nOVERLAP: {comparison['overlap_analysis']['overlap_percentage']}%")
print(f"Score difference: Pure mean={comparison['score_statistics']['pure_mean']:.4f}, "
      f"Biased mean={comparison['score_statistics']['biased_mean']:.4f}")


EXAMPLE 2: Evaluate with ROUGE
─────────────────────────────

# Reference (gold standard) - what an expert would extract
reference = '''
Deep learning revolutionized vision and we propose a novel sparse attention mechanism
for transformers. Results show 5% improvement over BERT on ImageNet and CIFAR-100.
'''

# Get candidate summary
candidate_text = ' '.join([s['sentence'] for s in biased_summary])

# Evaluate
evaluator = ROUGEEvaluator()
rouge_scores = evaluator.evaluate_summary(reference, candidate_text)

print("ROUGE SCORES:")
print(f"  ROUGE-1 F1: {rouge_scores['rouge_1']['f1']} (word overlap)")
print(f"  ROUGE-2 F1: {rouge_scores['rouge_2']['f1']} (phrase overlap)")
print(f"  ROUGE-L F1: {rouge_scores['rouge_l']['f1']} (structure)")


EXAMPLE 3: Analyze Bias Contributions
────────────────────────────────────

service = TextRankServiceImproved(bias_weight=0.2)
diagnostics = service.get_bias_diagnostics(abstract)

print("BIAS COMPONENT VALUES:")
print("Sentence | Position Bias | Structural Bias | Keyword Bias | PageRank")
for i in range(diagnostics["num_sentences"]):
    pos = diagnostics["position_bias"]["values"][i]
    struct = diagnostics["structural_bias"]["values"][i]
    kw = diagnostics["keyword_bias"]["values"][i]
    pr = diagnostics["pagerank_scores"].get(i, 0)
    print(f"  {i:4d}   | {pos:13.4f} | {struct:15.4f} | {kw:12.4f} | {pr:8.4f}")


EXAMPLE 4: Revert to Pure TextRank
──────────────────────────────────

service = TextRankServiceImproved(bias_weight=0.25)  # Initially biased
# ...run some tests...

# If you want to revert:
service.revert_to_pure_textrank()  # Disables all biases, sets bias_weight=0

summary = service.extract_key_sentences(abstract)
# Now equivalent to pure TextRank
"""

# ==============================================================================
# PART 5: QUICK DECISION TREE
# ==============================================================================

"""
CHOOSE YOUR CONFIGURATION:

┌─ Do abstracts in your domain follow IMRD structure? ──┐
│                                                       │
├─YES─────────────────────────────────────────────────┐ ├─NO──┐
│                                                    │ │      │
│  ┌─ Critical to capture structure? ────┐         │ │      │
│  │                                      │         │ │      │
│  ├─YES➜ Use Scenario 3 or 4           │         │ │      │
│  │    bias_weight=0.2-0.35            │         │ │      │
│  │    use_structural_bias=True         │         │ │      │
│  │                                      │         │ │      │
│  └─NO ➜ Use Scenario 2               │         │ │      │
│      bias_weight=0.1                 │         │ │      │
│      position_bias only              │         │ │      │
└────────────────────────────────────┘         │ │      │
                                               │ │ └─────┼────┐
                                               │ │        │    │
                                               │ └────────┼─Use Scenario 1
                                               │         │ Pure TextRank
                                               │         │ bias_weight=0
                                               │         │
                                         ┌─────┘         │
                                         │                │
                                    ┌────▼────────────────┴────────────────┐
                                    │ RECOMMENDATION                       │
                                    │                                      │
                                    │ If unsure: Use Scenario 2            │
                                    │ (light position bias)                │
                                    │                                      │
                                    │ Always validate with:                │
                                    │ - ROUGE evaluation                   │
                                    │ - Manual review                      │
                                    │ - Comparison vs. pure TextRank       │
                                    └──────────────────────────────────────┘
"""

# ==============================================================================
# END OF GUIDE
# ==============================================================================
