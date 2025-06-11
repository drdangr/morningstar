import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
  Alert,
  CircularProgress,
  Tab,
  Tabs,
  TextField,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Rating,
  Divider,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  SmartToy as AIIcon,
  Preview as PreviewIcon,
  Analytics as AnalyticsIcon,
  Speed as ProcessingIcon,
  ExpandMore as ExpandMoreIcon,
  Visibility as ViewIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import apiService from '../services/api';

// Mock data для демонстрации компонента
const mockAIResults = {
  totalProcessed: 51,
  totalPending: 0,
  averageQuality: 8.2,
  processingTime: '2.3s',
  lastUpdated: new Date().toISOString(),
  recentResults: [
    {
      id: 1,
      postTitle: 'Украинские дроны атаковали нефтезавод в Туле',
      originalContent: 'Украинские беспилотники атаковали нефтеперерабатывающий завод в Туле...',
      aiSummary: 'Атака беспилотников на нефтезавод в Туле: подробности инцидента и его последствия',
      aiCategory: 'Война',
      relevanceScore: 0.95,
      importanceScore: 8.5,
      urgencyScore: 9.0,
      qualityRating: null,
      processedAt: new Date(Date.now() - 3600000).toISOString(),
      channel: '@breakingmash'
    },
    {
      id: 2,
      postTitle: 'Павел Дуров объявил о новых функциях Telegram',
      originalContent: 'Основатель Telegram Павел Дуров анонсировал релиз новых функций...',
      aiSummary: 'Telegram получит новые функции: анонс от Павла Дурова',
      aiCategory: 'Технологии',
      relevanceScore: 0.78,
      importanceScore: 6.5,
      urgencyScore: 4.0,
      qualityRating: 4,
      processedAt: new Date(Date.now() - 7200000).toISOString(),
      channel: '@durov'
    }
  ]
};

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`ai-results-tabpanel-${index}`}
      aria-labelledby={`ai-results-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ pt: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

export default function AIResultsPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [aiResults, setAIResults] = useState(mockAIResults);
  const [selectedPost, setSelectedPost] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [qualityRating, setQualityRating] = useState(0);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleViewPost = (post) => {
    setSelectedPost(post);
    setQualityRating(post.qualityRating || 0);
    setDialogOpen(true);
  };

  const handleRateQuality = async (rating) => {
    setQualityRating(rating);
    // TODO: Отправить рейтинг в API
    console.log(`Rating post ${selectedPost?.id} with ${rating} stars`);
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
    setSelectedPost(null);
    setQualityRating(0);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('ru-RU');
  };

  const formatScore = (score) => {
    return typeof score === 'number' ? score.toFixed(1) : 'N/A';
  };

  // Статистические карточки
  const StatCard = ({ title, value, icon, color = 'primary' }) => (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography color="textSecondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4">
              {value}
            </Typography>
          </Box>
          <Box color={`${color}.main`}>
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <div>
          <Typography variant="h4" gutterBottom>
            AI Results Viewer
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Просмотр и анализ результатов AI обработки постов
          </Typography>
        </div>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => {
            setLoading(true);
            // TODO: Обновить данные с сервера
            setTimeout(() => setLoading(false), 1000);
          }}
          disabled={loading}
        >
          {loading ? 'Обновление...' : 'Обновить'}
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Статистические карточки */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Обработано постов"
            value={aiResults.totalProcessed}
            icon={<AIIcon fontSize="large" />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="В очереди"
            value={aiResults.totalPending}
            icon={<ProcessingIcon fontSize="large" />}
            color="warning"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Средняя оценка"
            value={formatScore(aiResults.averageQuality)}
            icon={<AnalyticsIcon fontSize="large" />}
            color="info"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Время обработки"
            value={aiResults.processingTime}
            icon={<PreviewIcon fontSize="large" />}
            color="secondary"
          />
        </Grid>
      </Grid>

      {/* Вкладки */}
      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="Результаты обработки" />
            <Tab label="Batch мониторинг" />
            <Tab label="Метрики качества" />
          </Tabs>
        </Box>

        {/* Вкладка 1: Результаты обработки */}
        <TabPanel value={tabValue} index={0}>
          <Typography variant="h6" gutterBottom>
            Последние обработанные посты
          </Typography>
          
          {aiResults.recentResults.map((result) => (
            <Accordion key={result.id} sx={{ mb: 1 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', pr: 2 }}>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="subtitle1" noWrap>
                      {result.postTitle}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                      <Chip size="small" label={result.channel} color="primary" variant="outlined" />
                      <Chip size="small" label={result.aiCategory} color="secondary" />
                      <Chip 
                        size="small" 
                        label={`Важность: ${formatScore(result.importanceScore)}`} 
                        color={result.importanceScore > 7 ? 'error' : 'default'}
                      />
                    </Box>
                  </Box>
                  <Box sx={{ textAlign: 'right' }}>
                    <Typography variant="body2" color="textSecondary">
                      {formatDate(result.processedAt)}
                    </Typography>
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleViewPost(result);
                      }}
                    >
                      <ViewIcon />
                    </IconButton>
                  </Box>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      Оригинальный контент:
                    </Typography>
                    <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                      {result.originalContent}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      AI резюме:
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 2 }}>
                      {result.aiSummary}
                    </Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                      <Typography variant="body2">
                        Релевантность: {formatScore(result.relevanceScore)}
                      </Typography>
                      <Typography variant="body2">
                        Срочность: {formatScore(result.urgencyScore)}
                      </Typography>
                      {result.qualityRating && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2">Оценка:</Typography>
                          <Rating value={result.qualityRating} readOnly size="small" />
                        </Box>
                      )}
                    </Box>
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          ))}
        </TabPanel>

        {/* Вкладка 2: Batch мониторинг */}
        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" gutterBottom>
            Мониторинг batch обработки
          </Typography>
          <Alert severity="info">
            <Typography variant="body2">
              Эта функция будет реализована на этапе STAGE 2: Python AI Services.
              Здесь будет отображаться статус batch обработки, очереди задач и конфликты приоритетов.
            </Typography>
          </Alert>
        </TabPanel>

        {/* Вкладка 3: Метрики качества */}
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            Метрики качества AI
          </Typography>
          <Alert severity="info">
            <Typography variant="body2">
              Эта функция будет реализована после внедрения Python AI Services.
              Здесь будут отображаться аналитические метрики качества AI обработки:
              точность категоризации, качество резюме, пользовательские оценки.
            </Typography>
          </Alert>
        </TabPanel>
      </Paper>

      {/* Диалог детального просмотра поста */}
      <Dialog open={dialogOpen} onClose={handleDialogClose} maxWidth="md" fullWidth>
        <DialogTitle>
          Детальный просмотр AI обработки
        </DialogTitle>
        <DialogContent>
          {selectedPost && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedPost.postTitle}
              </Typography>
              
              <Divider sx={{ my: 2 }} />
              
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>
                    📝 Оригинальный контент
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="body2">
                      {selectedPost.originalContent}
                    </Typography>
                  </Paper>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>
                    🤖 AI резюме
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'primary.50' }}>
                    <Typography variant="body2">
                      {selectedPost.aiSummary}
                    </Typography>
                  </Paper>
                </Grid>
                
                <Grid item xs={12}>
                  <Typography variant="subtitle1" gutterBottom>
                    📊 AI метрики
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
                    <Chip label={`Категория: ${selectedPost.aiCategory}`} color="secondary" />
                    <Chip label={`Релевантность: ${formatScore(selectedPost.relevanceScore)}`} />
                    <Chip label={`Важность: ${formatScore(selectedPost.importanceScore)}`} />
                    <Chip label={`Срочность: ${formatScore(selectedPost.urgencyScore)}`} />
                  </Box>
                </Grid>
                
                <Grid item xs={12}>
                  <Typography variant="subtitle1" gutterBottom>
                    ⭐ Оценка качества AI обработки
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Rating
                      value={qualityRating}
                      onChange={(event, newValue) => handleRateQuality(newValue)}
                      size="large"
                    />
                    <Typography variant="body2" color="textSecondary">
                      {qualityRating > 0 ? `${qualityRating} из 5` : 'Не оценено'}
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDialogClose}>Закрыть</Button>
          <Button variant="contained" onClick={handleDialogClose}>
            Сохранить оценку
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
} 