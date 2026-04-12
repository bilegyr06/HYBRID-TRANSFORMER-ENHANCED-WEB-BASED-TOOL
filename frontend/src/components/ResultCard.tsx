import { useState } from 'react';
import { Copy, Check, Download } from 'lucide-react';
import type { ProcessResult } from '../types';

interface ResultCardProps {
  result: ProcessResult;
  themes?: string[];
  isLoadingThemes?: boolean;
  onCopyToClipboard?: (text: string, id: string) => void;
  copiedId?: string | null;
  onExportAsText?: (filename: string, content: string) => void;
  onCopyAllResults?: (content: string) => void;
}

export default function ResultCard({ result, themes = [], isLoadingThemes = false, onCopyToClipboard, copiedId, onExportAsText, onCopyAllResults }: ResultCardProps) {
  const [activeTab, setActiveTab] = useState<'abstract' | 'extractive'>('abstract');
  const isCopied = copiedId === result.filename;

  const handleCopy = (text: string) => {
    if (onCopyToClipboard) {
      onCopyToClipboard(text, result.filename);
    } else {
      navigator.clipboard.writeText(text);
    }
  };

  return (
    <div className="border border-gray-800 rounded-2xl bg-gray-900 overflow-hidden hover:border-teal-500 transition">
      <div className="bg-gray-950 px-4 sm:px-6 md:px-8 py-4 sm:py-5 border-b border-gray-800">
        <h3 className="text-[0.95em] sm:text-[1.05em] font-semibold text-white truncate">📄 {result.filename}</h3>
        <p className="text-[0.75em] text-gray-500 mt-1">{result.extractive?.total_extracted || 0} key sentences</p>
      </div>

      <div className="flex border-b border-gray-800">
        <button onClick={() => setActiveTab('abstract')} className={`flex-1 py-3 px-4 text-[0.85em] sm:text-[0.95em] font-medium transition ${activeTab === 'abstract' ? 'text-teal-400 border-b-2 border-teal-400' : 'text-gray-400 hover:text-white'}`}>
          Summary (BART)
        </button>
        <button onClick={() => setActiveTab('extractive')} className={`flex-1 py-3 px-4 text-[0.85em] sm:text-[0.95em] font-medium transition ${activeTab === 'extractive' ? 'text-teal-400 border-b-2 border-teal-400' : 'text-gray-400 hover:text-white'}`}>
          Key Sentences (TextRank)
        </button>
      </div>

      <div className="p-4 sm:p-6 md:p-8">
        {activeTab === 'abstract' ? (
          <div className="space-y-4">
            <div className="bg-gray-800 rounded p-4 text-gray-100 text-[0.9em] leading-relaxed">{result.abstractive_summary}</div>
            <div className="flex gap-2 flex-wrap">
              <button onClick={() => handleCopy(result.abstractive_summary)} className="flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 rounded text-[0.85em] text-white transition">
                {isCopied ? <Check size={16} className="text-green-400" /> : <Copy size={16} />}
                {isCopied ? 'Copied!' : 'Copy'}
              </button>
              {onExportAsText && (
                <button onClick={() => onExportAsText(result.filename, result.abstractive_summary)} className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded text-[0.85em] text-gray-300 transition">
                  <Download size={16} />
                  Export
                </button>
              )}
            </div>
            {themes.length > 0 && (
              <div className="pt-4 border-t border-gray-800">
                <p className="text-[0.85em] text-gray-400 mb-2">Key Themes:</p>
                <div className="flex flex-wrap gap-2">
                  {isLoadingThemes ? Array(3).fill(0).map((_, i) => <div key={i} className="h-6 w-20 bg-gray-800 rounded-full animate-pulse" />) : themes.map((t, i) => <span key={i} className="px-3 py-1 text-[0.8em] bg-teal-900 text-teal-300 rounded-full border border-teal-700">{t}</span>)}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {result.extractive?.key_sentences?.map((s, i) => (
              <div key={i} className="border border-gray-800 rounded p-4 bg-gray-950 hover:border-teal-500 transition group">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-[0.75em] font-bold px-2 py-1 bg-teal-900 text-teal-300 rounded">#{s.rank}</span>
                      <span className="text-[0.75em] text-gray-500">Score: {s.score.toFixed(3)}</span>
                    </div>
                    <p className="text-[0.9em] text-gray-100 leading-relaxed">{s.sentence}</p>
                  </div>
                  <button onClick={() => handleCopy(s.sentence)} className="flex-shrink-0 p-2 text-gray-500 hover:text-teal-400 opacity-0 group-hover:opacity-100 transition">
                    {isCopied ? <Check size={16} className="text-green-400" /> : <Copy size={16} />}
                  </button>
                </div>
              </div>
            ))}
            {onCopyAllResults && (
              <button onClick={() => onCopyAllResults(result.extractive?.key_sentences?.map((s: any) => s.sentence).join('\n') || '')} className="w-full mt-4 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded text-[0.85em] text-gray-300 transition">
                Copy All Sentences
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
