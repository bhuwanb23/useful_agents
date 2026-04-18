import Docker from 'dockerode';
import { Readable } from 'stream';
import { logger } from '../../utils/logger';
import fs from 'fs/promises';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';

export interface ExecutionResult {
  success: boolean;
  stdout: string;
  stderr: string;
  exitCode: number;
  duration: number;
  testsPassed?: number;
  testsFailed?: number;
  compilationErrors?: string[];
}

export interface SandboxConfig {
  language: 'python' | 'node' | 'java' | 'go' | 'rust';
  timeout: number; // milliseconds
  memory: number; // MB
  cpus: number;
  networkEnabled: boolean;
}

export class DockerExecutor {
  private docker: Docker;
  private sandboxDir: string;

  constructor() {
    this.docker = new Docker({ socketPath: '/var/run/docker.sock' });
    this.sandboxDir = path.join(process.cwd(), 'sandboxes');
  }

  async initialize(): Promise<void> {
    await fs.mkdir(this.sandboxDir, { recursive: true });
    await this.ensureImages();
    logger.info('DockerExecutor initialized');
  }

  private async ensureImages(): Promise<void> {
    const images = [
      { name: 'python:3.11-slim', tag: 'python-sandbox' },
      { name: 'node:20-alpine', tag: 'node-sandbox' },
      { name: 'openjdk:17-slim', tag: 'java-sandbox' },
      { name: 'golang:1.21-alpine', tag: 'go-sandbox' },
      { name: 'rust:1.75-slim', tag: 'rust-sandbox' },
    ];

    for (const { name, tag } of images) {
      try {
        await this.docker.getImage(name).inspect();
        logger.info(`Image ${name} already exists`);
      } catch {
        logger.info(`Pulling image ${name}...`);
        await this.pullImage(name);
      }
    }
  }

  private pullImage(imageName: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.docker.pull(imageName, (err: any, stream: any) => {
        if (err) return reject(err);
        
        this.docker.modem.followProgress(stream, (err: any) => {
          if (err) return reject(err);
          logger.info(`Successfully pulled ${imageName}`);
          resolve();
        });
      });
    });
  }

  async executeCode(
    code: string,
    config: SandboxConfig,
    additionalFiles?: Record<string, string>
  ): Promise<ExecutionResult> {
    const sandboxId = uuidv4();
    const sandboxPath = path.join(this.sandboxDir, sandboxId);
    const startTime = Date.now();

    try {
      // Create sandbox directory
      await fs.mkdir(sandboxPath, { recursive: true });

      // Write main code file
      const mainFile = this.getMainFileName(config.language);
      await fs.writeFile(path.join(sandboxPath, mainFile), code);

      // Write additional files
      if (additionalFiles) {
        for (const [filename, content] of Object.entries(additionalFiles)) {
          await fs.writeFile(path.join(sandboxPath, filename), content);
        }
      }

      // Create Dockerfile
      const dockerfile = this.generateDockerfile(config);
      await fs.writeFile(path.join(sandboxPath, 'Dockerfile'), dockerfile);

      // Build image
      const imageName = `sandbox-${sandboxId}`;
      await this.buildImage(sandboxPath, imageName);

      // Run container
      const result = await this.runContainer(imageName, config, sandboxId);
      
      // Cleanup
      await this.cleanup(sandboxPath, imageName);

      const duration = Date.now() - startTime;
      return { ...result, duration };

    } catch (error) {
      await this.cleanup(sandboxPath, `sandbox-${sandboxId}`);
      logger.error('Code execution failed:', error);
      throw error;
    }
  }

  async runTests(
    repoPath: string,
    testCommand: string,
    config: SandboxConfig
  ): Promise<ExecutionResult> {
    const sandboxId = uuidv4();
    const sandboxPath = path.join(this.sandboxDir, sandboxId);
    const startTime = Date.now();

    try {
      // Copy repo to sandbox
      await this.copyDirectory(repoPath, sandboxPath);

      // Create test Dockerfile
      const dockerfile = this.generateTestDockerfile(config, testCommand);
      await fs.writeFile(path.join(sandboxPath, 'Dockerfile'), dockerfile);

      // Build and run
      const imageName = `test-${sandboxId}`;
      await this.buildImage(sandboxPath, imageName);
      const result = await this.runContainer(imageName, config, sandboxId);

      // Parse test results
      const parsedResult = this.parseTestOutput(result.stdout, result.stderr, config.language);

      await this.cleanup(sandboxPath, imageName);

      const duration = Date.now() - startTime;
      return { ...result, ...parsedResult, duration };

    } catch (error) {
      await this.cleanup(sandboxPath, `test-${sandboxId}`);
      logger.error('Test execution failed:', error);
      throw error;
    }
  }

  private async buildImage(contextPath: string, imageName: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.docker.buildImage(
        { context: contextPath, src: ['Dockerfile', '.'] },
        { t: imageName },
        (err: any, stream: any) => {
          if (err) return reject(err);

          this.docker.modem.followProgress(stream, (err: any) => {
            if (err) return reject(err);
            resolve();
          });
        }
      );
    });
  }

  private async runContainer(
    imageName: string,
    config: SandboxConfig,
    sandboxId: string
  ): Promise<Omit<ExecutionResult, 'duration'>> {
    const container = await this.docker.createContainer({
      Image: imageName,
      name: `exec-${sandboxId}`,
      HostConfig: {
        Memory: config.memory * 1024 * 1024,
        NanoCpus: config.cpus * 1e9,
        NetworkMode: config.networkEnabled ? 'bridge' : 'none',
        AutoRemove: true,
        ReadonlyRootfs: false,
      },
      Tty: false,
      AttachStdout: true,
      AttachStderr: true,
    });

    const stream = await container.attach({
      stream: true,
      stdout: true,
      stderr: true,
    });

    let stdout = '';
    let stderr = '';

    stream.on('data', (chunk: Buffer) => {
      const str = chunk.toString('utf8');
      if (str.includes('stdout')) {
        stdout += str;
      } else {
        stderr += str;
      }
    });

    await container.start();

    // Wait with timeout
    const exitCode = await Promise.race([
      container.wait(),
      new Promise<number>((_, reject) =>
        setTimeout(() => reject(new Error('Timeout')), config.timeout)
      ),
    ]).then((data: any) => data.StatusCode);

    // Try to stop if still running
    try {
      await container.stop({ t: 1 });
    } catch {}

    return {
      success: exitCode === 0,
      stdout: this.cleanDockerOutput(stdout),
      stderr: this.cleanDockerOutput(stderr),
      exitCode,
    };
  }

  private cleanDockerOutput(output: string): string {
    // Remove Docker stream headers
    return output
      .replace(/[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]/g, '')
      .replace(/\[.*?\]/g, '')
      .trim();
  }

  private generateDockerfile(config: SandboxConfig): string {
    const baseImages = {
      python: 'python:3.11-slim',
      node: 'node:20-alpine',
      java: 'openjdk:17-slim',
      go: 'golang:1.21-alpine',
      rust: 'rust:1.75-slim',
    };

    const runCommands = {
      python: 'python main.py',
      node: 'node main.js',
      java: 'javac Main.java && java Main',
      go: 'go run main.go',
      rust: 'rustc main.rs && ./main',
    };

    return `
FROM ${baseImages[config.language]}

WORKDIR /app

# Copy all files
COPY . .

# Install dependencies if needed
${this.getInstallCommand(config.language)}

# Run the code
CMD ${runCommands[config.language]}
`.trim();
  }

  private generateTestDockerfile(config: SandboxConfig, testCommand: string): string {
    const baseImages = {
      python: 'python:3.11-slim',
      node: 'node:20-alpine',
      java: 'openjdk:17-slim',
      go: 'golang:1.21-alpine',
      rust: 'rust:1.75-slim',
    };

    return `
FROM ${baseImages[config.language]}

WORKDIR /app

COPY . .

${this.getInstallCommand(config.language)}

CMD ${testCommand}
`.trim();
  }

  private getInstallCommand(language: string): string {
    const commands = {
      python: 'RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi',
      node: 'RUN if [ -f package.json ]; then npm ci --only=production; fi',
      java: 'RUN if [ -f pom.xml ]; then mvn dependency:resolve; fi',
      go: 'RUN if [ -f go.mod ]; then go mod download; fi',
      rust: 'RUN if [ -f Cargo.toml ]; then cargo build --release; fi',
    };
    return commands[language as keyof typeof commands] || '';
  }

  private getMainFileName(language: string): string {
    const files = {
      python: 'main.py',
      node: 'main.js',
      java: 'Main.java',
      go: 'main.go',
      rust: 'main.rs',
    };
    return files[language as keyof typeof files];
  }

  private parseTestOutput(stdout: string, stderr: string, language: string): {
    testsPassed?: number;
    testsFailed?: number;
    compilationErrors?: string[];
  } {
    const result: any = {};

    // Python pytest
    if (language === 'python') {
      const match = stdout.match(/(\d+) passed/);
      if (match) result.testsPassed = parseInt(match[1]);
      
      const failMatch = stdout.match(/(\d+) failed/);
      if (failMatch) result.testsFailed = parseInt(failMatch[1]);
    }

    // Node.js Jest/Mocha
    if (language === 'node') {
      const match = stdout.match(/Tests:\s+(\d+) passed/);
      if (match) result.testsPassed = parseInt(match[1]);
      
      const failMatch = stdout.match(/(\d+) failed/);
      if (failMatch) result.testsFailed = parseInt(failMatch[1]);
    }

    // Compilation errors
    if (stderr.includes('error:') || stderr.includes('Error:')) {
      result.compilationErrors = stderr
        .split('\n')
        .filter(line => line.includes('error') || line.includes('Error'))
        .slice(0, 10);
    }

    return result;
  }

  private async copyDirectory(src: string, dest: string): Promise<void> {
    await fs.mkdir(dest, { recursive: true });
    const entries = await fs.readdir(src, { withFileTypes: true });

    for (const entry of entries) {
      const srcPath = path.join(src, entry.name);
      const destPath = path.join(dest, entry.name);

      if (entry.isDirectory()) {
        if (!entry.name.startsWith('.') && entry.name !== 'node_modules') {
          await this.copyDirectory(srcPath, destPath);
        }
      } else {
        await fs.copyFile(srcPath, destPath);
      }
    }
  }

  private async cleanup(sandboxPath: string, imageName: string): Promise<void> {
    try {
      await fs.rm(sandboxPath, { recursive: true, force: true });
    } catch (err) {
      logger.error('Failed to remove sandbox directory:', err);
    }

    try {
      const image = this.docker.getImage(imageName);
      await image.remove({ force: true });
    } catch (err) {
      logger.error('Failed to remove Docker image:', err);
    }
  }

  async getContainerStats(): Promise<any[]> {
    const containers = await this.docker.listContainers({ all: true });
    return containers.filter(c => c.Names.some(n => n.includes('exec-') || n.includes('test-')));
  }

  async cleanupAll(): Promise<void> {
    const containers = await this.getContainerStats();
    for (const container of containers) {
      try {
        const c = this.docker.getContainer(container.Id);
        await c.stop();
        await c.remove();
      } catch {}
    }

    try {
      await fs.rm(this.sandboxDir, { recursive: true, force: true });
    } catch {}
  }
}

export const dockerExecutor = new DockerExecutor();
