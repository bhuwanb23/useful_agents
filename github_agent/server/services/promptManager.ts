/**
 * Prompt Version Management System
 * Loads and manages versioned prompts from database and files
 */

import { prisma } from '../index';
import { logger } from '../utils/logger';
import fs from 'fs/promises';
import path from 'path';

export interface PromptTemplate {
  id: string;
  name: string;
  version: string;
  systemPrompt: string;
  userPrompt: string;
  temperature: number;
  maxTokens: number;
  topP: number;
  isActive: boolean;
}

export class PromptManager {
  private promptCache: Map<string, PromptTemplate> = new Map();
  private readonly promptsDir = path.join(process.cwd(), 'prompts');

  /**
   * Initialize prompt manager - load prompts from files to database
   */
  async initialize() {
    try {
      // Ensure prompts directory exists
      await fs.mkdir(this.promptsDir, { recursive: true });

      // Load prompts from files
      await this.loadPromptsFromFiles();

      // Cache active prompts
      await this.refreshCache();

      logger.info('Prompt Manager initialized');
    } catch (error) {
      logger.error('Failed to initialize Prompt Manager:', error);
      throw error;
    }
  }

  /**
   * Load prompts from filesystem into database
   */
  private async loadPromptsFromFiles() {
    const agentTypes = [
      'analyzer',
      'fixer',
      'reviewer',
      'security',
      'tester',
      'docs',
      'manager',
    ];

    for (const agentType of agentTypes) {
      const agentDir = path.join(this.promptsDir, agentType);
      
      try {
        await fs.mkdir(agentDir, { recursive: true });
        
        // Try to read version files (e.g., v1.txt, v2.txt)
        const files = await fs.readdir(agentDir);
        const versionFiles = files.filter(f => f.match(/^v\d+\.txt$/));

        for (const file of versionFiles) {
          const version = file.replace('.txt', '');
          const filePath = path.join(agentDir, file);
          const content = await fs.readFile(filePath, 'utf-8');

          // Parse content (expect YAML-like format)
          const parsed = this.parsePromptFile(content);

          // Upsert to database
          await prisma.prompt.upsert({
            where: {
              name_version: {
                name: agentType,
                version: version,
              },
            },
            create: {
              name: agentType,
              version: version,
              systemPrompt: parsed.system,
              userPrompt: parsed.user,
              temperature: parsed.temperature ?? 0.7,
              maxTokens: parsed.maxTokens ?? 2000,
              topP: parsed.topP ?? 0.9,
              isActive: parsed.isActive ?? false,
              description: parsed.description,
              author: parsed.author,
            },
            update: {
              systemPrompt: parsed.system,
              userPrompt: parsed.user,
              temperature: parsed.temperature ?? 0.7,
              maxTokens: parsed.maxTokens ?? 2000,
              topP: parsed.topP ?? 0.9,
              description: parsed.description,
              author: parsed.author,
            },
          });

          logger.debug(`Loaded prompt: ${agentType}/${version}`);
        }
      } catch (error) {
        // Directory doesn't exist or no files - skip
        logger.debug(`No prompts found for ${agentType}`);
      }
    }
  }

  /**
   * Parse prompt file content (simple key: value format)
   */
  private parsePromptFile(content: string): {
    system: string;
    user: string;
    temperature?: number;
    maxTokens?: number;
    topP?: number;
    isActive?: boolean;
    description?: string;
    author?: string;
  } {
    const lines = content.split('\n');
    const result: any = {
      system: '',
      user: '',
    };

    let currentSection = '';
    let currentContent: string[] = [];

    for (const line of lines) {
      // Section headers
      if (line.startsWith('# SYSTEM')) {
        if (currentSection) {
          result[currentSection] = currentContent.join('\n').trim();
        }
        currentSection = 'system';
        currentContent = [];
      } else if (line.startsWith('# USER')) {
        if (currentSection) {
          result[currentSection] = currentContent.join('\n').trim();
        }
        currentSection = 'user';
        currentContent = [];
      } else if (line.startsWith('# CONFIG')) {
        if (currentSection) {
          result[currentSection] = currentContent.join('\n').trim();
        }
        currentSection = 'config';
        currentContent = [];
      } else if (currentSection === 'config' && line.includes(':')) {
        // Parse config line
        const [key, value] = line.split(':').map(s => s.trim());
        if (key === 'temperature') result.temperature = parseFloat(value);
        else if (key === 'maxTokens') result.maxTokens = parseInt(value);
        else if (key === 'topP') result.topP = parseFloat(value);
        else if (key === 'isActive') result.isActive = value === 'true';
        else if (key === 'description') result.description = value;
        else if (key === 'author') result.author = value;
      } else {
        currentContent.push(line);
      }
    }

    // Save last section
    if (currentSection && currentSection !== 'config') {
      result[currentSection] = currentContent.join('\n').trim();
    }

    return result;
  }

  /**
   * Refresh cache from database
   */
  private async refreshCache() {
    const activePrompts = await prisma.prompt.findMany({
      where: { isActive: true },
    });

    this.promptCache.clear();
    
    for (const prompt of activePrompts) {
      const key = `${prompt.name}:${prompt.version}`;
      this.promptCache.set(key, prompt);
    }

    logger.info(`Cached ${activePrompts.length} active prompts`);
  }

  /**
   * Get active prompt for an agent type
   */
  async getActivePrompt(agentType: string): Promise<PromptTemplate | null> {
    // First try cache
    const cached = Array.from(this.promptCache.values()).find(
      p => p.name === agentType && p.isActive
    );

    if (cached) {
      return cached;
    }

    // Fallback to database
    const prompt = await prisma.prompt.findFirst({
      where: {
        name: agentType,
        isActive: true,
      },
      orderBy: {
        createdAt: 'desc',
      },
    });

    return prompt;
  }

  /**
   * Get specific prompt version
   */
  async getPrompt(agentType: string, version: string): Promise<PromptTemplate | null> {
    const key = `${agentType}:${version}`;
    
    // Try cache
    if (this.promptCache.has(key)) {
      return this.promptCache.get(key)!;
    }

    // Fallback to database
    const prompt = await prisma.prompt.findUnique({
      where: {
        name_version: {
          name: agentType,
          version: version,
        },
      },
    });

    return prompt;
  }

  /**
   * Set active version for an agent type
   */
  async setActiveVersion(agentType: string, version: string): Promise<void> {
    // Deactivate all versions for this agent
    await prisma.prompt.updateMany({
      where: { name: agentType },
      data: { isActive: false },
    });

    // Activate the specified version
    await prisma.prompt.update({
      where: {
        name_version: {
          name: agentType,
          version: version,
        },
      },
      data: { isActive: true },
    });

    // Refresh cache
    await this.refreshCache();

    logger.info(`Set active prompt: ${agentType}/${version}`);
  }

  /**
   * Create new prompt version
   */
  async createPrompt(data: {
    name: string;
    version: string;
    systemPrompt: string;
    userPrompt: string;
    temperature?: number;
    maxTokens?: number;
    topP?: number;
    description?: string;
    author?: string;
    isActive?: boolean;
  }): Promise<PromptTemplate> {
    const prompt = await prisma.prompt.create({
      data: {
        name: data.name,
        version: data.version,
        systemPrompt: data.systemPrompt,
        userPrompt: data.userPrompt,
        temperature: data.temperature ?? 0.7,
        maxTokens: data.maxTokens ?? 2000,
        topP: data.topP ?? 0.9,
        description: data.description,
        author: data.author,
        isActive: data.isActive ?? false,
      },
    });

    // Also save to file
    await this.savePromptToFile(prompt);

    // Refresh cache if active
    if (prompt.isActive) {
      await this.refreshCache();
    }

    logger.info(`Created prompt: ${data.name}/${data.version}`);
    return prompt;
  }

  /**
   * Save prompt to filesystem
   */
  private async savePromptToFile(prompt: PromptTemplate) {
    const agentDir = path.join(this.promptsDir, prompt.name);
    await fs.mkdir(agentDir, { recursive: true });

    const filePath = path.join(agentDir, `${prompt.version}.txt`);
    
    const content = `# SYSTEM
${prompt.systemPrompt}

# USER
${prompt.userPrompt}

# CONFIG
temperature: ${prompt.temperature}
maxTokens: ${prompt.maxTokens}
topP: ${prompt.topP}
isActive: ${prompt.isActive}
${prompt.description ? `description: ${prompt.description}` : ''}
${prompt.author ? `author: ${prompt.author}` : ''}
`;

    await fs.writeFile(filePath, content, 'utf-8');
  }

  /**
   * List all prompts for an agent
   */
  async listPrompts(agentType?: string) {
    const prompts = await prisma.prompt.findMany({
      where: agentType ? { name: agentType } : undefined,
      orderBy: [
        { name: 'asc' },
        { createdAt: 'desc' },
      ],
    });

    return prompts;
  }
}

// Singleton instance
export const promptManager = new PromptManager();
