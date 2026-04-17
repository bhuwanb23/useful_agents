# File Guide - GitHub Agent System

## 📂 Complete File Structure

```
github-agent-system/
│
├── 📄 README.md                          ⭐ Start here - Project overview
├── 📄 ROADMAP.md                         📅 10-phase implementation plan
├── 📄 ARCHITECTURE.md                    🏗️ Technical architecture diagrams
├── 📄 PROJECT_SUMMARY.md                 📊 Executive summary & metrics
├── 📄 QUICK_START.md                     🚀 Quick reference guide
├── 📄 FILE_GUIDE.md                      📁 This file - Navigation help
│
├── 📁 src/
│   │
│   ├── 📄 App.tsx                        🎯 MAIN APP (450 lines)
│   │                                     → All 7 tab views
│   │                                     → State management
│   │                                     → Data integration
│   │
│   ├── 📄 main.tsx                       ⚡ React entry point
│   ├── 📄 index.css                      🎨 Tailwind imports
│   │
│   ├── 📁 components/                    🧩 UI Components (7 files)
│   │   ├── Layout.tsx                    → Header, footer, layout
│   │   ├── Navigation.tsx                → Tab navigation (7 tabs)
│   │   ├── StatCard.tsx                  → Metric cards
│   │   ├── AgentCard.tsx                 → Agent status cards
│   │   ├── IssueCard.tsx                 → GitHub issue display
│   │   ├── LogViewer.tsx                 → Terminal-style logs
│   │   └── ExecutionTimeline.tsx         → Agent execution view
│   │
│   ├── 📁 types/                         📐 TypeScript Definitions
│   │   └── index.ts                      → All type definitions
│   │                                     → 9 main interfaces
│   │                                     → 6 enums
│   │
│   ├── 📁 config/                        ⚙️ Configuration
│   │   └── agents.ts                     → 7 agent configs
│   │                                     → System settings
│   │                                     → Event types
│   │
│   ├── 📁 data/                          💾 Mock Data
│   │   └── mockData.ts                   → Repositories (3)
│   │                                     → Issues (3)
│   │                                     → Tasks (4)
│   │                                     → Executions (1)
│   │                                     → Logs (8)
│   │                                     → System stats
│   │
│   └── 📁 utils/                         🛠️ Utilities
│       └── cn.ts                         → Tailwind class merger
│
├── 📁 public/                            📦 Static Assets
│   └── (empty - ready for images)
│
├── 📁 dist/                              🏗️ Build Output
│   └── index.html                        → Production build (246 KB)
│
├── 📄 index.html                         📃 HTML template
├── 📄 package.json                       📦 Dependencies
├── 📄 tsconfig.json                      🔧 TypeScript config
└── 📄 vite.config.ts                     ⚡ Vite config

```

---

## 🎯 File Purposes - Quick Reference

### Documentation Files (6 files)

| File | Purpose | Lines | When to Read |
|------|---------|-------|--------------|
| **README.md** | Project overview, features, tech stack | 280 | First time setup |
| **ROADMAP.md** | Implementation plan (10 phases, 16 weeks) | 450 | Before starting development |
| **ARCHITECTURE.md** | Technical diagrams, data flow, scaling | 600 | Understanding system design |
| **PROJECT_SUMMARY.md** | Executive summary, metrics, status | 500 | Project overview for stakeholders |
| **QUICK_START.md** | Quick reference, customization guide | 350 | Daily development reference |
| **FILE_GUIDE.md** | This file - navigation help | 250 | When lost in files |

**Total Documentation**: ~2,430 lines

---

### Core Application Files (4 files)

#### 📄 `src/App.tsx` (450 lines) ⭐ MOST IMPORTANT
**What it does**: Main application with all 7 views
**Contains**:
- Tab routing logic
- Dashboard view (stats, issues, executions, logs)
- Repositories management view
- Issues tracking view
- Agents fleet view
- Executions monitoring view
- Logs viewer
- Approvals workflow view

**When to edit**:
- Adding new tabs
- Changing view layouts
- Updating data integration
- Modifying user workflows

**Key sections**:
```typescript
// Line 1-15: Imports
// Line 17-18: State management
// Line 20-165: Dashboard tab
// Line 167-210: Repositories tab
// Line 212-250: Issues tab
// Line 252-290: Agents tab
// Line 292-320: Executions tab
// Line 322-360: Logs tab
// Line 362-450: Approvals tab
```

---

#### 📄 `src/types/index.ts` (100 lines)
**What it does**: TypeScript type definitions
**Contains**:
- `AgentType`: 7 agent types
- `TaskStatus`: 7 status types
- `IssueType`: 4 issue types
- `Repository` interface
- `Issue` interface
- `Task` interface
- `AgentExecution` interface
- `LogEntry` interface
- `CodeChange` interface
- `Plan` interface
- `SystemStats` interface

**When to edit**:
- Adding new data structures
- Extending existing types
- Adding new agent types
- Modifying database schema

---

#### 📄 `src/config/agents.ts` (140 lines)
**What it does**: Agent configurations and system settings
**Contains**:
- `AGENT_CONFIGS`: 7 agent definitions
  - Analyzer Agent config
  - Fixer Agent config
  - Reviewer Agent config
  - Security Agent config
  - Test Writer Agent config
  - Docs Writer Agent config
  - Manager Agent config
- `SYSTEM_CONFIG`: Global settings
- `EVENT_TYPES`: Message bus events

**When to edit**:
- Changing agent models
- Adjusting timeouts/retries
- Modifying system settings
- Adding new event types

---

#### 📄 `src/data/mockData.ts` (180 lines)
**What it does**: Demo data for UI development
**Contains**:
- `mockRepositories`: 3 sample repos
- `mockIssues`: 3 sample issues
- `mockTasks`: 4 sample tasks
- `mockExecutions`: 1 active execution
- `mockLogs`: 8 log entries
- `mockSystemStats`: System metrics

**When to edit**:
- Adding demo scenarios
- Testing UI with different data
- Prototyping new features
- Development and testing

---

### UI Components (7 files - 700 lines total)

#### 📄 `src/components/Layout.tsx` (60 lines)
**What it renders**: 
```
┌─────────────────────────────────┐
│  Header (Logo, Title, Status)   │
├─────────────────────────────────┤
│                                 │
│         Main Content            │
│         (children)              │
│                                 │
├─────────────────────────────────┤
│  Footer (Tech stack info)       │
└─────────────────────────────────┘
```
**Props**: `{ children: ReactNode }`

---

#### 📄 `src/components/Navigation.tsx` (50 lines)
**What it renders**:
```
┌──────────┬──────────┬──────────┬──────────┐
│Dashboard │Repos     │Issues    │Agents    │...
└──────────┴──────────┴──────────┴──────────┘
```
**Props**: `{ activeTab: string, onTabChange: (tab) => void }`

---

#### 📄 `src/components/StatCard.tsx` (60 lines)
**What it renders**:
```
┌─────────────────────────┐
│ Active Monitoring    👁️ │
│                         │
│        2                │
│                         │
│ ↑ 12% vs last hour     │
└─────────────────────────┘
```
**Props**: `{ title, value, icon, trend?, color? }`

---

#### 📄 `src/components/AgentCard.tsx` (80 lines)
**What it renders**:
```
┌─────────────────────────────────┐
│ Code Fixer Agent      [running] │
│ Writes code to fix bugs         │
│                                 │
│ Model: ollama:codellama         │
│ Max Retries: 3 • Timeout: 60s   │
│                                 │
│ Active: 1    Completed: 5       │
│                                 │
│ Capabilities:                   │
│ [Code gen] [Bug fix] [+2 more]  │
└─────────────────────────────────┘
```
**Props**: `{ config, status, activeTasks?, completedToday? }`

---

#### 📄 `src/components/IssueCard.tsx` (90 lines)
**What it renders**:
```
┌─────────────────────────────────────────┐
│ 🐛 #142 Auth fails with OAuth2          │
│    acme-corp/web-app                    │
│                                         │
│ Users cannot login using Google         │
│ OAuth. Error 401 returned.              │
│                                         │
│ [bug]           Created 2h ago          │
└─────────────────────────────────────────┘
```
**Props**: `{ issue, repositoryName?, onSelect? }`

---

#### 📄 `src/components/LogViewer.tsx` (120 lines)
**What it renders**:
```
┌─ System Logs ──────────── 8 entries ─┐
│ ● ● ●                                │
├──────────────────────────────────────┤
│ 10:30:05 ℹ️ [INFO] Orchestrator     │
│          started monitoring...       │
│                                      │
│ 10:30:25 ⚠️ [WARNING] Code fix      │
│          attempt 1 rejected...       │
│                                      │
│ 10:31:00 ✓ [INFO] Code fix          │
│          attempt 2 approved          │
└──────────────────────────────────────┘
```
**Props**: `{ logs, maxHeight? }`

---

#### 📄 `src/components/ExecutionTimeline.tsx` (150 lines)
**What it renders**:
```
┌───────────────────────────────────────┐
│ [F] Fixer Agent        Running • 2m  │
├───────────────────────────────────────┤
│ 🧠 Reasoning:                         │
│ OAuth token validation failing...     │
├───────────────────────────────────────┤
│ Execution Timeline:                   │
│                                       │
│ ●─ +0s   [INFO] Starting analysis    │
│ │                                     │
│ ●─ +20s  [INFO] Retrieved embeddings │
│ │                                     │
│ ●─ +45s  [DEBUG] Found 3 modules     │
│ │                                     │
│ ●─ +90s  [WARNING] Attempt 1 failed  │
│ │                                     │
│ ●─ +120s [INFO] Applying fixes...    │
└───────────────────────────────────────┘
```
**Props**: `{ execution }`

---

### Configuration Files (3 files)

#### 📄 `package.json`
**Purpose**: Dependencies and scripts
**Key dependencies**:
- `react@19.2.3`
- `react-dom@19.2.3`
- `tailwindcss@4.1.17`
- `typescript@5.9.3`
- `vite@7.2.4`

**Scripts**:
```json
{
  "dev": "vite",
  "build": "vite build",
  "preview": "vite preview"
}
```

---

#### 📄 `tsconfig.json`
**Purpose**: TypeScript compiler settings
**Key settings**:
- Strict mode enabled
- JSX: React
- Module: ESNext
- Target: ES2020

---

#### 📄 `vite.config.ts`
**Purpose**: Vite build configuration
**Features**:
- React plugin
- Tailwind CSS
- Single-file build output
- TypeScript support

---

## 🎯 Editing Workflow

### To Add a New Feature

1. **Define types** in `src/types/index.ts`
2. **Create component** in `src/components/YourFeature.tsx`
3. **Add to App** in `src/App.tsx`
4. **Update config** if needed in `src/config/agents.ts`
5. **Add mock data** in `src/data/mockData.ts`

### To Modify Existing Feature

1. **Find component** in `src/components/`
2. **Check types** in `src/types/index.ts`
3. **Update component** logic
4. **Update App** if routing changed
5. **Test** with `npm run dev`

### To Change Styles

1. **Edit component** inline Tailwind classes
2. **Global styles** in `src/index.css`
3. **Colors**: Use slate (neutral), indigo (primary)
4. **Responsive**: sm, md, lg breakpoints

---

## 📊 File Statistics

| Category | Files | Lines | Purpose |
|----------|-------|-------|---------|
| **Documentation** | 6 | 2,430 | Guides, architecture, roadmap |
| **Application** | 1 | 450 | Main app (App.tsx) |
| **Components** | 7 | 700 | UI building blocks |
| **Configuration** | 3 | 420 | Types, config, mock data |
| **Setup** | 3 | 100 | Entry point, styles |
| **Config Files** | 3 | 200 | package.json, vite, tsconfig |
| **TOTAL** | 23 | 4,300 | Complete project |

---

## 🚦 Reading Order for New Developers

### Day 1: Understanding
1. **README.md** - Get overview
2. **PROJECT_SUMMARY.md** - Understand goals
3. **QUICK_START.md** - Learn basics
4. **Run `npm run dev`** - See it live

### Day 2: Architecture
5. **ARCHITECTURE.md** - Understand design
6. **ROADMAP.md** - See implementation plan
7. **src/types/index.ts** - Learn data structures
8. **src/config/agents.ts** - Understand agents

### Day 3: Code Exploration
9. **src/App.tsx** - Main application flow
10. **src/components/** - UI components
11. **src/data/mockData.ts** - Sample data
12. **Start coding!**

---

## 🔍 Quick Find

### "Where is...?"

| Looking for... | File | Line |
|---------------|------|------|
| Agent definitions | `src/config/agents.ts` | 8-105 |
| Type definitions | `src/types/index.ts` | 1-100 |
| Mock repositories | `src/data/mockData.ts` | 8-28 |
| Mock issues | `src/data/mockData.ts` | 30-60 |
| Dashboard view | `src/App.tsx` | 20-165 |
| Approval workflow | `src/App.tsx` | 362-450 |
| Navigation tabs | `src/components/Navigation.tsx` | 7-14 |
| Log viewer | `src/components/LogViewer.tsx` | 1-120 |
| System stats | `src/data/mockData.ts` | 160-168 |
| Event types | `src/config/agents.ts` | 125-148 |

---

## 🎨 Component Dependencies

```
App.tsx
├── Layout
│   └── (Header, Footer)
├── Navigation
├── StatCard (×4)
├── AgentCard (×7)
├── IssueCard (×N)
├── LogViewer
└── ExecutionTimeline
```

**Data Flow**:
```
mockData.ts → App.tsx → Components → UI
```

**Future Flow**:
```
WebSocket → State Manager → App.tsx → Components → UI
```

---

## 💡 Pro Tips

### File Navigation
- Use VS Code: `Cmd/Ctrl + P` to quick open
- Search in files: `Cmd/Ctrl + Shift + F`
- Symbol search: `Cmd/Ctrl + T`

### Component Development
- Hot reload enabled (changes show instantly)
- TypeScript errors in terminal
- Tailwind IntelliSense available

### Best Practices
- Keep components under 150 lines
- Extract reusable logic to utils
- Use TypeScript strict mode
- Follow existing patterns

---

## ✅ Checklist - File Understanding

- [ ] Read README.md
- [ ] Explored ARCHITECTURE.md
- [ ] Reviewed ROADMAP.md
- [ ] Understood src/types/index.ts
- [ ] Examined src/config/agents.ts
- [ ] Looked at src/data/mockData.ts
- [ ] Studied src/App.tsx structure
- [ ] Reviewed all 7 components
- [ ] Ran `npm run dev` successfully
- [ ] Built project with `npm run build`
- [ ] Understand data flow
- [ ] Know where to add features

---

**Total Files**: 23  
**Total Lines**: ~4,300  
**Languages**: TypeScript (95%), CSS (3%), Config (2%)  
**Components**: 7 reusable  
**Documentation**: Complete  

**Status**: ✅ Fully Documented - Ready to Navigate!
