import { Check, Clipboard, Copy } from 'lucide-react';
import type { SynthesisResult } from '../../types';

interface SynthesisSummaryCardProps {
  synthesis: SynthesisResult | null;
  summary: string;
  documentCount: number;
  copied: boolean;
  onCopy: () => void;
}

export default function SynthesisSummaryCard({
  synthesis,
  summary,
  documentCount,
  copied,
  onCopy,
}: SynthesisSummaryCardProps) {
  return (
    <div className="bg-gray-900/80 border border-gray-800/90 rounded-2xl overflow-hidden shadow-sm">
      <div className="bg-gray-950/70 px-4 sm:px-6 md:px-8 py-4 sm:py-5 border-b border-gray-800/90 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Clipboard className="w-6 h-6 text-teal-400 flex-shrink-0" />
          <div>
            <h2 className="font-semibold text-lg sm:text-xl text-white">
              {synthesis?.synthesis_degraded ? 'Generated Summary (Quality Check)' : 'Cohesive Abstractive Summary'}
            </h2>
            <p className="text-xs sm:text-sm text-gray-500 mt-1">
              {synthesis?.synthesis_degraded
                ? 'Extracted from key sentences due to quality constraints'
                : `Synthesized from ${synthesis?.metadata?.num_documents || documentCount} papers`}
            </p>
          </div>
        </div>
        {synthesis?.synthesis_degraded && (
          <div
            className="px-3 py-1 rounded-full bg-orange-500/15 border border-orange-500/40 flex items-center gap-2 text-xs text-orange-300 flex-shrink-0"
            title="Synthesis quality was below expected threshold, showing extracted key sentences instead"
          >
            <span>!</span>
            <span>Degraded</span>
          </div>
        )}
      </div>

      <div className="p-4 sm:p-6 md:p-8">
        <div className="relative">
          <button
            onClick={onCopy}
            className="absolute top-0 right-0 text-teal-300 hover:text-teal-200 flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-800 transition-all text-sm"
            title={copied ? 'Copied!' : 'Copy synthesis'}
          >
            {copied ? <Check size={16} className="text-green-400" /> : <Copy size={16} />}
            <span className="hidden sm:inline">Copy</span>
          </button>
          <p className="text-base sm:text-lg text-gray-200 leading-8 pr-20 whitespace-pre-wrap">
            {summary || 'No synthesis available.'}
          </p>
        </div>
      </div>
    </div>
  );
}
