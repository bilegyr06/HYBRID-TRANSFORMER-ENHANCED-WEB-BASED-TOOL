// src/pages/UploadPage.tsx
import { useState } from 'react';

interface UploadPageProps {
  onProcessComplete: (data: any) => void;   // We'll improve the type later
}

export default function UploadPage({ onProcessComplete }: UploadPageProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      file => file.type === 'application/pdf' || file.name.endsWith('.txt')
    );
    setFiles(prev => [...prev, ...droppedFiles]);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files).filter(
        file => file.type === 'application/pdf' || file.name.endsWith('.txt')
      );
      setFiles(prev => [...prev, ...selectedFiles]);
    }
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleProcess = async () => {
    if (files.length === 0) return;

    setIsProcessing(true);

    // TODO: Connect to FastAPI backend here later
    // For now, we'll simulate a response so the ResultsPage can show
    setTimeout(() => {
      const mockData = {
        status: "success",
        processed_files: files.length,
        results: files.map((file) => ({
          filename: file.name,
          extractive: {
            key_sentences: [
              {
                rank: 1,
                sentence: "This research provides a comprehensive overview of transformer-based architectures in natural language processing.",
                score: 0.95,
                original_position: 0
              },
              {
                rank: 2,
                sentence: "The hybrid approach combining TextRank and BART offers significant improvements in summary quality.",
                score: 0.87,
                original_position: 5
              },
              {
                rank: 3,
                sentence: "Key findings indicate that attention mechanisms are crucial for understanding complex research papers.",
                score: 0.82,
                original_position: 12
              }
            ],
            total_extracted: 3
          },
          abstractive_summary: "This paper discusses the application of transformer-based models in automated literature review systems. The study highlights how combining extractive methods (TextRank) with abstractive summarization (BART) creates a robust hybrid system for processing academic papers. The research demonstrates that attention mechanisms and pre-trained language models significantly improve both the accuracy and coherence of generated summaries, making them suitable for large-scale systematic reviews."
        }))
      };

      onProcessComplete(mockData);
      setIsProcessing(false);
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-900">
        <div className="max-w-6xl mx-auto px-8 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Automated Literature Review Assistant</h1>
            <p className="text-gray-400 mt-1">Hybrid TextRank + BART • Extract insights from research papers</p>
          </div>
          <button 
            onClick={() => window.location.reload()} 
            className="px-5 py-2 text-sm border border-gray-700 rounded-lg hover:bg-gray-800 transition"
          >
            My Reviews
          </button>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-8 py-12 grid grid-cols-12 gap-10">
        {/* Upload Section */}
        <div className="col-span-7">
          <div
            className={`border-2 border-dashed rounded-3xl p-16 text-center transition-all min-h-[420px] flex flex-col items-center justify-center
              ${isDragging ? 'border-teal-500 bg-teal-950/30' : 'border-gray-700 hover:border-gray-600'}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="text-teal-500 text-6xl mb-6">↑</div>
            <h3 className="text-2xl font-semibold mb-3">Drop PDFs or TXT files here</h3>
            <p className="text-gray-400 mb-8">Supports multiple files • Max 50MB per file</p>

            <label className="cursor-pointer bg-white hover:bg-gray-100 text-black px-8 py-3.5 rounded-xl font-medium transition">
              Choose Files
              <input
                type="file"
                multiple
                accept=".pdf,.txt"
                className="hidden"
                onChange={handleFileSelect}
              />
            </label>
          </div>

          {/* Selected Files List */}
          {files.length > 0 && (
            <div className="mt-8">
              <div className="flex justify-between items-center mb-4">
                <h4 className="font-medium">Selected Files ({files.length})</h4>
                <button
                  onClick={() => setFiles([])}
                  className="text-sm text-red-400 hover:text-red-500"
                >
                  Clear all
                </button>
              </div>

              <div className="space-y-3 max-h-80 overflow-y-auto pr-2">
                {files.map((file, index) => (
                  <div key={index} className="flex items-center justify-between bg-gray-900 p-4 rounded-2xl group">
                    <div className="flex items-center gap-4">
                      <div className="text-2xl">📄</div>
                      <div className="min-w-0">
                        <p className="font-medium truncate">{file.name}</p>
                        <p className="text-xs text-gray-500">
                          {(file.size / (1024 * 1024)).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="opacity-60 hover:opacity-100 text-red-400"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <button
            onClick={handleProcess}
            disabled={files.length === 0 || isProcessing}
            className={`mt-10 w-full py-4 text-lg font-semibold rounded-2xl transition-all ${
              files.length > 0 && !isProcessing
                ? 'bg-teal-600 hover:bg-teal-500 active:bg-teal-700'
                : 'bg-gray-700 cursor-not-allowed'
            }`}
          >
            {isProcessing ? 'Processing with Hybrid AI...' : 'Process with Hybrid AI'}
          </button>
        </div>

        {/* Right Sidebar - Info */}
        <div className="col-span-5">
          <div className="sticky top-8 bg-gray-900 border border-gray-800 rounded-3xl p-8">
            <h3 className="text-xl font-semibold mb-6">How the Hybrid System Works</h3>
            
            <div className="space-y-8">
              <div className="flex gap-5">
                <div className="w-9 h-9 rounded-2xl bg-teal-900 flex items-center justify-center flex-shrink-0 font-bold">1</div>
                <div className="text-gray-300">TextRank extracts the most important sentences from each paper</div>
              </div>
              <div className="flex gap-5">
                <div className="w-9 h-9 rounded-2xl bg-teal-900 flex items-center justify-center flex-shrink-0 font-bold">2</div>
                <div className="text-gray-300">BART generates coherent, human-like abstractive summaries</div>
              </div>
              <div className="flex gap-5">
                <div className="w-9 h-9 rounded-2xl bg-teal-900 flex items-center justify-center flex-shrink-0 font-bold">3</div>
                <div className="text-gray-300">Key themes and insights are automatically clustered</div>
              </div>
            </div>

            <div className="mt-12 text-xs text-gray-500 border-t border-gray-800 pt-6">
              Deji Ayodeji • Covenant University FYP 2025/2026
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}