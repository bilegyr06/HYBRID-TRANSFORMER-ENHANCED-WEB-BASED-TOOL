import { useCallback, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { saveReview } from '../../lib/api';
import type { ProcessResponse } from '../../types';
import { useAuth } from '../../hooks/useAuth';
import MyReviewsPage from '../../pages/MyReviewsPage';
import ResultsPage from '../../pages/ResultsPage';
import UploadPage from '../../pages/UploadPage';
import DashboardPage from '../../pages/DashboardPage';
import SettingsPage from '../../pages/SettingsPage';
import DesktopSidebar from './DesktopSidebar';
import MobileNavMenu from './MobileNavMenu';
import MobileTopBar from './MobileTopBar';
import { APP_PATHS, getAppPage, type AppPage } from './appNavigation';

export default function ProtectedAppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [currentPage, setCurrentPage] = useState<AppPage>(getAppPage(location.pathname));
  const [processData, setProcessData] = useState<ProcessResponse | null>(null);
  const [currentReviewTitle, setCurrentReviewTitle] = useState<string>('');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    setCurrentPage(getAppPage(location.pathname));
  }, [location.pathname]);

  const goToPage = useCallback((page: AppPage) => {
    setMobileMenuOpen(false);
    navigate(APP_PATHS[page]);
  }, [navigate]);

  const handleProcessComplete = useCallback((data: ProcessResponse) => {
    setProcessData(data);
    setCurrentReviewTitle('');
    goToPage('results');
  }, [goToPage]);

  const handleBackToUpload = useCallback(() => {
    setProcessData(null);
    setCurrentReviewTitle('');
    goToPage('upload');
  }, [goToPage]);

  const handleSaveReview = async () => {
    if (!processData) return;

    const title = currentReviewTitle.trim() || `Review ${new Date().toLocaleDateString('en-GB')}`;
    const extractiveSummary = processData.results
      .map((result) => result.extractive.key_sentences.map((sentence) => sentence.sentence).join(' '))
      .join('\n\n');
    const abstractiveSummary = processData.results
      .map((result) => result.abstractive_summary)
      .filter(Boolean)
      .join('\n\n');

    try {
      const response = await saveReview({
        title,
        input_abstracts_count: processData.processed_files,
        extractive_summary: extractiveSummary,
        abstractive_summary: processData.overall_synthesis || abstractiveSummary,
        key_themes: [],
        visualizations_metadata: {},
        rouge_scores: processData.results[0]?.metrics
          ? {
              rouge1: processData.results[0].metrics.rouge1,
              rouge2: processData.results[0].metrics.rouge2,
              rougeL: processData.results[0].metrics.rougeL,
            }
          : undefined,
      });

      if (response?.id) {
        alert('Review saved successfully!');
        setCurrentReviewTitle('');
      } else {
        alert('Failed to save review: Unknown error');
      }
    } catch (error) {
      console.error(error);
      alert('Could not save review. Please check the backend.');
    }
  };

  const handleViewReview = (reviewData: ProcessResponse) => {
    setProcessData(reviewData);
    goToPage('results');
  };

  const handleLogout = async () => {
    try {
      await logout();
      setProcessData(null);
      setCurrentReviewTitle('');
      navigate('/login', { replace: true });
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col md:flex-row">
      <MobileTopBar
        isOpen={mobileMenuOpen}
        onToggle={() => setMobileMenuOpen(prev => !prev)}
      />
      <MobileNavMenu
        isOpen={mobileMenuOpen}
        activePage={currentPage}
        onNavigate={goToPage}
        onLogout={handleLogout}
      />
      <DesktopSidebar
        user={user}
        activePage={currentPage}
        onNavigate={goToPage}
        onLogout={handleLogout}
      />

      <main className="flex-1 md:min-h-screen pt-14 md:pt-0 bg-[radial-gradient(circle_at_top_right,rgba(20,184,166,0.08),transparent_34%),linear-gradient(180deg,rgba(15,23,42,0.28),transparent_260px)]">
        {currentPage === 'dashboard' && (
          <DashboardPage user={user} onNavigate={goToPage} />
        )}

        {currentPage === 'upload' && (
          <UploadPage onProcessComplete={handleProcessComplete} />
        )}

        {currentPage === 'results' && processData && (
          <ResultsPage
            data={processData}
            onBack={handleBackToUpload}
            onSaveReview={handleSaveReview}
            onGoToMyReviews={() => goToPage('my-reviews')}
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
          <SettingsPage user={user} />
        )}
      </main>
    </div>
  );
}
