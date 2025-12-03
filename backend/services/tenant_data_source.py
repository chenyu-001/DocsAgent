"""
Tenant Data Source Service
租户数据源路由 - 根据部署模式路由到不同的数据源
"""
from typing import Optional, Dict
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool
import logging
import json

from models.tenant_models import Tenant, DeployMode
from api.config import settings

logger = logging.getLogger(__name__)


class DatabaseConnectionPool:
    """数据库连接池管理器"""

    def __init__(self):
        self._pools: Dict[str, sessionmaker] = {}
        self._default_engine = None

    def get_session(self, tenant: Tenant) -> Session:
        """
        获取租户的数据库会话

        Args:
            tenant: 租户对象

        Returns:
            Session: SQLAlchemy会话
        """
        if tenant.deploy_mode == DeployMode.CLOUD:
            # Cloud模式: 使用schema隔离
            return self._get_cloud_session(tenant)
        elif tenant.deploy_mode in [DeployMode.HYBRID, DeployMode.LOCAL]:
            # Hybrid/Local模式: 使用独立数据库
            return self._get_local_session(tenant)
        else:
            # 默认使用Cloud模式
            return self._get_cloud_session(tenant)

    def _get_cloud_session(self, tenant: Tenant) -> Session:
        """
        获取Cloud模式的数据库会话(使用schema隔离)

        Args:
            tenant: 租户对象

        Returns:
            Session: 数据库会话
        """
        pool_key = f"cloud_{tenant.id}"

        if pool_key not in self._pools:
            # 使用默认数据库连接,但指定schema
            schema_name = tenant.db_schema or f"tenant_{str(tenant.id).replace('-', '_')}"

            # 创建引擎
            engine = create_engine(
                settings.DATABASE_URL,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                connect_args={"options": f"-c search_path={schema_name},public"}
            )

            # 创建会话工厂
            self._pools[pool_key] = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine
            )

            logger.info(f"Created Cloud database pool for tenant {tenant.id} with schema {schema_name}")

        return self._pools[pool_key]()

    def _get_local_session(self, tenant: Tenant) -> Session:
        """
        获取Local/Hybrid模式的数据库会话(使用独立连接)

        Args:
            tenant: 租户对象

        Returns:
            Session: 数据库会话
        """
        if not tenant.db_connection:
            logger.warning(f"Tenant {tenant.id} has no db_connection configured, falling back to cloud mode")
            return self._get_cloud_session(tenant)

        pool_key = f"local_{tenant.id}"

        if pool_key not in self._pools:
            try:
                # 解密数据库连接字符串(实际项目中应该加密存储)
                db_url = self._decrypt_connection_string(tenant.db_connection)

                # 创建引擎
                engine = create_engine(
                    db_url,
                    poolclass=QueuePool,
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True
                )

                # 创建会话工厂
                self._pools[pool_key] = sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=engine
                )

                logger.info(f"Created Local database pool for tenant {tenant.id}")

            except Exception as e:
                logger.error(f"Failed to create local database pool for tenant {tenant.id}: {e}")
                raise

        return self._pools[pool_key]()

    def _decrypt_connection_string(self, encrypted: str) -> str:
        """
        解密数据库连接字符串

        TODO: 实际项目中应该使用真正的加密/解密
        目前只是简单返回

        Args:
            encrypted: 加密的连接字符串

        Returns:
            str: 解密后的连接字符串
        """
        # 实际项目中应该使用 cryptography 或 AWS KMS 等加密
        return encrypted

    def close_pool(self, tenant_id: str):
        """
        关闭租户的连接池(用于租户删除或配置更新)

        Args:
            tenant_id: 租户ID
        """
        for prefix in ["cloud_", "local_"]:
            pool_key = f"{prefix}{tenant_id}"
            if pool_key in self._pools:
                # 关闭所有连接
                session_factory = self._pools.pop(pool_key)
                if hasattr(session_factory, 'kw') and 'bind' in session_factory.kw:
                    engine = session_factory.kw['bind']
                    engine.dispose()
                logger.info(f"Closed database pool: {pool_key}")


# 全局连接池实例
_db_pool = DatabaseConnectionPool()


class VectorDBRouter:
    """向量数据库路由器"""

    def __init__(self):
        self._clients: Dict[str, any] = {}

    def get_client(self, tenant: Tenant):
        """
        获取租户的向量数据库客户端

        Args:
            tenant: 租户对象

        Returns:
            VectorDB客户端(Qdrant/Milvus等)
        """
        client_key = str(tenant.id)

        if client_key not in self._clients:
            self._clients[client_key] = self._create_vector_client(tenant)

        return self._clients[client_key]

    def _create_vector_client(self, tenant: Tenant):
        """
        创建向量数据库客户端

        Args:
            tenant: 租户对象

        Returns:
            VectorDB客户端
        """
        # 获取配置
        config = tenant.vector_db_config or {}
        namespace = tenant.vector_namespace or str(tenant.id)

        # 判断向量库类型
        vector_db_type = config.get("type", "qdrant")

        if vector_db_type == "qdrant":
            return self._create_qdrant_client(config, namespace)
        elif vector_db_type == "milvus":
            return self._create_milvus_client(config, namespace)
        else:
            logger.warning(f"Unknown vector db type: {vector_db_type}, using qdrant")
            return self._create_qdrant_client(config, namespace)

    def _create_qdrant_client(self, config: dict, namespace: str):
        """创建Qdrant客户端"""
        try:
            from qdrant_client import QdrantClient

            # 从配置获取连接信息
            host = config.get("host", settings.QDRANT_HOST)
            port = config.get("port", settings.QDRANT_PORT)

            client = QdrantClient(host=host, port=port)

            logger.info(f"Created Qdrant client with namespace: {namespace}")

            # 返回带命名空间的客户端包装器
            return QdrantClientWrapper(client, namespace)

        except Exception as e:
            logger.error(f"Failed to create Qdrant client: {e}")
            raise

    def _create_milvus_client(self, config: dict, namespace: str):
        """创建Milvus客户端"""
        try:
            from pymilvus import connections, Collection

            # 从配置获取连接信息
            host = config.get("host", "localhost")
            port = config.get("port", 19530)

            # 连接Milvus
            connections.connect(
                alias=namespace,
                host=host,
                port=port
            )

            logger.info(f"Created Milvus client with namespace: {namespace}")

            return MilvusClientWrapper(namespace)

        except Exception as e:
            logger.error(f"Failed to create Milvus client: {e}")
            raise

    def close_client(self, tenant_id: str):
        """
        关闭租户的向量数据库客户端

        Args:
            tenant_id: 租户ID
        """
        if tenant_id in self._clients:
            client = self._clients.pop(tenant_id)
            if hasattr(client, 'close'):
                client.close()
            logger.info(f"Closed vector db client for tenant: {tenant_id}")


# 全局向量库路由实例
_vector_router = VectorDBRouter()


class QdrantClientWrapper:
    """Qdrant客户端包装器 - 自动添加命名空间"""

    def __init__(self, client, namespace: str):
        self.client = client
        self.namespace = namespace

    def get_collection_name(self, base_name: str) -> str:
        """获取带命名空间的集合名"""
        return f"{self.namespace}_{base_name}"

    def __getattr__(self, name):
        """代理所有方法到原始客户端"""
        return getattr(self.client, name)


class MilvusClientWrapper:
    """Milvus客户端包装器 - 自动添加命名空间"""

    def __init__(self, namespace: str):
        self.namespace = namespace

    def get_collection_name(self, base_name: str) -> str:
        """获取带命名空间的集合名"""
        return f"{self.namespace}_{base_name}"


class TenantDataSource:
    """租户数据源 - 统一的数据源访问接口"""

    @staticmethod
    def get_database_session(tenant: Tenant) -> Session:
        """
        获取租户的数据库会话

        Args:
            tenant: 租户对象

        Returns:
            Session: 数据库会话
        """
        return _db_pool.get_session(tenant)

    @staticmethod
    def get_vector_db_client(tenant: Tenant):
        """
        获取租户的向量数据库客户端

        Args:
            tenant: 租户对象

        Returns:
            VectorDB客户端
        """
        return _vector_router.get_client(tenant)

    @staticmethod
    def close_tenant_connections(tenant_id: str):
        """
        关闭租户的所有连接(用于租户删除或配置更新)

        Args:
            tenant_id: 租户ID
        """
        _db_pool.close_pool(tenant_id)
        _vector_router.close_client(tenant_id)
        logger.info(f"Closed all connections for tenant: {tenant_id}")


class StorageRouter:
    """存储路由器 - 根据租户配置路由文件存储"""

    @staticmethod
    def get_storage_path(tenant: Tenant, filename: str) -> str:
        """
        获取文件的存储路径

        Args:
            tenant: 租户对象
            filename: 文件名

        Returns:
            str: 存储路径
        """
        storage_config = tenant.storage_config or {}
        storage_type = storage_config.get("type", "local")

        if storage_type == "local":
            # 本地存储
            base_path = storage_config.get("base_path", "/data/uploads")
            return f"{base_path}/{tenant.id}/{filename}"

        elif storage_type == "s3":
            # S3存储
            bucket = storage_config.get("bucket", "docsagent-uploads")
            return f"s3://{bucket}/{tenant.id}/{filename}"

        elif storage_type == "oss":
            # 阿里云OSS
            bucket = storage_config.get("bucket", "docsagent-uploads")
            return f"oss://{bucket}/{tenant.id}/{filename}"

        else:
            # 默认本地存储
            return f"/data/uploads/{tenant.id}/{filename}"
