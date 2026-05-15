interface SaveReviewSectionProps {
  reviewTitle: string;
  setReviewTitle: (title: string) => void;
  onSaveReview: () => void;
  onGoToMyReviews: () => void;
}

export default function SaveReviewSection({
  reviewTitle,
  setReviewTitle,
  onSaveReview,
  onGoToMyReviews,
}: SaveReviewSectionProps) {
  return (
    <div className="border-t border-gray-800 bg-gray-900 mt-8 sm:mt-12">
      <div className="max-w-full md:max-w-6xl mx-auto px-4 sm:px-6 md:px-8 py-8 sm:py-10">
        <h2 className="text-[1em] font-bold mb-6 text-center">Save This Review</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-2xl mx-auto">
          <div>
            <label className="block text-[0.85em] text-gray-400 mb-3">Review Title (optional)</label>
            <input
              type="text"
              value={reviewTitle}
              onChange={(event) => setReviewTitle(event.target.value)}
              placeholder="e.g. Transformer Models in Healthcare - March 2026"
              className="w-full bg-gray-950 border border-gray-700 rounded-lg px-4 py-2 text-white text-[0.9em] focus:outline-none focus:border-teal-500 transition"
            />
            <p className="text-[0.75em] text-gray-500 mt-2">Leave blank for auto-generated title</p>
          </div>
          <div className="flex flex-col justify-end gap-3">
            <button
              onClick={onSaveReview}
              disabled={!reviewTitle.trim()}
              className="w-full px-6 py-3 bg-teal-600 hover:bg-teal-500 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg transition text-white font-medium text-[0.9em] duration-200"
            >
              Save Review
            </button>
            <button
              onClick={onGoToMyReviews}
              className="w-full px-6 py-3 bg-gray-800 hover:bg-gray-700 rounded-lg transition text-gray-200 font-medium text-[0.9em] duration-200"
            >
              View My Reviews
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
