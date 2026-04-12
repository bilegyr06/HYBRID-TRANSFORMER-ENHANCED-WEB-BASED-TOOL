import { useState, useCallback } from 'react';
import { Menu, X, FileText, Upload, BookOpen, Settings } from 'lucide-react';
import UploadPage from './pages/UploadPage';
import ResultsPage from './pages/ResultsPage';
import MyReviewsPage from './pages/MyReviewsPage';
import type { ProcessResponse } from './types';

type Page = 'dashboard' | 'upload' | 'results' | 'my-reviews' | 'settings';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');
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

  // Navigation items with icons
  const navItems = [
    { label: 'Dashboard', page: 'dashboard' as const, icon: FileText, onClick: () => { setCurrentPage('dashboard'); setMobileMenuOpen(false); } },
    { label: 'Upload & Process', page: 'upload' as const, icon: Upload, onClick: () => { setCurrentPage('upload'); setMobileMenuOpen(false); } },
    { label: 'My Reviews', page: 'my-reviews' as const, icon: BookOpen, onClick: () => { setCurrentPage('my-reviews'); setMobileMenuOpen(false); } },
    { label: 'Settings', page: 'settings' as const, icon: Settings, onClick: () => { setCurrentPage('settings'); setMobileMenuOpen(false); } },
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col md:flex-row">
      {/* Mobile Top Navigation */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-50 bg-gray-900 border-b border-gray-800 px-4 py-2 flex items-center justify-between" style={{ height: '56px' }}>
        <div className="text-[0.9em] font-bold text-teal-400">LitReview AI</div>
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
        <div className="md:hidden fixed top-14 left-0 right-0 bg-gray-900 border-b border-gray-800 z-40">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.page}
                onClick={item.onClick}
                className={`w-full text-left px-4 py-3 border-b border-gray-800 transition flex items-center gap-3 ${
                  isActive(item.page)
                    ? 'text-teal-400 bg-gray-800 font-medium'
                    : 'text-gray-300 hover:bg-gray-800'
                }`}
              >
                <Icon size={18} />
                <span className="text-[0.85em]">{item.label}</span>
              </button>
            );
          })}
        </div>
      )}

      {/* Desktop Sidebar Navigation */}
      <div className="hidden md:flex md:flex-col md:w-56 bg-gray-900 border-r border-gray-800 sticky top-0 h-screen">
        {/* Sidebar Header */}
        <div className="p-6 border-b border-gray-800">
          <h2 className="text-[2em] font-bold text-teal-400">LitReview AI</h2>
          <p className="text-[0.75em] text-gray-500 mt-1">Academic Synthesis</p>
        </div>

        {/* Sidebar Navigation */}
        <nav className="flex-1 px-3 py-6 space-y-2 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.page}
                onClick={item.onClick}
                className={`w-full text-left px-4 py-3 rounded-lg transition flex items-center gap-3 ${
                  isActive(item.page)
                    ? 'text-teal-400 bg-gray-800 font-medium border-l-2 border-teal-500'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                <Icon size={16} />
                <span className="text-[0.85em]">{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Sidebar Footer */}
        <div className="border-t border-gray-800 p-4 text-[0.75em] text-gray-500">
          <p>v1.0 • TextRank + BART</p>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 md:min-h-screen pt-14 md:pt-0">
        {currentPage === 'dashboard' && (
          <div className="p-6 md:p-8">
            <h1 className="text-[1em] font-bold mb-8 text-white">Dashboard</h1>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div 
                onClick={() => { setCurrentPage('upload'); setMobileMenuOpen(false); }}
                className="bg-gray-900 border border-gray-800 rounded-lg p-6 cursor-pointer hover:border-teal-500 hover:bg-gray-850 transition"
              >
                <Upload size={32} className="text-teal-400 mb-4" />
                <h2 className="text-[0.9em] font-semibold mb-2">Upload & Process</h2>
                <p className="text-[0.8em] text-gray-400">Add new academic papers and generate synthesis</p>
              </div>
              <div 
                onClick={() => { setCurrentPage('my-reviews'); setMobileMenuOpen(false); }}
                className="bg-gray-900 border border-gray-800 rounded-lg p-6 cursor-pointer hover:border-teal-500 hover:bg-gray-850 transition"
              >
                <BookOpen size={32} className="text-teal-400 mb-4" />
                <h2 className="text-[0.9em] font-semibold mb-2">My Reviews</h2>
                <p className="text-[0.8em] text-gray-400">Access saved literature reviews</p>
              </div>
              <div 
                onClick={() => { setCurrentPage('settings'); setMobileMenuOpen(false); }}
                className="bg-gray-900 border border-gray-800 rounded-lg p-6 cursor-pointer hover:border-teal-500 hover:bg-gray-850 transition"
              >
                <Settings size={32} className="text-teal-400 mb-4" />
                <h2 className="text-[0.9em] font-semibold mb-2">Settings</h2>
                <p className="text-[0.8em] text-gray-400">Configure your preferences</p>
              </div>
            </div>
          </div>
        )}

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

        {currentPage === 'settings' && (
          <div className="p-6 md:p-8">
            <h1 className="text-[1em] font-bold mb-8 text-white">Settings</h1>
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 max-w-2xl">
              <h2 className="text-[0.9em] font-semibold mb-4">Preferences</h2>
              <p className="text-[0.85em] text-gray-400">Settings panel coming soon...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;