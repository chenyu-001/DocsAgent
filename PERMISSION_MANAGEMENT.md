# Permission Management Guide
# 权限管理实用指南

## Quick Start - Check Your Current Status

### 1. Check if migration succeeded

```bash
# Connect to database
docker-compose exec postgres psql -U docsagent -d docsagent

# Check tables exist
\dt

# Check default tenant
SELECT id, name, slug, status FROM tenants;

# Check your user is in tenant
SELECT tu.id, tu.user_id, u.username, tr.name as role
FROM tenant_users tu
JOIN users u ON tu.user_id = u.id
LEFT JOIN tenant_roles tr ON tu.role_id = tr.id;

# Exit
\q
```

Expected result:
- ✅ Default tenant exists (ID: 00000000-0000-0000-0000-000000000001)
- ✅ Your user is linked to default tenant
- ✅ User has a role (member/tenant_admin/guest)

---

## API Access - Using Tenant APIs

### Get Your Token

```bash
# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "your_user", "password": "your_pass"}'

# Save the token
export TOKEN="eyJ..."
```

### Check Tenant Info

```bash
# Get current tenant info
curl -X GET "http://localhost:8000/api/tenants/current/info" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001"
```

### List Users in Tenant

```bash
curl -X GET "http://localhost:8000/api/tenants/current/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001"
```

### List Roles

```bash
curl -X GET "http://localhost:8000/api/tenants/current/roles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001"
```

---

## Permission Management

### Understanding Permission Levels

**Permission Bits** (can be combined):
- `1` (READ) - View documents
- `2` (WRITE) - Edit documents
- `4` (DELETE) - Delete documents
- `8` (SHARE) - Share with others
- `16` (ADMIN) - Manage permissions
- `32` (DOWNLOAD) - Download files
- `64` (COMMENT) - Add comments
- `128` (EXPORT) - Export data

**Preset Combinations**:
- `33` (READER) = READ + DOWNLOAD
- `67` (EDITOR) = READ + WRITE + DOWNLOAD + COMMENT
- `255` (OWNER) = All permissions

### Create Custom Role

```bash
curl -X POST "http://localhost:8000/api/tenants/current/roles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "reviewer",
    "display_name": "Reviewer",
    "description": "Can view and comment on documents",
    "permissions": 97
  }'
```

Calculation: 97 = READ(1) + DOWNLOAD(32) + COMMENT(64) = 1 + 32 + 64

### Grant Permission to User

```bash
curl -X POST "http://localhost:8000/api/tenants/current/permissions/grant" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001" \
  -H "Content-Type: application/json" \
  -d '{
    "resource_type": "document",
    "resource_id": "123",
    "grantee_type": "user",
    "grantee_id": "456",
    "permission": 67
  }'
```

### Grant Permission to Role

```bash
curl -X POST "http://localhost:8000/api/tenants/current/permissions/grant" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001" \
  -H "Content-Type: application/json" \
  -d '{
    "resource_type": "folder",
    "resource_id": "789",
    "grantee_type": "role",
    "grantee_id": "role-uuid-here",
    "permission": 255
  }'
```

### Check Resource Permissions

```bash
curl -X GET "http://localhost:8000/api/tenants/current/permissions/document/123" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001"
```

---

## Database Management (Direct SQL)

### Promote User to Tenant Admin

```sql
-- Connect to database
docker-compose exec postgres psql -U docsagent -d docsagent

-- Find tenant admin role
SELECT id, name FROM tenant_roles WHERE name = 'tenant_admin' AND tenant_id = '00000000-0000-0000-0000-000000000001';

-- Update user's role (replace USER_ID and ROLE_ID)
UPDATE tenant_users
SET role_id = 'ROLE_ID_FROM_ABOVE'
WHERE user_id = YOUR_USER_ID
  AND tenant_id = '00000000-0000-0000-0000-000000000001';
```

### Add User to Tenant

```sql
-- Get user ID
SELECT id, username FROM users WHERE username = 'target_user';

-- Get default role
SELECT id FROM tenant_roles WHERE name = 'member' AND tenant_id = '00000000-0000-0000-0000-000000000001';

-- Add user to tenant
INSERT INTO tenant_users (id, tenant_id, user_id, role_id, status)
VALUES (
  gen_random_uuid(),
  '00000000-0000-0000-0000-000000000001',
  USER_ID_HERE,
  ROLE_ID_HERE,
  'active'
);
```

### Grant Document Permission

```sql
-- Grant permission to user
INSERT INTO resource_permissions (id, tenant_id, resource_type, resource_id, grantee_type, grantee_id, permission)
VALUES (
  gen_random_uuid(),
  '00000000-0000-0000-0000-000000000001',
  'document',
  '123',
  'user',
  '456',
  67  -- EDITOR permission
);
```

---

## Python Script for Batch Operations

Create `manage_permissions.py`:

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/app')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.config import settings
from models.tenant_permission_models import TenantUser, TenantRole, ResourcePermission, Permission
from models.user_models import User
import uuid

engine = create_engine(settings.database_url)
Session = sessionmaker(bind=engine)
db = Session()

DEFAULT_TENANT = '00000000-0000-0000-0000-000000000001'

def promote_to_admin(username):
    """Promote user to tenant admin"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        print(f"User {username} not found")
        return

    admin_role = db.query(TenantRole).filter(
        TenantRole.tenant_id == DEFAULT_TENANT,
        TenantRole.name == 'tenant_admin'
    ).first()

    tenant_user = db.query(TenantUser).filter(
        TenantUser.user_id == user.id,
        TenantUser.tenant_id == DEFAULT_TENANT
    ).first()

    if tenant_user:
        tenant_user.role_id = admin_role.id
        db.commit()
        print(f"✅ {username} promoted to tenant admin")
    else:
        print(f"User {username} not in tenant")

def list_users():
    """List all users in default tenant"""
    users = db.query(TenantUser).filter(
        TenantUser.tenant_id == DEFAULT_TENANT
    ).all()

    print(f"\nUsers in Default Tenant:")
    print("-" * 60)
    for tu in users:
        user = db.query(User).filter(User.id == tu.user_id).first()
        role_name = tu.role.name if tu.role else "No role"
        print(f"{user.username:20} | Role: {role_name:20} | Status: {tu.status}")

def grant_doc_permission(doc_id, user_id, perm=67):
    """Grant document permission to user"""
    rp = ResourcePermission(
        id=uuid.uuid4(),
        tenant_id=DEFAULT_TENANT,
        resource_type='document',
        resource_id=str(doc_id),
        grantee_type='user',
        grantee_id=str(user_id),
        permission=perm,
        granted_by=1
    )
    db.add(rp)
    db.commit()
    print(f"✅ Granted permission {Permission.to_string(perm)} to user {user_id} on doc {doc_id}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true', help='List users')
    parser.add_argument('--promote', help='Promote user to admin')
    parser.add_argument('--grant-doc', nargs=3, metavar=('DOC_ID', 'USER_ID', 'PERM'), help='Grant doc permission')

    args = parser.parse_args()

    if args.list:
        list_users()
    elif args.promote:
        promote_to_admin(args.promote)
    elif args.grant_doc:
        grant_doc_permission(args.grant_doc[0], args.grant_doc[1], int(args.grant_doc[2]))
    else:
        parser.print_help()
```

Usage:

```bash
# In container
docker-compose exec backend python manage_permissions.py --list
docker-compose exec backend python manage_permissions.py --promote alice
docker-compose exec backend python manage_permissions.py --grant-doc 123 456 67
```

---

## Common Tasks

### Task 1: Make yourself tenant admin

**Via API (requires existing admin)**:
```bash
# Not available yet - you need to be admin first
```

**Via Database**:
```sql
-- Find your user ID
SELECT id, username FROM users WHERE username = 'YOUR_USERNAME';

-- Get admin role ID
SELECT id FROM tenant_roles WHERE name = 'tenant_admin' AND tenant_id = '00000000-0000-0000-0000-000000000001';

-- Update your role
UPDATE tenant_users SET role_id = 'ADMIN_ROLE_ID' WHERE user_id = YOUR_USER_ID;
```

**Via Python Script** (easiest):
```bash
# Create the script above, then:
docker cp manage_permissions.py docsagent-backend:/app/
docker-compose exec backend python manage_permissions.py --promote YOUR_USERNAME
```

### Task 2: Create platform super admin

```sql
-- Make yourself platform super admin
INSERT INTO platform_admins (user_id, role)
VALUES (YOUR_USER_ID, 'super_admin');
```

Then you can use all platform APIs!

### Task 3: View audit logs

```sql
SELECT
  al.created_at,
  al.action,
  al.username,
  al.resource_type,
  al.resource_id,
  al.success
FROM audit_logs al
ORDER BY al.created_at DESC
LIMIT 20;
```

---

## Testing Permissions

### Test Permission Check

Create `test_permissions.py`:

```python
from services.permission_checker import PermissionChecker, PermissionContext
from models.tenant_permission_models import Permission, ResourceType
from api.db import get_db

db = next(get_db())
checker = PermissionChecker(db)

# Test if user 1 can read document 123
ctx = PermissionContext(
    user_id=1,
    tenant_id='00000000-0000-0000-0000-000000000001',
    resource_type=ResourceType.DOCUMENT,
    resource_id='123',
    required_permission=Permission.READ
)

try:
    result = checker.check(ctx)
    print(f"✅ Permission granted: {result}")
except Exception as e:
    print(f"❌ Permission denied: {e}")

# Get actual permissions
user_perm = checker.get_user_permission(ctx)
print(f"User has permissions: {Permission.to_string(user_perm)}")
```

---

## API Documentation

After restarting backend with the new routes:

Visit: **http://localhost:8000/docs**

You'll see new endpoints:
- `GET /api/tenants/current/info` - Get tenant info
- `GET /api/tenants/current/users` - List users
- `POST /api/tenants/current/users/invite` - Invite user
- `GET /api/tenants/current/roles` - List roles
- `POST /api/tenants/current/roles` - Create role
- `POST /api/tenants/current/permissions/grant` - Grant permission
- `GET /api/tenants/current/permissions/{type}/{id}` - View permissions

**Platform Admin Only**:
- `POST /api/tenants/` - Create tenant
- `GET /api/tenants/` - List all tenants
- `PATCH /api/tenants/{id}` - Update tenant

---

## Next Steps

1. **Restart backend** to load new tenant routes:
   ```bash
   docker-compose restart backend
   ```

2. **Make yourself admin** (choose one):
   - Use SQL to update your role
   - Use Python script
   - Ask another admin to promote you

3. **Test the APIs**:
   - Visit http://localhost:8000/docs
   - Try the tenant endpoints
   - Check permission responses

4. **Integrate with existing features**:
   - Add permission checks to document routes
   - Add tenant filtering to queries
   - Enable audit logging

---

## Troubleshooting

**Issue: "Permission denied" on tenant APIs**

Solution: You need tenant_admin role or platform_admin:
```sql
-- Make platform admin
INSERT INTO platform_admins (user_id, role) VALUES (YOUR_USER_ID, 'super_admin');
```

**Issue: "Tenant not found"**

Solution: Always pass X-Tenant-ID header:
```bash
-H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001"
```

**Issue: Can't see tenant routes in /docs**

Solution: Restart backend after adding routes to main.py

---

## Summary

Current setup:
- ✅ Database tables created
- ✅ Default tenant exists
- ✅ All users migrated to default tenant
- ✅ Tenant APIs available (after restart)
- ⏳ Need to integrate permission checks into existing routes
- ⏳ Need to make first user admin

Quick command to get started:
```bash
# Restart backend
docker-compose restart backend

# Make yourself platform admin
docker-compose exec postgres psql -U docsagent -d docsagent -c \
  "INSERT INTO platform_admins (user_id, role) VALUES (1, 'super_admin');"

# Test API
curl http://localhost:8000/api/tenants/current/info \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001"
```

Done! 🚀
