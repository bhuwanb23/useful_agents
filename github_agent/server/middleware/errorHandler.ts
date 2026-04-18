/**
 * Global error handler middleware
 */

import { Request, Response, NextFunction } from 'express';
import { logger } from '../utils/logger';

export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction
) {
  logger.error('Unhandled error:', {
    message: err.message,
    stack: err.stack,
    path: req.path,
    method: req.method,
  });

  // Don't leak error details in production
  const isDev = process.env.NODE_ENV === 'development';

  res.status(500).json({
    error: {
      message: isDev ? err.message : 'Internal server error',
      ...(isDev && { stack: err.stack }),
    },
  });
}
