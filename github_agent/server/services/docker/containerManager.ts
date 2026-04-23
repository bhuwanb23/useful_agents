import Docker from 'dockerode';
import * as path from 'path';
import { logger } from '../../utils/logger';

const docker = new Docker();

export interface TestResult {
  success: boolean;
  stdout: string;
  stderr: string;
  exitCode: number;
}

export class ContainerManager {
  async runTests(repoPath: string, language: string): Promise<TestResult> {
    logger.info(`Running tests for ${repoPath} (${language})`);

    const image = this.getTestImage(language);
    const command = this.getTestCommand(language);

    try {
      const container = await docker.createContainer({
        Image: image,
        Cmd: command,
        WorkingDir: '/workspace',
        HostConfig: {
          Binds: [`${repoPath}:/workspace:ro`],
          Memory: 512 * 1024 * 1024, // 512MB
          CpuShares: 512,
          NetworkMode: 'none', // Isolated
          AutoRemove: true
        },
        Tty: false
      });

      await container.start();

      const stream = await container.logs({
        follow: true,
        stdout: true,
        stderr: true
      });

      let stdout = '';
      let stderr = '';

      stream.on('data', (chunk: Buffer) => {
        const str = chunk.toString('utf8');
        if (str.startsWith('\u0001')) stdout += str.substring(8);
        else if (str.startsWith('\u0002')) stderr += str.substring(8);
      });

      const result = await container.wait();
      
      return {
        success: result.StatusCode === 0,
        stdout,
        stderr,
        exitCode: result.StatusCode
      };
    } catch (error: any) {
      logger.error('Test execution error:', error);
      return {
        success: false,
        stdout: '',
        stderr: error.message,
        exitCode: -1
      };
    }
  }

  async validateCode(code: string, filePath: string, language: string): Promise<TestResult> {
    logger.info(`Validating code for ${filePath}`);

    const image = this.getValidationImage(language);
    const command = this.getValidationCommand(language, filePath);

    try {
      const container = await docker.createContainer({
        Image: image,
        Cmd: command,
        WorkingDir: '/code',
        HostConfig: {
          Memory: 256 * 1024 * 1024,
          CpuShares: 256,
          NetworkMode: 'none',
          AutoRemove: true
        },
        Env: [`CODE=${Buffer.from(code).toString('base64')}`]
      });

      await container.start();
      const result = await container.wait();

      const logs = await container.logs({ stdout: true, stderr: true });
      const output = logs.toString('utf8');

      return {
        success: result.StatusCode === 0,
        stdout: output,
        stderr: result.StatusCode !== 0 ? output : '',
        exitCode: result.StatusCode
      };
    } catch (error: any) {
      logger.error('Code validation error:', error);
      return {
        success: false,
        stdout: '',
        stderr: error.message,
        exitCode: -1
      };
    }
  }

  async cleanupOldContainers(): Promise<void> {
    const containers = await docker.listContainers({ all: true });
    const oldContainers = containers.filter(c => 
      c.Labels['github-agent'] === 'test' &&
      Date.now() - c.Created * 1000 > 3600000 // 1 hour
    );

    for (const containerInfo of oldContainers) {
      try {
        const container = docker.getContainer(containerInfo.Id);
        await container.remove({ force: true });
        logger.info(`Cleaned up container ${containerInfo.Id}`);
      } catch (error) {
        logger.error(`Failed to cleanup container ${containerInfo.Id}:`, error);
      }
    }
  }

  private getTestImage(language: string): string {
    const images: Record<string, string> = {
      'typescript': 'node:20-alpine',
      'javascript': 'node:20-alpine',
      'python': 'python:3.11-alpine',
      'java': 'openjdk:17-alpine',
      'go': 'golang:1.21-alpine',
      'rust': 'rust:1.75-alpine'
    };
    return images[language] || 'alpine:latest';
  }

  private getTestCommand(language: string): string[] {
    const commands: Record<string, string[]> = {
      'typescript': ['sh', '-c', 'npm install && npm test'],
      'javascript': ['sh', '-c', 'npm install && npm test'],
      'python': ['sh', '-c', 'pip install -r requirements.txt && pytest'],
      'java': ['sh', '-c', 'mvn test'],
      'go': ['sh', '-c', 'go test ./...'],
      'rust': ['sh', '-c', 'cargo test']
    };
    return commands[language] || ['sh', '-c', 'echo "No tests available"'];
  }

  private getValidationImage(language: string): string {
    return this.getTestImage(language);
  }

  private getValidationCommand(language: string, filePath: string): string[] {
    const ext = path.extname(filePath);
    
    const commands: Record<string, string[]> = {
      '.ts': ['sh', '-c', 'echo "$CODE" | base64 -d | npx tsc --noEmit --stdin'],
      '.js': ['sh', '-c', 'echo "$CODE" | base64 -d | node --check'],
      '.py': ['sh', '-c', 'echo "$CODE" | base64 -d | python -m py_compile /dev/stdin'],
      '.java': ['sh', '-c', 'echo "$CODE" | base64 -d > Main.java && javac Main.java'],
      '.go': ['sh', '-c', 'echo "$CODE" | base64 -d | gofmt -e'],
      '.rs': ['sh', '-c', 'echo "$CODE" | base64 -d | rustc --crate-type lib -']
    };

    return commands[ext] || ['sh', '-c', 'echo "Validation not available"'];
  }
}

export const containerManager = new ContainerManager();
