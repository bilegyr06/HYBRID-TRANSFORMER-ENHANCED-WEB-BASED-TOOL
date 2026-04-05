import { useState, useCallback } from 'react';
import UploadPage from './pages/UploadPage';
import ResultsPage from './pages/ResultsPage';
import type { ProcessResponse } from './types';

function App() {
  const [currentPage, setCurrentPage] = useState<'upload' | 'results'>('upload');
  const [processData, setProcessData] = useState<ProcessResponse | null>(null);

  const handleProcessComplete = useCallback((data: ProcessResponse) => {
    setProcessData(data);
    setCurrentPage('results');
  }, []);

  const handleBackToUpload = useCallback(() => {
    setCurrentPage('upload');
    setProcessData(null);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {currentPage === 'upload' ? (
        <UploadPage onProcessComplete={handleProcessComplete} />
      ) : (
        <ResultsPage 
          data={processData} 
          onBack={handleBackToUpload} 
        />
      )
      }
    </div>
  )}

  export default App
