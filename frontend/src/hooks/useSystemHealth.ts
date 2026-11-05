import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';
import { HealthResponse } from '../types/api';

export function useSystemHealth(pollIntervalMs = 8000) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = useCallback(async () => {
    try {
      const data = await apiService.getHealth();
      setHealth(data);
      setError(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Backend unreachable';
      setError(msg);
      // If error occurs, keep last known or degraded representation
      setHealth(prev => prev ? { ...prev, status: 'unhealthy' } : null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, pollIntervalMs);
    return () => clearInterval(interval);
  }, [fetchHealth, pollIntervalMs]);

  return {
    health,
    isLoading,
    error,
    refresh: fetchHealth,
    isOnline: !error && health !== null,
  };
}

