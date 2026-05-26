# Visual Architecture & Flow Guide

## System Architecture Diagram

```
INPUT TEXT (Abstract)
    │
    ├─────────────────────────────────────────────┐
    │                                             │
    ▼                                             ▼
┌─────────────┐                        ┌──────────────────┐
│ PURE        │                        │ BIAS COMPONENTS  │
│ TEXTRANK    │                        │ (Optional)       │
│             │                        │                  │
│ 1. TF-IDF   │                        │ • Position bias  │
│ 2. Graph    │◄──────────────────────►│ • Structural     │
│ 3. PageRank │   influence via β      │ • Keyword        │
│             │                        │ • Length penalty │
└──────┬──────┘                        └──────┬───────────┘
       │                                      │
       │ PageRank[i]                         Bias[i]
       │                                      │
       └──────────────┬───────────────────────┘
                      │
                      ▼
          ┌──────────────────────────┐
          │ BLENDING FORMULA         │
          │                          │
          │ score[i] =              │
          │ (1-β)×PageRank[i] +     │
          │ β×Bias[i]               │
          │                          │
          │ β = bias_weight ∈ [0,1] │
          └────────────┬─────────────┘
                       │
                       ▼
          ┌──────────────────────────┐
          │ SORT & FILTER            │
          │                          │
          │ 1. Sort by score         │
          │ 2. Redundancy check      │
          │ 3. Force original order  │
          └────────────┬─────────────┘
                       │
                       ▼
          ┌──────────────────────────┐
          │ OUTPUT RESULTS           │
          │ • Sentence               │
          │ • Score                  │
          │ • Rank                   │
          │ • Components breakdown   │
          └──────────────────────────┘
```

---

## Parameter Control Flow

```
┌─ TextRankServiceImproved (api.routes)
│
├─ bias_weight: [0.0 to 1.0]
│  │
│  ├─ 0.0 = Pure TextRank
│  ├─ 0.15 = Light bias (default)
│  └─ 0.35 = Heavy bias
│
├─ Position Bias Configuration
│  ├─ use_position_bias: Enable/disable
│  ├─ position_weight: Relative importance
│  └─ position_decay: U-shape steepness
│
├─ Structural Bias Configuration
│  ├─ use_structural_bias: Enable/disable
│  └─ structural_weight: Relative importance
│
├─ Keyword Bias Configuration
│  ├─ use_keyword_bias: Enable/disable
│  └─ keyword_weight: Relative importance
│
└─ Length Penalty Configuration
   ├─ use_length_penalty: Enable/disable
   └─ min_sentence_length: Penalize if < threshold
```

---

## Score Blending Visualization

### Example: 3-Sentence Abstract

```
Sentence 0: "We propose a novel deep learning approach."
Sentence 1: "The method uses attention mechanisms."
Sentence 2: "Results improve baseline accuracy by 5%."

─────────────────────────────────────────────────────────

PURE TEXTRANK (PageRank scores):
     Sentence: 0    1    2
     Score:    0.30 0.20 0.35
              [════] [══] [═════]

BIAS COMPONENTS:
     Position: 1.0  0.5  0.9  (U-shaped)
              [███] [██] [███]
     Struct:   0.8  0.2  0.7  (IMRD keyword match)
              [██] [─] [██]
     Keyword:  0.6  0.3  0.8  (TF-IDF importance)
              [██] [─] [███]

COMBINED BIAS (normalized):
     Final:    0.80 0.33 0.80
              [███] [─] [███]

─────────────────────────────────────────────────────────

BLENDED SCORE with β=0.2:
     Sentence: 0    1    2
     Score:    0.36 0.21 0.40  ← Boosted opening & closing
              [════] [══] [═════]

(0.8×0.30 + 0.2×0.80 = 0.36) ✓ objective boosted
(0.8×0.20 + 0.2×0.33 = 0.21) ✓ filler unchanged
(0.8×0.35 + 0.2×0.80 = 0.40) ✓ conclusion boosted
```

---

## Bias Component Contribution Breakdown

### Position Bias (U-Shaped)

```
Decay = 0.3
n = 7 sentences

Score:  1.0┬───────────────────
         0.9├───┐           ┌───
         0.8├─┐ │         ┌─┤─┐
         0.7├─┼─┼────┬────┤─┼─┤
         0.6├─┤ │    │    │ ├─┤
         0.5├─┤ │    │    │ ├─┤
         0.4├─┤ ├────┤    │ ├─┤
         0.3├─┤ │    │    │ ├─┤
         0.2├─┤ │    │    │ ├─┤
         0.1├─┤ │    │    │ ├─┤
         0.0└─┴─┴────┴────┴─┴─┘
            0 1 2  3 4  5 6
            
↑        Opening  Middle  Closing
Boosted  sentences favor  sentences
```

### Structural Bias (Keyword Detection)

```
Sentence 1:
"We propose a novel deep learning method."
     [1]    [2]        [3]       [4]
Keywords: propose(1), novel(1), method(1) = 3/8 words
Bias = HIGH (0.85)

Sentence 3:
"The results demonstrate significant improvements."
     [1]      [2]
Keywords: results(1), demonstrate(1) = 2/7 words
Bias = MEDIUM (0.65)

Sentence 5:
"The dataset is very large."
NO academic keywords
Bias = LOW (0.15)
```

### Keyword Bias (TF-IDF Based)

```
Document topics: [deep_learning, neural_networks, attention, architecture]

Sentence: "We propose a novel deep learning architecture."
TF-IDF terms: [deep_learning(0.8), architecture(0.7), novel(0.5)]
Mean TF-IDF: 0.67 → HIGH bias

Sentence: "The paper is well written."
TF-IDF terms: [paper(0.1), written(0.05)]
Mean TF-IDF: 0.075 → LOW bias
```

---

## Evaluation Framework Flow

```
┌─────────────────────────────────────────────────────┐
│ Step 1: Prepare Reference Summaries                 │
│ (Manually extract key sentences)                   │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│ Step 2: Extract with Pure TextRank                 │
│ service_pure = TextRankServiceImproved(bias=0.0)  │
│ pure_summary = service_pure.extract_key_sentences() │
└┬─────────────────────────────────────────────────┬──┘
 │                                                 │
 │                                    ┌────────────▼──┐
 │                                    │ Step 3: Extract │
 │                                    │ with Biased     │
 │                                    │ service = ...   │
 │                                    │ (bias=0.2)      │
 │                                    └────────┬───────┘
 │                                            │
 ├──────────────────────┬─────────────────────┤
 │                      │                     │
 ▼                      ▼                     ▼
┌────────────────┐ ┌───────────────┐ ┌──────────────────┐
│ ROUGE Evaluate │ │ Analyze Bias  │ │ TextRankCompare  │
│                │ │               │ │                  │
│ pure_ROUGE_1   │ │ diagnostics = │ │ overlap =        │
│ = 0.68         │ │ get_bias_... │ │ show differences │
│                │ │               │ │ stats            │
│ biased_ROUGE_1 │ │ → Component   │ │                  │
│ = 0.72         │ │   breakdown   │ │ → Improvement %  │
│                │ │               │ │                  │
│ Improvement: 4%│ │               │ │                  │
└────────────────┘ └───────────────┘ └──────────────────┘
```

---

## Configuration Decision Tree

```
START: Choose your configuration
       │
       ├─ Do you know your domain structure? ──┐
       │                                        │
       NO                                      YES
       │                                        │
       │                                ┌──────▼─────┐
       │                                │ Is it      │
       │                                │ IMRD       │
       │                                │ structured?│
       │                                └──┬────┬───┘
       │                                  YES   NO
       │                                   │    └────┐
       │                                   │         │
       ├────────────┬──────────────────────┼─────────┘
       │            │                      │
       ▼            ▼                      ▼
    β=0.0      β=0.2              β=0.1 (light)
 Pure-only    All biases          Position only
      │            │                   │
      └────┬───────┼────────┬──────────┘
           │       │        │
           ▼       ▼        ▼
      Analyze → Tune → Evaluate
      baseline   params   (ROUGE)
           │       │        │
           └───────┴────────┘
           
          Production Deployment
```

---

## Phase-by-Phase Testing

```
PHASE 1: Baseline
────────────────
Beta = 0.0 (Pure TextRank)
└─→ Collect ROUGE scores
└─→ Establish performance baseline

PHASE 2: Light Testing  
─────────────────────
Beta = 0.1 (Position only)
└─→ Compare vs. baseline
└─→ ROUGE improvement < 3%? → Skip structural
└─→ ROUGE improvement > 3%? → Try moderate

PHASE 3: Moderate Testing
──────────────────────
Beta = 0.2 (All components balanced)
└─→ Compare vs. baseline
└─→ ROUGE improvement > 5%? → Use this
└─→ ROUGE improvement < 5%? → Try heavy

PHASE 4: Heavy Testing
──────────────────────
Beta = 0.3+ (Aggressive bias)
└─→ Compare vs. baseline
└─→ Still no improvement? → Stick with pure

PHASE 5: Production
──────────────────
Choose configuration with best ROUGE + qualitative review
└─→ Deploy
└─→ Monitor performance on new data
```

---

## File Dependency Graph

```
┌──────────────────────────────────────────┐
│ API Routes / FastAPI Integration        │
│ (Imports your choice of service)        │
└────┬─────────────────────────────────────┘
     │
     ├─────────────────┬────────────────┐
     │                 │                │
     ▼                 ▼                ▼
┌─────────────────┐ ┌──────────┐ ┌──────────────┐
│ service_pure    │ │ service_ │ │ dashboard    │
│ (β=0.0)         │ │ biased   │ │ (metrics)    │
│                 │ │ (β=0.2)  │ │              │
└────────┬────────┘ └────┬─────┘ └────┬─────────┘
         │                │            │
         │                │            ▼
         │                │      ┌──────────────────┐
         │                │      │evaluation_       │
         │                │      │framework.py      │
         │                │      │ • ROUGEEvaluator │
         │                │      │ • Comparator     │
         │                │      │ • Diagnostics    │
         │                │      └────┬─────────────┘
         │                │           │
         └────────────────┼───────────┤
                          │           │
                          ▼           │
         ┌────────────────────────────┤
         │ text_rank_service_        │
         │ improved.py               │
         │ (Main implementation)      │
         │                            │
         │ • extract_key_sentences()  │
         │ • get_bias_diagnostics()   │
         │ • revert_to_pure_textrank()│
         └────────────────────────────┘
```

---

## Score Evolution Example

```
Given: Abstract with 5 sentences
       bias_weight = 0.2

STEP 1: TF-IDF Computation
       Sentence 0: [0.2, 0.3, 0.1, ...]
       Sentence 1: [0.1, 0.2, 0.05, ...]
       ...

STEP 2: Graph Construction
       Similarity matrix 5×5
       Remove self-loops
       Apply threshold

STEP 3: PageRank Computation
       Sentence 0: 0.25
       Sentence 1: 0.15
       Sentence 2: 0.22
       Sentence 3: 0.20
       Sentence 4: 0.18

STEP 4: Compute Biases
       Position:   [1.0, 0.7, 0.3, 0.7, 1.0]
       Structural: [0.9, 0.2, 0.4, 0.8, 0.6]
       Keyword:    [0.7, 0.3, 0.5, 0.6, 0.8]
       Length:     [1.0, 1.0, 0.9, 1.0, 1.0]
       → Combined: [0.85, 0.38, 0.45, 0.73, 0.83]

STEP 5: Blend Scores
       Final = 0.8 × PageRank + 0.2 × Bias
       
       Sentence 0: 0.8×0.25 + 0.2×0.85 = 0.37 (↑ boosted)
       Sentence 1: 0.8×0.15 + 0.2×0.38 = 0.19 (↓ penalized)
       Sentence 2: 0.8×0.22 + 0.2×0.45 = 0.27 (→ stable)
       Sentence 3: 0.8×0.20 + 0.2×0.73 = 0.31 (↑ boosted)
       Sentence 4: 0.8×0.18 + 0.2×0.83 = 0.31 (↑ boosted)

STEP 6: Sort & Select Top-K
       Top 3: [0, 3, 4] (objective, result, conclusion)

STEP 7: Return in Original Order
       Output: [Sentence 0, Sentence 3, Sentence 4]
```

---

## Troubleshooting Decision Tree

```
Problem: ROUGE score didn't improve
│
├─ Is bias_weight too low (< 0.1)?
│  YES: Increase to 0.2
│  NO: Continue
│
├─ Are you using structural_bias on non-academic text?
│  YES: Disable use_structural_bias
│  NO: Continue
│
└─ Have you manually reviewed the differences?
   YES: Accept pure TextRank or try different parameters
   NO: Use TextRankComparator.compare_extractions()

Problem: Very short sentences selected
│
├─ Is use_length_penalty enabled?
│  NO: Enable it (set True)
│  YES: Continue
│
└─ Increase min_sentence_length to 7

Problem: Important structural info missing
│
├─ Is use_structural_bias enabled?
│  NO: Enable it
│  YES: Continue
│
├─ Increase structural_weight
│ └─ Also try increasing bias_weight
│
└─ Call get_bias_diagnostics() to verify keywords detected
```

---

This completes the comprehensive documentation package. All files are production-ready and fully explained!
