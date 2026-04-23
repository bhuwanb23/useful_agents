import { OllamaService } from './OllamaService';
import { CodebaseRAGService } from './CodebaseRAGService';

export interface ThoughtStep {
  step: number;
  thought: string;
  reasoning: string;
  action: string;
  result?: any;
  timestamp: Date;
}

export interface CoTAnalysis {
  question: string;
  thoughts: ThoughtStep[];
  conclusion: string;
  confidence: number;
  totalSteps: number;
}

/**
 * Chain of Thought Service
 * Forces LLM to think step-by-step before acting
 */
export class ChainOfThoughtService {
  private ollama: OllamaService;
  private rag: CodebaseRAGService;

  constructor() {
    this.ollama = new OllamaService();
    this.rag = new CodebaseRAGService();
  }

  /**
   * Execute Chain of Thought reasoning
   */
  async analyze(
    repositoryId: string,
    question: string,
    maxSteps: number = 5
  ): Promise<CoTAnalysis> {
    const thoughts: ThoughtStep[] = [];
    
    console.log(`[CoT] Starting analysis: ${question}`);

    for (let step = 1; step <= maxSteps; step++) {
      const thoughtStep = await this.executeThoughtStep(
        repositoryId,
        question,
        thoughts,
        step
      );

      thoughts.push(thoughtStep);

      // Check if we've reached a conclusion
      if (this.hasReachedConclusion(thoughtStep)) {
        console.log(`[CoT] Reached conclusion at step ${step}`);
        break;
      }
    }

    // Generate final conclusion
    const conclusion = await this.generateConclusion(thoughts);
    const confidence = this.calculateConfidence(thoughts);

    return {
      question,
      thoughts,
      conclusion,
      confidence,
      totalSteps: thoughts.length,
    };
  }

  /**
   * Execute a single thought step
   */
  private async executeThoughtStep(
    repositoryId: string,
    question: string,
    previousThoughts: ThoughtStep[],
    stepNumber: number
  ): Promise<ThoughtStep> {
    // Get relevant context
    const context = await this.rag.getRelevantContext(
      repositoryId,
      question,
      3
    );

    // Build prompt
    const prompt = this.buildCoTPrompt(
      question,
      previousThoughts,
      context,
      stepNumber
    );

    // Get LLM response
    const response = await this.ollama.chat([
      { role: 'system', content: prompt },
      { role: 'user', content: stepNumber === 1 ? question : 'Continue reasoning.' }
    ]);

    // Parse response
    const parsed = this.parseThoughtStep(response);

    // Execute action if specified
    let result;
    if (parsed.action && parsed.action !== 'none') {
      result = await this.executeAction(repositoryId, parsed.action);
    }

    return {
      step: stepNumber,
      thought: parsed.thought,
      reasoning: parsed.reasoning,
      action: parsed.action,
      result,
      timestamp: new Date(),
    };
  }

  /**
   * Build Chain of Thought prompt
   */
  private buildCoTPrompt(
    question: string,
    previousThoughts: ThoughtStep[],
    context: any[],
    stepNumber: number
  ): string {
    let prompt = `You are analyzing a codebase using Chain of Thought reasoning.

Question: ${question}

Your task is to think step by step. For each step, provide:
1. **Thought**: What you're thinking about right now
2. **Reasoning**: Why this thought is important
3. **Action**: What you need to do next (or "none" if you have the answer)

`;

    // Add context
    if (context.length > 0) {
      prompt += 'Relevant Code:\n';
      context.forEach((c, i) => {
        prompt += `[${i + 1}] ${c.metadata.file_path}:\n${c.content}\n\n`;
      });
    }

    // Add previous thoughts
    if (previousThoughts.length > 0) {
      prompt += 'Previous Thoughts:\n';
      previousThoughts.forEach(t => {
        prompt += `Step ${t.step}:\n`;
        prompt += `  Thought: ${t.thought}\n`;
        prompt += `  Reasoning: ${t.reasoning}\n`;
        prompt += `  Action: ${t.action}\n`;
        if (t.result) {
          prompt += `  Result: ${JSON.stringify(t.result)}\n`;
        }
        prompt += '\n';
      });
    }

    prompt += `Now, provide Step ${stepNumber} of your reasoning.\n`;
    prompt += 'Format:\nThought: [your thought]\nReasoning: [why this matters]\nAction: [what to do next or "none"]\n';

    return prompt;
  }

  /**
   * Parse thought step from LLM response
   */
  private parseThoughtStep(response: string): {
    thought: string;
    reasoning: string;
    action: string;
  } {
    const thoughtMatch = response.match(/Thought:\s*(.+?)(?=\nReasoning:|$)/s);
    const reasoningMatch = response.match(/Reasoning:\s*(.+?)(?=\nAction:|$)/s);
    const actionMatch = response.match(/Action:\s*(.+?)$/s);

    return {
      thought: thoughtMatch?.[1]?.trim() || 'No thought provided',
      reasoning: reasoningMatch?.[1]?.trim() || 'No reasoning provided',
      action: actionMatch?.[1]?.trim() || 'none',
    };
  }

  /**
   * Execute an action (search, read file, etc.)
   */
  private async executeAction(repositoryId: string, action: string): Promise<any> {
    const lowerAction = action.toLowerCase();

    // Parse action
    if (lowerAction.includes('search for')) {
      const query = action.replace(/search for/i, '').trim();
      return await this.rag.semanticSearch(repositoryId, query, 5);
    }

    if (lowerAction.includes('find definition of')) {
      const symbol = action.replace(/find definition of/i, '').trim();
      return await this.rag.findDefinition(repositoryId, symbol);
    }

    if (lowerAction.includes('find usages of')) {
      const symbol = action.replace(/find usages of/i, '').trim();
      return await this.rag.findUsages(repositoryId, symbol);
    }

    // If action not recognized, return null
    return null;
  }

  /**
   * Check if we've reached a conclusion
   */
  private hasReachedConclusion(step: ThoughtStep): boolean {
    const action = step.action.toLowerCase();
    return (
      action === 'none' ||
      action.includes('conclude') ||
      action.includes('answer is') ||
      action.includes('solution is')
    );
  }

  /**
   * Generate final conclusion from all thoughts
   */
  private async generateConclusion(thoughts: ThoughtStep[]): Promise<string> {
    const thoughtsSummary = thoughts.map(t =>
      `Step ${t.step}: ${t.thought}`
    ).join('\n');

    const prompt = `Based on the following reasoning steps, provide a concise conclusion:

${thoughtsSummary}

Conclusion:`;

    const conclusion = await this.ollama.chat([
      { role: 'user', content: prompt }
    ]);

    return conclusion.trim();
  }

  /**
   * Calculate confidence score based on reasoning quality
   */
  private calculateConfidence(thoughts: ThoughtStep[]): number {
    let confidence = 0.5; // Start at 50%

    // More steps = more thorough = higher confidence (up to a point)
    if (thoughts.length >= 3) confidence += 0.1;
    if (thoughts.length >= 5) confidence += 0.1;

    // Actions taken = active investigation = higher confidence
    const actionsCount = thoughts.filter(t => t.action !== 'none' && t.result).length;
    confidence += Math.min(actionsCount * 0.1, 0.3);

    return Math.min(confidence, 1.0);
  }

  /**
   * Explain reasoning path in natural language
   */
  explainReasoning(analysis: CoTAnalysis): string {
    let explanation = `Analysis of: "${analysis.question}"\n\n`;
    
    explanation += 'Reasoning Path:\n';
    analysis.thoughts.forEach(t => {
      explanation += `\n${t.step}. ${t.thought}\n`;
      explanation += `   → Why: ${t.reasoning}\n`;
      if (t.action !== 'none') {
        explanation += `   → Action: ${t.action}\n`;
      }
    });

    explanation += `\nConclusion: ${analysis.conclusion}\n`;
    explanation += `Confidence: ${(analysis.confidence * 100).toFixed(0)}%\n`;

    return explanation;
  }
}
