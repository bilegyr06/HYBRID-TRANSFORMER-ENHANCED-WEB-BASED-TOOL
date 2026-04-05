// frontend/src/pages/ResultsPage.tsx
import { useState } from 'react';
import type { ProcessResponse } from '../types';

interface ResultsPageProps {
  data: ProcessResponse | null;
  onBack: () => void;
}

export default function ResultsPage({ data, onBack }: ResultsPageProps) {
  const [activeTab, setActiveTab] = useState<'summary' | 'extractive'>('summary');

  if (!data) return <div>No results available</div>;

  return (
    <div className="min-h-screen bg-gray-950 text-white pb-12">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-900">
        <div className="max-w-6xl mx-auto px-8 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Literature Review Results</h1>
            <p className="text-gray-400">
              Processed {data.processed_files} document{data.processed_files > 1 ? 's' : ''}
            </p>
          </div>
          <button
            onClick={onBack}
            className="px-6 py-3 border border-gray-700 hover:bg-gray-800 rounded-xl transition flex items-center gap-2"
          >
            ← Back to Upload
          </button>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-8 py-10">
        {data.results.map((result, index) => (
          <div key={index} className="mb-12 bg-gray-900 border border-gray-800 rounded-3xl overflow-hidden">
            {/* File Header */}
            <div className="bg-gray-950 px-8 py-5 border-b border-gray-800 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="text-3xl">📄</div>
                <div>
                  <h3 className="font-semibold text-xl">{result.filename}</h3>
                  {result.error && (
                    <p className="text-red-400 text-sm mt-1">{result.error}</p>
                  )}
                </div>
              </div>
              <div className="text-sm text-gray-400">
                {result.extractive?.total_extracted || 0} key sentences extracted
              </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-gray-800">
              <button
                onClick={() => setActiveTab('summary')}
                className={`flex-1 py-4 text-center font-medium transition ${
                  activeTab === 'summary'
                    ? 'text-teal-400 border-b-2 border-teal-400'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                Abstractive Summary (BART)
              </button>
              <button
                onClick={() => setActiveTab('extractive')}
                className={`flex-1 py-4 text-center font-medium transition ${
                  activeTab === 'extractive'
                    ? 'text-teal-400 border-b-2 border-teal-400'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                Extractive Key Sentences (TextRank)
              </button>
            </div>

            {/* Content Area */}
            <div className="p-8">
              {activeTab === 'summary' ? (
                <div>
                  <p className="text-gray-300 leading-relaxed text-[17px]">
                    {result.abstractive_summary || "No summary generated."}
                  </p>
                </div>
              ) : (
                <ol className="space-y-6 list-none">
                  {result.extractive?.key_sentences && result.extractive.key_sentences.length > 0 ? (
                    result.extractive.key_sentences.map((sentence, i) => (
                      <li key={i} className="flex gap-5 bg-gray-950 p-5 rounded-2xl border border-gray-800">
                        <div className="w-8 h-8 rounded-full bg-teal-900 flex-shrink-0 flex items-center justify-center font-bold text-sm" aria-label={`Sentence ${i + 1}`}>
                          {i + 1}
                        </div>
                        <p className="text-gray-200 leading-relaxed">
                          {sentence.sentence}
                        </p>
                      </li>
                    ))
                  ) : (
                    <p className="text-gray-400 italic">No key sentences available.</p>
                  )}
                </ol>
              )}
            </div>
          </div>
        ))}

        {/* Overall Stats */}
        <div className="bg-gray-900 border border-gray-800 rounded-3xl p-8 text-center">
          <p className="text-teal-400 text-sm font-medium tracking-widest">
            HYBRID PIPELINE COMPLETE — TEXT-RANK + BART
          </p>
          <p className="text-gray-500 mt-2">
            Automated Literature Review Assistant • Ayodeji Ajayi (Covenant University)
          </p>
        </div>
      </div>
    </div>
  );
}