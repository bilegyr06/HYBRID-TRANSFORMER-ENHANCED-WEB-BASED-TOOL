import { ArrowLeft } from 'lucide-react';

interface ResultsHeaderProps {
  processedFiles: number;
  onBack: () => void;
}

export default function ResultsHeader({ processedFiles, onBack }: ResultsHeaderProps) {
  return (
    <header className="border-b border-gray-800/80 bg-gray-900/70 backdrop-blur">
      <div className="max-w-full md:max-w-6xl mx-auto px-4 sm:px-6 md:px-8 py-4 sm:py-5">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-4">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold">Analysis Results</h1>
            <p className="mt-1 text-xs text-gray-500">Review generated summaries, evidence, and document-level metrics.</p>
          </div>
          <div className="flex items-center gap-3 sm:justify-end">
            <p className="rounded-full border border-teal-500/20 bg-teal-500/10 px-3 py-1 text-teal-300 text-[0.75em] font-medium sm:text-right">
              {processedFiles} document{processedFiles !== 1 ? 's' : ''} analyzed
            </p>
            <button
              onClick={onBack}
              className="inline-flex items-center gap-2 rounded-xl border border-gray-700/80 px-3 py-2 text-[0.8em] text-gray-200 transition hover:border-teal-500/50 hover:bg-gray-800"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
