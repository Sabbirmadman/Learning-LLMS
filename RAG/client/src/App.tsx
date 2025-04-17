import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { initializeAuth } from '@/lib/redux/features/auth/authSlice';
import { RootState } from '@/store/store';
import { ProtectedRoute, PublicOnlyRoute } from '@/components/auth/protected-route';
import { Toaster } from "@/components/ui/sonner"
// Layout
import Layout from '@/components/layout/Layout';

// Pages
import LandingPage from '@/pages/LandingPage';
import LoginPage from '@/pages/login';
import SignupPage from '@/pages/SignupPage';
import ProfilePage from '@/pages/ProfilePage';
import MyFilesPage from '@/pages/MyFilesPage';
import ChatPage from '@/pages/ChatPage';
import ContentViewerPage from '@/pages/ContentViewerPage';
import { ThemeProvider } from './components/ui/theme-provider';

function App() {
  const dispatch = useDispatch();
  const { isLoading } = useSelector((state: RootState) => state.auth);
  
  useEffect(() => {
    dispatch(initializeAuth());
  }, [dispatch]);

  // Show loading state while auth is initializing
  if (isLoading) {
    return (
      <div className="h-screen w-full flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <ThemeProvider defaultTheme="system" storageKey="vite-ui-theme">
      <Router>
        <div className="min-h-screen flex flex-col">
          <main className="flex-grow">
            <Routes>
              <Route path="/" element={<Layout />}>
                {/* Public route - accessible to everyone */}
                <Route index element={<LandingPage />} />
                
                {/* Public ONLY routes - not accessible after login */}
                <Route element={<PublicOnlyRoute redirectPath="/profile" />}>
                  <Route path="login" element={<LoginPage />} />
                  <Route path="signup" element={<SignupPage />} />
                </Route>
                
                {/* Protected routes - require auth */}
                <Route element={<ProtectedRoute />}>
                  <Route path="profile" element={<ProfilePage />} />
                  <Route path="myfiles" element={<MyFilesPage />} />
                  <Route path="chat" element={<ChatPage />} />
                  <Route path="content/:type/:id" element={<ContentViewerPage />} />
                </Route>
                
                {/* Fallback route */}
                <Route path="*" element={<Navigate to="/" />} />
              </Route>
            </Routes>
          </main>
        </div>
      </Router>
      <Toaster />
    </ThemeProvider>
  );
}

export default App;