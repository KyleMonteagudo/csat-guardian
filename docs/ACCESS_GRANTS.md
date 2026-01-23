# CSAT Guardian - Access Grants Tracking

> **Purpose:** Track all access grants for future revocation when transitioning to private networking / jumpbox architecture.
> 
> **Last Updated:** January 23, 2026

---

## 🔐 Overview

This document tracks all access grants made during development. When the project transitions to:
- **Private networking** (VNet integration)
- **Jumpbox architecture** (no local workstation access)
- **Production deployment**

...these grants should be reviewed and revoked as appropriate.

---

## 📋 Active Access Grants

### Azure SQL Server Firewall Rules

| Rule Name | IP Range | Granted To | Date | Purpose | Revoke Command |
|-----------|----------|------------|------|---------|----------------|
| `AllowAzureServices` | 0.0.0.0 - 0.0.0.0 | Azure Services | 2026-01-23 | Allow Container Apps to access SQL | `az sql server firewall-rule delete --resource-group rg-csatguardian-dev --server sql-csatguardian-dev --name AllowAzureServices` |
| `AllowKyleLocalDev` | 149.76.66.8 | Kyle Monteagudo (Local Dev - Home IP) | 2026-01-23 | Local development/testing (requires VPN disconnected) | `az sql server firewall-rule delete --resource-group rg-csatguardian-dev --server sql-csatguardian-dev --name AllowKyleLocalDev` |

**Note:** VPN IPs (52.x.x.x range) were tested but removed. Local dev requires VPN disconnected or use jumpbox in future.

### Azure Key Vault RBAC Assignments

| Role | Principal | Principal ID | Date | Purpose | Revoke Command |
|------|-----------|--------------|------|---------|----------------|
| Key Vault Secrets Officer | Kyle Monteagudo | faead4f3-585b-450f-bd28-9c175c09260d | 2026-01-23 | Manage secrets during development | `az role assignment delete --assignee faead4f3-585b-450f-bd28-9c175c09260d --role "Key Vault Secrets Officer" --scope "/subscriptions/9ea57abb-990d-4601-94b5-2a2a6d418274/resourceGroups/rg-csatguardian-dev/providers/Microsoft.KeyVault/vaults/kv-csatguardian-dev"` |
| Key Vault Secrets User | Container App (Managed Identity) | (system-assigned) | 2026-01-23 | App reads secrets at runtime | Keep for production |

---

## 🚀 Transition Checklist (Future)

When transitioning to jumpbox/private networking:

### Phase 1: Set Up Private Networking
- [ ] Create VNet for CSAT Guardian
- [ ] Configure Private Endpoints for:
  - [ ] Azure SQL Database
  - [ ] Azure Key Vault
  - [ ] Azure Container Registry
  - [ ] Azure OpenAI (if supported)
- [ ] Set up Jumpbox VM in the VNet
- [ ] Configure NSG rules

### Phase 2: Revoke Public Access
- [ ] Remove `AllowKyleLocalDev` SQL firewall rule
- [ ] Disable public network access on SQL Server
- [ ] Disable public network access on Key Vault
- [ ] Review and remove unnecessary RBAC assignments

### Phase 3: Verify
- [ ] Confirm app works via private endpoints
- [ ] Confirm no public access remains
- [ ] Update documentation

---

## 📝 Commands to List Current Access

### List SQL Firewall Rules
```powershell
az sql server firewall-rule list --resource-group rg-csatguardian-dev --server sql-csatguardian-dev -o table
```

### List Key Vault RBAC Assignments
```powershell
az role assignment list --scope "/subscriptions/9ea57abb-990d-4601-94b5-2a2a6d418274/resourceGroups/rg-csatguardian-dev/providers/Microsoft.KeyVault/vaults/kv-csatguardian-dev" -o table
```

### List All Resource Group RBAC
```powershell
az role assignment list --resource-group rg-csatguardian-dev -o table
```

---

## 🗑️ Full Cleanup Commands (Emergency Revocation)

If you need to quickly revoke all local dev access:

```powershell
# Remove local dev SQL firewall rule
az sql server firewall-rule delete --resource-group rg-csatguardian-dev --server sql-csatguardian-dev --name AllowKyleLocalDev --yes

# Remove Key Vault Secrets Officer (keep if still needed for management)
# az role assignment delete --assignee faead4f3-585b-450f-bd28-9c175c09260d --role "Key Vault Secrets Officer" --scope "/subscriptions/9ea57abb-990d-4601-94b5-2a2a6d418274/resourceGroups/rg-csatguardian-dev/providers/Microsoft.KeyVault/vaults/kv-csatguardian-dev"
```

---

*This document should be updated whenever access is granted or revoked.*
