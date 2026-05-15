import { Upload } from 'lucide-react';

interface FileDropZoneProps {
  isDragging: boolean;
  onDragOver: (event: React.DragEvent<HTMLDivElement>) => void;
  onDragLeave: () => void;
  onDrop: (event: React.DragEvent<HTMLDivElement>) => void;
  onFileSelect: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

export default function FileDropZone({
  isDragging,
  onDragOver,
  onDragLeave,
  onDrop,
  onFileSelect,
}: FileDropZoneProps) {
  return (
    <div
      className={`border border-dashed rounded-2xl p-6 sm:p-8 md:p-12 lg:p-14 text-center transition-all min-h-[320px] sm:min-h-[380px] md:min-h-[420px] flex flex-col items-center justify-center bg-gray-900/60 shadow-sm
        ${isDragging ? 'border-teal-400 bg-teal-950/30 ring-4 ring-teal-500/10' : 'border-gray-700 hover:border-teal-500/60 hover:bg-gray-900/80'}`}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      <div className="mb-5 inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-teal-500/10 text-teal-300">
        <Upload className="h-8 w-8" />
      </div>
      <h3 className="text-xl sm:text-2xl font-semibold mb-2 sm:mb-3">Drop PDFs or TXT files here</h3>
      <p className="text-gray-400 mb-6 sm:mb-8 text-sm sm:text-base">
        Supports multiple files - Max 50MB per file
      </p>

      <label className="cursor-pointer bg-teal-500 hover:bg-teal-400 text-gray-950 px-6 sm:px-8 py-2.5 sm:py-3.5 rounded-xl font-semibold transition text-sm sm:text-base shadow-lg shadow-teal-950/30">
        Choose Files
        <input
          type="file"
          multiple
          accept=".pdf,.txt"
          className="hidden"
          onChange={onFileSelect}
        />
      </label>
    </div>
  );
}
