# 🤖 GitHub Agent System - Pro

An **autonomous agentic platform** for GitHub repository management powered by AI agents, RAG (Retrieval-Augmented Generation), and event-driven architecture.

## ✅ **PHASE 1 COMPLETE: Foundation & State Management**

### What's Implemented

✅ **PostgreSQL Database** - Complete Prisma schema with 12 tables  
✅ **BullMQ Task Queue** - 7 specialized queues (analyzer, fixer, reviewer, security, tester, docs, manager)  
✅ **Ollama Load Balancer** - Multi-instance support with health checking and failover  
✅ **Prompt Version Management** - Database-backed versioned prompts  
✅ **Backend API** - Express.js server with 8 route groups  
✅ **Docker Infrastructure** - Complete docker-compose for all services  

### Quick Start

```bash
# 1. Start infrastructure
docker-compose up -d

# 2. Install & setup database
npm install
npx prisma generate
npx prisma migrate dev

# 3. Pull Ollama model
docker exec github-agent-ollama-1 ollama pull llama3:8b

# 4. Start servers
npm run dev:server  # Backend on :3001
npm run dev         # Frontend on :5173
```

**See [PHASE_1_SETUP.md](./PHASE_1_SETUP.md) for detailed setup instructions.**

---

## 🏗️ Architecture Overview

This system implements a **Multi-Agent Orchestration** platform with the following key components:

### Core Components

1. **Event-Driven Micro-Agent Architecture**
   - Message Bus for agent communication
   - Stateful Memory (SQLite/PostgreSQL)
   - Task Queue for orchestration
   - Real-time event streaming

2. **Specialized AI Agents**
   - 🔍 **Analyzer Agent**: Issue classification and analysis
   - 🔧 **Code Fixer Agent**: Autonomous bug fixing and feature implementation
   - ✅ **Code Reviewer Agent**: Quality assurance and best practices validation
   - 🔒 **Security Scanner Agent**: Vulnerability detection and CVE checking
   - 🧪 **Test Writer Agent**: Automated test generation with coverage analysis
   - 📚 **Documentation Writer Agent**: Auto-generated docs and README updates
   - 🎯 **Manager Agent**: Multi-step planning and orchestration

3. **Advanced Features**
   - **RAG (Retrieval-Augmented Generation)**: ChromaDB vector database for codebase embeddings
   - **Self-Correction Loops**: ReAct pattern with retry mechanisms (up to 3 attempts)
   - **Human-in-the-Loop (HITL)**: Approval system for code changes
   - **Sandbox Execution**: Docker-based safe code execution environment
   - **Multi-Repository Support**: Monitor and manage multiple repos simultaneously

### Technology Stack

- **Frontend**: React 19 + TypeScript + Tailwind CSS
- **Build Tool**: Vite
- **AI Engine**: Ollama (local LLM) / vLLM (production)
- **Vector DB**: ChromaDB (for code embeddings)
- **Message Queue**: Redis + Celery
- **Database**: SQLite (dev) / PostgreSQL (production)
- **Framework**: LangGraph (multi-agent orchestration)

## 📁 Project Structure

```
src/
├── components/          # React UI components
│   ├── Layout.tsx      # Main layout with header/footer
│   ├── Navigation.tsx  # Tab navigation
│   ├── StatCard.tsx    # System statistics cards
│   ├── AgentCard.tsx   # Agent status display
│   ├── IssueCard.tsx   # GitHub issue cards
│   ├── LogViewer.tsx   # Real-time log viewer
│   └── ExecutionTimeline.tsx  # Agent execution timeline
├── config/             # Configuration files
│   └── agents.ts       # Agent configurations and capabilities
├── types/              # TypeScript type definitions
│   └── index.ts        # Core types (Agent, Task, Issue, etc.)
├── data/               # Mock data for development
│   └── mockData.ts     # Sample repositories, issues, tasks
└── App.tsx             # Main application component
```

## 🎯 Features Implemented (Base)

### ✅ Current Features
- [x] Multi-tab dashboard interface
- [x] System overview with real-time stats
- [x] Agent fleet management view
- [x] Issue tracking and monitoring
- [x] Execution timeline visualization
- [x] Real-time log viewer
- [x] Human-in-the-loop approval system
- [x] Repository monitoring interface
- [x] Type-safe architecture with TypeScript
- [x] Responsive UI with Tailwind CSS

### 🚧 Planned Features (Next Phase)

#### Phase 1: Core Intelligence
- [ ] RAG implementation with ChromaDB
- [ ] Vector embeddings for codebase analysis
- [ ] Self-correction loops (ReAct pattern)
- [ ] Feedback mechanism between agents
- [ ] Planning agent for multi-step tasks

#### Phase 2: Execution Environment
- [ ] Docker sandbox integration
- [ ] Safe code execution environment
- [ ] Automated testing in sandbox
- [ ] PR creation automation
- [ ] Git operations integration

#### Phase 3: Advanced Orchestration
- [ ] LangGraph integration
- [ ] Message bus (Redis) implementation
- [ ] Task queue (Celery) for async processing
- [ ] Real-time WebSocket updates
- [ ] Agent state persistence

#### Phase 4: Production Features
- [ ] Multi-repository control center
- [ ] GitHub API integration
- [ ] OAuth token management
- [ ] User authentication
- [ ] Role-based access control
- [ ] Audit logs and compliance

#### Phase 5: Intelligence Upgrades
- [ ] Code coverage analysis
- [ ] CVE database integration
- [ ] Dependency security scanning
- [ ] Performance benchmarking
- [ ] Code quality metrics

## 🧩 Agent Capabilities

### Analyzer Agent
- Issue type classification (bug/feature/security/docs)
- Severity assessment
- Related issue detection
- Dependency analysis

### Code Fixer Agent
- Autonomous code generation
- Bug fixing with context awareness
- Feature implementation
- Multi-file coordinated changes
- Dependency installation

### Code Reviewer Agent
- Code quality validation
- Best practices verification
- Performance analysis
- Security checks
- Test validation

### Security Scanner Agent
- Vulnerability detection
- CVE database queries
- Secret detection
- OWASP compliance checking
- Dependency security audit

### Test Writer Agent
- Unit test generation
- Integration test creation
- Code coverage analysis (target: 80%+)
- Edge case detection
- Test framework setup

### Documentation Writer Agent
- README updates
- API documentation generation
- Docstring creation
- Changelog maintenance
- Documentation site generation (Docusaurus/MkDocs)

### Manager Agent
- Task decomposition
- Dependency mapping
- Execution plan creation
- Multi-step orchestration
- Progress monitoring

## 🔄 Event-Driven Workflow

```
GitHub Issue → Analyzer → Manager (creates plan) → Fixer → Reviewer
                                                        ↓
                                                   [Rejected?]
                                                        ↓
                                                   Self-Correct (max 3x)
                                                        ↓
                                                   [Approved?]
                                                        ↓
                                              Security Scanner → Test Writer
                                                        ↓
                                              Docs Writer → Human Approval
                                                        ↓
                                                    Create PR
```

## 🚀 Getting Started

### Development
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## 📊 System Configuration

See `src/config/agents.ts` for:
- Agent models and timeouts
- Max retry attempts
- System-wide settings
- Event types and message bus configuration

## 🔐 Security

- All code changes require human approval (HITL)
- Sandbox execution prevents unsafe code
- Security agent validates all changes
- Secrets detection enabled
- Audit logging for compliance

## 📈 Monitoring

The dashboard provides real-time visibility into:
- Active agent executions
- Task progress and status
- System performance metrics
- Error rates and retry attempts
- Agent reasoning and decision-making

## 🎨 UI Features

- **Real-time Updates**: Live status of agent executions
- **Log Streaming**: Terminal-style log viewer with filtering
- **Timeline View**: Detailed execution timelines with reasoning
- **Approval Interface**: Review and approve code changes
- **Stats Dashboard**: System-wide metrics and KPIs

## 🔮 Future Enhancements

- **Multi-LLM Support**: OpenAI, Anthropic, local models
- **Cost Tracking**: Token usage and API cost monitoring
- **A/B Testing**: Compare different agent strategies
- **Learning System**: Improve agents based on approval rates
- **Custom Agents**: Plugin system for domain-specific agents

## 📝 Development Notes

This is the **base architecture setup**. The UI is fully functional with mock data. Next phases will implement:
1. Backend API integration
2. Real agent orchestration
3. RAG and vector database
4. GitHub API connectivity
5. Production deployment

---

**Status**: 🟢 Base Architecture Complete - Ready for Phase 1 Implementation
