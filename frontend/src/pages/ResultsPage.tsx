// frontend/src/pages/ResultsPage.tsx
import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { toast } from 'sonner';
import type { ProcessResponse } from '../types';

interface ResultsPageProps {
  data: ProcessResponse | null;
  onBack: () => void;
  onSaveReview: () => void;
  onGoToMyReviews: () => void;
  reviewTitle: string;
  setReviewTitle: (title: string) => void;
}

export default function ResultsPage({ 
  data, 
  onBack, 
  onSaveReview,
  onGoToMyReviews,
  reviewTitle, 
  setReviewTitle 
}: ResultsPageProps) {
  
  const [activeTabs, setActiveTabs] = useState<Record<string, 'summary' | 'extractive'>>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);

  if (!data) {
    return <div className="text-center py-20 text-gray-400">No results available</div>;
  }

  const copyToClipboard = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      toast.success('Copied to clipboard!');
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      toast.error('Failed to copy to clipboard');
    }
  };

  const getActiveTab = (filename: string) => activeTabs[filename] || 'summary';

  const setActiveTab = (filename: string, tab: 'summary' | 'extractive') => {
    setActiveTabs(prev => ({ ...prev, [filename]: tab }));
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white pb-12">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-900">
        <div className="max-w-6xl mx-auto px-8 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Literature Review Results</h1>
            <p className="text-gray-400">
              Processed {data.processed_files} document{data.processed_files !== 1 ? 's' : ''}
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={onBack}
              className="px-6 py-3 border border-gray-700 hover:bg-gray-800 rounded-xl transition"
            >
              ← Back to Upload
            </button>
            <button
              onClick={onGoToMyReviews}
              className="px-6 py-3 border border-gray-700 hover:bg-gray-800 rounded-xl transition"
            >
              My Reviews
            </button>
            <button
              onClick={onSaveReview}
              disabled={!reviewTitle.trim()}
              className="px-6 py-3 bg-teal-600 hover:bg-teal-500 disabled:bg-gray-700 rounded-xl transition"
            >
              Save Review
            </button>
          </div>
        </div>
      </div>

      {/* Save Title Input */}
      <div className="max-w-6xl mx-auto px-8 py-6">
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
          <label className="block text-sm text-gray-400 mb-2">Review Title (optional)</label>
          <input
            type="text"
            value={reviewTitle}
            onChange={(e) => setReviewTitle(e.target.value)}
            placeholder="e.g. Transformer Models in Healthcare - March 2026"
            className="w-full bg-gray-950 border border-gray-700 rounded-xl px-5 py-3 text-white focus:outline-none focus:border-teal-500"
          />
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-8">
        {data.results.map((result, index) => {
          const filename = result.filename;
          const activeTab = getActiveTab(filename);

          return (
            <div key={index} className="mb-12 bg-gray-900 border border-gray-800 rounded-3xl overflow-hidden">
              {/* File Header */}
              <div className="bg-gray-950 px-8 py-5 border-b border-gray-800 flex justify-between items-center">
                <div className="flex items-center gap-4">
                  <div className="text-3xl">📄</div>
                  <div>
                    <h3 className="font-semibold text-xl">{filename}</h3>
                    {result.error && <p className="text-red-400 text-sm mt-1">{result.error}</p>}
                  </div>
                </div>
                <div className="text-sm text-gray-400">
                  {result.extractive?.total_extracted || 0} key sentences extracted
                </div>
              </div>

              {/* Tabs */}
              <div className="flex border-b border-gray-800">
                <button
                  onClick={() => setActiveTab(filename, 'summary')}
                  className={`flex-1 py-4 font-medium transition ${
                    activeTab === 'summary' ? 'text-teal-400 border-b-2 border-teal-400' : 'text-gray-400 hover:text-white'
                  }`}
                >
                  Abstractive Summary (BART)
                </button>
                <button
                  onClick={() => setActiveTab(filename, 'extractive')}
                  className={`flex-1 py-4 font-medium transition ${
                    activeTab === 'extractive' ? 'text-teal-400 border-b-2 border-teal-400' : 'text-gray-400 hover:text-white'
                  }`}
                >
                  Extractive Key Sentences (TextRank)
                </button>
              </div>

              {/* Content Area */}
              <div className="p-8">
                {activeTab === 'summary' ? (
                  <div className="relative">
                    <button
                      onClick={() => copyToClipboard(result.abstractive_summary || "", `summary-${filename}`)}
                      className="absolute top-2 right-2 text-teal-400 hover:text-teal-300 flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-800 transition-all"
                      title={copiedId === `summary-${filename}` ? "Copied!" : "Copy summary"}
                    >
                      {copiedId === `summary-${filename}` ? (
                        <Check size={18} className="text-green-400" />
                      ) : (
                        <Copy size={18} />
                      )}
                    </button>
                    <p className="text-gray-200 leading-relaxed text-[17px] pr-24">
                      {result.abstractive_summary || "No summary available."}
                    </p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {result.extractive?.key_sentences?.map((sentence, i) => (
                      <div key={i} className="flex gap-5 bg-gray-950 p-6 rounded-2xl border border-gray-800 group">
                        <div className="w-8 h-8 rounded-full bg-teal-900 flex-shrink-0 flex items-center justify-center font-bold text-sm mt-1">
                          {i + 1}
                        </div>
                        <div className="flex-1">
                          <p className="text-gray-200 leading-relaxed">
                            {sentence.sentence}
                          </p>
                          <button
                            onClick={() => copyToClipboard(sentence.sentence, `sent-${filename}-${i}`)}
                            className="mt-4 text-teal-400 hover:text-teal-300 inline-flex items-center gap-1 px-3 py-1.5 rounded-lg hover:bg-gray-800 transition-all text-sm"
                            title={copiedId === `sent-${filename}-${i}` ? "Copied!" : "Copy sentence"}
                          >
                            {copiedId === `sent-${filename}-${i}` ? (
                              <Check size={16} className="text-green-400" />
                            ) : (
                              <Copy size={16} />
                            )}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="text-center text-gray-500 text-sm mt-16">
        Hybrid TextRank + BART Pipeline • Deji Ayodeji • Covenant University FYP 2025/2026
      </div>
    </div>
  );
}