import { OllamaService } from './OllamaService';
import { CodebaseRAGService } from './CodebaseRAGService';
import { ContextManager } from './ContextManager';
import { PrismaClient } from '@prisma/client';
import fs from 'fs/promises';
import path from 'path';

const prisma = new PrismaClient();

export interface PlanStep {
  step: number;
  description: string;
  files: string[];
  dependencies: number[]; // Which steps must complete first
  estimatedComplexity: 'low' | 'medium' | 'high';
  agent: 'fixer' | 'test_writer' | 'docs_writer';
}

export interface ExecutionPlan {
  issueId: string;
  title: string;
  analysis: string;
  steps: PlanStep[];
  estimatedTime: string;
  riskLevel: 'low' | 'medium' | 'high';
  requiresHumanReview: boolean;
}

export interface ReActThought {
  thought: string;
  action: string;
  observation: string;
  reasoning: string;
  timestamp: Date;
}

export class ManagerAgent {
  private ollama: OllamaService;
  private rag: CodebaseRAGService;
  private contextManager: ContextManager;

  constructor() {
    this.ollama = new OllamaService();
    this.rag = new CodebaseRAGService();
    this.contextManager = new ContextManager();
  }

  /**
   * Main planning function - creates step-by-step execution plan
   */
  async createExecutionPlan(
    repositoryId: string,
    issueId: string,
    issueTitle: string,
    issueBody: string
  ): Promise<ExecutionPlan> {
    console.log(`[ManagerAgent] Creating execution plan for issue: ${issueTitle}`);

    // Step 1: Analyze the issue with ReAct pattern
    const analysis = await this.analyzeIssueWithReAct(
      repositoryId,
      issueTitle,
      issueBody
    );

    // Step 2: Identify affected files
    const affectedFiles = await this.identifyAffectedFiles(
      repositoryId,
      issueTitle,
      issueBody,
      analysis
    );

    // Step 3: Generate step-by-step plan
    const steps = await this.generateSteps(
      repositoryId,
      issueTitle,
      issueBody,
      affectedFiles,
      analysis
    );

    // Step 4: Calculate risk and complexity
    const riskLevel = this.calculateRiskLevel(steps, affectedFiles);
    const estimatedTime = this.estimateCompletionTime(steps);
    const requiresHumanReview = riskLevel === 'high' || steps.length > 5;

    const plan: ExecutionPlan = {
      issueId,
      title: issueTitle,
      analysis: analysis.summary,
      steps,
      estimatedTime,
      riskLevel,
      requiresHumanReview,
    };

    // Save plan to database
    await this.savePlan(plan);

    console.log(`[ManagerAgent] Created plan with ${steps.length} steps`);
    return plan;
  }

  /**
   * ReAct Pattern: Thought -> Action -> Observation -> Reasoning
   */
  private async analyzeIssueWithReAct(
    repositoryId: string,
    issueTitle: string,
    issueBody: string
  ): Promise<{ thoughts: ReActThought[]; summary: string }> {
    const thoughts: ReActThought[] = [];
    
    // Load ReAct prompt
    const reactPrompt = await this.loadPrompt('manager_react_v1.txt');

    // Iteration 1: Initial understanding
    const thought1 = await this.reactIteration(
      repositoryId,
      reactPrompt,
      issueTitle,
      issueBody,
      null,
      thoughts
    );
    thoughts.push(thought1);

    // Iteration 2: Code investigation
    const thought2 = await this.reactIteration(
      repositoryId,
      reactPrompt,
      issueTitle,
      issueBody,
      thought1.action,
      thoughts
    );
    thoughts.push(thought2);

    // Iteration 3: Root cause analysis
    const thought3 = await this.reactIteration(
      repositoryId,
      reactPrompt,
      issueTitle,
      issueBody,
      thought2.action,
      thoughts
    );
    thoughts.push(thought3);

    // Generate summary
    const summary = await this.generateAnalysisSummary(thoughts);

    return { thoughts, summary };
  }

  /**
   * Single ReAct iteration
   */
  private async reactIteration(
    repositoryId: string,
    prompt: string,
    issueTitle: string,
    issueBody: string,
    previousAction: string | null,
    previousThoughts: ReActThought[]
  ): Promise<ReActThought> {
    // Get relevant context from codebase
    const context = await this.rag.getRelevantContext(
      repositoryId,
      issueTitle + ' ' + issueBody,
      5
    );

    // Build prompt with history
    const fullPrompt = this.buildReActPrompt(
      prompt,
      issueTitle,
      issueBody,
      context,
      previousThoughts
    );

    // Get LLM response
    const response = await this.ollama.chat([
      { role: 'system', content: fullPrompt },
      { role: 'user', content: previousAction || 'Begin analysis.' }
    ]);

    // Parse response into thought, action, observation
    const parsed = this.parseReActResponse(response);

    return {
      ...parsed,
      timestamp: new Date(),
    };
  }

  /**
   * Parse ReAct format response
   */
  private parseReActResponse(response: string): Omit<ReActThought, 'timestamp'> {
    const thoughtMatch = response.match(/Thought:\s*(.+?)(?=\n(?:Action|Observation|Reasoning|$))/s);
    const actionMatch = response.match(/Action:\s*(.+?)(?=\n(?:Observation|Reasoning|$))/s);
    const observationMatch = response.match(/Observation:\s*(.+?)(?=\n(?:Reasoning|$))/s);
    const reasoningMatch = response.match(/Reasoning:\s*(.+?)$/s);

    return {
      thought: thoughtMatch?.[1]?.trim() || 'No thought provided',
      action: actionMatch?.[1]?.trim() || 'No action specified',
      observation: observationMatch?.[1]?.trim() || 'No observation made',
      reasoning: reasoningMatch?.[1]?.trim() || 'No reasoning provided',
    };
  }

  /**
   * Build ReAct prompt with context
   */
  private buildReActPrompt(
    basePrompt: string,
    issueTitle: string,
    issueBody: string,
    context: any[],
    previousThoughts: ReActThought[]
  ): string {
    let prompt = basePrompt
      .replace('{{ISSUE_TITLE}}', issueTitle)
      .replace('{{ISSUE_BODY}}', issueBody);

    // Add context
    const contextStr = context.map((c, i) => 
      `[Context ${i + 1}] ${c.metadata.file_path}:\n${c.content}`
    ).join('\n\n');
    prompt = prompt.replace('{{CONTEXT}}', contextStr);

    // Add previous thoughts
    if (previousThoughts.length > 0) {
      const historyStr = previousThoughts.map((t, i) =>
        `[Iteration ${i + 1}]\nThought: ${t.thought}\nAction: ${t.action}\nObservation: ${t.observation}\nReasoning: ${t.reasoning}`
      ).join('\n\n');
      prompt += `\n\nPrevious Analysis:\n${historyStr}`;
    }

    return prompt;
  }

  /**
   * Identify all files affected by the issue
   */
  private async identifyAffectedFiles(
    repositoryId: string,
    issueTitle: string,
    issueBody: string,
    analysis: { thoughts: ReActThought[]; summary: string }
  ): Promise<string[]> {
    const prompt = await this.loadPrompt('manager_file_identification_v1.txt');

    const fullPrompt = prompt
      .replace('{{ISSUE_TITLE}}', issueTitle)
      .replace('{{ISSUE_BODY}}', issueBody)
      .replace('{{ANALYSIS}}', analysis.summary);

    // Search for relevant files
    const searchResults = await this.rag.semanticSearch(
      repositoryId,
      issueTitle + ' ' + issueBody,
      20
    );

    const contextStr = searchResults.map(r => r.metadata.file_path).join('\n');

    const response = await this.ollama.chat([
      { role: 'system', content: fullPrompt },
      { role: 'user', content: `Relevant files found:\n${contextStr}\n\nList all files that need to be modified.` }
    ]);

    // Parse file list from response
    const files = response
      .split('\n')
      .filter(line => line.match(/^[\w\/\.-]+\.(py|js|ts|tsx|jsx|java|go|rs|cpp|c|h)$/))
      .map(f => f.trim());

    return [...new Set(files)]; // Remove duplicates
  }

  /**
   * Generate step-by-step execution plan
   */
  private async generateSteps(
    repositoryId: string,
    issueTitle: string,
    issueBody: string,
    affectedFiles: string[],
    analysis: { thoughts: ReActThought[]; summary: string }
  ): Promise<PlanStep[]> {
    const prompt = await this.loadPrompt('manager_step_planning_v1.txt');

    const fullPrompt = prompt
      .replace('{{ISSUE_TITLE}}', issueTitle)
      .replace('{{ISSUE_BODY}}', issueBody)
      .replace('{{ANALYSIS}}', analysis.summary)
      .replace('{{FILES}}', affectedFiles.join('\n'));

    const response = await this.ollama.chat([
      { role: 'system', content: fullPrompt },
      { role: 'user', content: 'Create a detailed step-by-step plan.' }
    ]);

    // Parse steps from response
    const steps = this.parseStepsFromResponse(response, affectedFiles);

    return steps;
  }

  /**
   * Parse steps from LLM response
   */
  private parseStepsFromResponse(response: string, allFiles: string[]): PlanStep[] {
    const steps: PlanStep[] = [];
    const stepMatches = response.matchAll(/Step (\d+):\s*(.+?)(?=\nStep \d+:|$)/gs);

    let stepNumber = 1;
    for (const match of stepMatches) {
      const description = match[2].trim();
      
      // Extract files mentioned in this step
      const stepFiles = allFiles.filter(file => 
        description.toLowerCase().includes(file.toLowerCase())
      );

      // Extract dependencies
      const depMatches = description.matchAll(/(?:depends on|after|requires) step (\d+)/gi);
      const dependencies = Array.from(depMatches, m => parseInt(m[1]));

      // Determine complexity
      const complexity = this.determineStepComplexity(description, stepFiles);

      // Determine agent
      const agent = this.determineAgentForStep(description);

      steps.push({
        step: stepNumber++,
        description,
        files: stepFiles,
        dependencies,
        estimatedComplexity: complexity,
        agent,
      });
    }

    return steps;
  }

  /**
   * Determine complexity of a step
   */
  private determineStepComplexity(
    description: string,
    files: string[]
  ): 'low' | 'medium' | 'high' {
    const desc = description.toLowerCase();
    
    if (files.length > 3) return 'high';
    if (desc.includes('database') || desc.includes('migration')) return 'high';
    if (desc.includes('refactor') || desc.includes('redesign')) return 'high';
    if (desc.includes('test') || desc.includes('documentation')) return 'low';
    
    return 'medium';
  }

  /**
   * Determine which agent should handle a step
   */
  private determineAgentForStep(description: string): 'fixer' | 'test_writer' | 'docs_writer' {
    const desc = description.toLowerCase();
    
    if (desc.includes('test') || desc.includes('testing')) return 'test_writer';
    if (desc.includes('document') || desc.includes('readme')) return 'docs_writer';
    
    return 'fixer';
  }

  /**
   * Calculate overall risk level
   */
  private calculateRiskLevel(steps: PlanStep[], files: string[]): 'low' | 'medium' | 'high' {
    const highComplexityCount = steps.filter(s => s.estimatedComplexity === 'high').length;
    
    if (highComplexityCount > 2 || files.length > 10) return 'high';
    if (highComplexityCount > 0 || files.length > 5) return 'medium';
    
    return 'low';
  }

  /**
   * Estimate completion time
   */
  private estimateCompletionTime(steps: PlanStep[]): string {
    const minutes = steps.reduce((total, step) => {
      switch (step.estimatedComplexity) {
        case 'low': return total + 5;
        case 'medium': return total + 15;
        case 'high': return total + 30;
      }
    }, 0);

    if (minutes < 60) return `${minutes} minutes`;
    const hours = Math.round(minutes / 60 * 10) / 10;
    return `${hours} hours`;
  }

  /**
   * Generate analysis summary from thoughts
   */
  private async generateAnalysisSummary(thoughts: ReActThought[]): Promise<string> {
    const thoughtsStr = thoughts.map(t => 
      `${t.thought}\nAction: ${t.action}\nObservation: ${t.observation}`
    ).join('\n\n');

    const prompt = `Summarize the following analysis into a concise paragraph:\n\n${thoughtsStr}\n\nSummary:`;

    const summary = await this.ollama.chat([
      { role: 'user', content: prompt }
    ]);

    return summary.trim();
  }

  /**
   * Save plan to database
   */
  private async savePlan(plan: ExecutionPlan): Promise<void> {
    await prisma.$executeRaw`
      INSERT INTO execution_plans (
        issue_id, title, analysis, steps, estimated_time, risk_level, requires_human_review
      ) VALUES (
        ${plan.issueId},
        ${plan.title},
        ${plan.analysis},
        ${JSON.stringify(plan.steps)}::jsonb,
        ${plan.estimatedTime},
        ${plan.riskLevel},
        ${plan.requiresHumanReview}
      )
    `;
  }

  /**
   * Load prompt from file
   */
  private async loadPrompt(filename: string): Promise<string> {
    const promptPath = path.join(process.cwd(), 'server', 'prompts', 'manager', filename);
    return await fs.readFile(promptPath, 'utf-8');
  }

  /**
   * Execute plan step by step
   */
  async executePlan(planId: string): Promise<void> {
    console.log(`[ManagerAgent] Executing plan: ${planId}`);
    
    // Get plan from database
    const plan = await this.getPlan(planId);
    
    // Execute steps in dependency order
    const executed = new Set<number>();
    
    while (executed.size < plan.steps.length) {
      // Find next executable step
      const nextStep = plan.steps.find(step => 
        !executed.has(step.step) &&
        step.dependencies.every(dep => executed.has(dep))
      );

      if (!nextStep) {
        throw new Error('Circular dependency detected in plan');
      }

      // Execute step
      await this.executeStep(plan, nextStep);
      executed.add(nextStep.step);

      console.log(`[ManagerAgent] Completed step ${nextStep.step}/${plan.steps.length}`);
    }

    console.log(`[ManagerAgent] Plan execution complete`);
  }

  /**
   * Execute a single step
   */
  private async executeStep(plan: ExecutionPlan, step: PlanStep): Promise<void> {
    // This would integrate with CodeFixerAgent, TestWriterAgent, etc.
    // For now, just log the step
    console.log(`[ManagerAgent] Executing Step ${step.step}: ${step.description}`);
    console.log(`  Files: ${step.files.join(', ')}`);
    console.log(`  Agent: ${step.agent}`);
    console.log(`  Complexity: ${step.estimatedComplexity}`);
  }

  /**
   * Get plan from database
   */
  private async getPlan(planId: string): Promise<ExecutionPlan> {
    const result = await prisma.$queryRaw<any[]>`
      SELECT * FROM execution_plans WHERE id = ${planId}
    `;

    if (result.length === 0) {
      throw new Error(`Plan not found: ${planId}`);
    }

    return result[0] as ExecutionPlan;
  }
}
