import type { ProcessResponse, ProcessResult } from '../types';

export type ViewTab = 'synthesis' | 'results';
export type DocumentTab = 'summary' | 'extractive';

export type RichExtractiveSentence = {
  text: string;
  doc_id: string;
  sentence_id: number;
  score: number;
};

export type ResultMetrics = {
  rouge1: number;
  rouge2: number;
  rougeL: number;
  summaryLength: number;
  extractedSentences: number;
  compressionRatio: string;
};

export const emptyResultMetrics: ResultMetrics = {
  rouge1: 0,
  rouge2: 0,
  rougeL: 0,
  summaryLength: 0,
  extractedSentences: 0,
  compressionRatio: '0.0',
};

export const buildExtractiveSentences = (data: ProcessResponse): RichExtractiveSentence[] =>
  data.results.flatMap((result) =>
    (result.extractive?.key_sentences || []).map((sentence) => ({
      text: sentence.sentence,
      doc_id: result.filename,
      sentence_id: sentence.rank ?? sentence.original_position,
      score: sentence.score,
    }))
  );

export const buildAnalysisDocuments = (data: ProcessResponse): Record<string, string> =>
  Object.fromEntries(
    data.results
      .map((result) => [result.filename, result.original_text || ''] as const)
      .filter(([, text]) => text.trim().length > 0)
  );

export const topKSentences = (sentences: RichExtractiveSentence[], k: number) =>
  [...sentences]
    .sort((left, right) => right.score - left.score)
    .slice(0, Math.max(2, k));

export const buildResultMetrics = (result: ProcessResult): ResultMetrics => {
  const words = (result.abstractive_summary || '').split(/\s+/).filter(Boolean).length;
  const sentences = result.extractive?.key_sentences?.length || 0;

  return {
    rouge1: result.metrics?.rouge1 || 0,
    rouge2: result.metrics?.rouge2 || 0,
    rougeL: result.metrics?.rougeL || 0,
    summaryLength: words,
    extractedSentences: sentences,
    compressionRatio: sentences > 0
      ? ((1 - words / (sentences * 25)) * 100).toFixed(1)
      : '0.0',
  };
};

export const copyableResultText = (result: ProcessResult) => `
SUMMARY:
${result.abstractive_summary}

KEY SENTENCES:
${result.extractive?.key_sentences?.map((sentence) => sentence.sentence).join('\n\n')}
`.trim();
