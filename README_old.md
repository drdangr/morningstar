# Telegram Digest Bot - Мультитенантная платформа цифровых изданий

## 🚀 Новая архитектура: Платформа для множественных тематических ботов

**Telegram Digest Bot** представляет собой **мультитенантную платформу** для создания тематических публичных ботов — как различные журналы от одного издательского дома.

### 📰 Концепция "Цифрового издательства"

**Главная идея:** Один администратор (главный редактор) создает множество специализированных публичных ботов, каждый из которых фокусируется на определенной тематике и имеет собственную аудиторию.

**Примеры тематических ботов:**
- 🇺🇸 **"США Дайджест"** - новости из США для русскоязычной аудитории
- 🛡️ **"Военные Сводки"** - аналитика военных конфликтов  
- 💰 **"Крипто Новости"** - события в мире криптовалют
- 🎭 **"Культурный Дайджест"** - события искусства и культуры
- 🏛️ **"Политический Пульс"** - политические новости и аналитика

### 🏗️ Архитектурные принципы

#### **Централизованное управление**
- **Единая админ-панель** для управления всеми ботами
- **Shared инфраструктура:** один userbot, одна AI система, одна база данных
- **Общий пул каналов:** каналы могут использоваться несколькими ботами
- **Централизованный posts cache** с инкрементальными обновлениями

#### **Мультитенантная архитектура**
- **Изоляция аудиторий:** каждый бот имеет отдельную базу пользователей
- **Персонализированная доставка:** AI создает дайджесты под специфику каждого бота
- **Индивидуальная монетизация:** разные тарифы и модели оплаты для каждого бота
- **Отдельная аналитика:** метрики engagement, конверсии, доходности по ботам

#### **AI-driven контент**
- **Умная категоризация:** AI анализирует каждый пост и назначает точную категорию
- **Тематическая фильтрация:** AI понимает специфику каждого бота и отбирает релевантный контент
- **Гибкие промпты:** каждый бот может иметь уникальные AI инструкции
- **Мультиязычность:** поддержка генерации контента на разных языках

#### **Conflict Management система**
```
Priority System (0=highest, 5=lowest):
├── 0: EMERGENCY_NEWS     - срочные новости (отменяют все)
├── 1: ADMIN_MANUAL       - ручные команды администратора  
├── 2: USER_PREMIUM       - платные запросы пользователей
├── 3: PROMPT_REBUILD     - обновление AI промптов
├── 4: SCHEDULED          - плановые дайджесты
└── 5: BACKGROUND         - фоновые задачи
```

### 👥 Пользовательские роли

#### **🧑‍💼 Главный редактор (Администратор)**
- **Создание и настройка ботов:** определение тематики, каналов, категорий
- **Управление AI промптами:** настройка качества и стиля контента для каждого бота
- **Аналитика по ботам:** сравнение performance, engagement, монетизации
- **Мониторинг системы:** отслеживание posts cache, конфликтов задач, AI обработки

#### **📱 Читатели публичных ботов**
- **Подписка на тематические дайджесты:** выбор ботов по интересам
- **Персонализация внутри бота:** фильтрация категорий, настройка времени доставки
- **Премиум возможности:** частые обновления, push уведомления, эксклюзивные дайджесты
- **Обратная связь:** оценка качества контента для улучшения AI

### 💰 Монетизация

#### **Модель freemium по ботам:**
- **Бесплатный тариф:** ежедневные дайджесты, базовые категории
- **Премиум подписка:** частые обновления, эксклюзивные каналы, приоритетная поддержка
- **Микротранзакции:** дайджесты по запросу, срочные новости
- **Enterprise:** API доступ, кастомизация, приватные каналы

#### **Биллинг система:**
- **Единый аккаунт пользователя** с балансом для всех ботов платформы
- **Разные тарифы по ботам:** "США Дайджест" $5/месяц, "Крипто" $10/месяц
- **Транзакционная история** с детализацией по ботам и услугам
- **Лимиты использования** с graceful degradation для бесплатных пользователей

## 🏛️ Архитектура системы

### Общая схема мультитенантной платформы
```
┌─────────────────────────────────────────────────────────┐
│                    ADMIN PANEL                         │
│  Управление ботами │ AI Settings │ Мониторинг          │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│                 BACKEND API                             │
│  Public Bots │ Users │ Subscriptions │ Billing          │
└─────────────────┬───────────────────────────────────────┘
                  │
   ┌──────────────┼──────────────┐
   │              │              │
   ▼              ▼              ▼
┌─────────┐  ┌──────────┐  ┌────────────┐
│ USERBOT │  │AI SERVICE│  │ PUBLIC BOTS│
│ Сбор    │  │ Python   │  │ Bot #1, #2 │
│ контента│  │ модуль   │  │ Bot #3...  │
└─────────┘  └──────────┘  └────────────┘
     │              │              │
     └──────────────┼──────────────┘
                    ▼
         ┌─────────────────────┐
         │    POSTS CACHE      │
         │    PostgreSQL       │
         │   с партиционированием │
         └─────────────────────┘
```

### Data Flow Architecture
```
1. СБОР ДАННЫХ:
   ├── Scheduled crawling по каналам (каждые 15 минут)
   ├── Manual triggers из админ-панели
   ├── Real-time Telegram Updates API
   └── On-demand requests от публичных ботов

2. ОБРАБОТКА:
   ├── Centralized posts cache с retention management  
   ├── AI analysis через Python модуль (не N8N)
   ├── Conflict management с priority system
   └── Batch processing для больших объемов

3. ДОСТАВКА:
   ├── Персонализированные дайджесты по ботам
   ├── Push notifications для премиум пользователей
   ├── API endpoints для внешних интеграций
   └── Web preview для публичного доступа
```

## 🎯 Текущий статус проекта

**✅ STAGE 5 ЗАВЕРШЕН** (декабрь 2025) - **Монолитная система работает**
- **✅ Полнофункциональная база:** Admin Panel, Backend API, AI обработка, публичный бот
- **✅ Критические проблемы решены:** индивидуальная категоризация постов v7.3, N8N batch processing исправлен
- **✅ Система готова к эволюции:** отличная основа для перехода к мультитенантности

**🚀 STAGE 6 В РАЗРАБОТКЕ** - **Multi-tenant Architecture Evolution**

### Наследование vs Новая разработка

#### ✅ **Компоненты для ПОЛНОГО наследования:**
1. **Backend API (FastAPI)** - отлично спроектирован
   - **Готово:** CRUD для каналов/категорий, валидация, REST endpoints
   - **Добавить:** модели PublicBot, BotUser, UserSubscription, Billing

2. **Admin Panel (React + MUI)** - современный интерфейс  
   - **Готово:** компонентная архитектура, навигация, валидация
   - **Добавить:** секции Public Bots, LLM Settings, мониторинг постов

3. **Database схема** - хорошая основа PostgreSQL
   - **Готово:** channels, categories, digests, settings
   - **Добавить:** партиционирование, posts_cache, биллинг

#### 🔄 **Компоненты для АДАПТАЦИИ:**
4. **Userbot** - отработанная логика сбора
   - **Адаптировать:** centralized posts_cache, мультиканальный сбор

5. **AI логика** - из N8N workflows в Python модуль
   - **Перенести:** Dynamic prompts, Binary Relevance, structured instructions

#### ❌ **Компоненты для ЗАМЕНЫ:**
6. **N8N workflows** → **Python AI Service** 
   - **Причина:** проблемы с batch processing, зависимость от внешнего сервиса

7. **Telegram-бот** → **Мультитенантная архитектура**
   - **Причина:** единый бот → множественные тематические боты

## 📋 План разработки Stage 6

### **Этап 1: Backend расширение** (1 неделя)
- Мультитенантные модели: PublicBot, BotUser, UserSubscription  
- Posts cache table с retention management
- LLM провайдеры settings (OpenAI, Anthropic, локальные)
- Биллинг система (базовая)

### **Этап 2: Admin Panel + детальный мониторинг** (1 неделя)
```
📊 Новые секции админ-панели:
├── 📈 Posts Analytics (posts viewer, AI analysis)
├── 🤖 Public Bots (создание, настройка, аналитика)  
├── ⚙️ LLM Settings (провайдер, модель, лимиты)
├── 📋 Digest Viewer (исходные → AI → финальный)
└── 🎛️ Collection Triggers (manual, scheduled)
```

### **Этап 3: Userbot с централизованным кешем** (3-4 дня)
- Centralized posts_cache с инкрементальными обновлениями
- Manual triggers из админ-панели
- Мониторинг накопленных постов

### **Этап 4: AI Service на Python** (1 неделя)  
- Замена N8N workflows на Python модуль
- Batch processing с conflict management
- Гибкие настройки LLM провайдеров

### **Этап 5: AI Testing & Tuning** (3-4 дня)
- A/B тестирование разных LLM моделей на накопленных данных
- Оптимизация промптов и параметров
- Настройка качества для разных тематик

### **Этап 6: Мультитенантная система ботов** (1 неделя)
- Архитектура PublicBot с каналами и категориями
- Shared AI Service для всех ботов
- Первый тематический бот с мультитенантным функционалом

### **Этап 7: Второй бот для тестирования** (3-4 дня)
- Создание второго тематического бота
- Тестирование изоляции аудиторий  
- Валидация shared инфраструктуры

### **Этап 8: Polishing публичных ботов** (3-4 дня)
- UI/UX для пользователей
- Онбординг и объяснение уникальности каждого бота
- Красивые дайджесты с брендингом

### **Этап 9a: Conflict Management** (3-4 дня)
- Priority система для задач обработки
- Queue management с Redis/Celery

### **Этап 9b: Emergency News & Real-time** (3-4 дня)
- Детекция срочных новостей
- Instant processing и push уведомления

### **Этап 9c: User Demand Triggers** (3-4 дня)  
- Платные дайджесты по запросу
- On-demand обновления для премиум пользователей

### **Этап 10: Механики монетизации** (1 неделя)
- Биллинг система с транзакциями
- Тарифные планы по ботам
- Payment gateway интеграция

### **Этап 11: Advanced Analytics** (3-4 дня)
- Cross-bot performance analytics
- Revenue optimization
- User engagement metrics

## 💻 Технологический стек

### **Сохраняем (проверенные технологии):**
- **Backend:** FastAPI + SQLAlchemy + PostgreSQL
- **Frontend:** React + Material UI + TypeScript  
- **Database:** PostgreSQL с партиционированием
- **Infrastructure:** Docker + Docker Compose

### **Новые технологии:**
- **AI Service:** Python asyncio + OpenAI/Anthropic SDK
- **Queue System:** Redis + Celery для conflict management
- **Monitoring:** Prometheus + Grafana (модульно)
- **Real-time:** Telegram Updates API или WebSockets

### **Заменяем:**
- **❌ N8N workflows** → **✅ Python AI Service**
  - Причина: лучший контроль, debugging, тестирование

## 🗄️ Новая архитектура базы данных

### **Мультитенантные таблицы:**

```sql
-- Публичные боты платформы
CREATE TABLE public_bots (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,           -- "США Дайджест"
    description TEXT,                      -- Описание тематики
    telegram_bot_token VARCHAR(500) NOT NULL,
    telegram_username VARCHAR(255),       -- @usa_digest_bot
    is_active BOOLEAN DEFAULT true,
    branding JSONB,                       -- Логотип, цвета, стиль
    ai_instructions TEXT,                 -- Кастомные промпты для AI
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Связи ботов с каналами и категориями
CREATE TABLE bot_channels (
    bot_id INTEGER REFERENCES public_bots(id),
    channel_id INTEGER REFERENCES channels(id),
    PRIMARY KEY (bot_id, channel_id)
);

CREATE TABLE bot_categories (  
    bot_id INTEGER REFERENCES public_bots(id),
    category_id INTEGER REFERENCES categories(id),
    priority INTEGER DEFAULT 0,           -- Приоритет категории для бота
    PRIMARY KEY (bot_id, category_id)
);

-- Пользователи публичных ботов
CREATE TABLE bot_users (
    id SERIAL PRIMARY KEY,
    bot_id INTEGER REFERENCES public_bots(id),
    telegram_id BIGINT NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    language VARCHAR(10) DEFAULT 'ru',
    timezone VARCHAR(50) DEFAULT 'Europe/Moscow',
    is_active BOOLEAN DEFAULT true,
    subscription_tier VARCHAR(50) DEFAULT 'free', -- free, premium, enterprise
    balance DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(bot_id, telegram_id)
);

-- Подписки пользователей на категории внутри бота
CREATE TABLE user_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES bot_users(id),
    category_id INTEGER REFERENCES categories(id),
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, category_id)
);

-- Централизованный кеш постов
CREATE TABLE posts_cache (
    id SERIAL PRIMARY KEY,
    channel_id INTEGER REFERENCES channels(id),
    telegram_message_id BIGINT,
    content TEXT,
    media_type VARCHAR(50),
    media_url TEXT,
    views INTEGER DEFAULT 0,
    posted_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT NOW(),
    ai_processed BOOLEAN DEFAULT false,
    ai_category VARCHAR(255),
    ai_summary TEXT,
    ai_metrics JSONB,                     -- importance, urgency, significance
    retention_until TIMESTAMP,           -- Автоматическое удаление
    INDEX(channel_id, posted_at),
    INDEX(ai_processed, collected_at),
    INDEX(retention_until)
) PARTITION BY RANGE (posted_at);       -- Партиционирование по дате

-- Биллинг система
CREATE TABLE billing_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES bot_users(id),
    bot_id INTEGER REFERENCES public_bots(id),
    transaction_type VARCHAR(50),         -- subscription, on_demand, refund
    amount DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50),                   -- pending, completed, failed
    payment_provider VARCHAR(100),
    provider_transaction_id VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### **LLM Settings система:**
```sql
CREATE TABLE llm_providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,           -- "openai", "anthropic", "local"
    display_name VARCHAR(255),            -- "OpenAI GPT-4"
    api_endpoint VARCHAR(500),
    auth_type VARCHAR(50),                -- "bearer", "api_key", "none"
    models JSONB,                         -- Список доступных моделей
    rate_limits JSONB,                    -- Лимиты API
    pricing JSONB,                        -- Стоимость за токен
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE llm_settings (
    id SERIAL PRIMARY KEY,
    bot_id INTEGER REFERENCES public_bots(id),
    provider_id INTEGER REFERENCES llm_providers(id),
    model_name VARCHAR(255),
    max_tokens INTEGER DEFAULT 4000,
    temperature DECIMAL(3,2) DEFAULT 0.3,
    custom_params JSONB,
    monthly_budget DECIMAL(10,2),        -- Лимит бюджета
    is_active BOOLEAN DEFAULT true,
    UNIQUE(bot_id)                       -- Один LLM на бота
);
```

## 🔧 Модернизированные компоненты

### **Admin Panel новые секции:**

#### **Public Bots Management:**
```jsx
// Новые компоненты админ-панели
<PublicBotsPage>
  <BotCreationDialog />        // Создание нового тематического бота
  <BotChannelsManager />       // Привязка каналов к боту  
  <BotCategoriesManager />     // Настройка категорий для бота
  <BotAnalytics />            // Метрики: пользователи, engagement, revenue
  <BotAISettings />           // Кастомные промпты и LLM настройки
</PublicBotsPage>

<LLMSettingsPage>
  <ProviderManager />         // Управление OpenAI, Anthropic, локальные
  <ModelSelector />           // Выбор модели по ботам
  <BudgetManager />           // Лимиты расходов на AI по ботам  
  <PerformanceAnalytics />    // A/B тесты качества разных моделей
</LLMSettingsPage>

<PostsMonitoringPage>
  <PostsViewer />             // Просмотр содержания постов с AI анализом
  <DigestPreview />           // Превью: исходные посты → AI → финальный дайджест
  <ConflictManager />         // Мониторинг приоритетных задач
  <CacheManager />            // Управление retention и партиционированием
</PostsMonitoringPage>
```

### **Python AI Service архитектура:**

```python
# ai_service/main.py
class AIProcessingService:
    async def process_posts_batch(self, posts: List[Post], bot_config: BotConfig):
        """Обработка батча постов для конкретного бота"""
        
        # 1. Формирование промпта под специфику бота
        prompt = self.build_bot_specific_prompt(bot_config)
        
        # 2. Вызов LLM с учетом настроек бота
        llm_response = await self.call_llm(
            provider=bot_config.llm_provider,
            model=bot_config.llm_model,
            prompt=prompt,
            posts=posts
        )
        
        # 3. Парсинг и валидация ответа
        processed_posts = self.parse_llm_response(llm_response)
        
        # 4. Сохранение в posts_cache с AI анализом
        await self.save_ai_analysis(processed_posts)
        
        return processed_posts

# ai_service/conflict_manager.py  
class ConflictManager:
    async def handle_processing_request(self, request: ProcessingRequest):
        """Управление конфликтами задач обработки"""
        
        # Проверка priority и отмена менее важных задач
        await self.cancel_lower_priority_tasks(request.priority)
        
        # Resource semaphore для лимитов API
        async with self.ai_api_semaphore:
            return await self.process_request(request)
```

## 🚀 Готовность к разработке

**✅ План одобрен**  
**✅ Архитектура проработана**  
**✅ Технологии выбраны**  
**✅ Миграционная стратегия ясна**

**Следующий шаг:** Обновление ROADMAP.md с детальными задачами Stage 6