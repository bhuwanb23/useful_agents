import { ChromaClient, Collection } from 'chromadb';
import axios from 'axios';
import { logger } from '../../utils/logger';
import { config } from '../../config';

export class VectorStore {
  private client: ChromaClient;
  private collection: Collection | null = null;
  private readonly collectionName = 'code_embeddings';

  constructor() {
    this.client = new ChromaClient({ path: config.chromaUrl });
  }

  async initialize(): Promise<void> {
    try {
      this.collection = await this.client.getOrCreateCollection({
        name: this.collectionName,
        metadata: { description: 'Code embeddings for RAG' }
      });
      logger.info('ChromaDB collection initialized');
    } catch (error) {
      logger.error('Failed to initialize ChromaDB:', error);
      throw error;
    }
  }

  async addDocument(
    id: string,
    text: string,
    metadata: Record<string, any>
  ): Promise<void> {
    if (!this.collection) throw new Error('Collection not initialized');

    const embedding = await this.generateEmbedding(text);
    
    await this.collection.add({
      ids: [id],
      embeddings: [embedding],
      documents: [text],
      metadatas: [metadata]
    });
  }

  async search(
    query: string,
    limit: number = 5
  ): Promise<Array<{ id: string; document: string; metadata: any; distance: number }>> {
    if (!this.collection) throw new Error('Collection not initialized');

    const queryEmbedding = await this.generateEmbedding(query);
    
    const results = await this.collection.query({
      queryEmbeddings: [queryEmbedding],
      nResults: limit,
      include: ['documents', 'metadatas', 'distances']
    });

    return results.ids[0].map((id, idx) => ({
      id,
      document: results.documents[0][idx] || '',
      metadata: results.metadatas[0][idx] || {},
      distance: results.distances![0][idx]
    }));
  }

  async deleteDocument(id: string): Promise<void> {
    if (!this.collection) throw new Error('Collection not initialized');
    await this.collection.delete({ ids: [id] });
  }

  async clearAll(): Promise<void> {
    if (!this.collection) throw new Error('Collection not initialized');
    await this.client.deleteCollection({ name: this.collectionName });
    await this.initialize();
  }

  private async generateEmbedding(text: string): Promise<number[]> {
    try {
      const response = await axios.post(
        `${config.ollamaUrl}/api/embeddings`,
        {
          model: 'nomic-embed-text',
          prompt: text
        },
        { timeout: 30000 }
      );

      return response.data.embedding;
    } catch (error) {
      logger.error('Failed to generate embedding:', error);
      throw new Error('Embedding generation failed');
    }
  }
}

export const vectorStore = new VectorStore();
