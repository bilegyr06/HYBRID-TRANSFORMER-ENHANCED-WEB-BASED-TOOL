interface UploadListProps {
  files: File[];
  onRemove: (index: number | string) => void;
}

export default function UploadList({ files, onRemove }: UploadListProps) {
  if (files.length === 0) return null;

  const handleClearAll = () => {
    files.forEach((_, i) => onRemove(i));
  };

  return (
    <div className="space-y-3 sm:space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-[0.95em] sm:text-[1em] font-semibold text-white">📄 Files ({files.length})</h3>
        <button onClick={handleClearAll} className="text-[0.85em] text-red-400 hover:text-red-500">
          Clear all
        </button>
      </div>
      <div className="max-h-96 overflow-y-auto space-y-2 sm:space-y-3 pr-2">
        {files.map((file, i) => (
          <div key={i} className="flex items-center justify-between p-3 sm:p-4 bg-gray-900 border border-gray-800 rounded-lg hover:border-teal-500 transition group">
            <div className="flex items-center gap-3 min-w-0 flex-1">
              <span className="text-xl flex-shrink-0">📄</span>
              <div className="min-w-0">
                <p className="text-[0.9em] text-white truncate">{file.name}</p>
                <p className="text-[0.8em] text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
            </div>
            <button onClick={() => onRemove(i)} className="ml-2 text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition">✕</button>
          </div>
        ))}
      </div>
    </div>
  );
}
