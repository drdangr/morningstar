import React from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Box,
  CssBaseline,
  Button
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Storage as StorageIcon,
  Psychology as PsychologyIcon,
  SmartToy as SmartToyIcon,
  Settings as SettingsIcon,
  Category as CategoryIcon,
  Radio as RadioIcon,
  Android as AndroidIcon
} from '@mui/icons-material';

// Импорт страниц
import DashboardPage from '../pages/DashboardPage';
import PostsCachePage from '../pages/PostsCachePage_v2';
import AIResultsPage from '../pages/AIResultsPage';
import CategoriesPage from '../pages/CategoriesPage';
import ChannelsPage from '../pages/ChannelsPage';
import PublicBotsPage from '../pages/PublicBotsPage';
import LLMSettingsPage from '../pages/LLMSettingsPage';
import UserbotPage from '../pages/UserbotPage';

const drawerWidth = 240;

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Userbot', icon: <AndroidIcon />, path: '/userbot' },
  { text: 'Posts Cache', icon: <StorageIcon />, path: '/posts-cache' },
  { text: 'AI Results', icon: <PsychologyIcon />, path: '/ai-results' },
  { text: 'Categories', icon: <CategoryIcon />, path: '/categories' },
  { text: 'Channels', icon: <RadioIcon />, path: '/channels' },
  { text: 'Public Bots', icon: <SmartToyIcon />, path: '/public-bots' },
  { text: 'System Settings', icon: <SettingsIcon />, path: '/llm-settings' },
];

function Layout() {
  const location = useLocation();

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar 
        position="fixed" 
        sx={{ 
          width: `calc(100% - ${drawerWidth}px)`, 
          ml: `${drawerWidth}px`,
          backgroundColor: '#1976d2'
        }}
      >
        <Toolbar>
          <Typography variant="h6" noWrap component="div">
            MorningStar Admin Panel
          </Typography>
        </Toolbar>
      </AppBar>
      
      <Drawer
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
        variant="permanent"
        anchor="left"
      >
        <Toolbar />
        <Box sx={{ overflow: 'auto' }}>
          <List>
            {menuItems.map((item) => (
              <ListItem 
                key={item.text}
                component={Link} 
                to={item.path}
                sx={{
                  backgroundColor: location.pathname === item.path ? 'rgba(25, 118, 210, 0.12)' : 'transparent',
                  '&:hover': {
                    backgroundColor: 'rgba(25, 118, 210, 0.08)',
                  },
                }}
              >
                <ListItemIcon sx={{ color: location.pathname === item.path ? '#1976d2' : 'inherit' }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={item.text} 
                  sx={{ color: location.pathname === item.path ? '#1976d2' : 'inherit' }}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>
      
      <Box 
        component="main" 
        sx={{ 
          flexGrow: 1, 
          bgcolor: 'background.default', 
          p: 3,
          minHeight: '100vh'
        }}
      >
        <Toolbar />
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/userbot" element={<UserbotPage />} />
          <Route path="/posts-cache" element={<PostsCachePage />} />
          <Route path="/ai-results" element={<AIResultsPage />} />
          <Route path="/categories" element={<CategoriesPage />} />
          <Route path="/channels" element={<ChannelsPage />} />
          <Route path="/public-bots" element={<PublicBotsPage />} />
          <Route path="/llm-settings" element={<LLMSettingsPage />} />
        </Routes>
      </Box>
    </Box>
  );
}

export default Layout; 