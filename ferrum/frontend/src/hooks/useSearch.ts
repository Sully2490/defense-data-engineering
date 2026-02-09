'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { SearchResponse } from '@/lib/types';

export function useSearch() {
  const [data, setData] = useState<SearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function search(query: string, useAI: boolean = true) {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post<SearchResponse>('/search', {
        query,
        use_ai: useAI,
      });
      setData(response);
    } catch (err: any) {
      setError(err.message || 'Search failed');
    } finally {
      setIsLoading(false);
    }
  }

  return { data, isLoading, error, search };
}
