from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import Dict, Any, Union

# Загрузка переменных окружения
load_dotenv()

# Настройка базы данных
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.dirname(os.path.abspath(__file__))}/morningstar.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# FastAPI приложение
app = FastAPI(
    title="MorningStar Admin API",
    description="API для админ-панели MorningStar Bot",
    version="1.0.0"
)

# CORS middleware для админ-панели
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели SQLAlchemy
channel_categories = Table(
    'channel_categories', Base.metadata,
    Column('channel_id', Integer, ForeignKey('channels.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    emoji = Column(String, default="📝")
    is_active = Column(Boolean, default=True)
    ai_prompt = Column(Text)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связи
    channels = relationship("Channel", secondary=channel_categories, back_populates="categories")

class Channel(Base):
    __tablename__ = "channels"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    title = Column(String, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    last_parsed = Column(DateTime)
    error_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связи
    categories = relationship("Category", secondary=channel_categories, back_populates="channels")

class ConfigSetting(Base):
    __tablename__ = "config_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(Text)
    value_type = Column(String, default="string")  # string, integer, boolean, float, json
    category = Column(String)
    description = Column(Text)
    is_editable = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Функция для создания начальных настроек
def create_default_settings():
    """Создать начальные настройки системы"""
    db = SessionLocal()
    try:
        # Получаем список существующих ключей настроек
        existing_keys = {setting.key for setting in db.query(ConfigSetting).all()}
        print(f"Найдено существующих настроек: {len(existing_keys)}")
        print(f"Существующие ключи: {existing_keys}")
        
        default_settings = [
            {
                "key": "CHECK_INTERVAL",
                "value": "30",
                "value_type": "integer",
                "category": "system",
                "description": "Интервал проверки каналов в минутах",
                "is_editable": True
            },
            {
                "key": "MAX_POSTS_PER_DIGEST",
                "value": "10",
                "value_type": "integer",
                "category": "digest",
                "description": "Максимальное количество постов в дайджесте",
                "is_editable": True
            },
            {
                "key": "DIGEST_GENERATION_TIME",
                "value": "09:00",
                "value_type": "string",
                "category": "digest",
                "description": "Время генерации дайджестов",
                "is_editable": True
            },
            {
                "key": "AI_MODEL",
                "value": "gpt-4",
                "value_type": "string",
                "category": "ai",
                "description": "Модель AI для обработки контента",
                "is_editable": True
            },
            {
                "key": "MAX_SUMMARY_LENGTH",
                "value": "150",
                "value_type": "integer",
                "category": "ai",
                "description": "Максимальная длина summary в символах",
                "is_editable": True
            },
            {
                "key": "ENABLE_NOTIFICATIONS",
                "value": "true",
                "value_type": "boolean",
                "category": "system",
                "description": "Включить уведомления администратора",
                "is_editable": True
            },
            {
                "key": "LOG_LEVEL",
                "value": "INFO",
                "value_type": "string",
                "category": "system",
                "description": "Уровень логирования (DEBUG, INFO, WARNING, ERROR)",
                "is_editable": True
            },
            {
                "key": "BACKUP_RETENTION_DAYS",
                "value": "30",
                "value_type": "integer",
                "category": "system",
                "description": "Количество дней хранения резервных копий",
                "is_editable": True
            },
            {
                "key": "COLLECTION_DEPTH_DAYS",
                "value": "3",
                "value_type": "integer",
                "category": "system",
                "description": "Сколько дней назад собирать посты из каналов",
                "is_editable": True
            },
            {
                "key": "MAX_POSTS_PER_CHANNEL",
                "value": "50",
                "value_type": "integer",
                "category": "system",
                "description": "Максимальное количество постов с одного канала",
                "is_editable": True
            },
            {
                "key": "MAX_POSTS_FOR_AI_ANALYSIS",
                "value": "10",
                "value_type": "integer",
                "category": "ai",
                "description": "Максимальное количество постов для AI анализа",
                "is_editable": True
            }
        ]
        
        # Добавляем только отсутствующие настройки
        added_count = 0
        for setting_data in default_settings:
            if setting_data["key"] not in existing_keys:
                db_setting = ConfigSetting(**setting_data)
                db.add(db_setting)
                added_count += 1
                print(f"Добавлена настройка: {setting_data['key']}")
        
        if added_count > 0:
            db.commit()
            print(f"Добавлено {added_count} новых настроек")
        else:
            print("Все настройки уже существуют")
        
    except Exception as e:
        print(f"Ошибка при создании начальных настроек: {e}")
        db.rollback()
    finally:
        db.close()

# Создаем начальные настройки при запуске
create_default_settings()

# Pydantic модели
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    emoji: str = Field("📝", max_length=10)
    is_active: bool = True
    ai_prompt: Optional[str] = None
    sort_order: int = 0

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ChannelBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: bool = True

class ChannelCreate(ChannelBase):
    pass

class ChannelUpdate(ChannelBase):
    pass

class ChannelResponse(ChannelBase):
    id: int
    last_parsed: Optional[datetime] = None
    error_count: int = 0
    created_at: datetime
    updated_at: datetime
    categories: List['CategoryResponse'] = []
    
    class Config:
        from_attributes = True

class ConfigSettingBase(BaseModel):
    key: str = Field(..., min_length=1, max_length=255)
    value: Optional[str] = None
    value_type: str = Field("string", pattern="^(string|integer|boolean|float|json)$")
    category: Optional[str] = None
    description: Optional[str] = None
    is_editable: bool = True

class ConfigSettingCreate(ConfigSettingBase):
    pass

class ConfigSettingUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None
    is_editable: Optional[bool] = None

class ConfigSettingResponse(ConfigSettingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ConfigManager класс
class ConfigManager:
    def __init__(self, db: Session):
        self.db = db
        self.env_vars = dict(os.environ)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение конфигурации из .env или БД"""
        # Сначала проверяем .env (приоритет для секретных данных)
        if key in self.env_vars:
            return self.env_vars[key]
        
        # Затем проверяем БД
        db_setting = self.db.query(ConfigSetting).filter(ConfigSetting.key == key).first()
        if db_setting:
            return self._parse_value(db_setting.value, db_setting.value_type)
        
        return default
    
    def set_db_setting(self, key: str, value: str, value_type: str = "string") -> ConfigSetting:
        """Обновить или создать настройку в БД"""
        db_setting = self.db.query(ConfigSetting).filter(ConfigSetting.key == key).first()
        if db_setting:
            db_setting.value = value
            db_setting.value_type = value_type
            db_setting.updated_at = func.now()
        else:
            db_setting = ConfigSetting(key=key, value=value, value_type=value_type)
            self.db.add(db_setting)
        
        self.db.commit()
        self.db.refresh(db_setting)
        return db_setting
    
    def _parse_value(self, value: str, value_type: str) -> Any:
        """Парсинг значения в соответствии с типом"""
        if value is None:
            return None
        
        try:
            if value_type == "integer":
                return int(value)
            elif value_type == "boolean":
                return value.lower() in ("true", "1", "yes", "on")
            elif value_type == "float":
                return float(value)
            elif value_type == "json":
                import json
                return json.loads(value)
            else:  # string
                return value
        except (ValueError, json.JSONDecodeError):
            return value  # возвращаем как строку если парсинг не удался

# Зависимости
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API Routes для категорий
@app.get("/api/categories", response_model=List[CategoryResponse])
def get_categories(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """Получить список категорий с возможностью поиска и фильтрации"""
    query = db.query(Category)
    
    if active_only:
        query = query.filter(Category.is_active == True)
    
    if search:
        query = query.filter(Category.name.contains(search))
    
    categories = query.order_by(Category.sort_order, Category.name).offset(skip).limit(limit).all()
    return categories

@app.post("/api/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """Создать новую категорию"""
    # Проверяем уникальность имени
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Категория с таким именем уже существует"
        )
    
    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@app.get("/api/categories/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Получить категорию по ID"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    return category

@app.put("/api/categories/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, category: CategoryUpdate, db: Session = Depends(get_db)):
    """Обновить категорию"""
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    
    # Проверяем уникальность имени (исключая текущую категорию)
    existing = db.query(Category).filter(
        Category.name == category.name,
        Category.id != category_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Категория с таким именем уже существует"
        )
    
    for field, value in category.model_dump().items():
        setattr(db_category, field, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

@app.delete("/api/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Удалить категорию"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    
    db.delete(category)
    db.commit()
    return {"message": "Категория успешно удалена"}

# API Routes для каналов
@app.get("/api/channels", response_model=List[ChannelResponse])
def get_channels(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """Получить список каналов с возможностью поиска и фильтрации"""
    from sqlalchemy.orm import selectinload
    
    query = db.query(Channel).options(selectinload(Channel.categories))
    
    if active_only:
        query = query.filter(Channel.is_active == True)
    
    if search:
        query = query.filter(
            Channel.title.contains(search) | 
            Channel.username.contains(search)
        )
    
    channels = query.order_by(Channel.title).offset(skip).limit(limit).all()
    return channels

@app.post("/api/channels", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
def create_channel(channel: ChannelCreate, db: Session = Depends(get_db)):
    """Создать новый канал"""
    # Проверяем уникальность telegram_id
    existing = db.query(Channel).filter(Channel.telegram_id == channel.telegram_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Канал с таким Telegram ID уже существует"
        )
    
    db_channel = Channel(**channel.model_dump())
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    return db_channel

@app.get("/api/channels/{channel_id}", response_model=ChannelResponse)
def get_channel(channel_id: int, db: Session = Depends(get_db)):
    """Получить канал по ID"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Канал не найден"
        )
    return channel

@app.put("/api/channels/{channel_id}", response_model=ChannelResponse)
def update_channel(channel_id: int, channel: ChannelUpdate, db: Session = Depends(get_db)):
    """Обновить канал"""
    db_channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not db_channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Канал не найден"
        )
    
    # Проверяем уникальность telegram_id (исключая текущий канал)
    existing = db.query(Channel).filter(
        Channel.telegram_id == channel.telegram_id,
        Channel.id != channel_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Канал с таким Telegram ID уже существует"
        )
    
    for field, value in channel.model_dump().items():
        setattr(db_channel, field, value)
    
    db.commit()
    db.refresh(db_channel)
    return db_channel

@app.delete("/api/channels/{channel_id}")
def delete_channel(channel_id: int, db: Session = Depends(get_db)):
    """Удалить канал"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Канал не найден"
        )
    
    db.delete(channel)
    db.commit()
    return {"message": "Канал успешно удален"}

# Дополнительные endpoints
@app.get("/api/health")
def health_check():
    """Проверка состояния API"""
    return {"status": "ok", "timestamp": datetime.now()}

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """Получить базовую статистику"""
    categories_count = db.query(Category).count()
    channels_count = db.query(Channel).count()
    active_categories = db.query(Category).filter(Category.is_active == True).count()
    active_channels = db.query(Channel).filter(Channel.is_active == True).count()
    
    # Статистика связей
    total_links = db.query(channel_categories).count()
    
    return {
        "categories": {
            "total": categories_count,
            "active": active_categories
        },
        "channels": {
            "total": channels_count,
            "active": active_channels
        },
        "channel_category_links": total_links
    }

# API для управления связями канал-категория
@app.get("/api/channels/{channel_id}/categories", response_model=List[CategoryResponse])
def get_channel_categories(channel_id: int, db: Session = Depends(get_db)):
    """Получить все категории для конкретного канала"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Канал не найден"
        )
    return channel.categories

@app.post("/api/channels/{channel_id}/categories/{category_id}")
def add_category_to_channel(channel_id: int, category_id: int, db: Session = Depends(get_db)):
    """Добавить категорию к каналу"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Канал не найден"
        )
    
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    
    # Проверяем, что связь еще не существует
    if category in channel.categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Категория уже привязана к этому каналу"
        )
    
    channel.categories.append(category)
    db.commit()
    
    return {"message": "Категория успешно добавлена к каналу"}

@app.delete("/api/channels/{channel_id}/categories/{category_id}")
def remove_category_from_channel(channel_id: int, category_id: int, db: Session = Depends(get_db)):
    """Удалить категорию от канала"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Канал не найден"
        )
    
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    
    # Проверяем, что связь существует
    if category not in channel.categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Категория не привязана к этому каналу"
        )
    
    channel.categories.remove(category)
    db.commit()
    
    return {"message": "Категория успешно удалена от канала"}

@app.get("/api/categories/{category_id}/channels", response_model=List[ChannelResponse])
def get_category_channels(category_id: int, db: Session = Depends(get_db)):
    """Получить все каналы для конкретной категории"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    return category.channels

# API для настроек системы
@app.get("/api/settings", response_model=List[ConfigSettingResponse])
def get_settings(
    category: Optional[str] = None,
    editable_only: bool = False,
    db: Session = Depends(get_db)
):
    """Получить список настроек с возможностью фильтрации"""
    query = db.query(ConfigSetting)
    
    if category:
        query = query.filter(ConfigSetting.category == category)
    
    if editable_only:
        query = query.filter(ConfigSetting.is_editable == True)
    
    settings = query.order_by(ConfigSetting.category, ConfigSetting.key).all()
    return settings

@app.get("/api/settings/categories")
def get_setting_categories():
    """Получить список всех категорий настроек"""
    # Временная заглушка с основными категориями
    return {"categories": ["system", "digest", "ai"]}

@app.post("/api/settings", response_model=ConfigSettingResponse, status_code=status.HTTP_201_CREATED)
def create_setting(setting: ConfigSettingCreate, db: Session = Depends(get_db)):
    """Создать новую настройку"""
    # Проверяем уникальность ключа
    existing = db.query(ConfigSetting).filter(ConfigSetting.key == setting.key).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Настройка с таким ключом уже существует"
        )
    
    db_setting = ConfigSetting(**setting.model_dump())
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

@app.get("/api/settings/{setting_id}", response_model=ConfigSettingResponse)
def get_setting(setting_id: int, db: Session = Depends(get_db)):
    """Получить настройку по ID"""
    setting = db.query(ConfigSetting).filter(ConfigSetting.id == setting_id).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Настройка не найдена"
        )
    return setting

@app.put("/api/settings/{setting_id}", response_model=ConfigSettingResponse)
def update_setting(setting_id: int, setting: ConfigSettingUpdate, db: Session = Depends(get_db)):
    """Обновить настройку"""
    db_setting = db.query(ConfigSetting).filter(ConfigSetting.id == setting_id).first()
    if not db_setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Настройка не найдена"
        )
    
    # Обновляем только предоставленные поля
    for field, value in setting.model_dump(exclude_unset=True).items():
        setattr(db_setting, field, value)
    
    db.commit()
    db.refresh(db_setting)
    return db_setting

@app.delete("/api/settings/{setting_id}")
def delete_setting(setting_id: int, db: Session = Depends(get_db)):
    """Удалить настройку"""
    setting = db.query(ConfigSetting).filter(ConfigSetting.id == setting_id).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Настройка не найдена"
        )
    
    db.delete(setting)
    db.commit()
    return {"message": "Настройка успешно удалена"}

# Endpoint для получения конфигурации через ConfigManager
@app.get("/api/config/{key}")
def get_config_value(key: str, db: Session = Depends(get_db)):
    """Получить значение конфигурации через ConfigManager"""
    config = ConfigManager(db)
    value = config.get(key)
    
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Конфигурация не найдена"
        )
    
    return {"key": key, "value": value}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 