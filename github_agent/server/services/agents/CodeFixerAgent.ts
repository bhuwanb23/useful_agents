import { selfCorrectionLoop } from './SelfCorrectionLoop';
import { ragService } from '../rag/RAGService';
import { ollamaClient } from '../ollama/OllamaClient';
import { promptManager } from '../prompts/PromptManager';
import { logger } from '../../utils/logger';
import { prisma } from '../../db';
import path from 'path';
import fs from 'fs/promises';

export interface FixRequest {
  taskId: string;
  issueId: string;
  repoPath: string;
  issueTitle: string;
  issueBody: string;
  language: 'python' | 'node' | 'java' | 'go' | 'rust';
  relevantFiles?: string[];
}

export interface FixResult {
  success: boolean;
  modifiedFiles: Map<string, string>;
  reasoning: string;
  attempts: number;
  duration: number;
  testsPassed: boolean;
  errors?: string[];
}

export class CodeFixerAgent {
  private agentType = 'fixer';

  async fix(request: FixRequest): Promise<FixResult> {
    const startTime = Date.now();
    logger.info(`CodeFixerAgent starting fix for issue ${request.issueId}`);

    try {
      // Step 1: Analyze issue and find relevant code
      const context = await this.gatherContext(request);

      // Step 2: Generate initial fix
      const initialFix = await this.generateFix(request, context);

      // Step 3: Execute self-correction loop with testing
      const correctionResult = await selfCorrectionLoop.executeWithCorrection(
        request.taskId,
        request.repoPath,
        request.language,
        initialFix.modifiedFiles,
        request.issueBody,
        this.agentType
      );

      // Step 4: Validate before PR
      if (correctionResult.success) {
        const validation = await selfCorrectionLoop.validateBeforePR(
          request.repoPath,
          correctionResult.finalFiles,
          request.language
        );

        if (!validation.approved) {
          logger.warn('Fix validation failed:', validation.reasons);
          
          return {
            success: false,
            modifiedFiles: correctionResult.finalFiles,
            reasoning: `Validation failed: ${validation.reasons.join(', ')}`,
            attempts: correctionResult.attempts.length,
            duration: Date.now() - startTime,
            testsPassed: false,
            errors: validation.reasons,
          };
        }
      }

      // Log final result
      await this.logResult(request.taskId, correctionResult);

      return {
        success: correctionResult.success,
        modifiedFiles: correctionResult.finalFiles,
        reasoning: this.buildReasoning(correctionResult),
        attempts: correctionResult.attempts.length,
        duration: Date.now() - startTime,
        testsPassed: correctionResult.success,
        errors: correctionResult.errorMessages,
      };

    } catch (error) {
      logger.error('CodeFixerAgent error:', error);
      
      return {
        success: false,
        modifiedFiles: new Map(),
        reasoning: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        attempts: 0,
        duration: Date.now() - startTime,
        testsPassed: false,
        errors: [error instanceof Error ? error.message : 'Unknown error'],
      };
    }
  }

  private async gatherContext(request: FixRequest): Promise<{
    relevantCode: Array<{ file: string; content: string; score: number }>;
    relatedIssues: Array<{ id: string; title: string; solution?: string }>;
    stackTrace?: string;
  }> {
    logger.info('Gathering context for fix...');

    // Use RAG to find relevant code
    const searchQuery = `${request.issueTitle}\n${request.issueBody}`;
    const relevantCode = await ragService.searchCode(
      request.repoPath,
      searchQuery,
      10
    );

    // Extract stack trace if present
    const stackTrace = this.extractStackTrace(request.issueBody);

    // Find related issues (from database)
    const relatedIssues = await this.findRelatedIssues(request.issueTitle, request.repoPath);

    return {
      relevantCode,
      relatedIssues,
      stackTrace,
    };
  }

  private extractStackTrace(issueBody: string): string | undefined {
    // Look for common stack trace patterns
    const stackTracePatterns = [
      /Traceback \(most recent call last\):[\s\S]+?(?=\n\n|$)/,
      /Error:[\s\S]+?at .+:\d+:\d+/,
      /Exception in thread[\s\S]+?at .+\(.+:\d+\)/,
      /panic:[\s\S]+?goroutine \d+/,
    ];

    for (const pattern of stackTracePatterns) {
      const match = issueBody.match(pattern);
      if (match) {
        return match[0];
      }
    }

    return undefined;
  }

  private async findRelatedIssues(issueTitle: string, repoPath: string): Promise<
    Array<{ id: string; title: string; solution?: string }>
  > {
    try {
      const issues = await prisma.issue.findMany({
        where: {
          repository: { path: repoPath },
          status: 'closed',
        },
        take: 5,
        orderBy: { closedAt: 'desc' },
      });

      return issues.map(issue => ({
        id: issue.id,
        title: issue.title,
        solution: undefined, // Could be extracted from PR description
      }));
    } catch {
      return [];
    }
  }

  private async generateFix(
    request: FixRequest,
    context: Awaited<ReturnType<typeof this.gatherContext>>
  ): Promise<{
    modifiedFiles: Map<string, string>;
    reasoning: string;
  }> {
    logger.info('Generating fix using LLM...');

    // Build context for LLM
    const codeContext = context.relevantCode
      .slice(0, 5)
      .map(c => `// ${c.file} (relevance: ${c.score.toFixed(2)})\n${c.content}`)
      .join('\n\n---\n\n');

    const relatedContext = context.relatedIssues
      .map(i => `- ${i.title}`)
      .join('\n');

    // Get prompt
    const prompt = await promptManager.getPrompt('fixer', 1);
    
    const fullPrompt = prompt.content
      .replace('{issue_title}', request.issueTitle)
      .replace('{issue_body}', request.issueBody)
      .replace('{stack_trace}', context.stackTrace || 'No stack trace available')
      .replace('{code_context}', codeContext)
      .replace('{related_issues}', relatedContext || 'None');

    // Generate fix
    const response = await ollamaClient.generateWithModel(fullPrompt, 'deepseek-coder:33b');

    // Parse response
    const { modifiedFiles, reasoning } = this.parseFixResponse(response.response);

    logger.info(`Generated fix affecting ${modifiedFiles.size} files`);

    return { modifiedFiles, reasoning };
  }

  private parseFixResponse(response: string): {
    modifiedFiles: Map<string, string>;
    reasoning: string;
  } {
    const modifiedFiles = new Map<string, string>();
    let reasoning = '';

    // Extract reasoning
    const reasoningMatch = response.match(/(?:Reasoning|Analysis|Solution):?\s*(.+?)(?:\n\n|```)/s);
    if (reasoningMatch) {
      reasoning = reasoningMatch[1].trim();
    }

    // Extract file modifications
    const fileBlockRegex = /```(?:[\w]+)?\s*(?:\/\/|#)\s*(.+?)\n([\s\S]+?)```/g;
    let match;

    while ((match = fileBlockRegex.exec(response)) !== null) {
      const filepath = match[1].trim();
      const content = match[2].trim();
      modifiedFiles.set(filepath, content);
    }

    return { modifiedFiles, reasoning };
  }

  private buildReasoning(result: any): string {
    const parts: string[] = [];

    parts.push(`Fix completed in ${result.attempts.length} attempt(s)`);

    if (result.success) {
      parts.push('All tests passed');
    } else {
      parts.push('Failed to pass all tests');
    }

    result.attempts.forEach((attempt: any, idx: number) => {
      parts.push(`\nAttempt ${idx + 1}: ${attempt.llmReasoning}`);
      if (!attempt.success && attempt.testResults.errorMessages.length > 0) {
        parts.push(`  Errors: ${attempt.testResults.errorMessages.slice(0, 2).join(', ')}`);
      }
    });

    return parts.join('\n');
  }

  private async logResult(taskId: string, result: any): Promise<void> {
    try {
      await prisma.agentLog.create({
        data: {
          taskId,
          agentType: this.agentType,
          action: 'fix_complete',
          status: result.success ? 'success' : 'failed',
          metadata: {
            attempts: result.attempts.length,
            finalSuccess: result.success,
            filesModified: result.finalFiles.size,
            errors: result.errorMessages,
          },
        },
      });
    } catch (error) {
      logger.error('Failed to log result:', error);
    }
  }

  async quickFix(
    filePath: string,
    errorMessage: string,
    language: 'python' | 'node' | 'java' | 'go' | 'rust'
  ): Promise<string> {
    logger.info(`Quick fix for ${filePath}: ${errorMessage}`);

    const code = await fs.readFile(filePath, 'utf-8');

    const prompt = `You are a code fixing expert. Fix the following error:

Error: ${errorMessage}

File: ${filePath}
\`\`\`${language}
${code}
\`\`\`

Provide ONLY the corrected code, no explanations.`;

    const response = await ollamaClient.generateWithModel(prompt, 'deepseek-coder:7b');

    // Extract code from response
    const codeMatch = response.response.match(/```[\w]*\n([\s\S]+?)```/);
    return codeMatch ? codeMatch[1].trim() : response.response.trim();
  }

  async explainFix(modifiedFiles: Map<string, string>, issueDescription: string): Promise<string> {
    const changes = Array.from(modifiedFiles.entries())
      .map(([file, _]) => `- Modified ${file}`)
      .join('\n');

    const prompt = `Explain the following code changes made to fix this issue:

Issue: ${issueDescription}

Changes:
${changes}

Provide a clear, technical explanation suitable for a pull request description.`;

    const response = await ollamaClient.generateWithModel(prompt, 'llama3.1:8b');
    return response.response;
  }
}

export const codeFixerAgent = new CodeFixerAgent();
