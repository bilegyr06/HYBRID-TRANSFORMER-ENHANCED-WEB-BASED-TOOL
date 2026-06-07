export interface UploadDetail {
  filename: string;
  original_filename?: string;
  size_kb: number;
  preview: string;
}

export interface UploadResponse {
  status: string;
  files_uploaded: number;
  details: UploadDetail[];
  message: string;
}

export interface KeySentence {
  sentence: string;
  score: number;
  rank: number;
  original_position: number;
}

export interface ExtractiveResult {
  key_sentences: KeySentence[];
  total_extracted: number;
}

export interface Metrics {
  rouge1: number;
  rouge2: number;
  rougeL: number;
}

export interface SynthesisProvenanceSentence {
  index: number;
  text: string;
  doc_id: string;
  sentence_id: number;
  score: number;
}

export interface SynthesisMetadata {
  total_input_sentences: number;
  documents_represented: string[];
  num_documents: number;
  word_count: number;
  char_count: number;
  target_length_range: string;
  avg_input_score: number;
  faithfulness_score: number;
}

export interface SynthesisThemeCluster {
  title: string;
  description: string;
  themes: string[];
}

export interface SynthesisResult {
  abstractive_summary: string;
  key_themes: string[];
  key_themes_clustered?: SynthesisThemeCluster[];
  overall_rouge_scores?: Metrics;
  provenance: SynthesisProvenanceSentence[];
  theme_support: Record<string, SynthesisProvenanceSentence[]>;
  representative_quotes: Record<string, SynthesisProvenanceSentence | null>;
  theme_support_counts: Record<string, number>;
  metadata: SynthesisMetadata;
  synthesis_degraded?: boolean;
  quality_score?: number;
  has_hallucination?: boolean;
  token_overlap?: number;
  length_ok?: boolean;
  coherence_ok?: boolean;
}

export interface SynthesisApiResponse {
  status: string;
  data: SynthesisResult;
  message?: string;
}

export interface AnalysisRequest {
  mode?: 'overall' | 'individual';
  filenames?: string[];
  documents?: Record<string, string>;
  compute_rouge?: boolean;
  top_k?: number;
  coverage_target?: number;
}

export interface AnalysisDocumentResult {
  filename: string;
  extractive: ExtractiveResult;
  abstractive_summary: string;
  key_themes: string[];
  metrics?: Metrics;
  error?: string;
}

export interface AnalysisResponse {
  status: string;
  mode: 'overall' | 'individual';
  processed_files: number;
  results: AnalysisDocumentResult[];
  overall_synthesis?: string | null;
  synthesis?: SynthesisResult | null;
  synthesis_message?: string | null;
}

export interface ProcessResult {
  filename: string;
  extractive: ExtractiveResult;
  abstractive_summary: string;
  original_text?: string;
  key_themes?: string[];
  metrics?: Metrics;
  error?: string;
}

export interface ProcessResponse {
  status: string;
  processed_files: number;
  results: ProcessResult[];
  overall_synthesis?: string | null;
  synthesis?: SynthesisResult | null;
  synthesis_message?: string | null;
}

// Add this at the end of the file
export interface ProcessRequest {
  filenames: string[];
}
