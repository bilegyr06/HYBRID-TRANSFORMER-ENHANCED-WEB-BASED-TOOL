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
        <div className="max-w-6xl mx-auto px-8 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">My Reviews</h1>
            <p className="text-gray-400">Previously processed literature reviews</p>
          </div>
          <button
            onClick={onBack}
            className="px-6 py-3 border border-gray-700 hover:bg-gray-800 rounded-xl transition"
          >
            ← Back to Upload
          </button>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-8 py-10">
        {loading && (
          <div className="text-center py-20">
            <div className="animate-spin inline-block w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full mx-auto"></div>
            <p className="text-gray-400 mt-4">Loading your reviews...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-950 border border-red-800 text-red-300 p-6 rounded-2xl text-center">
            {error}
          </div>
        )}

        {!loading && !error && reviews.length === 0 && (
          <div className="text-center py-20 text-gray-400">
            <p className="text-2xl mb-4">No reviews yet</p>
            <p>Process some papers first to see them here.</p>
          </div>
        )}

        <div className="grid gap-6">
          {reviews.map((review) => (
            <div
              key={review.id}
              className="bg-gray-900 border border-gray-800 rounded-3xl p-8 hover:border-teal-600 transition group"
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-xl font-semibold mb-2">{review.title}</h3>
                  <p className="text-gray-400 text-sm">
                    {formatDate(review.date)} • {review.processed_files} paper{review.processed_files !== 1 ? 's' : ''}
                  </p>
                </div>
                <button
                  onClick={() => handleViewReview(review.id)}
                  className="px-6 py-3 bg-teal-600 hover:bg-teal-500 rounded-xl text-sm font-medium transition group-hover:scale-105"
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