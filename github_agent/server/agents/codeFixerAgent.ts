import { BaseAgent, AgentContext, AgentResult } from './baseAgent';
import { codeSearch } from '../services/rag/codeSearch';
import { containerManager } from '../services/docker/containerManager';
import { prisma } from '../index';
import * as fs from 'fs/promises';
import * as path from 'path';

export class CodeFixerAgent extends BaseAgent {
  constructor() {
    super('CodeFixer', 'v1');
  }

  protected async run(context: AgentContext): Promise<AgentResult> {
    const issue = await prisma.issue.findUnique({
      where: { id: context.issueId },
      include: { repository: true }
    });

    if (!issue) {
      return { success: false, output: '', error: 'Issue not found' };
    }

    // Step 1: Get relevant context from RAG
    const { context: ragContext, sources } = await codeSearch.buildContextForIssue(context.issueId);

    // Step 2: Build prompt with context
    const basePrompt = await this.getPrompt('fixer');
    const fullPrompt = this.buildFixPrompt(basePrompt, issue, ragContext, context);

    // Step 3: Get fix from LLM
    const fixResponse = await this.callLLM(fullPrompt);
    const { filePath, code } = this.parseFixResponse(fixResponse);

    if (!filePath || !code) {
      return {
        success: false,
        output: fixResponse,
        error: 'Failed to parse fix response'
      };
    }

    // Step 4: Validate code doesn't break compilation
    const language = this.detectLanguage(filePath);
    const validation = await containerManager.validateCode(code, filePath, language);

    if (!validation.success) {
      return {
        success: false,
        output: code,
        error: `Code validation failed: ${validation.stderr}`,
        metadata: { filePath, validation }
      };
    }

    // Step 5: Run tests in sandbox
    const repoPath = issue.repository.clonePath || '';
    const testResult = await containerManager.runTests(repoPath, language);

    if (!testResult.success) {
      return {
        success: false,
        output: code,
        error: `Tests failed: ${testResult.stderr}`,
        metadata: { filePath, testResult }
      };
    }

    return {
      success: true,
      output: code,
      metadata: {
        filePath,
        sources: sources.map(s => s.filePath),
        validation,
        testResult
      }
    };
  }

  private buildFixPrompt(
    basePrompt: string,
    issue: any,
    ragContext: string,
    context: AgentContext
  ): string {
    let prompt = basePrompt
      .replace('{{ISSUE_TITLE}}', issue.title)
      .replace('{{ISSUE_DESCRIPTION}}', issue.description)
      .replace('{{RELEVANT_CODE}}', ragContext);

    if (context.previousError && context.attempt > 1) {
      prompt += `\n\nPREVIOUS ATTEMPT FAILED:\n${context.previousError}\n\nPlease fix the issues and try again.`;
    }

    return prompt;
  }

  private parseFixResponse(response: string): { filePath: string; code: string } {
    const filePathMatch = response.match(/FILE:\s*(.+)/);
    const codeMatch = response.match(/```[\w]*\n([\s\S]+?)\n```/);

    return {
      filePath: filePathMatch ? filePathMatch[1].trim() : '',
      code: codeMatch ? codeMatch[1] : ''
    };
  }

  private detectLanguage(filePath: string): string {
    const ext = path.extname(filePath);
    const langMap: Record<string, string> = {
      '.ts': 'typescript',
      '.tsx': 'typescript',
      '.js': 'javascript',
      '.jsx': 'javascript',
      '.py': 'python',
      '.java': 'java',
      '.go': 'go',
      '.rs': 'rust'
    };
    return langMap[ext] || 'unknown';
  }
}

export const codeFixerAgent = new CodeFixerAgent();
