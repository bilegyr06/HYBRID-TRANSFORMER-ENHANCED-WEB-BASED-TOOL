// frontend/src/pages/MyReviewsPage.tsx
import { useState, useEffect } from 'react';
import type { ProcessResponse } from '../types';

interface Review {
  id: string;
  title: string;
  date: string;
  processed_files: number;
}

interface MyReviewsPageProps {
  onBack: () => void;
  onViewReview: (review: ProcessResponse) => void;
}

export default function MyReviewsPage({ onBack, onViewReview }: MyReviewsPageProps) {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchReviews = async () => {
    try {
      setLoading(true);
      const response = await fetch("http://localhost:8000/api/reviews");
      
      if (!response.ok) throw new Error("Failed to fetch reviews");
      
      const data = await response.json();
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

  const handleViewReview = async (reviewId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/reviews/${reviewId}`);
      if (!response.ok) throw new Error("Failed to load review");
      
      const fullReview: ProcessResponse = await response.json();
      onViewReview(fullReview);
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
      <div className="border-b border-gray-800 bg-gray-900">
        <div className="max-w-full md:max-w-6xl mx-auto px-4 sm:px-6 md:px-8 py-4 sm:py-6">
          <h1 className="text-[1em] font-bold">My Reviews</h1>
          <p className="text-gray-400 text-[0.85em]">Previously processed literature reviews</p>
        </div>
      </div>

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
              className="bg-gray-900 border border-gray-800 rounded-2xl sm:rounded-3xl p-2.5 sm:p-6 md:p-8 hover:border-teal-600 transition group"
            >
              <div className="flex flex-col sm:flex-row justify-between items-start gap-3 sm:gap-4">
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg sm:text-xl font-semibold mb-2 truncate">{review.title}</h3>
                  <p className="text-gray-400 text-xs sm:text-sm">
                    {formatDate(review.date)} • {review.processed_files} paper{review.processed_files !== 1 ? 's' : ''}
                  </p>
                </div>
                <button
                  onClick={() => handleViewReview(review.id)}
                  className="px-4 sm:px-6 py-2 sm:py-3 bg-teal-600 hover:bg-teal-500 rounded-xl text-xs sm:text-sm font-medium transition group-hover:scale-105 whitespace-nowrap flex-shrink-0"
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