interface ReviewCardProps {
  review: { id: string; title: string; date: string; processed_files?: number };
  onView: (id: string) => void;
}

export default function ReviewCard({ review, onView }: ReviewCardProps) {
  const formatDate = (d: string) => {
    try {
      return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch {
      return d;
    }
  };

  return (
    <div className="border border-gray-800 rounded-lg p-4 sm:p-5 bg-gray-900 hover:border-teal-500 transition">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">📄</span>
            <h4 className="text-[0.95em] font-semibold text-white truncate">{review.title}</h4>
          </div>
          <p className="text-[0.8em] text-gray-500">{formatDate(review.date)}</p>
          {review.processed_files && <p className="text-[0.8em] text-gray-500">{review.processed_files} paper{review.processed_files !== 1 ? 's' : ''}</p>}
        </div>
        <button onClick={() => onView(review.id)} className="flex-shrink-0 px-4 py-2 text-[0.85em] bg-teal-600 hover:bg-teal-700 rounded text-white transition font-medium">
          View
        </button>
      </div>
    </div>
  );
}
