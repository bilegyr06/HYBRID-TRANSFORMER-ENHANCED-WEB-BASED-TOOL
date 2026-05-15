import { useEffect, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import ProtectedAppShell from './components/layout/ProtectedAppShell';
import { PrivateRoute } from './components/layout/PrivateRoute';
import { useAuth } from './hooks/useAuth';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

function App() {
  const { user, fetchCurrentUser, isLoading: authLoading } = useAuth();
  const [isAuthenticating, setIsAuthenticating] = useState(true);

  useEffect(() => {
    const restoreSession = async () => {
      try {
        await fetchCurrentUser();
      } catch (err) {
        console.error('Failed to restore session', err);
      } finally {
        setIsAuthenticating(false);
      }
    };

    restoreSession();
  }, [fetchCurrentUser]);

  if (isAuthenticating || authLoading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500" />
          <p className="text-white mt-4">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <LoginPage />} />
      <Route path="/register" element={user ? <Navigate to="/dashboard" replace /> : <RegisterPage />} />
      <Route
        path="*"
        element={(
          <PrivateRoute>
            <ProtectedAppShell />
          </PrivateRoute>
        )}
      />
    </Routes>
  );
}

export default App;
