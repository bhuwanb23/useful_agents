import { glob } from 'glob';
import * as fs from 'fs/promises';
import * as path from 'path';
import { vectorStore } from './vectorStore';
import { logger } from '../../utils/logger';
import { get_encoding } from 'tiktoken';

interface CodeChunk {
  id: string;
  content: string;
  metadata: {
    filePath: string;
    language: string;
    startLine: number;
    endLine: number;
    type: 'function' | 'class' | 'import' | 'generic';
    name?: string;
  };
}

export class CodeIndexer {
  private readonly maxChunkSize = 500;
  private readonly encoding = get_encoding('cl100k_base');

  async indexRepository(repoPath: string, repoId: number): Promise<void> {
    logger.info(`Starting indexing for repository: ${repoPath}`);

    const files = await this.findCodeFiles(repoPath);
    logger.info(`Found ${files.length} code files`);

    for (const filePath of files) {
      await this.indexFile(filePath, repoPath, repoId);
    }

    logger.info(`Completed indexing for repository: ${repoPath}`);
  }

  private async findCodeFiles(repoPath: string): Promise<string[]> {
    const patterns = [
      '**/*.ts', '**/*.tsx', '**/*.js', '**/*.jsx',
      '**/*.py', '**/*.java', '**/*.go', '**/*.rs',
      '**/*.cpp', '**/*.c', '**/*.h'
    ];

    const ignorePatterns = [
      '**/node_modules/**', '**/dist/**', '**/build/**',
      '**/.git/**', '**/venv/**', '**/__pycache__/**'
    ];

    let allFiles: string[] = [];
    
    for (const pattern of patterns) {
      const files = await glob(pattern, {
        cwd: repoPath,
        absolute: true,
        ignore: ignorePatterns
      });
      allFiles = allFiles.concat(files);
    }

    return allFiles;
  }

  private async indexFile(filePath: string, repoPath: string, repoId: number): Promise<void> {
    try {
      const content = await fs.readFile(filePath, 'utf-8');
      const relativePath = path.relative(repoPath, filePath);
      const language = this.detectLanguage(filePath);

      const chunks = this.chunkCode(content, relativePath, language);

      for (const chunk of chunks) {
        const chunkId = `repo_${repoId}_${chunk.id}`;
        await vectorStore.addDocument(chunkId, chunk.content, {
          ...chunk.metadata,
          repoId
        });
      }

      logger.debug(`Indexed: ${relativePath} (${chunks.length} chunks)`);
    } catch (error) {
      logger.error(`Failed to index ${filePath}:`, error);
    }
  }

  private chunkCode(content: string, filePath: string, language: string): CodeChunk[] {
    const lines = content.split('\n');
    const chunks: CodeChunk[] = [];
    
    let currentChunk: string[] = [];
    let currentStartLine = 0;
    let chunkIndex = 0;

    for (let i = 0; i < lines.length; i++) {
      currentChunk.push(lines[i]);

      const chunkText = currentChunk.join('\n');
      const tokenCount = this.encoding.encode(chunkText).length;

      if (tokenCount >= this.maxChunkSize) {
        chunks.push({
          id: `${filePath}_${chunkIndex}`,
          content: chunkText,
          metadata: {
            filePath,
            language,
            startLine: currentStartLine,
            endLine: i,
            type: this.detectChunkType(chunkText, language)
          }
        });

        currentChunk = [];
        currentStartLine = i + 1;
        chunkIndex++;
      }
    }

    if (currentChunk.length > 0) {
      chunks.push({
        id: `${filePath}_${chunkIndex}`,
        content: currentChunk.join('\n'),
        metadata: {
          filePath,
          language,
          startLine: currentStartLine,
          endLine: lines.length - 1,
          type: this.detectChunkType(currentChunk.join('\n'), language)
        }
      });
    }

    return chunks;
  }

  private detectLanguage(filePath: string): string {
    const ext = path.extname(filePath);
    const langMap: Record<string, string> = {
      '.ts': 'typescript', '.tsx': 'typescript',
      '.js': 'javascript', '.jsx': 'javascript',
      '.py': 'python', '.java': 'java',
      '.go': 'go', '.rs': 'rust',
      '.cpp': 'cpp', '.c': 'c', '.h': 'c'
    };
    return langMap[ext] || 'unknown';
  }

  private detectChunkType(content: string, language: string): 'function' | 'class' | 'import' | 'generic' {
    const trimmed = content.trim();

    if (language === 'typescript' || language === 'javascript') {
      if (trimmed.startsWith('import ') || trimmed.startsWith('export ')) return 'import';
      if (trimmed.includes('function ') || trimmed.includes('const ') || /=>\s*{/.test(trimmed)) return 'function';
      if (trimmed.includes('class ')) return 'class';
    }

    if (language === 'python') {
      if (trimmed.startsWith('import ') || trimmed.startsWith('from ')) return 'import';
      if (trimmed.startsWith('def ')) return 'function';
      if (trimmed.startsWith('class ')) return 'class';
    }

    return 'generic';
  }
}

export const codeIndexer = new CodeIndexer();
