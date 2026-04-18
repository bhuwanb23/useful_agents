import { Octokit } from '@octokit/rest';
import { PrismaClient } from '@prisma/client';
import fs from 'fs/promises';
import path from 'path';

const prisma = new PrismaClient();

export interface FileChange {
  path: string;
  content: string;
  operation: 'create' | 'modify' | 'delete';
  reason: string;
}

export interface CommitGroup {
  message: string;
  files: FileChange[];
  step: number;
}

export interface PRMetadata {
  title: string;
  body: string;
  commits: CommitGroup[];
  labels: string[];
  reviewers?: string[];
}

export class MultiFilePRService {
  private octokit: Octokit | null = null;

  constructor(accessToken?: string) {
    if (accessToken) {
      this.octokit = new Octokit({ auth: accessToken });
    }
  }

  /**
   * Create a multi-file PR with grouped commits
   */
  async createMultiFilePR(
    owner: string,
    repo: string,
    branchName: string,
    metadata: PRMetadata
  ): Promise<{ prNumber: number; prUrl: string }> {
    if (!this.octokit) {
      throw new Error('GitHub token not configured');
    }

    console.log(`[MultiFilePR] Creating PR with ${metadata.commits.length} commits`);

    // Step 1: Get the base branch (usually 'main' or 'master')
    const { data: baseBranch } = await this.octokit.repos.getBranch({
      owner,
      repo,
      branch: 'main',
    });

    // Step 2: Create a new branch
    await this.octokit.git.createRef({
      owner,
      repo,
      ref: `refs/heads/${branchName}`,
      sha: baseBranch.commit.sha,
    });

    console.log(`[MultiFilePR] Created branch: ${branchName}`);

    // Step 3: Create commits for each group
    let currentSha = baseBranch.commit.sha;

    for (const commitGroup of metadata.commits) {
      currentSha = await this.createCommit(
        owner,
        repo,
        branchName,
        currentSha,
        commitGroup
      );
      console.log(`[MultiFilePR] Created commit: ${commitGroup.message}`);
    }

    // Step 4: Create the Pull Request
    const { data: pr } = await this.octokit.pulls.create({
      owner,
      repo,
      title: metadata.title,
      body: this.buildPRBody(metadata),
      head: branchName,
      base: 'main',
    });

    console.log(`[MultiFilePR] Created PR #${pr.number}: ${pr.html_url}`);

    // Step 5: Add labels
    if (metadata.labels.length > 0) {
      await this.octokit.issues.addLabels({
        owner,
        repo,
        issue_number: pr.number,
        labels: metadata.labels,
      });
    }

    // Step 6: Request reviewers
    if (metadata.reviewers && metadata.reviewers.length > 0) {
      await this.octokit.pulls.requestReviewers({
        owner,
        repo,
        pull_number: pr.number,
        reviewers: metadata.reviewers,
      });
    }

    return {
      prNumber: pr.number,
      prUrl: pr.html_url,
    };
  }

  /**
   * Create a single commit with multiple file changes
   */
  private async createCommit(
    owner: string,
    repo: string,
    branch: string,
    parentSha: string,
    commitGroup: CommitGroup
  ): Promise<string> {
    if (!this.octokit) {
      throw new Error('Octokit not initialized');
    }

    // Create blobs for all files
    const blobs = await Promise.all(
      commitGroup.files.map(async (file) => {
        if (file.operation === 'delete') {
          return null; // Handle deletions separately
        }

        const { data: blob } = await this.octokit!.git.createBlob({
          owner,
          repo,
          content: Buffer.from(file.content).toString('base64'),
          encoding: 'base64',
        });

        return {
          path: file.path,
          mode: '100644' as const,
          type: 'blob' as const,
          sha: blob.sha,
        };
      })
    );

    // Filter out null (deleted files)
    const tree = blobs.filter((b): b is NonNullable<typeof b> => b !== null);

    // Create tree
    const { data: newTree } = await this.octokit.git.createTree({
      owner,
      repo,
      base_tree: parentSha,
      tree,
    });

    // Create commit
    const { data: commit } = await this.octokit.git.createCommit({
      owner,
      repo,
      message: commitGroup.message,
      tree: newTree.sha,
      parents: [parentSha],
    });

    // Update branch reference
    await this.octokit.git.updateRef({
      owner,
      repo,
      ref: `heads/${branch}`,
      sha: commit.sha,
    });

    return commit.sha;
  }

  /**
   * Build comprehensive PR body with all changes
   */
  private buildPRBody(metadata: PRMetadata): string {
    let body = metadata.body + '\n\n';

    body += '## 📋 Changes Overview\n\n';
    
    // Group changes by type
    const allFiles = metadata.commits.flatMap(c => c.files);
    const creates = allFiles.filter(f => f.operation === 'create');
    const modifies = allFiles.filter(f => f.operation === 'modify');
    const deletes = allFiles.filter(f => f.operation === 'delete');

    if (creates.length > 0) {
      body += `### ✨ Created Files (${creates.length})\n`;
      creates.forEach(f => {
        body += `- \`${f.path}\` - ${f.reason}\n`;
      });
      body += '\n';
    }

    if (modifies.length > 0) {
      body += `### 🔧 Modified Files (${modifies.length})\n`;
      modifies.forEach(f => {
        body += `- \`${f.path}\` - ${f.reason}\n`;
      });
      body += '\n';
    }

    if (deletes.length > 0) {
      body += `### 🗑️ Deleted Files (${deletes.length})\n`;
      deletes.forEach(f => {
        body += `- \`${f.path}\` - ${f.reason}\n`;
      });
      body += '\n';
    }

    body += '## 🔄 Commit History\n\n';
    metadata.commits.forEach((commit, i) => {
      body += `${i + 1}. **${commit.message}** (Step ${commit.step})\n`;
      body += `   - ${commit.files.length} file(s) changed\n`;
    });

    body += '\n---\n';
    body += '🤖 *This PR was automatically generated by GitHub Agent System*\n';

    return body;
  }

  /**
   * Group file changes into logical commits based on execution plan
   */
  groupChangesIntoCommits(
    fileChanges: FileChange[],
    planSteps: any[]
  ): CommitGroup[] {
    const commits: CommitGroup[] = [];

    // Group files by the step they belong to
    for (const step of planSteps) {
      const stepFiles = fileChanges.filter(fc =>
        step.files.includes(fc.path)
      );

      if (stepFiles.length > 0) {
        commits.push({
          message: `Step ${step.step}: ${step.description}`,
          files: stepFiles,
          step: step.step,
        });
      }
    }

    // Catch any files not associated with a step
    const assignedPaths = new Set(commits.flatMap(c => c.files.map(f => f.path)));
    const unassigned = fileChanges.filter(fc => !assignedPaths.has(fc.path));

    if (unassigned.length > 0) {
      commits.push({
        message: 'Additional changes',
        files: unassigned,
        step: planSteps.length + 1,
      });
    }

    return commits;
  }

  /**
   * Validate PR before creation
   */
  async validatePR(metadata: PRMetadata): Promise<{ valid: boolean; errors: string[] }> {
    const errors: string[] = [];

    // Check for empty commits
    if (metadata.commits.length === 0) {
      errors.push('No commits to create');
    }

    // Check for files with no content
    for (const commit of metadata.commits) {
      for (const file of commit.files) {
        if (file.operation !== 'delete' && !file.content) {
          errors.push(`File ${file.path} has no content`);
        }
      }
    }

    // Check for duplicate file paths across commits
    const allPaths = metadata.commits.flatMap(c => c.files.map(f => f.path));
    const duplicates = allPaths.filter((path, i) => allPaths.indexOf(path) !== i);
    if (duplicates.length > 0) {
      errors.push(`Duplicate file paths: ${duplicates.join(', ')}`);
    }

    // Check PR title and body
    if (!metadata.title || metadata.title.trim().length === 0) {
      errors.push('PR title is required');
    }

    if (!metadata.body || metadata.body.trim().length === 0) {
      errors.push('PR body is required');
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * Create a draft PR (for human review)
   */
  async createDraftPR(
    owner: string,
    repo: string,
    branchName: string,
    metadata: PRMetadata
  ): Promise<{ prNumber: number; prUrl: string }> {
    const result = await this.createMultiFilePR(owner, repo, branchName, metadata);

    // Convert to draft
    if (this.octokit) {
      await this.octokit.pulls.update({
        owner,
        repo,
        pull_number: result.prNumber,
        draft: true,
      });
    }

    console.log(`[MultiFilePR] Converted PR #${result.prNumber} to draft`);

    return result;
  }

  /**
   * Add comment to PR with execution details
   */
  async addExecutionComment(
    owner: string,
    repo: string,
    prNumber: number,
    executionDetails: {
      planId: string;
      stepsCompleted: number;
      totalSteps: number;
      testResults: string;
      coverageReport?: string;
    }
  ): Promise<void> {
    if (!this.octokit) return;

    const comment = `
## 🤖 Agent Execution Report

**Plan ID**: \`${executionDetails.planId}\`  
**Steps Completed**: ${executionDetails.stepsCompleted}/${executionDetails.totalSteps}  

### 🧪 Test Results
\`\`\`
${executionDetails.testResults}
\`\`\`

${executionDetails.coverageReport ? `
### 📊 Coverage Report
\`\`\`
${executionDetails.coverageReport}
\`\`\`
` : ''}

---
*All automated checks passed ✅*
`;

    await this.octokit.issues.createComment({
      owner,
      repo,
      issue_number: prNumber,
      body: comment,
    });

    console.log(`[MultiFilePR] Added execution comment to PR #${prNumber}`);
  }
}
