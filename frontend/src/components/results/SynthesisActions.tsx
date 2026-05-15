import { Download, FileText, RotateCw } from 'lucide-react';

interface SynthesisActionsProps {
  busy: boolean;
  onRegenerate: () => void;
  onSave: () => void;
  onExport: () => void;
}

export default function SynthesisActions({
  busy,
  onRegenerate,
  onSave,
  onExport,
}: SynthesisActionsProps) {
  return (
    <div className="flex flex-wrap gap-3 justify-center">
      <button
        onClick={onRegenerate}
        disabled={busy}
        className="inline-flex items-center gap-2 px-4 sm:px-6 py-2 sm:py-3 bg-gray-900 border border-gray-700 rounded-lg hover:bg-gray-800 transition text-sm text-gray-200 disabled:opacity-50"
      >
        <RotateCw className="w-4 h-4" />
        Regenerate Summary
      </button>
      <button
        onClick={onSave}
        disabled={busy}
        className="inline-flex items-center gap-2 px-4 sm:px-6 py-2 sm:py-3 bg-teal-600 hover:bg-teal-700 rounded-lg transition text-sm font-medium text-white disabled:opacity-50"
      >
        <FileText className="w-4 h-4" />
        Save to Project Library
      </button>
      <button
        onClick={onExport}
        disabled={busy}
        className="inline-flex items-center gap-2 px-4 sm:px-6 py-2 sm:py-3 bg-gray-900 border border-gray-700 rounded-lg hover:bg-gray-800 transition text-sm text-gray-200 disabled:opacity-50"
      >
        <Download className="w-4 h-4" />
        Export Full Report
      </button>
    </div>
  );
}
