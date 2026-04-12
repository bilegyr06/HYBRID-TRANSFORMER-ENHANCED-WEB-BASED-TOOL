interface SaveReviewSectionProps {
  title: string;
  onTitleChange: (title: string) => void;
  onSave: () => void;
  onViewReviews: () => void;
  isSaveDisabled?: boolean;
}

export default function SaveReviewSection({ title, onTitleChange, onSave, onViewReviews, isSaveDisabled = false }: SaveReviewSectionProps) {
  return (
    <div className="border border-gray-800 rounded-lg p-4 sm:p-6 bg-gray-900">
      <h3 className="text-[0.95em] sm:text-[1.05em] font-semibold text-white mb-4">Save This Review</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-end">
        <div>
          <label className="block text-[0.85em] text-gray-400 mb-2">Review Title (optional)</label>
          <input
            type="text"
            value={title}
            onChange={(e) => onTitleChange(e.target.value)}
            placeholder="e.g., Transformer Models Review"
            className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded text-[0.9em] text-white placeholder-gray-600 focus:border-teal-500 focus:outline-none transition"
          />
        </div>

        <div className="flex gap-2">
          <button
            onClick={onSave}
            disabled={isSaveDisabled}
            className="flex-1 px-4 py-2.5 text-[0.9em] bg-teal-600 hover:bg-teal-700 disabled:opacity-50 rounded text-white font-medium transition"
          >
            Save
          </button>
          <button
            onClick={onViewReviews}
            className="flex-1 px-4 py-2.5 text-[0.9em] bg-gray-800 hover:bg-gray-700 rounded text-gray-200 font-medium transition border border-gray-700"
          >
            Reviews
          </button>
        </div>
      </div>
    </div>
  );
}
