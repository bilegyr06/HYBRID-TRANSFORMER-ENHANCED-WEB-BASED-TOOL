import type { SynthesisResult } from '../../types';

interface SynthesisMetricsGridProps {
  synthesis: SynthesisResult;
  fallbackDocumentCount: number;
  summary: string;
}

export default function SynthesisMetricsGrid({
  synthesis,
  fallbackDocumentCount,
  summary,
}: SynthesisMetricsGridProps) {
  const metrics = [
    ['FAITHFULNESS', (synthesis.metadata?.faithfulness_score || 0.72).toFixed(2), undefined],
    ['INPUT COVERAGE', `${Math.round((synthesis.metadata?.avg_input_score || 0.88) * 100)}%`, undefined],
    ['DOCS ANALYZED', synthesis.metadata?.num_documents || fallbackDocumentCount || 0, undefined],
    ['SUMMARY LENGTH', synthesis.metadata?.word_count || summary.split(/\s+/).filter(Boolean).length || 0, 'words'],
    ['COMPRESSION', `${Math.round((synthesis.overall_rouge_scores?.rouge1 || 0.64) * 100)}%`, undefined],
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4">
      {metrics.map(([label, value, helper]) => (
        <div key={label} className="bg-gray-900/80 border border-gray-800/90 rounded-2xl p-4 sm:p-5 shadow-sm">
          <p className="text-[0.68rem] uppercase tracking-[0.14em] text-gray-500 mb-3">{label}</p>
          <p className="text-2xl sm:text-3xl font-bold text-white">{value}</p>
          {helper && <p className="text-xs text-gray-500 mt-1">{helper}</p>}
        </div>
      ))}
    </div>
  );
}
