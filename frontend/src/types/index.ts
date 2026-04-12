export interface UploadDetail {
  filename: string;
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

export interface ProcessResult {
  filename: string;
  extractive: ExtractiveResult;
  abstractive_summary: string;
  metrics?: Metrics;
  error?: string;
}

export interface ProcessResponse {
  status: string;
  processed_files: number;
  results: ProcessResult[];
  overall_synthesis?: string | null;
}

// Add this at the end of the file
export interface ProcessRequest {
  filenames: string[];
}

export interface ExtractThemesResponse {
  status: string;
  themes: string[];
}