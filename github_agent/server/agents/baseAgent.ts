import axios from 'axios';
import { config } from '../config';
import { logger } from '../utils/logger';
import { prisma } from '../index';
import { promptManager } from '../services/promptManager';

export interface AgentContext {
  issueId: number;
  repoId: number;
  attempt: number;
  maxAttempts: number;
  previousError?: string;
}

export interface AgentResult {
  success: boolean;
  output: string;
  error?: string;
  metadata?: Record<string, any>;
}

export abstract class BaseAgent {
  protected name: string;
  protected version: string;
  protected maxAttempts: number = 3;

  constructor(name: string, version: string = 'v1') {
    this.name = name;
    this.version = version;
  }

  async execute(context: AgentContext): Promise<AgentResult> {
    logger.info(`[${this.name}] Starting execution for issue ${context.issueId}`);

    for (let attempt = 1; attempt <= this.maxAttempts; attempt++) {
      try {
        const result = await this.run({ ...context, attempt });

        if (result.success) {
          logger.info(`[${this.name}] Success on attempt ${attempt}`);
          return result;
        }

        if (attempt < this.maxAttempts) {
          logger.warn(`[${this.name}] Attempt ${attempt} failed, retrying...`);
          context.previousError = result.error;
        }
      } catch (error: any) {
        logger.error(`[${this.name}] Error on attempt ${attempt}:`, error);
        
        if (attempt === this.maxAttempts) {
          return {
            success: false,
            output: '',
            error: error.message
          };
        }
        
        context.previousError = error.message;
      }
    }

    return {
      success: false,
      output: '',
      error: `Failed after ${this.maxAttempts} attempts`
    };
  }

  protected abstract run(context: AgentContext): Promise<AgentResult>;

  protected async callLLM(prompt: string, systemPrompt?: string): Promise<string> {
    try {
      const response = await axios.post(
        `${config.ollamaUrl}/api/generate`,
        {
          model: config.ollamaModel,
          prompt,
          system: systemPrompt,
          stream: false
        },
        { timeout: 120000 }
      );

      return response.data.response;
    } catch (error: any) {
      logger.error('LLM call failed:', error);
      throw new Error(`LLM error: ${error.message}`);
    }
  }

  protected async getPrompt(promptName: string): Promise<string> {
    return await promptManager.getPrompt(promptName, this.version);
  }

  protected async logThought(executionId: number, thought: string): Promise<void> {
    await prisma.agentLog.create({
      data: {
        executionId,
        agentType: this.name,
        logLevel: 'INFO',
        message: thought
      }
    });

    logger.info(`[${this.name}] ${thought}`);
  }
}
