import { dockerExecutor, ExecutionResult, SandboxConfig } from './DockerExecutor';
import { logger } from '../../utils/logger';
import { prisma } from '../../db';
import path from 'path';
import fs from 'fs/promises';

export interface TestConfig {
  repoPath: string;
  language: 'python' | 'node' | 'java' | 'go' | 'rust';
  testCommand: string;
  setupCommands?: string[];
  timeout?: number;
  retries?: number;
}

export interface TestRunResult {
  success: boolean;
  results: ExecutionResult[];
  totalPassed: number;
  totalFailed: number;
  compilationSuccess: boolean;
  errorMessages: string[];
  duration: number;
}

export class TestRunner {
  private defaultTimeout = 300000; // 5 minutes
  private defaultRetries = 3;

  async runTests(config: TestConfig): Promise<TestRunResult> {
    const startTime = Date.now();
    const results: ExecutionResult[] = [];
    const errorMessages: string[] = [];

    try {
      // Detect test framework and command if not provided
      if (!config.testCommand) {
        config.testCommand = await this.detectTestCommand(config.repoPath, config.language);
      }

      // First, verify compilation
      const compilationResult = await this.checkCompilation(config);
      results.push(compilationResult);

      if (!compilationResult.success) {
        return {
          success: false,
          results,
          totalPassed: 0,
          totalFailed: 0,
          compilationSuccess: false,
          errorMessages: compilationResult.compilationErrors || [compilationResult.stderr],
          duration: Date.now() - startTime,
        };
      }

      // Run setup commands
      if (config.setupCommands) {
        for (const cmd of config.setupCommands) {
          await this.runSetupCommand(config.repoPath, cmd, config.language);
        }
      }

      // Run tests
      const sandboxConfig: SandboxConfig = {
        language: config.language,
        timeout: config.timeout || this.defaultTimeout,
        memory: 2048,
        cpus: 2,
        networkEnabled: true,
      };

      const testResult = await dockerExecutor.runTests(
        config.repoPath,
        config.testCommand,
        sandboxConfig
      );

      results.push(testResult);

      const totalPassed = testResult.testsPassed || 0;
      const totalFailed = testResult.testsFailed || 0;

      if (!testResult.success) {
        errorMessages.push(...this.parseErrorMessages(testResult.stderr));
      }

      return {
        success: testResult.success && totalFailed === 0,
        results,
        totalPassed,
        totalFailed,
        compilationSuccess: true,
        errorMessages,
        duration: Date.now() - startTime,
      };

    } catch (error) {
      logger.error('Test run failed:', error);
      errorMessages.push(error instanceof Error ? error.message : 'Unknown error');

      return {
        success: false,
        results,
        totalPassed: 0,
        totalFailed: 0,
        compilationSuccess: false,
        errorMessages,
        duration: Date.now() - startTime,
      };
    }
  }

  async runTestsWithRetry(
    config: TestConfig,
    onFailure?: (errors: string[]) => Promise<void>
  ): Promise<TestRunResult> {
    const maxRetries = config.retries || this.defaultRetries;
    let lastResult: TestRunResult | null = null;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      logger.info(`Test attempt ${attempt}/${maxRetries}`);

      lastResult = await this.runTests(config);

      if (lastResult.success) {
        logger.info(`Tests passed on attempt ${attempt}`);
        return lastResult;
      }

      if (attempt < maxRetries && onFailure) {
        logger.info(`Tests failed, triggering retry callback...`);
        await onFailure(lastResult.errorMessages);
      }
    }

    logger.warn(`Tests failed after ${maxRetries} attempts`);
    return lastResult!;
  }

  private async checkCompilation(config: TestConfig): Promise<ExecutionResult> {
    const compileCommands: Record<string, string> = {
      python: 'python -m py_compile **/*.py',
      node: 'npx tsc --noEmit || node --check **/*.js',
      java: 'javac -d build src/**/*.java',
      go: 'go build ./...',
      rust: 'cargo check',
    };

    const command = compileCommands[config.language];
    if (!command) {
      return {
        success: true,
        stdout: 'Compilation check not applicable',
        stderr: '',
        exitCode: 0,
        duration: 0,
      };
    }

    const sandboxConfig: SandboxConfig = {
      language: config.language,
      timeout: 60000, // 1 minute for compilation
      memory: 1024,
      cpus: 2,
      networkEnabled: false,
    };

    try {
      return await dockerExecutor.runTests(config.repoPath, command, sandboxConfig);
    } catch (error) {
      return {
        success: false,
        stdout: '',
        stderr: error instanceof Error ? error.message : 'Compilation failed',
        exitCode: 1,
        duration: 0,
        compilationErrors: [error instanceof Error ? error.message : 'Unknown error'],
      };
    }
  }

  private async detectTestCommand(repoPath: string, language: string): Promise<string> {
    const detectors: Record<string, () => Promise<string>> = {
      python: async () => {
        if (await this.fileExists(path.join(repoPath, 'pytest.ini'))) return 'pytest -v';
        if (await this.fileExists(path.join(repoPath, 'setup.py'))) return 'python -m unittest discover';
        return 'pytest -v';
      },
      node: async () => {
        const pkgJson = await this.readPackageJson(repoPath);
        if (pkgJson?.scripts?.test) return 'npm test';
        if (await this.fileExists(path.join(repoPath, 'jest.config.js'))) return 'npx jest';
        if (await this.fileExists(path.join(repoPath, '.mocharc.json'))) return 'npx mocha';
        return 'npm test';
      },
      java: async () => {
        if (await this.fileExists(path.join(repoPath, 'pom.xml'))) return 'mvn test';
        if (await this.fileExists(path.join(repoPath, 'build.gradle'))) return 'gradle test';
        return 'mvn test';
      },
      go: async () => 'go test ./...',
      rust: async () => 'cargo test',
    };

    const detector = detectors[language];
    return detector ? await detector() : 'echo "No test command detected"';
  }

  private async fileExists(filepath: string): Promise<boolean> {
    try {
      await fs.access(filepath);
      return true;
    } catch {
      return false;
    }
  }

  private async readPackageJson(repoPath: string): Promise<any> {
    try {
      const content = await fs.readFile(path.join(repoPath, 'package.json'), 'utf-8');
      return JSON.parse(content);
    } catch {
      return null;
    }
  }

  private async runSetupCommand(
    repoPath: string,
    command: string,
    language: 'python' | 'node' | 'java' | 'go' | 'rust'
  ): Promise<void> {
    const sandboxConfig: SandboxConfig = {
      language,
      timeout: 60000,
      memory: 1024,
      cpus: 1,
      networkEnabled: true,
    };

    await dockerExecutor.runTests(repoPath, command, sandboxConfig);
  }

  private parseErrorMessages(stderr: string): string[] {
    const lines = stderr.split('\n');
    const errors: string[] = [];

    for (const line of lines) {
      if (
        line.includes('FAILED') ||
        line.includes('Error:') ||
        line.includes('error:') ||
        line.includes('AssertionError') ||
        line.includes('Exception')
      ) {
        errors.push(line.trim());
      }
    }

    return errors.slice(0, 20); // Limit to 20 most relevant errors
  }

  async validateCodeChange(
    originalRepoPath: string,
    modifiedFiles: Map<string, string>,
    language: 'python' | 'node' | 'java' | 'go' | 'rust'
  ): Promise<{
    valid: boolean;
    testResults: TestRunResult;
    errors: string[];
  }> {
    // Create temporary repo with modified files
    const tempPath = path.join(process.cwd(), 'temp', `validate-${Date.now()}`);
    
    try {
      // Copy original repo
      await this.copyRepo(originalRepoPath, tempPath);

      // Apply modifications
      for (const [filepath, content] of modifiedFiles) {
        await fs.writeFile(path.join(tempPath, filepath), content);
      }

      // Run tests
      const testResults = await this.runTests({
        repoPath: tempPath,
        language,
        testCommand: await this.detectTestCommand(tempPath, language),
      });

      // Cleanup
      await fs.rm(tempPath, { recursive: true, force: true });

      return {
        valid: testResults.success,
        testResults,
        errors: testResults.errorMessages,
      };

    } catch (error) {
      await fs.rm(tempPath, { recursive: true, force: true }).catch(() => {});
      
      return {
        valid: false,
        testResults: {
          success: false,
          results: [],
          totalPassed: 0,
          totalFailed: 0,
          compilationSuccess: false,
          errorMessages: [error instanceof Error ? error.message : 'Validation failed'],
          duration: 0,
        },
        errors: [error instanceof Error ? error.message : 'Validation failed'],
      };
    }
  }

  private async copyRepo(src: string, dest: string): Promise<void> {
    await fs.mkdir(dest, { recursive: true });
    const entries = await fs.readdir(src, { withFileTypes: true });

    for (const entry of entries) {
      const srcPath = path.join(src, entry.name);
      const destPath = path.join(dest, entry.name);

      if (entry.isDirectory()) {
        if (!entry.name.startsWith('.') && entry.name !== 'node_modules' && entry.name !== '__pycache__') {
          await this.copyRepo(srcPath, destPath);
        }
      } else {
        await fs.copyFile(srcPath, destPath);
      }
    }
  }

  async getTestCoverage(repoPath: string, language: string): Promise<{
    coverage: number;
    coveredLines: number;
    totalLines: number;
  }> {
    const coverageCommands: Record<string, string> = {
      python: 'pytest --cov=. --cov-report=json',
      node: 'npx jest --coverage --coverageReporters=json',
      java: 'mvn test jacoco:report',
      go: 'go test -coverprofile=coverage.out ./...',
      rust: 'cargo tarpaulin --out Json',
    };

    const command = coverageCommands[language];
    if (!command) {
      return { coverage: 0, coveredLines: 0, totalLines: 0 };
    }

    const sandboxConfig: SandboxConfig = {
      language: language as any,
      timeout: 300000,
      memory: 2048,
      cpus: 2,
      networkEnabled: true,
    };

    try {
      const result = await dockerExecutor.runTests(repoPath, command, sandboxConfig);
      
      // Parse coverage from output (simplified - would need proper JSON parsing)
      const coverageMatch = result.stdout.match(/(\d+)%/);
      const coverage = coverageMatch ? parseInt(coverageMatch[1]) : 0;

      return {
        coverage,
        coveredLines: 0,
        totalLines: 0,
      };

    } catch {
      return { coverage: 0, coveredLines: 0, totalLines: 0 };
    }
  }
}

export const testRunner = new TestRunner();
