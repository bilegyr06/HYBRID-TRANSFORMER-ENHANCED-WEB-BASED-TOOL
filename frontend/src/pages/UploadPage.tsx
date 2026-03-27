import { useState } from 'react';
import DragDropUploader from '../components/DragDropUploader';
import { Button } from '@/components/ui/button';
import { uploadFiles, processFiles } from '../lib/api';
import type { ProcessResponse } from '../types';

export default function UploadPage({ 
  onProcessComplete 
}: { 
  onProcessComplete: (data: ProcessResponse) => void 
}) {
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFilesSelected = (files: File[]) => {
    setUploadedFiles(prev => [...prev, ...files]);
    setError(null);
  };

  const handleRemoveFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleProcess = async () => {
    if (uploadedFiles.length === 0) return;

    setIsProcessing(true);
    setError(null);

    try {
      // Step 1: Upload files
      await uploadFiles(uploadedFiles);

      // Step 2: Process all uploaded files (for now we process everything)
      const filenames = uploadedFiles.map(f => f.name);
      const result = await processFiles(filenames);

      onProcessComplete(result);
    } catch (err: any) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-12 px-6">
      <div className="text-center mb-10">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-3">
          Automated Literature Review Assistant
        </h1>
        <p className="text-gray-600 dark:text-gray-400 text-lg">
          Upload research papers and get key insights using hybrid TextRank + BART
        </p>
      </div>

      <DragDropUploader 
        onFilesSelected={handleFilesSelected} 
        uploadedFiles={uploadedFiles} 
        onRemove={handleRemoveFile} 
      />

      {error && (
        <div className="mt-6 p-4 bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 rounded-lg">
          {error}
        </div>
      )}

      <div className="mt-8 flex justify-center">
        <Button 
          onClick={handleProcess}
          disabled={uploadedFiles.length === 0 || isProcessing}
          size="lg"
          className="px-10 py-6 text-lg"
        >
          {isProcessing ? "Processing with Hybrid AI..." : "Process with Hybrid AI"}
        </Button>
      </div>
    </div>
  );
}