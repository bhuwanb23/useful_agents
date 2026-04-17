# GitHub Agent System - Technical Architecture

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  React + TypeScript + Tailwind CSS                       │  │
│  │  - Dashboard  - Agents View  - Approvals  - Logs        │  │
│  │  - Real-time WebSocket Updates                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          API Gateway                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  REST API (Express.js) + WebSocket Server                │  │
│  │  - Authentication  - Rate Limiting  - Request Validation │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Orchestration Layer                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Orchestrator                          │  │
│  │  - Task Dispatching  - Agent Lifecycle  - State Machine │  │
│  │  - Error Handling    - Recovery Logic                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Message Bus (Redis)                    │  │
│  │  Events: task.created, agent.started, fix.completed     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                Task Queue (Celery + Redis)               │  │
│  │  - Priority Queue  - Task Scheduling  - Workers         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Agent Layer                              │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐     │
│  │  Analyzer   │    Fixer    │  Reviewer   │  Security   │     │
│  │   Agent     │    Agent    │   Agent     │   Agent     │     │
│  └─────────────┴─────────────┴─────────────┴─────────────┘     │
│  ┌─────────────┬─────────────┬─────────────────────────────┐   │
│  │ Test Writer │ Docs Writer │    Manager Agent            │   │
│  │   Agent     │    Agent    │  (Planning & Orchestration) │   │
│  └─────────────┴─────────────┴─────────────────────────────┘   │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              LLM Interface Layer                         │  │
│  │  - Ollama (Local)  - OpenAI  - Anthropic                │  │
│  │  - Prompt Engineering  - Context Management             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Intelligence Layer                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              RAG (Retrieval-Augmented Generation)        │  │
│  │                                                          │  │
│  │  ┌────────────────┐      ┌─────────────────────────┐   │  │
│  │  │  Code Indexer  │ ───▶ │  ChromaDB (Vectors)     │   │  │
│  │  │  - Embeddings  │      │  - Semantic Search      │   │  │
│  │  │  - Chunking    │      │  - Context Retrieval    │   │  │
│  │  └────────────────┘      └─────────────────────────┘   │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │         ReAct Engine (Reasoning + Acting)          │ │  │
│  │  │  - Thought Process  - Action Planning             │ │  │
│  │  │  - Self-Correction  - Feedback Loops              │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Execution Layer                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Docker Sandbox Environment                  │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │  │
│  │  │ Container1 │  │ Container2 │  │ Container3 │         │  │
│  │  │ (Python)   │  │ (Node.js)  │  │ (Go)       │  ...    │  │
│  │  └────────────┘  └────────────┘  └────────────┘         │  │
│  │  - Isolated Execution  - Resource Limits                │  │
│  │  - Network Isolation   - Automatic Cleanup              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Integration Layer                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   GitHub API Client                      │  │
│  │  - Repository Operations  - Issue Management            │  │
│  │  - PR Creation           - Webhook Handling             │  │
│  │  - OAuth Authentication  - Rate Limiting                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Git Operations                        │  │
│  │  - Clone  - Branch  - Commit  - Push  - Merge           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Persistence Layer                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PostgreSQL (Primary Database)                           │  │
│  │  - Users  - Repositories  - Issues  - Tasks              │  │
│  │  - Executions  - Logs  - Approvals                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  SQLite (Agent Memory - Stateful)                        │  │
│  │  - Task State  - Agent Context  - Execution History     │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Redis (Cache + Message Queue)                           │  │
│  │  - Session Cache  - Task Queue  - Pub/Sub               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow - Bug Fix Example

### Step-by-Step Workflow

```
1. GitHub Webhook → New Issue Created (#142)
                     ▼
2. Orchestrator receives event via Message Bus
                     ▼
3. Orchestrator dispatches task to Analyzer Agent
                     ▼
4. Analyzer Agent:
   - Fetches issue details from GitHub
   - Classifies: BUG, HIGH severity
   - Searches for related issues using RAG
   - Publishes: analyzer.completed event
                     ▼
5. Manager Agent (triggered by analyzer.completed):
   - Creates execution plan (plan.json)
     Step 1: Analyze codebase
     Step 2: Generate fix
     Step 3: Review fix
     Step 4: Run tests
     Step 5: Security scan
   - Publishes: plan.created event
                     ▼
6. Code Fixer Agent (triggered by plan.step_1):
   - Retrieves relevant code via RAG
   - Analyzes 3 related files using embeddings
   - Generates fix using LLM + context
   - Applies changes to local repo
   - Publishes: fix.completed event
                     ▼
7. Code Reviewer Agent (triggered by fix.completed):
   - Loads changed files
   - Validates syntax and logic
   - Checks best practices
   - Result: REJECTED (missing edge case)
   - Publishes: review.rejected event
                     ▼
8. Code Fixer Agent (self-correction loop):
   - Receives rejection feedback
   - Analyzes review comments
   - Generates improved fix (Attempt 2/3)
   - Publishes: fix.completed event
                     ▼
9. Code Reviewer Agent (2nd review):
   - Re-validates changes
   - Runs static analysis
   - Result: APPROVED (Score: 95/100)
   - Publishes: review.approved event
                     ▼
10. Security Scanner Agent:
    - Scans for vulnerabilities
    - Checks CVE database
    - Secret detection
    - Result: PASS (no issues)
    - Publishes: security.passed event
                     ▼
11. Test Writer Agent:
    - Generates unit tests
    - Checks code coverage
    - Runs tests in sandbox
    - Result: 85% coverage, all pass
    - Publishes: tests.completed event
                     ▼
12. Documentation Writer Agent:
    - Updates relevant docs
    - Generates changelog entry
    - Publishes: docs.completed event
                     ▼
13. Human Approval Gate:
    - System status: awaiting_approval
    - Dashboard shows pending approval
    - Human reviews changes and approves
    - Publishes: approval.granted event
                     ▼
14. GitHub Integration:
    - Creates new branch
    - Commits all changes
    - Pushes to remote
    - Creates Pull Request
    - Posts summary comment
    - Links to issue #142
                     ▼
15. Workflow Complete:
    - Total time: 3m 45s
    - Status: SUCCESS
    - PR: #144 created
    - Notifies stakeholders
```

---

## 🧠 Agent Communication Pattern

### Event-Driven Architecture

```javascript
// Example: Message Bus Events

// 1. Task Created
{
  type: "task.created",
  payload: {
    taskId: "task-123",
    issueId: "issue-456",
    agentType: "analyzer",
    priority: "high"
  },
  timestamp: "2026-01-15T10:30:00Z"
}

// 2. Agent Started
{
  type: "agent.started",
  payload: {
    executionId: "exec-789",
    taskId: "task-123",
    agentType: "analyzer",
    model: "ollama:llama3"
  },
  timestamp: "2026-01-15T10:30:05Z"
}

// 3. Fix Completed
{
  type: "fix.completed",
  payload: {
    taskId: "task-124",
    filesChanged: ["src/auth.ts", "src/middleware.ts"],
    linesChanged: 45,
    reasoning: "Fixed OAuth token validation..."
  },
  timestamp: "2026-01-15T10:32:00Z"
}

// 4. Review Rejected
{
  type: "review.rejected",
  payload: {
    taskId: "task-125",
    reason: "Missing error handling for edge case",
    suggestions: ["Add try-catch", "Validate input"],
    score: 65
  },
  timestamp: "2026-01-15T10:33:00Z"
}

// 5. Approval Required
{
  type: "approval.required",
  payload: {
    issueId: "issue-456",
    prNumber: 144,
    changes: {
      files: 3,
      additions: 78,
      deletions: 12
    },
    tests: "passed",
    security: "passed"
  },
  timestamp: "2026-01-15T10:35:00Z"
}
```

---

## 🎯 Scaling Strategy

### Horizontal Scaling

```
┌─────────────────────────────────────────────┐
│         Load Balancer (nginx)               │
└─────────────────────────────────────────────┘
           ▼           ▼           ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │  API     │ │  API     │ │  API     │
    │ Server 1 │ │ Server 2 │ │ Server 3 │
    └──────────┘ └──────────┘ └──────────┘
           ▼           ▼           ▼
    ┌─────────────────────────────────────┐
    │      Redis Cluster (Message Bus)    │
    └─────────────────────────────────────┘
           ▼           ▼           ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │  Worker  │ │  Worker  │ │  Worker  │
    │  Pool 1  │ │  Pool 2  │ │  Pool 3  │
    │ (5 agents)│ │(5 agents)│ │(5 agents)│
    └──────────┘ └──────────┘ └──────────┘
```

### Database Sharding

```
Repositories 1-1000    → PostgreSQL Shard 1
Repositories 1001-2000 → PostgreSQL Shard 2
Repositories 2001+     → PostgreSQL Shard 3

ChromaDB Collections:
- codebase-repo-1
- codebase-repo-2
- codebase-repo-N
```

---

## 🔒 Security Architecture

### Defense in Depth

```
Layer 1: Network Security
- WAF (Web Application Firewall)
- DDoS Protection
- Rate Limiting

Layer 2: Authentication & Authorization
- OAuth 2.0 / JWT
- Role-Based Access Control (RBAC)
- API Key Management

Layer 3: Application Security
- Input Validation
- Output Encoding
- CSRF Protection
- Security Headers

Layer 4: Data Security
- Encryption at Rest (AES-256)
- Encryption in Transit (TLS 1.3)
- Secret Management (Vault)

Layer 5: Execution Security
- Docker Sandbox (isolated)
- Resource Limits (CPU/Memory)
- Network Isolation
- Read-only Filesystems

Layer 6: Monitoring & Audit
- Security Event Logging
- Intrusion Detection
- Vulnerability Scanning
- Compliance Audits
```

---

## 📊 Monitoring Stack

```
┌─────────────────────────────────────────────┐
│           Application Metrics               │
│  - Agent execution times                    │
│  - Task success/failure rates               │
│  - LLM token usage                          │
│  - API response times                       │
└─────────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────┐
│         Prometheus (Metrics Collection)     │
└─────────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────┐
│         Grafana (Visualization)             │
│  - Real-time Dashboards                     │
│  - Alert Configuration                      │
│  - Performance Graphs                       │
└─────────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────┐
│         AlertManager                        │
│  - Slack Notifications                      │
│  - Email Alerts                             │
│  - PagerDuty Integration                    │
└─────────────────────────────────────────────┘
```

---

## 🚀 Deployment Architecture

### Kubernetes Deployment

```yaml
# Example: Agent Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: code-fixer-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: code-fixer
  template:
    metadata:
      labels:
        app: code-fixer
    spec:
      containers:
      - name: agent
        image: github-agent-system/fixer:latest
        resources:
          limits:
            memory: "2Gi"
            cpu: "1000m"
        env:
        - name: OLLAMA_URL
          value: "http://ollama-service:11434"
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
```

---

## 📈 Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Task Processing Time | < 5 min | N/A |
| API Response Time | < 200ms | N/A |
| WebSocket Latency | < 100ms | N/A |
| System Uptime | 99.9% | N/A |
| Agent Success Rate | > 85% | N/A |
| Code Coverage | > 80% | N/A |
| Security Scan Time | < 30s | N/A |
| PR Creation Time | < 60s | N/A |

---

## 🔄 Disaster Recovery

### Backup Strategy
- **Database**: Daily full backup + hourly incrementals
- **Code Embeddings**: Weekly snapshots
- **Agent State**: Real-time replication to standby
- **Configuration**: Version-controlled in Git

### Recovery Procedures
1. **Service Failure**: Auto-restart via Kubernetes
2. **Database Failure**: Failover to replica (< 30s)
3. **Agent Crash**: Task re-queued automatically
4. **Complete Outage**: Restore from backup (< 4h)

---

**Status**: 🟢 Architecture Documented - Ready for Implementation
