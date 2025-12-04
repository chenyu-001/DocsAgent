#!/usr/bin/env python3
"""
检查枚举类型的值
"""
from sqlalchemy import create_engine, text
from api.config import settings
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_enum_values():
    engine = create_engine(settings.database_url)

    try:
        with engine.connect() as conn:
            logger.info("=" * 60)
            logger.info("检查枚举类型的值")
            logger.info("=" * 60)

            # 查询所有枚举类型及其值
            result = conn.execute(text("""
                SELECT t.typname as enum_name, e.enumlabel as enum_value
                FROM pg_type t
                JOIN pg_enum e ON t.oid = e.enumtypid
                WHERE t.typtype = 'e'
                ORDER BY t.typname, e.enumsortorder
            """))

            current_enum = None
            for row in result:
                if row[0] != current_enum:
                    current_enum = row[0]
                    logger.info(f"\n{current_enum}:")
                logger.info(f"  - {row[1]}")

    except Exception as e:
        logger.error(f"错误: {e}")
    finally:
        engine.dispose()

if __name__ == "__main__":
    check_enum_values()
