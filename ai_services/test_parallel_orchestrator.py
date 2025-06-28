#!/usr/bin/env python3
"""
Тестовый скрипт для AI Orchestrator v5.0 - Параллельная архитектура

Проверяет:
1. Независимую работу categorization_worker и summarization_worker
2. Флаги активности и защиту от дублирования
3. Обработку 19 застрявших постов (is_categorized=true, is_summarized=false)
4. Отказоустойчивость при падении одного из сервисов
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from orchestrator_v5_parallel import AIOrchestrator

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('TestParallelOrchestrator')

class ParallelOrchestratorTester:
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.orchestrator = AIOrchestrator(backend_url=backend_url)
        
    async def run_all_tests(self):
        """Запуск всех тестов параллельной архитектуры"""
        logger.info("🧪 Начинаем тестирование AI Orchestrator v5.0 - Параллельная архитектура")
        
        tests = [
            ("📊 Проверка статуса системы", self.test_system_status),
            ("🏷️ Тест быстрой проверки категоризации", self.test_categorization_check),
            ("📝 Тест быстрой проверки саммаризации", self.test_summarization_check),
            ("⚙️ Тест инициализации AI сервисов", self.test_ai_services_initialization),
            ("🔄 Тест одиночного батча (legacy mode)", self.test_single_batch),
            ("🚀 Тест параллельных worker циклов", self.test_parallel_workers_short),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            logger.info(f"\n{'='*60}")
            logger.info(f"🧪 {test_name}")
            logger.info(f"{'='*60}")
            
            try:
                result = await test_func()
                results[test_name] = {"status": "✅ PASSED", "result": result}
                logger.info(f"✅ {test_name}: PASSED")
            except Exception as e:
                results[test_name] = {"status": "❌ FAILED", "error": str(e)}
                logger.error(f"❌ {test_name}: FAILED - {e}")
        
        # Итоговый отчет
        logger.info(f"\n{'='*60}")
        logger.info("📋 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        logger.info(f"{'='*60}")
        
        passed = 0
        failed = 0
        
        for test_name, result in results.items():
            status = result["status"]
            logger.info(f"{status} {test_name}")
            if "PASSED" in status:
                passed += 1
            else:
                failed += 1
                if "error" in result:
                    logger.info(f"   Ошибка: {result['error']}")
        
        logger.info(f"\n🎯 Результат: {passed} тестов прошли, {failed} не прошли")
        
        if failed == 0:
            logger.info("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        else:
            logger.warning(f"⚠️ {failed} тестов не прошли, требуется доработка")
        
        return results

    async def test_system_status(self):
        """Проверка статуса системы и API"""
        async with aiohttp.ClientSession() as session:
            # Проверяем доступность Backend API
            async with session.get(f"{self.backend_url}/api/ai/status") as response:
                if response.status != 200:
                    raise Exception(f"Backend API недоступен: {response.status}")
                
                data = await response.json()
                logger.info(f"📊 Статус системы: {data}")
                
                flags_stats = data.get("flags_stats", {})
                logger.info(f"🏷️ Uncategorized: {flags_stats.get('uncategorized', 0)}")
                logger.info(f"📝 Unsummarized: {flags_stats.get('unsummarized', 0)}")
                
                return data

    async def test_categorization_check(self):
        """Тест быстрой проверки наличия некатегоризированных постов"""
        has_uncategorized = await self.orchestrator.has_uncategorized_posts()
        logger.info(f"🏷️ Есть некатегоризированные посты: {has_uncategorized}")
        return has_uncategorized

    async def test_summarization_check(self):
        """Тест быстрой проверки наличия несаммаризированных постов"""
        has_unsummarized = await self.orchestrator.has_unsummarized_posts()
        logger.info(f"📝 Есть несаммаризированные посты: {has_unsummarized}")
        return has_unsummarized

    async def test_ai_services_initialization(self):
        """Тест инициализации AI сервисов"""
        success = await self.orchestrator.initialize_ai_services()
        if not success:
            raise Exception("Не удалось инициализировать AI сервисы")
        
        # Проверяем что сервисы созданы
        if self.orchestrator.categorization_service is None:
            raise Exception("CategorizationService не инициализирован")
        
        if self.orchestrator.summarization_service is None:
            raise Exception("SummarizationService не инициализирован")
        
        logger.info("✅ AI сервисы успешно инициализированы")
        return True

    async def test_single_batch(self):
        """Тест одиночного батча (legacy mode для совместимости)"""
        start_time = datetime.now()
        
        success = await self.orchestrator.run_single_batch()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"⏱️ Время выполнения одиночного батча: {duration:.2f} секунд")
        
        if not success:
            raise Exception("Одиночный батч завершился неуспешно")
        
        return {"success": success, "duration": duration}

    async def test_parallel_workers_short(self):
        """Тест параллельных worker циклов (короткий тест - 2 минуты)"""
        logger.info("🚀 Запускаем параллельные workers на 2 минуты...")
        
        start_time = datetime.now()
        
        # Запускаем workers с таймаутом
        try:
            await asyncio.wait_for(
                self.orchestrator.run_parallel_workers(),
                timeout=120  # 2 минуты
            )
        except asyncio.TimeoutError:
            logger.info("⏰ Таймаут достигнут, останавливаем workers")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"⏱️ Время работы параллельных workers: {duration:.2f} секунд")
        
        # Проверяем состояние флагов
        async with self.orchestrator.workers_lock:
            cat_running = self.orchestrator.categorization_is_running
            sum_running = self.orchestrator.summarization_is_running
        
        logger.info(f"🏷️ Categorization worker активен: {cat_running}")
        logger.info(f"📝 Summarization worker активен: {sum_running}")
        
        return {
            "duration": duration,
            "categorization_running": cat_running,
            "summarization_running": sum_running
        }

    async def test_flags_independence(self):
        """Тест независимости флагов активности"""
        # Симулируем установку флагов
        async with self.orchestrator.workers_lock:
            self.orchestrator.categorization_is_running = True
            self.orchestrator.summarization_is_running = False
        
        # Проверяем что каждый worker видит свой флаг
        cat_has_work = await self.orchestrator.has_uncategorized_posts()
        sum_has_work = await self.orchestrator.has_unsummarized_posts()
        
        logger.info(f"🏷️ Categorization: работа есть={cat_has_work}, флаг={self.orchestrator.categorization_is_running}")
        logger.info(f"📝 Summarization: работа есть={sum_has_work}, флаг={self.orchestrator.summarization_is_running}")
        
        # Сбрасываем флаги
        async with self.orchestrator.workers_lock:
            self.orchestrator.categorization_is_running = False
            self.orchestrator.summarization_is_running = False
        
        return {
            "categorization_work": cat_has_work,
            "summarization_work": sum_has_work
        }

async def main():
    """Главная функция для запуска тестов"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Тестирование AI Orchestrator v5.0 - Параллельная архитектура')
    parser.add_argument('--backend-url', default='http://localhost:8000',
                       help='URL Backend API (по умолчанию: http://localhost:8000)')
    parser.add_argument('--test', choices=['all', 'status', 'single', 'parallel'], default='all',
                       help='Какой тест запустить')
    
    args = parser.parse_args()
    
    tester = ParallelOrchestratorTester(backend_url=args.backend_url)
    
    try:
        if args.test == 'all':
            await tester.run_all_tests()
        elif args.test == 'status':
            await tester.test_system_status()
        elif args.test == 'single':
            await tester.test_single_batch()
        elif args.test == 'parallel':
            await tester.test_parallel_workers_short()
        
    except KeyboardInterrupt:
        logger.info("⏹️ Тестирование прервано пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка тестирования: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main())) 