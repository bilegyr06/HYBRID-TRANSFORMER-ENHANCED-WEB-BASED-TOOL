import { FileText } from 'lucide-react';

interface SelectedFilesListProps {
  files: File[];
  isProcessing: boolean;
  onClear: () => void;
  onRemove: (index: number) => void;
  onProcess: () => void;
}

export default function SelectedFilesList({
  files,
  isProcessing,
  onClear,
  onRemove,
  onProcess,
}: SelectedFilesListProps) {
  if (files.length === 0) return null;

  return (
    <div className="mt-6 sm:mt-8">
      <div className="flex justify-between items-center mb-3 sm:mb-4">
        <h4 className="font-medium text-sm sm:text-base">Selected Files ({files.length})</h4>
        <button onClick={onClear} className="text-xs sm:text-sm text-red-400 hover:text-red-500">
          Clear all
        </button>
      </div>

      <div className="space-y-2 sm:space-y-3 max-h-60 sm:max-h-80 overflow-y-auto pr-2">
        {files.map((file, index) => (
          <div key={`${file.name}-${index}`} className="flex items-center justify-between bg-gray-900/80 border border-gray-800 p-3 sm:p-4 rounded-xl group">
            <div className="flex items-center gap-2 sm:gap-4 min-w-0">
              <FileText className="h-6 w-6 text-teal-400 flex-shrink-0" />
              <div className="min-w-0">
                <p className="font-medium truncate text-sm sm:text-base">{file.name}</p>
                <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
            </div>
            <button
              onClick={() => onRemove(index)}
              className="text-red-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition text-xs sm:text-sm ml-2 flex-shrink-0"
            >
              Remove
            </button>
          </div>
        ))}
      </div>

      <button
        onClick={onProcess}
        disabled={isProcessing || files.length === 0}
        className="w-full mt-6 sm:mt-8 py-3 sm:py-4 bg-teal-500 hover:bg-teal-400 disabled:bg-gray-700 text-gray-950 disabled:text-gray-400 font-semibold rounded-xl transition text-sm sm:text-base"
      >
        {isProcessing ? 'Processing...' : 'Process Documents'}
      </button>
    </div>
  );
}
