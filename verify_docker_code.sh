#!/bin/bash
# 验证 Docker 容器内的代码是否是最新的

echo "==================================="
echo "验证 Docker 容器内的代码"
echo "==================================="

echo -e "\n1. 检查容器内的 main.py (第 54 行应该是中间件注册):"
docker exec docsagent-backend sed -n '53,55p' /app/api/main.py

echo -e "\n2. 检查容器内的 tenant_context.py (应该继承 BaseHTTPMiddleware):"
docker exec docsagent-backend grep -A 5 "class TenantMiddleware" /app/services/tenant_context.py | head -10

echo -e "\n3. 检查容器是否有 check_tenant.py 诊断脚本:"
docker exec docsagent-backend ls -lh /app/check_tenant.py 2>&1

echo -e "\n4. 检查 Python 导入是否正常:"
docker exec docsagent-backend python -c "from services.tenant_context import TenantMiddleware; print('✅ TenantMiddleware 导入成功')" 2>&1

echo -e "\n==================================="
echo "检查完成"
echo "==================================="
