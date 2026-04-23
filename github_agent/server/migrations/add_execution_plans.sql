-- Migration: Add execution_plans table
-- Stores Manager Agent planning data

CREATE TABLE IF NOT EXISTS execution_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  issue_id VARCHAR(255) NOT NULL,
  title TEXT NOT NULL,
  analysis TEXT NOT NULL,
  steps JSONB NOT NULL,
  estimated_time VARCHAR(100),
  risk_level VARCHAR(20) CHECK (risk_level IN ('low', 'medium', 'high')),
  requires_human_review BOOLEAN DEFAULT false,
  status VARCHAR(50) DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP
);

-- Index for fast issue lookup
CREATE INDEX IF NOT EXISTS idx_execution_plans_issue_id 
ON execution_plans(issue_id);

-- Index for status queries
CREATE INDEX IF NOT EXISTS idx_execution_plans_status 
ON execution_plans(status);

-- Table for storing individual step executions
CREATE TABLE IF NOT EXISTS plan_step_executions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id UUID REFERENCES execution_plans(id) ON DELETE CASCADE,
  step_number INTEGER NOT NULL,
  description TEXT NOT NULL,
  status VARCHAR(50) DEFAULT 'pending',
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  result JSONB,
  error TEXT,
  UNIQUE(plan_id, step_number)
);

-- Index for plan step lookups
CREATE INDEX IF NOT EXISTS idx_plan_step_executions_plan_id 
ON plan_step_executions(plan_id);

-- Table for Chain of Thought reasoning logs
CREATE TABLE IF NOT EXISTS cot_reasoning_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id UUID REFERENCES execution_plans(id) ON DELETE CASCADE,
  question TEXT NOT NULL,
  thoughts JSONB NOT NULL,
  conclusion TEXT,
  confidence DECIMAL(3,2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Comments
COMMENT ON TABLE execution_plans IS 'Stores execution plans created by Manager Agent';
COMMENT ON TABLE plan_step_executions IS 'Tracks individual step executions within a plan';
COMMENT ON TABLE cot_reasoning_logs IS 'Stores Chain of Thought reasoning for analysis';
