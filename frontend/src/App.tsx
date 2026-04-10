import { useState, useCallback } from 'react';
import UploadPage from './pages/UploadPage';
import ResultsPage from './pages/ResultsPage';
import MyReviewsPage from './pages/MyReviewsPage';
import type { ProcessResponse } from './types';

type Page = 'upload' | 'results' | 'my-reviews';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('upload');
  const [processData, setProcessData] = useState<ProcessResponse | null>(null);
  const [currentReviewTitle, setCurrentReviewTitle] = useState<string>("");

  const handleProcessComplete = useCallback((data: ProcessResponse) => {
    setProcessData(data);
    setCurrentPage('results');
  }, []);

  const handleBackToUpload = useCallback(() => {
    setCurrentPage('upload');
    setProcessData(null);
  }, []);

  const handleGoToMyReviews = useCallback(() => {
    setCurrentPage('my-reviews');
  }, []);

  // Save current review
  const handleSaveReview = async () => {
    if (!processData) return;

    const title = currentReviewTitle.trim() || 
      `Review ${new Date().toLocaleDateString('en-GB')}`;

    try {
      const response = await fetch("http://localhost:8000/api/save-review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: title,
          results: processData.results
        }),
      });

      if (response.ok) {
        alert("Review saved successfully! You can view it in My Reviews.");
        setCurrentReviewTitle(""); // clear title
      } else {
        alert("Failed to save review.");
      }
    } catch (error) {
      console.error(error);
      alert("Could not save review. Backend may not be running.");
    }
  };

  const handleViewReview = (reviewData: ProcessResponse) => {
    setProcessData(reviewData);
    setCurrentPage('results');
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {currentPage === 'upload' && (
        <UploadPage 
          onProcessComplete={handleProcessComplete}
          onGoToMyReviews={handleGoToMyReviews}
        />
      )}

      {currentPage === 'results' && processData && (
        <ResultsPage 
          data={processData} 
          onBack={handleBackToUpload}
          onSaveReview={handleSaveReview}
          reviewTitle={currentReviewTitle}
          setReviewTitle={setCurrentReviewTitle}
        />
      )}

      {currentPage === 'my-reviews' && (
        <MyReviewsPage 
          onBack={handleBackToUpload}
          onViewReview={handleViewReview}
        />
      )}
    </div>
  );
}

export default App;