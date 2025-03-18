// src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import 'antd/dist/reset.css';
import './App.css';

import Header from './components/common/Header';
import Footer from './components/common/Footer';
import HomePage from './pages/HomePage';
import RecognitionPage from './pages/RecognitionPage';
import HistoryPage from './pages/HistoryPage';
import SettingsPage from './pages/SettingsPage';

const { Content } = Layout;

function App() {
  return (
    <Router>
      <Layout className="app-layout">
        <Header />
        <Content className="app-content">
          <div className="content-container">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/recognition" element={<RecognitionPage />} />
              <Route path="/history" element={<HistoryPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </div>
        </Content>
        <Footer />
        <ToastContainer position="top-right" autoClose={5000} />
      </Layout>
    </Router>
  );
}

export default App;