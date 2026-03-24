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
    <div className="space-y-6">
      <Card 
        className={`border-2 border-dashed p-12 text-center transition-colors ${isDragging ? 'border-teal-500 bg-teal-50 dark:bg-teal-950' : 'border-gray-300 dark:border-gray-700'}`}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        <Upload className="mx-auto h-16 w-16 text-teal-500 mb-4" />
        <h3 className="text-2xl font-semibold mb-2">Drop PDFs or TXT files here</h3>
        <p className="text-gray-500 dark:text-gray-400 mb-6">or</p>
        
        <label className="cursor-pointer">
          <Button asChild>
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
        <div className="space-y-3">
          <h4 className="font-medium">Uploaded Files ({uploadedFiles.length})</h4>
          {uploadedFiles.map((file, idx) => (
            <Card key={idx} className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-teal-500" />
                <div>
                  <p className="font-medium">{file.name}</p>
                  <p className="text-sm text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => onRemove(idx)}>
                <X className="h-4 w-4" />
              </Button>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}