/**
 * Ollama Load Balancer
 * Manages multiple Ollama instances with health checking and load distribution
 */

import axios, { AxiosError } from 'axios';
import { prisma } from '../index';
import { logger } from '../utils/logger';

export interface OllamaServer {
  id: string;
  url: string;
  name: string | null;
  isActive: boolean;
  isHealthy: boolean;
  activeJobs: number;
  maxConcurrent: number;
  avgResponseTime: number | null;
  lastHealthCheck: Date | null;
}

export interface GenerateRequest {
  model: string;
  prompt: string;
  system?: string;
  stream?: boolean;
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  context?: number[];
}

export interface GenerateResponse {
  model: string;
  created_at: string;
  response: string;
  done: boolean;
  context?: number[];
  total_duration?: number;
  load_duration?: number;
  prompt_eval_count?: number;
  prompt_eval_duration?: number;
  eval_count?: number;
  eval_duration?: number;
}

export class OllamaLoadBalancer {
  private healthCheckInterval: NodeJS.Timeout | null = null;
  private readonly healthCheckIntervalMs = 30000; // 30 seconds

  /**
   * Initialize servers from environment or database
   */
  async initialize() {
    // Parse servers from environment
    const serverUrls = process.env.OLLAMA_SERVERS?.split(',') || [
      process.env.OLLAMA_BASE_URL || 'http://localhost:11434',
    ];

    // Ensure all servers exist in database
    for (const url of serverUrls) {
      const trimmedUrl = url.trim();
      
      await prisma.ollamaServer.upsert({
        where: { url: trimmedUrl },
        create: {
          url: trimmedUrl,
          name: `Ollama Server (${trimmedUrl})`,
          isActive: true,
          isHealthy: false,
          maxConcurrent: parseInt(process.env.OLLAMA_MAX_CONCURRENT || '1'),
        },
        update: {
          isActive: true,
        },
      });
    }

    // Start health checks
    this.startHealthChecks();
    
    logger.info(`Ollama Load Balancer initialized with ${serverUrls.length} servers`);
  }

  /**
   * Start periodic health checks
   */
  private startHealthChecks() {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
    }

    // Run immediately
    this.checkAllServersHealth();

    // Then run periodically
    this.healthCheckInterval = setInterval(() => {
      this.checkAllServersHealth();
    }, this.healthCheckIntervalMs);

    logger.info('Health check scheduler started');
  }

  /**
   * Check health of all servers
   */
  private async checkAllServersHealth() {
    const servers = await prisma.ollamaServer.findMany({
      where: { isActive: true },
    });

    await Promise.all(
      servers.map(server => this.checkServerHealth(server))
    );
  }

  /**
   * Check health of a single server
   */
  private async checkServerHealth(server: OllamaServer) {
    try {
      const startTime = Date.now();
      
      // Try to get server version/tags (lightweight check)
      const response = await axios.get(`${server.url}/api/tags`, {
        timeout: 5000,
      });

      const responseTime = Date.now() - startTime;

      // Update as healthy
      await prisma.ollamaServer.update({
        where: { id: server.id },
        data: {
          isHealthy: true,
          lastHealthCheck: new Date(),
          avgResponseTime: responseTime,
        },
      });

      logger.debug(`Server ${server.url} is healthy (${responseTime}ms)`);
      
      return true;
    } catch (error) {
      // Mark as unhealthy
      await prisma.ollamaServer.update({
        where: { id: server.id },
        data: {
          isHealthy: false,
          lastHealthCheck: new Date(),
        },
      });

      logger.warn(`Server ${server.url} health check failed:`, {
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      
      return false;
    }
  }

  /**
   * Get the best available server (least loaded, healthy)
   */
  async getBestServer(): Promise<OllamaServer | null> {
    const servers = await prisma.ollamaServer.findMany({
      where: {
        isActive: true,
        isHealthy: true,
      },
      orderBy: [
        { activeJobs: 'asc' },          // Least loaded first
        { avgResponseTime: 'asc' },     // Then fastest
      ],
    });

    // Filter servers that aren't at max capacity
    const availableServers = servers.filter(
      s => s.activeJobs < s.maxConcurrent
    );

    if (availableServers.length === 0) {
      logger.warn('No available Ollama servers (all at capacity or unhealthy)');
      return null;
    }

    return availableServers[0];
  }

  /**
   * Increment active job count for a server
   */
  private async incrementServerJobs(serverId: string) {
    await prisma.ollamaServer.update({
      where: { id: serverId },
      data: {
        activeJobs: { increment: 1 },
        totalJobs: { increment: 1 },
      },
    });
  }

  /**
   * Decrement active job count for a server
   */
  private async decrementServerJobs(serverId: string) {
    await prisma.ollamaServer.update({
      where: { id: serverId },
      data: {
        activeJobs: { decrement: 1 },
      },
    });
  }

  /**
   * Send a generation request to the best available server
   */
  async generate(request: GenerateRequest): Promise<GenerateResponse> {
    const server = await this.getBestServer();

    if (!server) {
      throw new Error('No available Ollama servers');
    }

    logger.info(`Routing request to ${server.url} (model: ${request.model})`);

    try {
      // Increment job count
      await this.incrementServerJobs(server.id);

      const startTime = Date.now();

      // Make the request
      const response = await axios.post<GenerateResponse>(
        `${server.url}/api/generate`,
        {
          ...request,
          stream: false, // Non-streaming for now
        },
        {
          timeout: 120000, // 2 minute timeout
        }
      );

      const duration = Date.now() - startTime;

      // Update server metrics
      await prisma.ollamaServer.update({
        where: { id: server.id },
        data: {
          avgResponseTime: Math.round(
            (server.avgResponseTime || 0) * 0.8 + duration * 0.2
          ), // Moving average
        },
      });

      logger.info(`Request completed in ${duration}ms`, {
        server: server.url,
        model: request.model,
        tokens: response.data.eval_count,
      });

      return response.data;
    } catch (error) {
      logger.error('Ollama generation failed:', {
        server: server.url,
        error: error instanceof AxiosError 
          ? error.message 
          : 'Unknown error',
      });

      // If server error, mark as unhealthy
      if (error instanceof AxiosError && !error.response) {
        await prisma.ollamaServer.update({
          where: { id: server.id },
          data: { isHealthy: false },
        });
      }

      throw error;
    } finally {
      // Always decrement job count
      await this.decrementServerJobs(server.id);
    }
  }

  /**
   * Get all server stats
   */
  async getServerStats() {
    const servers = await prisma.ollamaServer.findMany({
      orderBy: { createdAt: 'asc' },
    });

    return servers.map(s => ({
      id: s.id,
      url: s.url,
      name: s.name,
      isActive: s.isActive,
      isHealthy: s.isHealthy,
      activeJobs: s.activeJobs,
      totalJobs: s.totalJobs,
      maxConcurrent: s.maxConcurrent,
      avgResponseTime: s.avgResponseTime,
      lastHealthCheck: s.lastHealthCheck,
      utilizationPercent: Math.round((s.activeJobs / s.maxConcurrent) * 100),
    }));
  }

  /**
   * Manually trigger health check for all servers
   */
  async triggerHealthCheck() {
    await this.checkAllServersHealth();
  }

  /**
   * Stop health checks (for graceful shutdown)
   */
  stop() {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
      logger.info('Health check scheduler stopped');
    }
  }
}

// Singleton instance
export const ollamaLoadBalancer = new OllamaLoadBalancer();
