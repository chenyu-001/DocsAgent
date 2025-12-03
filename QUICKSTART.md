# Quick Start - Multi-Tenant Migration for Docker

## TL;DR - Fastest Way

```powershell
# Option 1: PowerShell script (recommended for Windows)
.\migrate.ps1

# Option 2: Direct Python (if script fails)
docker-compose exec backend python init_db.py

# Option 3: Direct SQL
docker exec -i docsagent-postgres psql -U docsagent -d docsagent < backend/migrations/002_add_multi_tenant.sql
```

---

## Step-by-Step

### 1. Start Docker Services

```bash
docker-compose up -d
```

Check status:
```bash
docker-compose ps
```

You should see:
- ✅ docsagent-postgres (healthy)
- ✅ docsagent-backend (running)
- ✅ docsagent-qdrant (running)

### 2. Run Migration

**Windows PowerShell:**
```powershell
.\migrate.ps1
```

**Windows CMD:**
```cmd
.\run_migration.bat
```

**Linux/Mac:**
```bash
docker-compose exec backend bash /app/run_migration.sh
```

**Manual (any platform):**
```bash
# Enter backend container
docker-compose exec backend bash

# Run migration
cd /app
python init_db.py

# Exit
exit
```

### 3. Verify

```bash
# Check database
docker-compose exec postgres psql -U docsagent -d docsagent

# In psql:
\dt                                    # List tables
SELECT * FROM tenants;                 # Check default tenant
SELECT * FROM tenant_roles;            # Check roles
\q                                     # Quit
```

Expected results:
- ✅ Table `tenants` exists
- ✅ Table `tenant_users` exists
- ✅ Table `tenant_roles` exists
- ✅ Table `resource_permissions` exists
- ✅ Table `audit_logs` exists
- ✅ Default tenant: `00000000-0000-0000-0000-000000000001`
- ✅ 3 system roles: tenant_admin, member, guest

### 4. Test API

```bash
# Health check
curl http://localhost:8000/health

# API docs
# Visit: http://localhost:8000/docs
```

---

## Troubleshooting

### Issue: "bash not found"

Your container uses a minimal image. Use Python instead:

```bash
docker-compose exec backend python init_db.py
```

### Issue: "docker-compose not found"

Use new syntax:

```bash
# Old
docker-compose exec backend bash

# New
docker compose exec backend bash
```

### Issue: "Cannot connect to database"

Check PostgreSQL is running:

```bash
docker-compose ps postgres
docker-compose logs postgres
```

Restart if needed:

```bash
docker-compose restart postgres
docker-compose restart backend
```

### Issue: "Table already exists"

Migration was already run. Skip or reset:

```bash
# Reset (WARNING: deletes all data!)
docker-compose exec backend python init_db.py --drop
```

### Issue: PowerShell execution policy

Enable script execution:

```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then run script
.\migrate.ps1
```

---

## Common Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f backend

# Restart a service
docker-compose restart backend

# Enter container
docker-compose exec backend bash

# Database shell
docker-compose exec postgres psql -U docsagent -d docsagent

# Rebuild container
docker-compose up -d --build backend
```

---

## What Gets Created

### Database Tables (9 new)
- `tenants` - Tenant organizations
- `tenant_features` - Feature toggles
- `departments` - Organizational structure
- `tenant_roles` - Custom roles
- `tenant_users` - User-tenant associations
- `resource_permissions` - Fine-grained permissions
- `platform_admins` - System administrators
- `audit_logs` - Audit trail
- `login_history` - Login tracking

### Default Tenant
- **ID**: `00000000-0000-0000-0000-000000000001`
- **Name**: Default Tenant
- **Slug**: default
- All existing users migrated to this tenant

### System Roles
- **tenant_admin** - Full access (permission: 255)
- **member** - Edit access (permission: 67)
- **guest** - Read only (permission: 33)

---

## Next Steps

1. ✅ Migration complete
2. ✅ Start backend: `docker-compose up -d`
3. ✅ Test API: http://localhost:8000/docs
4. ✅ Read full guide: `MULTI_TENANT_GUIDE.md`
5. ✅ Create test tenant:
   ```bash
   docker-compose exec backend python init_db.py --create-test-tenant
   ```

---

## API Examples

### Get Tenant Info

```bash
curl -X GET "http://localhost:8000/api/tenants/current/info" \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Login

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "your_user", "password": "your_pass"}'
```

### Create Role

```bash
curl -X POST "http://localhost:8000/api/tenants/current/roles" \
  -H "X-Tenant-ID: tenant-uuid" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "reviewer",
    "display_name": "Reviewer",
    "permissions": 97
  }'
```

---

## Files Added

- `backend/models/tenant_models.py` - Tenant models
- `backend/models/tenant_permission_models.py` - Permission system
- `backend/models/audit_models.py` - Audit logging
- `backend/services/permission_checker.py` - Permission validation
- `backend/services/tenant_context.py` - Tenant middleware
- `backend/services/tenant_data_source.py` - Data routing
- `backend/services/audit_service.py` - Audit service
- `backend/routes/tenants.py` - Tenant APIs
- `backend/migrations/002_add_multi_tenant.sql` - Database migration
- `backend/init_db.py` - Init script
- `backend/run_migration.sh` - Linux/Mac script
- `run_migration.bat` - Windows batch
- `migrate.ps1` - PowerShell script
- `MULTI_TENANT_GUIDE.md` - Full documentation
- `DOCKER_SETUP.md` - Docker guide

---

## Need Help?

1. Check logs: `docker-compose logs -f backend`
2. Check database: `docker-compose exec postgres psql -U docsagent -d docsagent`
3. Read guides: `MULTI_TENANT_GUIDE.md`, `DOCKER_SETUP.md`
4. Submit issue with logs on GitHub

---

**Done!** Your multi-tenant system is ready.
