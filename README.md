# Telegram Digest Bot - Мультитенантная платформа цифровых изданий

## 🚀 ОБНОВЛЕНИЕ 6/28/2025: Текущее состояние AI Orchestrator

**⚠️ ТЕКУЩИЕ ПРОБЛЕМЫ AI ORCHESTRATOR:**

**🔍 Выявленные ограничения:**
- AI Orchestrator работает последовательно (сначала категоризация, потом саммаризация)
- Батчевая саммаризация не работает - LLM игнорирует промпты в batch режиме
- Система переведена на сингловый режим обработки для качественных результатов
- Параллельность двух AI сервисов фактически не реализована

**🔄 ТЕКУЩАЯ АРХИТЕКТУРА - Последовательная обработка:**

### **🔄 Реальная архитектура: Последовательная обработка**

**Принцип работы:**
1. **Двухэтапная обработка** - сначала выполняется вся категоризация, затем саммаризация
2. **Boolean flags система** - каждый сервис имеет флаг `is_categorized`, `is_summarized`
3. **Сингловый режим саммаризации** - каждый пост обрабатывается отдельно для качества
4. **Батчевая категоризация** - работает стабильно в batch режиме

```python
# Текущая последовательная архитектура
async def ai_processing_cycle():
    # Этап 1: Категоризация (батчевая)
    if has_uncategorized_posts():
        await process_categorization_batch()  # Работает в batch режиме
    
    # Этап 2: Саммаризация (сингловая)
    if has_unsummarized_posts():
        await process_summarization_single()  # По одному посту
```

**⚠️ Текущие ограничения:**
- **🔴 Нет параллельности**: сервисы работают последовательно
- **🔴 Медленная саммаризация**: каждый пост обрабатывается отдельно
- **🟡 Батчевая саммаризация не работает**: LLM игнорирует промпты в batch режиме
- **🟡 Увеличенное время обработки**: из-за отсутствия параллельности

**✅ Что работает стабильно:**
- Boolean Flags Architecture для атомарного управления статусами
- Endpoint `PUT /api/ai/results/sync-status` для независимых обновлений флагов
- Защита от Race Conditions с помощью asyncio.Lock()
- Качественная саммаризация в сингловом режиме

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

## 🖥️ Admin Panel UI Architecture

### **Структура интерфейса администратора**

Админ-панель организована в виде современного веб-приложения с боковой навигацией и многоуровневой архитектурой управления:

#### **📊 Dashboard**
- **Обзор системы:** статистика по всем ботам, каналам, пользователям
- **Recent Activity:** последние действия в системе
- **System Status:** состояние компонентов (Backend, Userbot, AI Services)
- **Quick Actions:** быстрые действия для администратора

#### **🏷️ Categories** 
- **CRUD операции:** создание, редактирование, удаление категорий
- **AI Prompts:** настройка промптов для категоризации контента
- **Статистика:** использование категорий по ботам и каналам

#### **📺 Channels**
- **Управление каналами:** добавление, настройка, мониторинг Telegram каналов
- **Валидация:** проверка доступности и корректности каналов
- **Статистика сбора:** метрики по количеству постов, ошибкам, последнему обновлению

#### **🤖 Public Bots** *(Новая секция - в разработке)*
**Многоуровневая архитектура управления тематическими ботами:**

##### **Уровень 1: Bot Management Dashboard**
```
┌─────────────────────────────────────────────────────────────┐
│ 🤖 Public Bots Management                    [+ Создать бота] │
├─────────────────────────────────────────────────────────────┤
│ 📊 Обзор: 12 активных • 3 в разработке • 2 приостановлены    │
│                                                             │
│ 🔍 [Поиск ботов...]  📂 [Все] [Активные] [Тестовые]        │
│                                                             │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│ │ 🇺🇸 USA News │ │ 🛡️ Military  │ │ 💰 Crypto    │ │ 🎭 Arts │ │
│ │ 1.2K users  │ │ 856 users   │ │ 2.1K users  │ │ 445 u.  │ │
│ │ 🟢 Активен  │ │ 🟡 Настройка │ │ 🟢 Активен  │ │ 🔴 Пауза │ │
│ │ 3 дайджеста │ │ 1 дайджест  │ │ 2 дайджеста │ │ 1 дайдж │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
└─────────────────────────────────────────────────────────────┘
```

##### **Уровень 2: Bot Configuration (3-колоночный layout)**
```
┌─────────────────────────────────────────────────────────────┐
│ ← Назад  🇺🇸 USA News Bot  [👁️ Превью] [🚀 Запустить]      │
├─────────────────────────────────────────────────────────────┤
│ 📋 Digest Settings │ 📺 Channels (45) │ 🏷️ Topics (12)     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 🎨 Tone of Voice & AI Prompts                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 📝 Custom AI Instructions                               │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ При анализе новостей из США учитывай:               │ │ │
│ │ │ - Фокус на влиянии на русскоязычную аудиторию      │ │ │
│ │ │ - Объясняй американские реалии простым языком      │ │ │
│ │ │ - Избегай излишней политизации                     │ │ │
│ │ │ - Подчеркивай экономические последствия            │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ │ 💡 Шаблоны: [Нейтральный] [Аналитический] [Популярный] │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ 📅 Delivery Schedule                                        │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ПН ВТ СР ЧТ ПТ СБ ВС                                   │ │
│ │ ✅ ✅ ✅ ✅ ✅ ❌ ❌                                   │ │
│ │                                                         │ │
│ │ 🌅 08:00 Утренний (15 постов, 200 символов)            │ │
│ │ 🌞 13:00 Дневной (10 постов, 150 символов)             │ │
│ │ 🌙 19:00 Вечерний (12 постов, 180 символов)            │ │
│ │ [+ Добавить время]                                      │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Ключевые особенности:**
- **Индивидуальные AI промпты:** каждый бот имеет уникальные инструкции для AI
- **Tone of Voice система:** предустановленные стили (Нейтральный, Аналитический, Популярный, Срочный, Экспертный)
- **Гибкое расписание:** настройка времени доставки дайджестов с индивидуальными параметрами
- **Bulk операции:** массовое управление каналами и категориями
- **Превью дайджестов:** предварительный просмотр результата AI обработки

#### **📊 Post Cache Monitor** 
**Двухтабовая архитектура для мониторинга постов:**

##### **📦 RAW POSTS** - Данные Userbot
- **Быстрый просмотр**: собранные данные из Telegram каналов без AI обработки
- **Статистика сбора**: метрики по каналам, времени сбора, ошибкам
- **Управление кешем**: очистка, фильтрация, поиск по содержимому
- **Производительность**: быстрая загрузка без JOIN'ов с AI данными
- **Общая статистика**: всего постов, используемых каналов, размер данных
##### **🧠 AI Results Viewer**
- **Просмотр AI анализа:** результаты обработки постов искусственным интеллектом
- **Метрики качества:** оценка точности категоризации и суммаризации
- **A/B тестирование:** сравнение разных AI моделей и промптов
- **Отладка:** диагностика проблем AI обработки


#### **⚙️ LLM Settings**
**Двухтабовая система настройки AI:**

##### **🌐 Глобальные настройки** - состоит из 3х аккордеонов:

###### **🧠 Выбор LLM Моделей** 
Индивидуальные настройки LLM для каждого AI сервиса:
- **Категоризация**: модель (gpt-4o-mini), max_tokens (1000), temperature (0.3)
- **Суммаризация**: модель (gpt-4o), max_tokens (2000), temperature (0.7), top_p (1.0)
- **Анализ**: модель (gpt-4o-mini), max_tokens (1500), temperature (0.5)
- **Расчет стоимости**: автоматический подсчет месячных затрат по моделям
- **Рекомендации**: подсказки по выбору оптимальных моделей для задач

###### **⚠️ Настройки дайджестов** [УСТАРЕВШИЕ - требуют ревизии]
- ~~Время генерации дайджестов~~ - **УСТАРЕЛО!** Теперь у каждого бота свое расписание
- ~~Максимальное количество постов в дайджесте~~ - **УСТАРЕЛО!** Должно быть настройкой каждого бота
- **Статус**: эти настройки нужно убрать из глобальных и добавить в индивидуальные настройки ботов

###### **🔧 Системные настройки** 
Общие параметры платформы (смешанное состояние):
- **Актуальные**: fallback значения для новых ботов, системные лимиты
- **Устаревшие**: параметры до перехода на мультитенантность ботов  
- **Требуют ревизии**: множество настроек нуждаются в классификации и очистке

##### **🤖 Шаблон Public Bot**
- **Дефолтные поля**: значения по умолчанию для новых публичных ботов
- **Delivery Schedule**: JSON структура расписания доставки по дням недели
- **AI Prompts**: шаблоны промптов для категоризации и саммаризации
- **⚠️ НУЖДАЕТСЯ В РЕВИЗИИ**: структура требует обновления под текущую архитектуру

#### **🛠️ Дополнительные компоненты:**
**Специализированные модули для расширенного управления:**

##### **🤖 Bot Configuration Components:**
- **BotConfigurationTabs**: многоуровневые настройки публичных ботов с табовой навигацией
- **BotDeliverySettings**: расписание и параметры доставки (сложные JSONB структуры)
- **BotChannelsManager**: управление каналами для конкретного бота
- **BotCategoriesManager**: управление категориями для конкретного бота
- **BotGeneralSettings**: основные настройки публичного бота

##### **📊 Data Management:**
- **BotSelector**: универсальный компонент фильтрации данных по публичным ботам
- **DataCleanup**: инструменты очистки и управления данными (сброс AI результатов, пересчет)
- **ChannelCategoriesDialog**: диалог управления связями канал-категория

##### **🧠 AI RESULTS** - Мультитенантные результаты (нуждается в доработке)
три аккордеона:
###### **AI Orchestrator и сервисы**: Управление AI Orchestrator
- **Фоновый процесс AI Orchestrator**
- **Мультитенантная статистика AI сервисов**
- **Детальная статистика AI Orchestrator**
###### **Мультитентальная Статистика по ботам**
- **Общая мультитенантная статистика**
- **Статистика по ботам** 
###### **Мультитентальные данные**
- **Статистика по ботам**
- ** Мультитенантная очистка данных**


### 🔧 Модернизированные компоненты

#### **Admin Panel новые секции:**

##### **Public Bots Management:**
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

##### **🎨 UI Infrastructure:**
- **Layout**: боковая навигация с адаптивным дизайном


### **📋 Актуальная структура навигации:**
```
🏠 Dashboard
📂 Categories  
📺 Channels
🤖 Public Bots
📊 Post Cache Monitor  ← двухтабовая архитектура
⚙️ LLM Settings       ← двухтабовая архитектура  
🧠 AI Results          ← отдельная страница
```

### **Техническая реализация UI:**
- **Framework:** React + Material UI (без TypeScript)
- **Архитектура:** Компонентная с переиспользуемыми элементами
- **Навигация:** Боковое меню с иконками (Layout.jsx)
- **Responsive Design:** Адаптивность для разных размеров экрана
- **API Integration:** REST API интеграция с localhost:8000

### **🗂️ Активные файлы компонентов:**
```
📁 pages/
├── DashboardPage.jsx                    ← основная
├── CategoriesPage.jsx                   ← основная
├── ChannelsPage.jsx                     ← основная  
├── PublicBotsPage.jsx                   ← основная
├── PostsCachePage_v2.jsx               ← АКТИВНАЯ версия
├── LLMSettingsPage_v4.jsx              ← АКТИВНАЯ версия
├── AIResultsPage.jsx                    ← основная
└── [множество _backup, _old версий]     ← архивные

📁 components/
├── Layout.jsx                           ← навигация
├── Posts/
│   ├── RawPostsTab.jsx                 ← таб RAW POSTS
│   ├── AIResultsTab.jsx                ← таб AI RESULTS  
│   └── BotSelector.jsx                 ← фильтр по ботам
└── [Bot* компоненты]                   ← управление ботами
```

### **⚠️ Техническое состояние:**
- **Множественные версии**: в pages/ есть много _backup, _v2, _v4 файлов
- **Активные версии**: PostsCachePage_v2.jsx, LLMSettingsPage_v4.jsx
- **Требует очистки**: архивные файлы можно перенести в /archive/

## 🎯 STAGE 1.5 Task 2: Settings Reorganization ✅ ЗАВЕРШЕНО

**Дата завершения**: 6/12/2025  
**Статус**: ✅ ЧАСТИЧНО ЗАВЕРШЕНО И ПРОТЕСТИРОВАНО, требует очистки и доработки

### Достижения Task 2:

#### 1. Архитектура Public Bots
- ✅ Создана революционная 2-уровневая архитектура управления ботами
- ✅ Bot Management Dashboard с карточками ботов и статистикой
- ✅ Bot Configuration с 3-колоночным layout (Digest Settings, Channels, Topics)
- ✅ Индивидуальные AI промпты для каждого бота (categorization_prompt, summarization_prompt)

#### 2. Сложная система расписания доставки
- ✅ JSONB `delivery_schedule` с поддержкой множественных доставок в день
- ✅ Индивидуальные параметры для каждого времени доставки
- ✅ Поддержка временных зон и именованных дайджестов
- ✅ Гибкое включение/отключение дней недели

#### 3. База данных
- ✅ Таблица `public_bots` 
- ✅ GIN индекс для JSONB поля delivery_schedule
- ✅ Полная совместимость с PostgreSQL

#### 4. Backend API
- ✅ Полный CRUD для Public Bots (/api/public-bots)
- ✅ Валидация уникальности имен ботов
- ✅ Toggle-status endpoint для быстрого управления
- ✅ Поддержка сложных JSONB запросов

#### 5. Frontend
- ✅ Современная страница Public Bots с карточным интерфейсом
- ✅ Реальная интеграция с API (loading states, error handling)
- ✅ Обновленная навигация (переименование "Posts Cache" → "Userbot")

#### 6. Тестирование
- ✅ Все CRUD операции протестированы и работают 
- ✅ Создание, чтение, обновление, удаление ботов
- ✅ Сложные расписания сохраняются и загружаются корректно
- ✅ Валидация и error handling функционируют

### Пример упрощенного расписания:
```json
{
  "monday": ["08:00", "19:00"],
  "tuesday": ["08:00", "19:00"], 
  "wednesday": ["08:00", "13:00", "19:00"],
  "thursday": ["08:00", "19:00"],
  "friday": ["08:00", "19:00"],
  "saturday": [],
  "sunday": []
}
```

**Принцип работы:**
- **Простое расписание** - только времена доставки по дням недели
- **Единые настройки бота** - все дайджесты используют одинаковые параметры (max_posts, max_summary_length, AI промпты)
- **Автоматическая генерация** - система сама определяет какие посты включить в дайджест на основе времени последней доставки

**Готовность этапа Task 3: Python AI Services**

## 🎯 Текущий статус проекта (7/10/2025)

### 📊 Готовность компонентов:
- **✅ Backend API**: 100% готов - полный CRUD, мультитенантность, все endpoints
- **✅ Admin Panel**: 95% готов - все основные функции, требуются UI улучшения
- **✅ Database**: 100% готов - PostgreSQL, все таблицы, индексы, миграции
- **✅ Userbot**: 100% готов - стабильный сбор данных, дедупликация
- **🟡 AI Services**: 80% готов - категоризация работает, саммаризация только в сингловом режиме
- **🟡 Public Bot**: 80% готов - базовый функционал работает, нет доставки по расписанию
- **🔴 AI Orchestrator**: 70% готов - работает последовательно, нет параллельности

### ⚠️ Текущие ограничения и проблемы:
- **🔴 Батчевая саммаризация не работает**: LLM игнорирует промпты в batch режиме, выдает однострочные ответы
- **🔴 Нет параллельности AI сервисов**: категоризация и саммаризация работают последовательно
- **🟡 Доставка по расписанию**: функция есть в админ-панели, но не реализована в публичном боте
- **🟡 UI доработки**: требуются улучшения интерфейса админ-панели
- **🟡 Индексы БД**: отложены до появления проблем с производительностью (10,000+ постов)

### 🚧 Текущий этап:
**✅ STAGE 1.5 Task 2 ЗАВЕРШЕН** (6/12/2025) - **Public Bots Management готов**
- **✅ Работающие компоненты:** Admin Panel, Backend API, Userbot, Public Bots Management
- **🚨 КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ:** N8N ПОЛНОСТЬЮ УДАЛЕН из проекта! Переход на кастомную Python AI обработку
- **🚧 Статус:** Готово к STAGE 1.5 Task 3 - создание Python AI Services

**🚀 СЛЕДУЮЩИЙ ЭТАП** - **Исправление технических долгов AI системы**

### Наследование vs Новая разработка

#### ✅ **Компоненты для ПОЛНОГО наследования:**
1. **Backend API (FastAPI)** - отлично спроектирован
   - **Готово:** CRUD для каналов/категорий, валидация, REST endpoints
   - **Добавить:** модели PublicBot, BotUser, UserSubscription, Billing

2. **Admin Panel (React + MUI)** - современный интерфейс  
   - **Готово:** компонентная архитектура, навигация, валидация
   - **Очистить и\или доработать:** секции Public Bots, LLM Settings, мониторинг постов

3. **Database схема** - хорошая основа PostgreSQL
   - **Готово:** channels, categories, digests, settings
   - **Добавить:** партиционирование, posts_cache, биллинг

#### 🔄 **Компоненты для АДАПТАЦИИ:**
4. **Userbot** - отработанная логика сбора
   - **Адаптировать:** centralized posts_cache, мультиканальный сбор
   - **усточивость к перезаливке повторяющихся постов или частичному обновлению:** оттестировать

5. **AI логика** - перенесено в Python модули
   

#### ❌ **Компоненты для ПОЛНОЙ ЗАМЕНЫ:**
6. **N8N workflows** → **Python AI Service** 
   - **Статус:** ❌ **N8N должен быть ПОЛНОСТЬЮ УДАЛЕН** (6/11/2025)
   - **Причина:** Batch processing нестабилен, ограничения по производительности
   - **Решение:** 3-слойная архитектура обработки данных

7. **Telegram-бот** → **Мультитенантная PublicBot система**
   - **Причина:** единый бот → множественные тематические боты с собственными аудиториями


### **Эволюция в мультитенантную (ДОБАВИТЬ уровень):**
```  
Каналы → Categories → PublicBots (выбирают каналы+категории) → AI под бота → BotUsers (подписки)
```

**⚠️ ВАЖНО:** Исправить терминологическую путаницу `Topics` → `Categories` везде в коде и интерфейсе!

## 🏗️ Новая 3-слойная архитектура обработки данных


### **3 СЛОЯ НОВОЙ АРХИТЕКТУРЫ DATAFLOW:**

#### **СЛОЙ 1: РЕДАКТУРА (Администратор)**
```
👨‍💼 Администратор управляет:
├── 🏷️ Категории (description, ai_prompt для категоризации)
├── 🤖 PublicBot конфигурация:
│   ├── categorization_prompt для AI CategorizationService
│   ├── summarization_prompt для AI SummarizationService  
│   ├── список каналов для бота
│   ├── список категорий для бота
│   └── доступные языки для бота
├── ⚙️ Параметры системы (глубина выборки, расписание)
└── 🌐 Мультиязычные настройки
```

#### **СЛОЙ 2: СБОР ДАННЫХ (Userbot)**
```
🤖 Userbot выполняет:
├── 📅 Планировочный сбор из ВСЕХ каналов (по расписанию) - предстоит сделать
├── ⚡ Real-time получение обновлений (если возможно) - предстоит сделать
├── 💾 Сохранение raw данных в centralized posts_cache
└── 🎯 Независимая работа от AI обработки
```

#### **СЛОЙ 3: ОБРАБОТКА ДАННЫХ (Python AI модуль)**
```
🧠 AI модуль создает для КАЖДОГО PublicBot индивидуальные данные:

📝 SummarizationService:
├── Генерирует саммари для каждого языка бота
├── Использует bot.summarization_prompt
└── Асинхронная обработка

🎯 CategorizationService:  
├── Определяет релевантные категории из списка бота
├── Оценивает релевантность (importance/urgency/value)
├── Использует bot.categorization_prompt
└── Независимая работа от SummarizationService

💾 Результат: processed_data партиционированная по public_bot_id
```

#### **СЛОЙ 4: ПОЛЬЗОВАТЕЛЬСКИЙ ИНТЕРФЕЙС (Telegram Bots)**
```
👤 Пользователь PublicBot:
├── 🎛️ Фильтрация по каналам (из списка бота)
├── 🏷️ Фильтрация по категориям (из списка бота)  
├── 📱 Получение персонализированных дайджестов
├── 💬 Обратная связь: (не готово, предстоит сделать)
│   ├── ⭐ Оценка каналов и категорий
│   ├── 📝 Оценка качества саммаризации
│   └── 🌐 Переключение языка
└── 💰 Премиум функции (по запросу, push уведомления, не готово, предстоит сделать) 
```

### **Ключевые преимущества новой архитектуры:**

#### **🎯 Индивидуальный Tone of Voice:**
- **"USA Digest":** формальный стиль, политический контекст
- **"Tech News":** технический жаргон, инновационный подход
- **"Cultural Pulse":** эмоциональный стиль, креативная подача

#### **⚡ Асинхронная обработка:**
- SummarizationService и CategorizationService работают независимо
- Можно использовать разные LLM модели (быстрые vs точные)
- Масштабирование по потребностям каждого бота

#### **💾 Эффективное хранение:**
- Общий posts_cache для всех ботов (экономия места)
- Индивидуальная processed_data для каждого бота (персонализация)
- Партиционирование по public_bot_id для производительности

## 📋 План разработки Stage 6

### **Приоритетные задачи для исправления:**

#### **🔧 Исправление технических долгов:**
- **Task 0.7**: Исправление батчевой саммаризации - исследовать альтернативные подходы к промптам
- **Task 0.8**: Реализация параллельности AI Orchestrator - независимые worker'ы для каждого сервиса
- **Task 0.9**: Доставка по расписанию в публичном боте - интеграция с delivery_schedule из БД
- **Task 0.10**: UI улучшения админ-панели - оптимизация интерфейса и UX

#### **🏗️ Новая структура БД (единая PostgreSQL с партиционированием):**

##### **🤖 Таблица public_bots - ОБНОВЛЕННАЯ СТРУКТУРА (6/12/2025):**
```sql
-- 1. PublicBots конфигурация с РАСШИРЕННЫМ РАСПИСАНИЕМ ДОСТАВКИ
CREATE TABLE public_bots (
    id SERIAL PRIMARY KEY,
    
    -- Основная информация
    name VARCHAR NOT NULL,
    description TEXT,
    status VARCHAR DEFAULT 'setup',
    
    -- Telegram Bot данные
    bot_token VARCHAR,                    -- Токен Telegram бота
    welcome_message TEXT,                 -- Приветственное сообщение
    default_language VARCHAR DEFAULT 'ru', -- Язык по умолчанию
    
    -- Digest Settings (базовые)
    max_posts_per_digest INTEGER DEFAULT 10,
    max_summary_length INTEGER DEFAULT 150,
    
    -- AI Prompts (разделенные по функциям)
    categorization_prompt TEXT,           -- Промпт для категоризации постов
    summarization_prompt TEXT,            -- Промпт для суммаризации (включает tone of voice)
    
    -- СЛОЖНОЕ РАСПИСАНИЕ ДОСТАВКИ (НОВАЯ АРХИТЕКТУРА)
    delivery_schedule JSONB DEFAULT '{
        "monday": {
            "enabled": true,
            "times": [
                {"time": "08:00", "max_posts": 15, "max_summary_length": 200, "name": "Утренний"},
                {"time": "13:00", "max_posts": 10, "max_summary_length": 150, "name": "Дневной"},
                {"time": "19:00", "max_posts": 12, "max_summary_length": 180, "name": "Вечерний"}
            ]
        },
        "tuesday": {"enabled": true, "times": [{"time": "08:00", "max_posts": 15, "max_summary_length": 200, "name": "Утренний"}]},
        "wednesday": {"enabled": true, "times": [{"time": "08:00", "max_posts": 15, "max_summary_length": 200, "name": "Утренний"}]},
        "thursday": {"enabled": true, "times": [{"time": "08:00", "max_posts": 15, "max_summary_length": 200, "name": "Утренний"}]},
        "friday": {"enabled": true, "times": [{"time": "08:00", "max_posts": 15, "max_summary_length": 200, "name": "Утренний"}]},
        "saturday": {"enabled": false, "times": []},
        "sunday": {"enabled": false, "times": []}
    }',
    
    -- Timezone для корректного расчета времени доставки
    timezone VARCHAR DEFAULT 'Europe/Moscow',
    
    -- Legacy поля для совместимости
    digest_generation_time VARCHAR DEFAULT '09:00',  -- Основное время (для простых случаев)
    digest_schedule VARCHAR DEFAULT 'daily',         -- Простое расписание (daily/weekly)
    
    -- Statistics
    users_count INTEGER DEFAULT 0,
    digests_count INTEGER DEFAULT 0,
    channels_count INTEGER DEFAULT 0,
    topics_count INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Индексы для производительности
CREATE INDEX idx_public_bots_name ON public_bots(name);
CREATE INDEX idx_public_bots_status ON public_bots(status);
CREATE INDEX idx_public_bots_token ON public_bots(bot_token);
CREATE INDEX idx_public_bots_schedule ON public_bots USING GIN (delivery_schedule);
```

##### **📅 Структура delivery_schedule (JSONB):**
```json
{
  "monday": {
    "enabled": true,
    "times": [
      {
        "time": "08:00",                    // Время доставки (HH:MM)
        "max_posts": 15,                    // Максимум постов для этого времени
        "max_summary_length": 200,          // Максимальная длина резюме
        "name": "Утренний дайджест"         // Название дайджеста
      },
      {
        "time": "13:00",
        "max_posts": 10,
        "max_summary_length": 150,
        "name": "Дневные новости"
      },
      {
        "time": "19:00",
        "max_posts": 12,
        "max_summary_length": 180,
        "name": "Вечерняя сводка"
      }
    ]
  },
  "tuesday": {
    "enabled": true,
    "times": [
      {"time": "08:00", "max_posts": 15, "max_summary_length": 200, "name": "Утренний"}
    ]
  },
  "saturday": {
    "enabled": false,                       // День отключен
    "times": []                             // Нет доставок
  },
  "sunday": {
    "enabled": false,
    "times": []
  }
}
```

##### **🎯 Возможности сложного расписания:**
- **Индивидуальные настройки по дням недели** - разные расписания для будних/выходных
- **Множественные времена доставки в день** - утром, днем, вечером
- **Разные параметры для каждого времени** - количество постов, длина резюме
- **Именованные дайджесты** - "Утренний", "Дневной", "Вечерний"
- **Поддержка временных зон** - корректная доставка по местному времени
- **Гибкое включение/выключение дней** - можно отключить выходные
- **JSON структура для легкого расширения** - добавление новых параметров
- **GIN индекс для быстрых запросов** - эффективный поиск по расписанию

##### **💡 Примеры использования:**
```sql
-- Найти всех ботов с доставкой в понедельник в 08:00
SELECT * FROM public_bots 
WHERE delivery_schedule->'monday'->>'enabled' = 'true'
AND delivery_schedule->'monday'->'times' @> '[{"time": "08:00"}]';

-- Получить все времена доставки для бота в понедельник
SELECT jsonb_array_elements(delivery_schedule->'monday'->'times') 
FROM public_bots WHERE id = 1;

-- Найти ботов с отключенными выходными
SELECT name FROM public_bots 
WHERE delivery_schedule->'saturday'->>'enabled' = 'false'
AND delivery_schedule->'sunday'->>'enabled' = 'false';
```

-- 2. Связи ботов с каналами и категориями (Many-to-Many)
CREATE TABLE bot_channels (
    bot_id INTEGER REFERENCES public_bots(id) ON DELETE CASCADE,
    channel_id INTEGER REFERENCES channels(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (bot_id, channel_id)
);

CREATE TABLE bot_categories (  
    bot_id INTEGER REFERENCES public_bots(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 0,           -- Приоритет категории для бота
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (bot_id, category_id)
);

-- 3. Централизованный кеш постов (RAW данные от Userbot)
CREATE TABLE posts_cache (
    id BIGSERIAL PRIMARY KEY,
    channel_id INTEGER REFERENCES channels(id),
    telegram_message_id BIGINT,
    content TEXT,
    media_type VARCHAR(50),
    media_url TEXT,
    views INTEGER DEFAULT 0,
    posted_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT NOW(),
    retention_until TIMESTAMP,           -- Автоматическое удаление
    UNIQUE(channel_id, telegram_message_id)
) PARTITION BY RANGE (posted_at);       -- Партиционирование по дате

-- 4. Processed данные для каждого PublicBot (результаты AI обработки)
CREATE TABLE processed_data (
    id BIGSERIAL,
    post_id BIGINT REFERENCES posts_cache(id),
    public_bot_id INTEGER REFERENCES public_bots(id),
    summaries JSONB NOT NULL,            -- {ru: "краткое содержание", en: "summary"}
    categories JSONB NOT NULL,           -- {categories: ["Политика"], relevance_scores: [0.95]}
    metrics JSONB NOT NULL,              -- {importance: 8, urgency: 6, value: 9}
    processed_at TIMESTAMP DEFAULT NOW(),
    processing_version VARCHAR(50) DEFAULT 'v1.0',
    UNIQUE(post_id, public_bot_id)       -- Один processed record на пост-бот пару
) PARTITION BY HASH (public_bot_id);    -- Партиционирование по ботам

-- 5. Пользователи мультитенантных ботов
CREATE TABLE bot_users (
    id BIGSERIAL PRIMARY KEY,
    public_bot_id INTEGER REFERENCES public_bots(id),
    telegram_user_id BIGINT NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    preferred_language VARCHAR(10) DEFAULT 'ru',
    timezone VARCHAR(50) DEFAULT 'Europe/Moscow',
    subscription_tier VARCHAR(50) DEFAULT 'free', -- free, premium, enterprise
    balance DECIMAL(10,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(public_bot_id, telegram_user_id)
);

-- 6. Подписки пользователей на каналы и категории внутри бота
CREATE TABLE user_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES bot_users(id) ON DELETE CASCADE,
    subscription_type VARCHAR(20) NOT NULL, -- 'channel' или 'category'
    target_id INTEGER NOT NULL,             -- channel_id или category_id
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, subscription_type, target_id)
);

-- 7. LLM Providers система
CREATE TABLE llm_providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,   -- "openai", "anthropic", "local"
    display_name VARCHAR(255),           -- "OpenAI GPT-4"
    api_endpoint VARCHAR(500),
    auth_type VARCHAR(50),               -- "bearer", "api_key", "none"
    models JSONB DEFAULT '[]',           -- Список доступных моделей
    rate_limits JSONB DEFAULT '{}',     -- Лимиты API
    pricing JSONB DEFAULT '{}',         -- Стоимость за токен
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE llm_settings (
    id SERIAL PRIMARY KEY,
    bot_id INTEGER REFERENCES public_bots(id) ON DELETE CASCADE,
    provider_id INTEGER REFERENCES llm_providers(id),
    model_name VARCHAR(255),
    max_tokens INTEGER DEFAULT 4000,
    temperature DECIMAL(3,2) DEFAULT 0.3,
    custom_params JSONB DEFAULT '{}',
    monthly_budget DECIMAL(10,2),       -- Лимит бюджета
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(bot_id)                      -- Один LLM на бота
);

-- 8. Биллинг система
CREATE TABLE billing_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES bot_users(id) ON DELETE CASCADE,
    bot_id INTEGER REFERENCES public_bots(id),
    transaction_type VARCHAR(50) NOT NULL,  -- subscription, on_demand, refund
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50) DEFAULT 'pending',   -- pending, completed, failed, refunded
    payment_provider VARCHAR(100),
    provider_transaction_id VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_billing_user ON billing_transactions (user_id, created_at);
CREATE INDEX idx_billing_bot ON billing_transactions (bot_id, created_at);
CREATE INDEX idx_billing_status ON billing_transactions (status, created_at);
```

#### **⚙️ Индексы и партиционирование:**
```sql
-- Индексы для производительности
CREATE INDEX idx_posts_cache_channel_time ON posts_cache (channel_id, posted_at);
CREATE INDEX idx_posts_cache_collected ON posts_cache (collected_at);
CREATE INDEX idx_posts_cache_retention ON posts_cache (retention_until);

CREATE INDEX idx_processed_data_bot_time ON processed_data (public_bot_id, processed_at);
CREATE INDEX idx_processed_data_post ON processed_data (post_id);
CREATE INDEX idx_processed_summaries_gin ON processed_data USING gin (summaries);
CREATE INDEX idx_processed_categories_gin ON processed_data USING gin (categories);

CREATE INDEX idx_bot_users_telegram ON bot_users (public_bot_id, telegram_user_id);
CREATE INDEX idx_user_subscriptions_user ON user_subscriptions (user_id, subscription_type);

-- Партиционирование posts_cache (по месяцам)
CREATE TABLE posts_cache_2025_06 PARTITION OF posts_cache 
    FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');
CREATE TABLE posts_cache_2025_07 PARTITION OF posts_cache 
    FOR VALUES FROM ('2025-07-01') TO ('2025-08-01');

-- Партиционирование processed_data (по ботам)
CREATE TABLE processed_data_0 PARTITION OF processed_data FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE processed_data_1 PARTITION OF processed_data FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE processed_data_2 PARTITION OF processed_data FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE processed_data_3 PARTITION OF processed_data FOR VALUES WITH (MODULUS 4, REMAINDER 3);
```

#### **🔄 Миграции от текущей схемы:**
- Rename `topics` → `categories` (терминологическая унификация)
- Migrate `digests` table данные в новую `processed_data` структуру  
- Создание начальных LLM провайдеров (OpenAI, Anthropic)
- Обновление Backend API models под новую схему

### **Перспективные задачи развития:**

#### **🔬 Исследование и улучшения:**
- **Векторизация и кластеризация**: мета-уровень AI сервис для создания динамических кластеров тем
- **Индексы БД**: создание индексов для оптимизации при 10,000+ постов
- **Расширение UI**: дополнительные функции админ-панели
#### **🎯 Перспективные направления:**
- **Монетизация**: биллинг система, тарифные планы
- **Аналитика**: cross-bot метрики, revenue optimization
- **Масштабирование**: queue management, real-time processing

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
  - **Статус:** ✅ **ПОЛНОСТЬЮ УДАЛЕН** (6/11/2025)
  - **Причина:** Нестабильный batch processing, ограниченные возможности debugging
  - **Решение:** Асинхронные Python микросервисы для AI обработки

## 🗄️ Новая архитектура базы данных

### **Мультитенантные таблицы:**

```sql
-- Публичные боты платформы
CREATE TABLE public_bots (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    telegram_bot_token VARCHAR(500) NOT NULL,
    telegram_username VARCHAR(255),       -- @usa_digest_bot
    summarization_prompt TEXT NOT NULL,
    categorization_prompt TEXT NOT NULL,
    supported_languages TEXT[] DEFAULT '{"ru"}',
    branding JSONB DEFAULT '{}',          -- Логотип, цвета, стиль
    is_active BOOLEAN DEFAULT true,
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

-- Централизованный кеш постов (RAW данные от Userbot)
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
    retention_until TIMESTAMP,           -- Автоматическое удаление
    INDEX(channel_id, posted_at),
    INDEX(collected_at),
    INDEX(retention_until)
) PARTITION BY RANGE (posted_at);       -- Партиционирование по дате

-- Processed данные для каждого PublicBot (результаты AI обработки)
CREATE TABLE processed_data (
    id BIGSERIAL,
    post_id BIGINT REFERENCES posts_cache(id),
    public_bot_id INTEGER REFERENCES public_bots(id),
    summaries JSONB NOT NULL,            -- {ru: "краткое содержание", en: "summary"}
    categories JSONB NOT NULL,           -- {categories: ["Политика"], relevance_scores: [0.95]}
    metrics JSONB NOT NULL,              -- {importance: 8, urgency: 6, value: 9}
    processed_at TIMESTAMP DEFAULT NOW(),
    processing_version VARCHAR(50) DEFAULT 'v1.0',
    UNIQUE(post_id, public_bot_id),      -- Один processed record на пост-бот пару
    INDEX(public_bot_id, processed_at),
    INDEX(post_id)
) PARTITION BY HASH (public_bot_id);    -- Партиционирование по ботам

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



### **Python AI Service архитектура:**

#### **🧠 AI Services (CategorizationService + SummarizationService)**
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
```

#### **🎯 AI Orchestrator - Умное управление AI обработкой**

**Основные принципы:**
- **🚀 Умный запуск** с проверкой необработанных данных при старте системы
- **📊 Приоритизация задач** по активности ботов и времени дайджестов
- **🚨 Система прерываний** для критических операций (новые данные, пользовательские запросы)
- **🔄 Батч обработка до 30 постов** с автоматическим fallback на отдельные посты
- **📡 Реактивная обработка** новых данных от Userbot
- **📊 Полный мониторинг** с уведомлениями о перегрузке LLM

**Приоритеты задач:**
```
CRITICAL (5)  - Принудительные операции, новые данные
URGENT (4)    - Пользовательские запросы  
HIGH (3)      - Активные боты, скорые дайджесты
NORMAL (2)    - Плановая обработка
BACKGROUND (1) - Фоновые задачи
```

**📖 Подробная документация:** [AI Orchestrator Architecture](docs/AI_ORCHESTRATOR_ARCHITECTURE.md)

```python
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

---

## 🔗 Запуск текущей системы (ОБНОВЛЕННАЯ АРХИТЕКТУРА)

### Пошаговый запуск всех компонентов

#### 1. Backend API (первым делом)
```bash
cd C:\Work\MorningStarBot3\backend
python main.py
```
**Результат:** API на `http://localhost:8000` + Swagger документация

#### 2. Admin Panel (веб-интерфейс)
```bash
cd C:\Work\MorningStarBot3\frontend\admin-panel
npm install && npm run dev
```
**Результат:** Веб-интерфейс на `http://localhost:3000`

#### 3. AI Services (Python модуль)
```bash
cd C:\Work\MorningStarBot3\ai_services
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001
```
**Результат:** AI Services на `http://localhost:8001`

#### 4. Публичный Telegram-бот
```bash
cd C:\Work\MorningStarBot3\bot
python src/bot.py
```

#### 5. Userbot (сбор контента)
```bash
cd C:\Work\MorningStarBot3\userbot  
python src/bot.py
```

### End-to-End проверка системы:
✅ Backend API → ✅ Admin Panel → ✅ AI Services → ✅ Публичный бот → ✅ Userbot

**⚠️ Примечание:** AI Services работают в последовательном режиме из-за проблем с батчевой саммаризацией
