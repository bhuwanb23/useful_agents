/**
 * Local Code Executor
 * Replaces DockerExecutor to run code directly on the OS
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import { logger } from '../../utils/logger';
import fs from 'fs/promises';
import path from 'path';

const execAsync = promisify(exec);

export interface ExecutionResult {
  success: boolean;
  stdout: string;
  stderr: string;
  exitCode: number;
  duration: number;
}

export class LocalExecutor {
  private sandboxDir: string;

  constructor() {
    this.sandboxDir = path.join(process.cwd(), 'temp_execution');
  }

  async initialize(): Promise<void> {
    await fs.mkdir(this.sandboxDir, { recursive: true });
    logger.info('LocalExecutor initialized (Docker bypassed)');
  }

  async executeCode(code: string, language: string): Promise<ExecutionResult> {
    const startTime = Date.now();
    const runId = Math.random().toString(36).substring(7);
    const fileName = this.getFileName(language, runId);
    const filePath = path.join(this.sandboxDir, fileName);

    try {
      await fs.writeFile(filePath, code);
      const command = this.getRunCommand(language, filePath);
      
      const { stdout, stderr } = await execAsync(command, { timeout: 30000 });

      return {
        success: true,
        stdout,
        stderr,
        exitCode: 0,
        duration: Date.now() - startTime
      };
    } catch (error: any) {
      return {
        success: false,
        stdout: error.stdout || '',
        stderr: error.stderr || error.message,
        exitCode: error.code || 1,
        duration: Date.now() - startTime
      };
    } finally {
      // Clean up file
      await fs.unlink(filePath).catch(() => {});
    }
  }

  private getFileName(lang: string, id: string) {
    if (lang === 'python') return `run_${id}.py`;
    return `run_${id}.js`;
  }

  private getRunCommand(lang: string, path: string) {
    if (lang === 'python') return `python3 ${path}`;
    return `node ${path}`;
  }
}

export const dockerExecutor = new LocalExecutor();
