import { Copy, Check } from 'lucide-react';

interface SynthesisCardProps {
  synthesis: string;
  onCopy?: (text: string) => void;
  isCopied?: boolean;
}

export default function SynthesisCard({ synthesis, onCopy, isCopied = false }: SynthesisCardProps) {
  const handleCopy = () => {
    if (onCopy) onCopy(synthesis);
    else navigator.clipboard.writeText(synthesis);
  };

  return (
    <div className="border border-gray-800 rounded-2xl bg-gray-900 overflow-hidden hover:border-teal-500 transition mb-8">
      <div className="bg-gray-950 px-4 sm:px-6 md:px-8 py-4 sm:py-5 border-b border-gray-800">
        <h3 className="text-[1em] font-semibold text-white">Cross-Document Synthesis</h3>
        <p className="text-[0.8em] text-gray-500 mt-1">Unified insights from all papers</p>
      </div>
      <div className="p-4 sm:p-6 md:p-8 space-y-4">
        <div className="bg-gray-800 rounded p-4 text-gray-100 text-[0.9em] leading-relaxed">{synthesis}</div>
        <button onClick={handleCopy} className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-teal-600 hover:bg-teal-700 rounded text-[0.9em] text-white transition font-medium">
          {isCopied ? <Check size={16} className="text-green-400" /> : <Copy size={16} />}
          {isCopied ? 'Copied!' : 'Copy All'}
        </button>
      </div>
    </div>
  );
}
