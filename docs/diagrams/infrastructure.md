# CSAT Guardian - Infrastructure Diagrams

> **Last Updated**: January 23, 2026  
> **Purpose**: Visual documentation for stakeholder and security reviews

---

## 1. Full Infrastructure Overview

```mermaid
flowchart TB
    subgraph Internet["☁️ Internet"]
        DevMachine["💻 Developer Machine<br/>(Local Development)"]
        GitHubActions["🔄 GitHub Actions<br/>(CI/CD Pipeline)"]
    end

    subgraph AzureGov["🏛️ Azure Government (USGov Virginia)"]
        subgraph RG["📦 Resource Group: rg-csatguardian-dev"]
            
            subgraph VNet["🔒 Virtual Network: vnet-csatguardian-dev<br/>Address Space: 10.100.0.0/16"]
                
                subgraph AppSubnet["Subnet: snet-appservice<br/>10.100.1.0/24"]
                    AppService["🌐 App Service<br/>app-csatguardian-dev<br/>(Streamlit POC)<br/>Python 3.12 | Linux B1"]
                end
                
                subgraph PESubnet["Subnet: snet-privateendpoints<br/>10.100.2.0/24"]
                    PE_SQL["🔗 Private Endpoint<br/>pep-sql<br/>10.100.2.4"]
                    PE_KV["🔗 Private Endpoint<br/>pep-kv<br/>10.100.2.5"]
                    PE_OAI["🔗 Private Endpoint<br/>pep-oai<br/>10.100.2.6"]
                end
            end
            
            subgraph PaaS["PaaS Services (Private Access Only*)"]
                SQL["🗄️ Azure SQL<br/>sql-csatguardian-dev<br/>.database.usgovcloudapi.net"]
                KV["🔐 Key Vault<br/>kv-csatguardian-dev<br/>.vault.usgovcloudapi.net"]
                OAI["🤖 Azure OpenAI<br/>oai-csatguardian-dev<br/>.openai.azure.us<br/>Model: gpt-4o"]
            end
            
            subgraph DNS["🌐 Private DNS Zones"]
                DNS_SQL["privatelink.database<br/>.usgovcloudapi.net"]
                DNS_KV["privatelink.vaultcore<br/>.usgovcloudapi.net"]
                DNS_OAI["privatelink.openai<br/>.azure.us"]
            end
            
            AppInsights["📊 App Insights<br/>appi-csatguardian-dev"]
            LogAnalytics["📋 Log Analytics<br/>log-csatguardian-dev"]
        end
    end

    subgraph Future["🔮 Future Integration"]
        Teams["💬 Microsoft Teams<br/>(Bot Service)"]
        DfM["📋 DfM API<br/>(Case Data Source)"]
    end

    %% Connections
    DevMachine -->|"az login<br/>(Public, for now)"| KV
    DevMachine -->|"ODBC<br/>(Public, for now)"| SQL
    DevMachine -->|"REST API<br/>(Public, for now)"| OAI
    
    GitHubActions -->|"Bicep Deploy"| RG
    
    AppService -->|"VNet Integration<br/>(All outbound via VNet)"| AppSubnet
    AppService --> PE_SQL
    AppService --> PE_KV
    AppService --> PE_OAI
    
    PE_SQL -.->|"Private Link"| SQL
    PE_KV -.->|"Private Link"| KV
    PE_OAI -.->|"Private Link"| OAI
    
    DNS_SQL -.->|"A Record"| PE_SQL
    DNS_KV -.->|"A Record"| PE_KV
    DNS_OAI -.->|"A Record"| PE_OAI
    
    AppInsights --> LogAnalytics
    AppService -.->|"Telemetry"| AppInsights
    
    Teams -.->|"Future"| AppService
    DfM -.->|"Future"| AppService

    %% Styling
    classDef vnet fill:#e1f5fe,stroke:#01579b
    classDef subnet fill:#fff3e0,stroke:#e65100
    classDef pe fill:#f3e5f5,stroke:#7b1fa2
    classDef paas fill:#e8f5e9,stroke:#2e7d32
    classDef dns fill:#fce4ec,stroke:#c2185b
    classDef future fill:#f5f5f5,stroke:#9e9e9e,stroke-dasharray: 5 5
    
    class VNet vnet
    class AppSubnet,PESubnet subnet
    class PE_SQL,PE_KV,PE_OAI pe
    class SQL,KV,OAI,AppService paas
    class DNS_SQL,DNS_KV,DNS_OAI dns
    class Teams,DfM future
```

> **\* Note**: Public access is currently enabled for local development. Will be disabled after App Service deployment is validated.

---

## 2. Data Flow Diagram

```mermaid
flowchart LR
    subgraph Sources["📥 Data Sources"]
        DfM["DfM API<br/>(Mock for POC)"]
        SQL_Source["Azure SQL<br/>(Sample Data)"]
    end

    subgraph Processing["⚙️ Processing"]
        Monitor["Monitor Service<br/>(Scheduled Scan)"]
        Sentiment["Sentiment Service<br/>(AI Analysis)"]
        Alert["Alert Service<br/>(Threshold Check)"]
    end

    subgraph AI["🤖 AI Layer"]
        OpenAI["Azure OpenAI<br/>gpt-4o"]
    end

    subgraph Output["📤 Output"]
        TeamsAlert["Teams Alert<br/>(Mock for POC)"]
        Dashboard["Streamlit Dashboard<br/>(POC UI)"]
        SQLResults["Azure SQL<br/>(Alert History)"]
    end

    DfM -->|"1. Fetch Cases"| Monitor
    SQL_Source -->|"1. Fetch Cases"| Monitor
    Monitor -->|"2. Analyze Each Case"| Sentiment
    Sentiment -->|"3. Call AI"| OpenAI
    OpenAI -->|"4. Return Score"| Sentiment
    Sentiment -->|"5. Check Thresholds"| Alert
    Alert -->|"6a. Send Alert"| TeamsAlert
    Alert -->|"6b. Store Result"| SQLResults
    Alert -->|"6c. Update UI"| Dashboard

    style OpenAI fill:#e8f5e9,stroke:#2e7d32
    style Dashboard fill:#e3f2fd,stroke:#1565c0
```

---

## 3. Authentication Flow

```mermaid
sequenceDiagram
    autonumber
    participant Dev as Developer Machine
    participant AzCLI as Azure CLI
    participant AAD as Azure AD
    participant App as App Service
    participant MI as Managed Identity
    participant KV as Key Vault
    participant SQL as Azure SQL
    participant OAI as Azure OpenAI

    Note over Dev,OAI: Local Development (Current)
    Dev->>AzCLI: az login (Azure Gov)
    AzCLI->>AAD: Authenticate
    AAD-->>AzCLI: Token
    Dev->>KV: Get secrets (DefaultAzureCredential)
    KV-->>Dev: Secrets (API Key, Connection String)
    Dev->>SQL: Connect (Connection String)
    Dev->>OAI: Call API (API Key)

    Note over Dev,OAI: Production (App Service)
    App->>MI: Request token
    MI->>AAD: Authenticate (System-assigned)
    AAD-->>MI: Token
    App->>KV: Get secrets (via Private Endpoint)
    KV-->>App: Secrets
    App->>SQL: Connect (via Private Endpoint)
    App->>OAI: Call API (via Private Endpoint)
```

---

## 4. Network Security Flow

```mermaid
flowchart TB
    subgraph Public["🌐 Public Internet"]
        User["End User"]
        Dev["Developer"]
    end

    subgraph AzureGov["🏛️ Azure Government"]
        subgraph VNet["🔒 VNet: 10.100.0.0/16"]
            AppService["App Service<br/>(VNet Integrated)"]
            
            subgraph PrivateEndpoints["Private Endpoints"]
                PE1["SQL: 10.100.2.4"]
                PE2["KV: 10.100.2.5"]
                PE3["OAI: 10.100.2.6"]
            end
        end
        
        SQL["Azure SQL"]
        KV["Key Vault"]
        OAI["Azure OpenAI"]
        
        NSG["Network Security<br/>Group (Future)"]
    end

    User -->|"HTTPS (Public)"| AppService
    Dev -->|"HTTPS (Public)*"| SQL
    Dev -->|"HTTPS (Public)*"| KV
    Dev -->|"HTTPS (Public)*"| OAI
    
    AppService -->|"Private (VNet)"| PE1
    AppService -->|"Private (VNet)"| PE2
    AppService -->|"Private (VNet)"| PE3
    
    PE1 -.->|"Private Link"| SQL
    PE2 -.->|"Private Link"| KV
    PE3 -.->|"Private Link"| OAI

    style VNet fill:#e1f5fe,stroke:#01579b
    style PrivateEndpoints fill:#f3e5f5,stroke:#7b1fa2
```

> **\* Note**: Public access for developers is temporary. Will be disabled post-deployment.

---

## 5. Component Inventory

| Component | Resource Name | Type | Endpoint/IP | Status |
|-----------|--------------|------|-------------|--------|
| **VNet** | vnet-csatguardian-dev | Virtual Network | 10.100.0.0/16 | ✅ Deployed |
| **App Subnet** | snet-appservice | Subnet | 10.100.1.0/24 | ✅ Deployed |
| **PE Subnet** | snet-privateendpoints | Subnet | 10.100.2.0/24 | ✅ Deployed |
| **App Service** | app-csatguardian-dev | Web App | .azurewebsites.us | ✅ Deployed |
| **App Service Plan** | asp-csatguardian-dev | Plan | Linux B1 | ✅ Deployed |
| **Azure OpenAI** | oai-csatguardian-dev | Cognitive Services | .openai.azure.us | ✅ Deployed |
| **SQL Server** | sql-csatguardian-dev | SQL Server | .database.usgovcloudapi.net | ✅ Deployed |
| **SQL Database** | sqldb-csatguardian-dev | SQL Database | (on server) | ✅ Deployed |
| **Key Vault** | kv-csatguardian-dev | Key Vault | .vault.usgovcloudapi.net | ✅ Deployed |
| **PE - SQL** | pep-csatguardian-dev-sql | Private Endpoint | 10.100.2.4 | ✅ Deployed |
| **PE - Key Vault** | pep-csatguardian-dev-kv | Private Endpoint | 10.100.2.5 | ✅ Deployed |
| **PE - OpenAI** | pep-csatguardian-dev-oai | Private Endpoint | 10.100.2.6 | ✅ Deployed |
| **DNS - SQL** | privatelink.database.usgovcloudapi.net | Private DNS Zone | - | ✅ Deployed |
| **DNS - KV** | privatelink.vaultcore.usgovcloudapi.net | Private DNS Zone | - | ✅ Deployed |
| **DNS - OAI** | privatelink.openai.azure.us | Private DNS Zone | - | ✅ Deployed |

---

## How to Render These Diagrams

### Option 1: GitHub (Native Support)
GitHub renders Mermaid diagrams automatically in markdown files.

### Option 2: VS Code Extension
Install "Markdown Preview Mermaid Support" extension.

### Option 3: Export to PNG/SVG
Use [mermaid.live](https://mermaid.live) to paste the diagram code and export.

### Option 4: Azure Architecture Diagrams
For formal security reviews, consider recreating in:
- [draw.io](https://draw.io) (free)
- Microsoft Visio
- Azure Architecture Icons (PowerPoint)

---

*Last Updated: January 23, 2026*
