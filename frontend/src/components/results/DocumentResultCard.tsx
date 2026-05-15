import { Check, Copy, Download, FileText } from 'lucide-react';
import { exportAsPDF, exportAsText } from '../../lib/exportResults';
import { copyableResultText, type DocumentTab, type ResultMetrics } from '../../lib/results';
import type { ProcessResult } from '../../types';

interface DocumentResultCardProps {
  result: ProcessResult;
  activeTab: DocumentTab;
  metrics: ResultMetrics;
  themes: string[];
  isLoadingThemes: boolean;
  copiedId: string | null;
  onTabChange: (filename: string, tab: DocumentTab) => void;
  onCopy: (text: string, id: string) => void;
}

export default function DocumentResultCard({
  result,
  activeTab,
  metrics,
  themes,
  isLoadingThemes,
  copiedId,
  onTabChange,
  onCopy,
}: DocumentResultCardProps) {
  const filename = result.filename;

  return (
    <div className="mb-8 sm:mb-10 bg-gray-900/80 border border-gray-800/90 rounded-2xl overflow-hidden shadow-sm">
      <div className="bg-gray-950/70 px-4 sm:px-6 md:px-8 py-4 sm:py-5 border-b border-gray-800/90 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 sm:gap-4">
        <div className="flex items-center gap-2 sm:gap-4 min-w-0">
          <FileText className="h-7 w-7 text-teal-400 flex-shrink-0" />
          <div className="min-w-0">
            <h3 className="font-semibold text-lg sm:text-xl truncate">{filename}</h3>
            {result.error && <p className="text-red-400 text-xs sm:text-sm mt-1">{result.error}</p>}
          </div>
        </div>
        <div className="text-xs sm:text-sm text-gray-400 flex-shrink-0">
          {result.extractive?.total_extracted || 0} key sentences extracted
        </div>
      </div>

      <div className="flex border-b border-gray-800/90 overflow-x-auto bg-gray-950/30">
        {[
          ['summary', 'Abstractive Summary (BART)'],
          ['extractive', 'Extractive Key Sentences (TextRank)'],
        ].map(([tab, label]) => (
          <button
            key={tab}
            onClick={() => onTabChange(filename, tab as DocumentTab)}
            className={`flex-1 py-3 sm:py-4 font-medium transition text-xs sm:text-sm md:text-base whitespace-nowrap ${
              activeTab === tab ? 'text-teal-400 border-b-2 border-teal-400' : 'text-gray-400 hover:text-white'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="bg-gray-950/60 border-b border-gray-800/90 px-4 sm:px-6 md:px-8 py-3 sm:py-4">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-3 md:gap-4">
          {[
            ['ROUGE-1', metrics.rouge1, 'text-teal-400'],
            ['ROUGE-2', metrics.rouge2, 'text-teal-400'],
            ['ROUGE-L', metrics.rougeL, 'text-teal-400'],
            ['Summary Length', `${metrics.summaryLength} words`, 'text-purple-400'],
            ['Compression', `${metrics.compressionRatio}%`, 'text-blue-400'],
          ].map(([label, value, color]) => (
            <div key={label} className="bg-gray-900/80 border border-gray-800 rounded-xl p-2.5 sm:p-3">
              <p className="text-[0.68rem] uppercase tracking-[0.1em] text-gray-500">{label}</p>
              <p className={`text-base sm:text-lg font-semibold ${color}`}>{value}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="p-4 sm:p-6 md:p-8" data-export={filename}>
        {activeTab === 'summary' ? (
          <div className="space-y-4 sm:space-y-6">
            <div className="relative">
              <button
                onClick={() => onCopy(result.abstractive_summary || '', `summary-${filename}`)}
                className="absolute top-2 right-2 text-teal-400 hover:text-teal-300 flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1 sm:py-2 rounded-lg hover:bg-gray-800 transition-all text-xs sm:text-sm"
                title={copiedId === `summary-${filename}` ? 'Copied!' : 'Copy summary'}
              >
                {copiedId === `summary-${filename}` ? <Check size={16} className="text-green-400" /> : <Copy size={16} />}
                <span className="hidden sm:inline">Copy</span>
              </button>
              <p className="text-base sm:text-lg text-gray-200 leading-relaxed pr-12 sm:pr-24">
                {result.abstractive_summary || 'No summary available.'}
              </p>
            </div>

            <KeyThemes themes={themes} isLoading={isLoadingThemes} />
          </div>
        ) : (
          <div className="space-y-3 sm:space-y-6">
            {result.extractive?.key_sentences?.map((sentence, index) => (
              <div key={`${sentence.rank}-${index}`} className="flex gap-3 sm:gap-5 bg-gray-950/70 p-3 sm:p-4 md:p-6 rounded-xl border border-gray-800/90 group">
                <div className="w-7 sm:w-8 h-7 sm:h-8 rounded-full bg-teal-900 flex-shrink-0 flex items-center justify-center font-bold text-xs sm:text-sm">
                  {index + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm sm:text-base text-gray-200 leading-relaxed">
                    {sentence.sentence}
                  </p>
                  <div className="mt-2 sm:mt-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-0">
                    <div className="flex gap-2 sm:gap-4 text-xs text-gray-500 flex-wrap">
                      <span>Score: <span className="text-teal-400">{sentence.score.toFixed(3)}</span></span>
                      <span>Rank: <span className="text-teal-400">#{sentence.rank}</span></span>
                      <span>Position: <span className="text-teal-400">{sentence.original_position}</span></span>
                    </div>
                    <button
                      onClick={() => onCopy(sentence.sentence, `sent-${filename}-${index}`)}
                      className="text-teal-400 hover:text-teal-300 inline-flex items-center gap-1 px-2 sm:px-3 py-1 sm:py-1.5 rounded-lg hover:bg-gray-800 transition-all text-xs sm:text-sm whitespace-nowrap"
                      title={copiedId === `sent-${filename}-${index}` ? 'Copied!' : 'Copy sentence'}
                    >
                      {copiedId === `sent-${filename}-${index}` ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
                      <span className="hidden sm:inline">Copy</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bg-gray-950/70 border-t border-gray-800/90 px-4 sm:px-6 md:px-8 py-3 sm:py-4 flex flex-col sm:flex-row gap-2 sm:gap-3">
        <button
          onClick={() => onCopy(copyableResultText(result), `all-${filename}`)}
          className="flex items-center justify-center sm:justify-start gap-2 px-3 sm:px-4 py-2 sm:py-2.5 bg-gray-800/80 hover:bg-gray-700 rounded-xl transition text-xs sm:text-sm font-medium text-gray-300 flex-1 sm:flex-none"
          title="Copy both summary and all key sentences"
        >
          <Copy size={16} />
          <span>Copy All</span>
        </button>
        <button
          onClick={() => exportAsText(filename, result.abstractive_summary || '', result.extractive?.key_sentences || [])}
          className="flex items-center justify-center sm:justify-start gap-2 px-3 sm:px-4 py-2 sm:py-2.5 bg-gray-800/80 hover:bg-gray-700 rounded-xl transition text-xs sm:text-sm font-medium text-gray-300 flex-1 sm:flex-none"
          title="Export as text file"
        >
          <FileText size={16} />
          <span>Export TXT</span>
        </button>
        <button
          onClick={() => exportAsPDF(filename)}
          className="flex items-center justify-center sm:justify-start gap-2 px-3 sm:px-4 py-2 sm:py-2.5 bg-teal-500 hover:bg-teal-400 rounded-xl transition text-xs sm:text-sm font-semibold text-gray-950 flex-1 sm:flex-none"
          title="Export as PDF"
        >
          <Download size={16} />
          <span>Export PDF</span>
        </button>
      </div>
    </div>
  );
}

function KeyThemes({ themes, isLoading }: { themes: string[]; isLoading: boolean }) {
  if (isLoading) {
    return (
      <div>
        <h4 className="text-xs sm:text-sm font-semibold text-gray-400 mb-2 sm:mb-3">Key Themes</h4>
        <div className="flex gap-2">
          {[1, 2, 3].map((index) => (
            <div key={index} className="h-6 sm:h-7 w-16 sm:w-20 bg-gray-800 rounded-full animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (themes.length === 0) return null;

  return (
    <div>
      <h4 className="text-xs sm:text-sm font-semibold text-gray-400 mb-2 sm:mb-3">Key Themes</h4>
      <div className="flex flex-wrap gap-2">
        {themes.map((theme) => (
          <span
            key={theme}
            className="px-2.5 sm:px-3 py-1 sm:py-1.5 bg-teal-900/40 text-teal-300 text-xs sm:text-sm rounded-full border border-teal-700/50 hover:bg-teal-900/60 transition"
          >
            #{theme}
          </span>
        ))}
      </div>
    </div>
  );
}
