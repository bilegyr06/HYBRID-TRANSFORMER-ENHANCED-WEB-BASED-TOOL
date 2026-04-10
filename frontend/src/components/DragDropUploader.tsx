import { useState, useCallback } from 'react';
import { Upload, X, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface Props {
  onFilesSelected: (files: File[]) => void;
  uploadedFiles: File[];
  onRemove: (index: number) => void;
}

export default function DragDropUploader({ onFilesSelected, uploadedFiles, onRemove }: Props) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files).filter(f => 
      f.type === 'application/pdf' || f.name.endsWith('.txt')
    );
    onFilesSelected(files);
  }, [onFilesSelected]);

  return (
    <div className="space-y-4 sm:space-y-6">
      <Card 
        className={`border-2 border-dashed p-6 sm:p-8 md:p-12 text-center transition-colors ${isDragging ? 'border-teal-500 bg-teal-50 dark:bg-teal-950' : 'border-gray-300 dark:border-gray-700'}`}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        <Upload className="mx-auto h-12 sm:h-14 md:h-16 w-12 sm:w-14 md:w-16 text-teal-500 mb-3 sm:mb-4" />
        <h3 className="text-lg sm:text-2xl font-semibold mb-2">Drop PDFs or TXT files here</h3>
        <p className="text-gray-500 dark:text-gray-400 mb-4 sm:mb-6 text-sm sm:text-base">or</p>
        
        <label className="cursor-pointer">
          <Button asChild className="text-xs sm:text-sm px-3 sm:px-4 py-2 sm:py-2.5">
            <span>Choose Files</span>
          </Button>
          <input
            type="file"
            multiple
            accept=".pdf,.txt"
            className="hidden"
            onChange={(e) => {
              if (e.target.files) onFilesSelected(Array.from(e.target.files));
            }}
          />
        </label>
      </Card>

      {uploadedFiles.length > 0 && (
        <div className="space-y-2 sm:space-y-3">
          <h4 className="font-medium text-sm sm:text-base">Uploaded Files ({uploadedFiles.length})</h4>
          {uploadedFiles.map((file, idx) => (
            <Card key={idx} className="flex items-center justify-between p-3 sm:p-4">
              <div className="flex items-center gap-2 sm:gap-3 min-w-0">
                <FileText className="h-4 sm:h-5 w-4 sm:w-5 text-teal-500 flex-shrink-0" />
                <div className="min-w-0">
                  <p className="font-medium text-xs sm:text-sm truncate">{file.name}</p>
                  <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => onRemove(idx)} className="flex-shrink-0">
                <X className="h-4 w-4" />
              </Button>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}