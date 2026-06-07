// src/pages/UploadPage.tsx
import { useState } from 'react';
import FileDropZone from '../components/upload/FileDropZone';
import ProductFooter from '../components/upload/ProductFooter';
import SelectedFilesList from '../components/upload/SelectedFilesList';
import UploadHeader from '../components/upload/UploadHeader';
import UploadInfoPanel from '../components/upload/UploadInfoPanel';
import { API_BASE_URL } from '../lib/config';
import { isSupportedDocument } from '../lib/files';
import type { ProcessResponse, UploadResponse } from '../types';

interface UploadPageProps {
  onProcessComplete: (data: ProcessResponse) => void;
}

export default function UploadPage({ onProcessComplete }: UploadPageProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const addSupportedFiles = (incomingFiles: File[]) => {
    setFiles(prev => [...prev, ...incomingFiles.filter(isSupportedDocument)]);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    addSupportedFiles(Array.from(e.dataTransfer.files));
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      addSupportedFiles(Array.from(e.target.files));
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
        formData.append('files', file);
      });

      const uploadResponse = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!uploadResponse.ok) {
        throw new Error('Upload failed');
      }

      const uploadData: UploadResponse = await uploadResponse.json();
      const uploadedFilenames = uploadData.details.map((detail) => detail.filename);

      const processResponse = await fetch(`${API_BASE_URL}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filenames: uploadedFilenames,
        }),
      });

      if (!processResponse.ok) {
        throw new Error('Processing failed');
      }

      const realData: ProcessResponse = await processResponse.json();
      onProcessComplete(realData);
    } catch (error) {
      console.error('Error:', error);
      alert('Could not connect to backend. Check console for details.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <UploadHeader />

      <div className="max-w-full md:max-w-6xl mx-auto px-4 sm:px-6 md:px-8 py-8 sm:py-12 grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 md:gap-10">
        <div>
          <FileDropZone
            isDragging={isDragging}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onFileSelect={handleFileSelect}
          />
          <SelectedFilesList
            files={files}
            isProcessing={isProcessing}
            onClear={() => setFiles([])}
            onRemove={removeFile}
            onProcess={handleProcess}
          />
        </div>

        <UploadInfoPanel />
      </div>

      <ProductFooter />
    </div>
  );
}
