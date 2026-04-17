import { testRunner, TestRunResult } from '../docker/TestRunner';
import { ollamaClient } from '../ollama/OllamaClient';
import { promptManager } from '../prompts/PromptManager';
import { logger } from '../../utils/logger';
import { prisma } from '../../db';

export interface CorrectionAttempt {
  attempt: number;
  modifiedFiles: Map<string, string>;
  testResults: TestRunResult;
  llmReasoning: string;
  success: boolean;
}

export interface SelfCorrectionResult {
  success: boolean;
  attempts: CorrectionAttempt[];
  finalFiles: Map<string, string>;
  totalDuration: number;
  errorMessages: string[];
}

export class SelfCorrectionLoop {
  private maxAttempts = 3;

  async executeWithCorrection(
    taskId: string,
    repoPath: string,
    language: 'python' | 'node' | 'java' | 'go' | 'rust',
    initialFiles: Map<string, string>,
    issueDescription: string,
    agentType: string = 'fixer'
  ): Promise<SelfCorrectionResult> {
    const startTime = Date.now();
    const attempts: CorrectionAttempt[] = [];
    let currentFiles = new Map(initialFiles);

    logger.info(`Starting self-correction loop for task ${taskId}`);

    for (let attempt = 1; attempt <= this.maxAttempts; attempt++) {
      logger.info(`Attempt ${attempt}/${this.maxAttempts}`);

      // Log attempt in database
      await this.logAttempt(taskId, attempt, 'running');

      // Run tests on current code
      const testResults = await testRunner.runTests({
        repoPath,
        language,
        testCommand: '', // Auto-detect
      });

      // Check if tests pass
      if (testResults.success && testResults.totalFailed === 0) {
        logger.info(`Tests passed on attempt ${attempt}!`);
        
        const correctionAttempt: CorrectionAttempt = {
          attempt,
          modifiedFiles: currentFiles,
          testResults,
          llmReasoning: 'Tests passed - no correction needed',
          success: true,
        };
        
        attempts.push(correctionAttempt);
        await this.logAttempt(taskId, attempt, 'success', testResults);

        return {
          success: true,
          attempts,
          finalFiles: currentFiles,
          totalDuration: Date.now() - startTime,
          errorMessages: [],
        };
      }

      // Tests failed - attempt correction
      logger.warn(`Tests failed on attempt ${attempt}. Errors:`, testResults.errorMessages);
      await this.logAttempt(taskId, attempt, 'failed', testResults);

      if (attempt < this.maxAttempts) {
        // Generate correction using LLM
        const correction = await this.generateCorrection(
          currentFiles,
          testResults,
          issueDescription,
          attempt,
          agentType
        );

        const correctionAttempt: CorrectionAttempt = {
          attempt,
          modifiedFiles: currentFiles,
          testResults,
          llmReasoning: correction.reasoning,
          success: false,
        };

        attempts.push(correctionAttempt);

        // Apply corrections
        currentFiles = correction.modifiedFiles;
        
        logger.info(`Applied corrections from LLM. Reasoning: ${correction.reasoning}`);
      } else {
        // Final attempt failed
        const correctionAttempt: CorrectionAttempt = {
          attempt,
          modifiedFiles: currentFiles,
          testResults,
          llmReasoning: 'Max attempts reached',
          success: false,
        };
        
        attempts.push(correctionAttempt);
      }
    }

    // All attempts exhausted
    logger.error(`Self-correction failed after ${this.maxAttempts} attempts`);

    return {
      success: false,
      attempts,
      finalFiles: currentFiles,
      totalDuration: Date.now() - startTime,
      errorMessages: attempts[attempts.length - 1].testResults.errorMessages,
    };
  }

  private async generateCorrection(
    currentFiles: Map<string, string>,
    testResults: TestRunResult,
    issueDescription: string,
    attemptNumber: number,
    agentType: string
  ): Promise<{
    modifiedFiles: Map<string, string>;
    reasoning: string;
  }> {
    // Build context from test failures
    const errorContext = this.buildErrorContext(testResults);

    // Get correction prompt
    const prompt = await promptManager.getPrompt(`${agentType}_correction`, 1);
    
    const fullPrompt = prompt.content
      .replace('{issue}', issueDescription)
      .replace('{attempt}', attemptNumber.toString())
      .replace('{errors}', errorContext)
      .replace('{code}', Array.from(currentFiles.entries())
        .map(([path, content]) => `// ${path}\n${content}`)
        .join('\n\n'));

    // Call LLM for correction
    const response = await ollamaClient.generateWithModel(fullPrompt, 'deepseek-coder:33b');

    // Parse LLM response
    const { reasoning, modifiedFiles } = this.parseCorrectionResponse(response.response, currentFiles);

    return { modifiedFiles, reasoning };
  }

  private buildErrorContext(testResults: TestRunResult): string {
    const context: string[] = [];

    if (!testResults.compilationSuccess) {
      context.push('COMPILATION ERRORS:');
      testResults.errorMessages.forEach(err => context.push(`  - ${err}`));
    }

    if (testResults.totalFailed > 0) {
      context.push(`\nTEST FAILURES (${testResults.totalFailed} failed):`);
      testResults.errorMessages.forEach(err => context.push(`  - ${err}`));
    }

    // Include stderr from test runs
    testResults.results.forEach(result => {
      if (result.stderr) {
        context.push('\nDETAILED ERROR OUTPUT:');
        context.push(result.stderr.slice(0, 2000)); // Limit to 2000 chars
      }
    });

    return context.join('\n');
  }

  private parseCorrectionResponse(
    response: string,
    originalFiles: Map<string, string>
  ): {
    reasoning: string;
    modifiedFiles: Map<string, string>;
  } {
    const modifiedFiles = new Map(originalFiles);
    let reasoning = 'LLM correction applied';

    // Extract reasoning (usually in markdown or after "Reasoning:" or "Analysis:")
    const reasoningMatch = response.match(/(?:Reasoning|Analysis|Thought):?\s*(.+?)(?:\n\n|```)/s);
    if (reasoningMatch) {
      reasoning = reasoningMatch[1].trim();
    }

    // Extract code blocks
    const codeBlockRegex = /```(?:[\w]+)?\s*(?:\/\/\s*(.+?))?\n([\s\S]+?)```/g;
    let match;

    while ((match = codeBlockRegex.exec(response)) !== null) {
      const filepath = match[1]?.trim() || 'unknown';
      const code = match[2].trim();

      // Try to match with existing files
      for (const [existingPath, _] of originalFiles) {
        if (existingPath.includes(filepath) || filepath.includes(existingPath)) {
          modifiedFiles.set(existingPath, code);
          break;
        }
      }
    }

    return { reasoning, modifiedFiles };
  }

  private async logAttempt(
    taskId: string,
    attempt: number,
    status: 'running' | 'success' | 'failed',
    testResults?: TestRunResult
  ): Promise<void> {
    try {
      await prisma.agentLog.create({
        data: {
          taskId,
          agentType: 'fixer',
          action: `correction_attempt_${attempt}`,
          status,
          metadata: testResults ? {
            passed: testResults.totalPassed,
            failed: testResults.totalFailed,
            compilationSuccess: testResults.compilationSuccess,
            errors: testResults.errorMessages.slice(0, 5),
            duration: testResults.duration,
          } : {},
        },
      });
    } catch (error) {
      logger.error('Failed to log correction attempt:', error);
    }
  }

  async validateBeforePR(
    repoPath: string,
    modifiedFiles: Map<string, string>,
    language: 'python' | 'node' | 'java' | 'go' | 'rust',
    minCoverage: number = 70
  ): Promise<{
    approved: boolean;
    reasons: string[];
    testResults: TestRunResult;
    coverage?: number;
  }> {
    const reasons: string[] = [];

    // 1. Run tests
    const validation = await testRunner.validateCodeChange(repoPath, modifiedFiles, language);

    if (!validation.valid) {
      reasons.push('Tests failed');
      reasons.push(...validation.errors.slice(0, 3));
      
      return {
        approved: false,
        reasons,
        testResults: validation.testResults,
      };
    }

    // 2. Check test coverage
    const coverageResult = await testRunner.getTestCoverage(repoPath, language);
    
    if (coverageResult.coverage < minCoverage) {
      reasons.push(`Test coverage too low: ${coverageResult.coverage}% (minimum: ${minCoverage}%)`);
      
      return {
        approved: false,
        reasons,
        testResults: validation.testResults,
        coverage: coverageResult.coverage,
      };
    }

    // 3. All checks passed
    return {
      approved: true,
      reasons: ['All tests passed', `Coverage: ${coverageResult.coverage}%`],
      testResults: validation.testResults,
      coverage: coverageResult.coverage,
    };
  }

  async executeWithFeedbackLoop(
    taskId: string,
    repoPath: string,
    language: 'python' | 'node' | 'java' | 'go' | 'rust',
    issueDescription: string,
    codeGenerator: (feedback?: string[]) => Promise<Map<string, string>>
  ): Promise<SelfCorrectionResult> {
    const startTime = Date.now();
    const attempts: CorrectionAttempt[] = [];
    let feedback: string[] | undefined = undefined;

    for (let attempt = 1; attempt <= this.maxAttempts; attempt++) {
      logger.info(`Feedback loop attempt ${attempt}/${this.maxAttempts}`);

      // Generate code (with feedback from previous attempt)
      const generatedFiles = await codeGenerator(feedback);

      // Validate code
      const validation = await testRunner.validateCodeChange(repoPath, generatedFiles, language);

      const correctionAttempt: CorrectionAttempt = {
        attempt,
        modifiedFiles: generatedFiles,
        testResults: validation.testResults,
        llmReasoning: feedback ? `Applied feedback: ${feedback.join(', ')}` : 'Initial attempt',
        success: validation.valid,
      };

      attempts.push(correctionAttempt);
      await this.logAttempt(taskId, attempt, validation.valid ? 'success' : 'failed', validation.testResults);

      if (validation.valid) {
        logger.info(`Feedback loop succeeded on attempt ${attempt}`);
        
        return {
          success: true,
          attempts,
          finalFiles: generatedFiles,
          totalDuration: Date.now() - startTime,
          errorMessages: [],
        };
      }

      // Prepare feedback for next iteration
      feedback = validation.errors;
      logger.info(`Attempt ${attempt} failed. Feedback: ${feedback.join(', ')}`);
    }

    logger.error(`Feedback loop exhausted after ${this.maxAttempts} attempts`);

    return {
      success: false,
      attempts,
      finalFiles: attempts[attempts.length - 1].modifiedFiles,
      totalDuration: Date.now() - startTime,
      errorMessages: attempts[attempts.length - 1].testResults.errorMessages,
    };
  }
}

export const selfCorrectionLoop = new SelfCorrectionLoop();
