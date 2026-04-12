// src/pages/UploadPage.tsx
import { useState } from 'react';
import type { ProcessResponse } from '../types';

interface UploadPageProps {
  onProcessComplete: (data: ProcessResponse) => void;
  onGoToMyReviews: () => void;
}

export default function UploadPage({ onProcessComplete, onGoToMyReviews }: UploadPageProps) {
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

    try {
      const formData = new FormData();
      files.forEach((file) => {
        formData.append("files", file);
      });

      // STEP 1: Upload files
      const uploadResponse = await fetch("http://localhost:8000/api/upload", {
        method: "POST",
        body: formData,
      });

      if (!uploadResponse.ok) {
        throw new Error("Upload failed");
      }

      // STEP 2: Process the uploaded files
      const processResponse = await fetch("http://localhost:8000/api/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filenames: files.map(f => f.name)
        }),
      });

      if (!processResponse.ok) {
        throw new Error("Processing failed");
      }

      const realData: ProcessResponse = await processResponse.json();

      onProcessComplete(realData);
    } catch (error) {
      console.error("Error:", error);
      alert("Could not connect to backend. Check console for details.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-900">
        <div className="max-w-full md:max-w-6xl mx-auto px-4 sm:px-6 md:px-8 py-4 sm:py-6">
          <h1 className="text-[1em] font-bold">Upload & Process Papers</h1>
          <p className="text-gray-400 mt-1 text-[0.85em]">Hybrid TextRank + BART • Extract insights from research papers</p>
        </div>
      </div>

      <div className="max-w-full md:max-w-6xl mx-auto px-4 sm:px-6 md:px-8 py-8 sm:py-12 grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 md:gap-10">
        {/* Upload Area */}
        <div
          className={`border-2 border-dashed rounded-2xl sm:rounded-3xl p-6 sm:p-8 md:p-12 lg:p-16 text-center transition-all min-h-[320px] sm:min-h-[380px] md:min-h-[420px] flex flex-col items-center justify-center
            ${isDragging ? 'border-teal-500 bg-teal-950/30' : 'border-gray-700 hover:border-gray-600'}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
            <div className="text-teal-500 text-5xl sm:text-6xl lg:text-7xl mb-4 sm:mb-6">↑</div>
            <h3 className="text-xl sm:text-2xl font-semibold mb-2 sm:mb-3">Drop PDFs or TXT files here</h3>
            <p className="text-gray-400 mb-6 sm:mb-8 text-sm sm:text-base">Supports multiple files • Max 50MB per file</p>

            <label className="cursor-pointer bg-white hover:bg-gray-100 text-black px-6 sm:px-8 py-2.5 sm:py-3.5 rounded-xl font-medium transition text-sm sm:text-base">
              Choose Files
              <input
                type="file"
                multiple
                accept=".pdf,.txt"
                className="hidden"
                onChange={handleFileSelect}
              />
            </label>

          {/* Selected Files */}
          {files.length > 0 && (
            <div className="mt-6 sm:mt-8">
              <div className="flex justify-between items-center mb-3 sm:mb-4">
                <h4 className="font-medium text-sm sm:text-base">Selected Files ({files.length})</h4>
                <button onClick={() => setFiles([])} className="text-xs sm:text-sm text-red-400 hover:text-red-500">
                  Clear all
                </button>
              </div>

              <div className="space-y-2 sm:space-y-3 max-h-60 sm:max-h-80 overflow-y-auto pr-2">
                {files.map((file, index) => (
                  <div key={index} className="flex items-center justify-between bg-gray-900 p-3 sm:p-4 rounded-xl sm:rounded-2xl group">
                    <div className="flex items-center gap-2 sm:gap-4 min-w-0">
                      <div className="text-xl sm:text-2xl flex-shrink-0">📄</div>
                      <div className="min-w-0">
                        <p className="font-medium truncate text-sm sm:text-base">{file.name}</p>
                        <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
                      </div>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="text-red-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition text-xs sm:text-sm ml-2 flex-shrink-0"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>

              <button
                onClick={handleProcess}
                disabled={isProcessing || files.length === 0}
                className="w-full mt-6 sm:mt-8 py-3 sm:py-4 bg-teal-600 hover:bg-teal-500 disabled:bg-gray-700 text-white font-semibold rounded-xl sm:rounded-2xl transition text-sm sm:text-base"
              >
                {isProcessing ? 'Processing...' : 'Process Documents'}
              </button>
            </div>
          )}
        </div>

        {/* Info Panel */}
        <div className="space-y-4 sm:space-y-6">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl sm:rounded-3xl p-4 sm:p-6 md:p-8">
            <h3 className="text-lg sm:text-xl font-semibold mb-3 sm:mb-4">How it works</h3>
            <ol className="space-y-3 sm:space-y-4 text-xs sm:text-sm text-gray-300">
              <li className="flex gap-2 sm:gap-3">
                <span className="font-bold text-teal-400 flex-shrink-0">1</span>
                <span>Upload PDF or TXT documents about your research topic</span>
              </li>
              <li className="flex gap-2 sm:gap-3">
                <span className="font-bold text-teal-400 flex-shrink-0">2</span>
                <span>Our AI extracts key sentences using TextRank algorithm</span>
              </li>
              <li className="flex gap-2 sm:gap-3">
                <span className="font-bold text-teal-400 flex-shrink-0">3</span>
                <span>BART model generates abstractive summaries</span>
              </li>
              <li className="flex gap-2 sm:gap-3">
                <span className="font-bold text-teal-400 flex-shrink-0">4</span>
                <span>Save your review with a custom title for future reference</span>
              </li>
            </ol>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-2xl sm:rounded-3xl p-4 sm:p-6 md:p-8">
            <h3 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-3">Supported Formats</h3>
            <div className="space-y-2 text-xs sm:text-sm text-gray-400">
              <p>PDF (.pdf)</p>
              <p>Plain Text (.txt)</p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="text-center text-gray-500 text-sm mt-16 pb-8">
        Hybrid TextRank + BART Pipeline • Deji Ayodeji • Covenant University FYP 2025/2026
      </div>
    </div>
  );
}