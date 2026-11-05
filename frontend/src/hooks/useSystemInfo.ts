import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';
import { SystemInfoResponse } from '../types/api';

export function useSystemInfo() {
  const [info, setInfo] = useState<SystemInfoResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInfo = useCallback(async () => {
    try {
      const data = await apiService.getSystemInfo();
      setInfo(data);
      setError(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve system metadata';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchInfo();
  }, [fetchInfo]);

  return {
    info,
    isLoading,
    error,
    refresh: fetchInfo,
  };
}

