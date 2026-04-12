import { useState, useCallback } from 'react';
import { Menu, X } from 'lucide-react';
import UploadPage from './pages/UploadPage';
import ResultsPage from './pages/ResultsPage';
import MyReviewsPage from './pages/MyReviewsPage';
import type { ProcessResponse } from './types';

type Page = 'upload' | 'results' | 'my-reviews';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('upload');
  const [processData, setProcessData] = useState<ProcessResponse | null>(null);
  const [currentReviewTitle, setCurrentReviewTitle] = useState<string>("");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleProcessComplete = useCallback((data: ProcessResponse) => {
    setProcessData(data);
    setCurrentPage('results');
    setMobileMenuOpen(false);
  }, []);

  const handleBackToUpload = useCallback(() => {
    setCurrentPage('upload');
    setProcessData(null);
    setCurrentReviewTitle("");
    setMobileMenuOpen(false);
  }, []);

  const handleGoToMyReviews = useCallback(() => {
    setCurrentPage('my-reviews');
    setMobileMenuOpen(false);
  }, []);

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
          results: processData.results,
          overall_synthesis: processData.overall_synthesis || null
        }),
      });

      if (response.ok) {
        alert("Review saved successfully!");
        setCurrentReviewTitle("");
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
    setMobileMenuOpen(false);
  };

  const isActive = (page: Page) => currentPage === page;

  // Navigation items
  const navItems = [
    { label: 'Upload', page: 'upload' as const, onClick: () => { setCurrentPage('upload'); setMobileMenuOpen(false); } },
    { label: 'My Reviews', page: 'my-reviews' as const, onClick: () => { setCurrentPage('my-reviews'); setMobileMenuOpen(false); } },
  ];

  if (currentPage === 'results') {
    navItems.push({ 
      label: 'Results', 
      page: 'results' as const,
      onClick: () => setMobileMenuOpen(false)
    });
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col md:flex-row">
      {/* Mobile Top Navigation */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-50 bg-gray-900 border-b border-gray-800 px-4 py-3 flex items-center justify-between h-16">
        <div className="text-lg font-bold text-teal-400">LitReview AI</div>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="text-gray-400 hover:text-white transition"
          aria-label="Toggle menu"
        >
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed top-16 left-0 right-0 bg-gray-900 border-b border-gray-800 z-40">
          {navItems.map((item) => (
            <button
              key={item.page}
              onClick={item.onClick}
              className={`w-full text-left px-4 py-3 border-b border-gray-800 transition ${
                isActive(item.page)
                  ? 'text-teal-400 bg-gray-800 font-medium'
                  : 'text-gray-300 hover:bg-gray-800'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}

      {/* Desktop Sidebar Navigation */}
      <div className="hidden md:flex md:flex-col md:w-64 bg-gray-900 border-r border-gray-800 sticky top-0 h-screen">
        {/* Sidebar Header */}
        <div className="p-6 border-b border-gray-800">
          <h1 className="text-xm font-bold text-teal-400">LitReview AI</h1>
          <p className="text-xs text-gray-500 mt-1">Automated Literature Review</p>
        </div>

        {/* Sidebar Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
          {navItems.map((item) => (
            <button
              key={item.page}
              onClick={item.onClick}
              className={`w-full text-left px-4 py-3 rounded-xl transition ${
                isActive(item.page)
                  ? 'text-teal-400 bg-gray-800 font-medium border-l-2 border-teal-500'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>

        {/* Sidebar Footer */}
        <div className="border-t border-gray-800 p-4 text-xs text-gray-500">
          <p>v1.0 - TextRank + BART Hybrid</p>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 md:min-h-screen pt-16 md:pt-0">
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
            onGoToMyReviews={handleGoToMyReviews}
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
    </div>
  );
}

export default App;