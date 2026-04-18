import { vectorStore } from './vectorStore';
import { logger } from '../../utils/logger';
import { prisma } from '../../db/client';

export interface SearchResult {
  filePath: string;
  content: string;
  language: string;
  startLine: number;
  endLine: number;
  relevanceScore: number;
}

export class CodeSearch {
  async findDefinition(
    functionName: string,
    repoId: number
  ): Promise<SearchResult[]> {
    const query = `function definition: ${functionName}`;
    const results = await vectorStore.search(query, 5);

    return results
      .filter(r => r.metadata.repoId === repoId)
      .map(r => ({
        filePath: r.metadata.filePath,
        content: r.document,
        language: r.metadata.language,
        startLine: r.metadata.startLine,
        endLine: r.metadata.endLine,
        relevanceScore: 1 - r.distance
      }))
      .filter(r => r.relevanceScore > 0.7);
  }

  async findUsages(
    variableName: string,
    repoId: number
  ): Promise<SearchResult[]> {
    const query = `usage of ${variableName}`;
    const results = await vectorStore.search(query, 10);

    return results
      .filter(r => r.metadata.repoId === repoId)
      .filter(r => r.document.includes(variableName))
      .map(r => ({
        filePath: r.metadata.filePath,
        content: r.document,
        language: r.metadata.language,
        startLine: r.metadata.startLine,
        endLine: r.metadata.endLine,
        relevanceScore: 1 - r.distance
      }))
      .filter(r => r.relevanceScore > 0.6);
  }

  async findRelevantContext(
    issueDescription: string,
    repoId: number,
    limit: number = 5
  ): Promise<SearchResult[]> {
    const results = await vectorStore.search(issueDescription, limit * 2);

    return results
      .filter(r => r.metadata.repoId === repoId)
      .map(r => ({
        filePath: r.metadata.filePath,
        content: r.document,
        language: r.metadata.language,
        startLine: r.metadata.startLine,
        endLine: r.metadata.endLine,
        relevanceScore: 1 - r.distance
      }))
      .filter(r => r.relevanceScore > 0.5)
      .slice(0, limit);
  }

  async findSimilarCode(
    codeSnippet: string,
    repoId: number,
    limit: number = 5
  ): Promise<SearchResult[]> {
    const results = await vectorStore.search(codeSnippet, limit);

    return results
      .filter(r => r.metadata.repoId === repoId)
      .map(r => ({
        filePath: r.metadata.filePath,
        content: r.document,
        language: r.metadata.language,
        startLine: r.metadata.startLine,
        endLine: r.metadata.endLine,
        relevanceScore: 1 - r.distance
      }));
  }

  async buildContextForIssue(
    issueId: number
  ): Promise<{ context: string; sources: SearchResult[] }> {
    const issue = await prisma.issue.findUnique({
      where: { id: issueId },
      include: { repository: true }
    });

    if (!issue) throw new Error('Issue not found');

    const relevantCode = await this.findRelevantContext(
      issue.title + '\n' + issue.description,
      issue.repositoryId,
      5
    );

    const context = relevantCode
      .map(
        r =>
          `File: ${r.filePath} (lines ${r.startLine}-${r.endLine})\n` +
          `Relevance: ${(r.relevanceScore * 100).toFixed(1)}%\n` +
          `\`\`\`${r.language}\n${r.content}\n\`\`\``
      )
      .join('\n\n---\n\n');

    return { context, sources: relevantCode };
  }
}

export const codeSearch = new CodeSearch();
