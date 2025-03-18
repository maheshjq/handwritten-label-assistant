import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import MainLayout from './components/layout/MainLayout';
import Dashboard from './pages/Dashboard';
import Recognition from './pages/Recognition';
import Review from './pages/Review';
import Settings from './pages/Settings';
import './App.css';

const queryClient = new QueryClient();

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <MainLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/recognition" element={<Recognition />} />
          <Route path="/review" element={<Review />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </MainLayout>
    </QueryClientProvider>
  );
};

export default App;
