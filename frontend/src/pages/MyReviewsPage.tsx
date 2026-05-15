// frontend/src/pages/MyReviewsPage.tsx
import { useState, useEffect } from 'react';
import { ArrowLeft } from 'lucide-react';
import type { ProcessResponse } from '../types';
import { getMyReview, getMyReviews, type SavedReviewListItem } from '../lib/api';

interface MyReviewsPageProps {
  onBack: () => void;
  onViewReview: (review: ProcessResponse) => void;
}

export default function MyReviewsPage({ onBack, onViewReview }: MyReviewsPageProps) {
  const [reviews, setReviews] = useState<SavedReviewListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchReviews = async () => {
    try {
      setLoading(true);
      const data = await getMyReviews();
      setReviews(data.reviews || []);
    } catch (err) {
      setError("Could not load reviews. Make sure backend is running.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReviews();
  }, []);

  const handleViewReview = async (reviewId: number) => {
    try {
      const fullReview = await getMyReview(reviewId);
      onViewReview({
        status: 'success',
        processed_files: fullReview.input_abstracts_count,
        overall_synthesis: null,
        results: [
          {
            filename: fullReview.title || `Review ${reviewId}`,
            extractive: {
              key_sentences: [],
              total_extracted: 0,
            },
            abstractive_summary: fullReview.abstractive_summary,
            metrics: undefined,
          },
        ],
      });
    } catch (err) {
      alert("Could not load this review. Please try again.");
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800/80 bg-gray-900/70 backdrop-blur">
        <div className="max-w-full md:max-w-6xl mx-auto px-4 sm:px-6 md:px-8 py-4 sm:py-5 md:py-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2 md:gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-teal-400 mb-2">Library</p>
              <h1 className="text-2xl md:text-3xl font-bold">My Reviews</h1>
            </div>
            <button
              onClick={onBack}
              className="inline-flex items-center gap-2 rounded-xl border border-gray-700/80 px-3 py-2 text-xs text-gray-200 transition hover:border-teal-500/50 hover:bg-gray-800 sm:text-sm"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-full md:max-w-6xl mx-auto px-2 sm:px-6 md:px-8 py-8 sm:py-10">
        {loading && (
          <div className="text-center py-20">
            <div className="animate-spin inline-block w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full mx-auto"></div>
            <p className="text-gray-400 mt-4 text-sm sm:text-base">Loading your reviews...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-950 border border-red-800 text-red-300 p-4 sm:p-6 rounded-2xl text-center text-xs sm:text-base">
            {error}
          </div>
        )}

        {!loading && !error && reviews.length === 0 && (
          <div className="text-center py-20 text-gray-400">
            <p className="text-xl sm:text-2xl mb-4">No reviews yet</p>
            <p className="text-sm sm:text-base">Process some papers first to see them here.</p>
          </div>
        )}

        <div className="grid gap-3 sm:gap-4 md:gap-6">
          {reviews.map((review) => (
            <div
              key={review.id}
              className="bg-gray-900/80 border border-gray-800/90 rounded-2xl p-4 sm:p-6 md:p-7 hover:border-teal-500/50 transition group shadow-sm"
            >
              <div className="flex flex-col sm:flex-row justify-between items-start gap-3 sm:gap-4">
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg sm:text-xl font-semibold mb-2 truncate">{review.title}</h3>
                  <p className="text-gray-400 text-xs sm:text-sm">
                    {formatDate(review.created_at)} - {review.input_abstracts_count} paper{review.input_abstracts_count !== 1 ? 's' : ''}
                  </p>
                </div>
                <button
                  onClick={() => handleViewReview(review.id)}
                  className="px-4 sm:px-6 py-2 sm:py-3 bg-teal-500 hover:bg-teal-400 rounded-xl text-xs sm:text-sm font-semibold text-gray-950 transition whitespace-nowrap flex-shrink-0"
                >
                  View Review
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}


