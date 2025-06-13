import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

import Layout from './components/Layout';
import DashboardPage from './pages/DashboardPage';
import CategoriesPage from './pages/CategoriesPage';
import ChannelsPage from './pages/ChannelsPage';
import PublicBotsPage from './pages/PublicBotsPage';
import PostsCachePage from './pages/PostsCachePage';
import LLMSettingsPage from './pages/LLMSettingsPage_v4';
import AIResultsPage from './pages/AIResultsPage';
import './App.css'

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/categories" element={<CategoriesPage />} />
            <Route path="/channels" element={<ChannelsPage />} />
            <Route path="/public-bots" element={<PublicBotsPage />} />
            <Route path="/posts-cache" element={<PostsCachePage />} />
            <Route path="/ai-results" element={<AIResultsPage />} />
            <Route path="/settings" element={<LLMSettingsPage />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default App;
