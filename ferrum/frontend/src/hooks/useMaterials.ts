'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Material, PaginatedResponse } from '@/lib/types';

interface UseMaterialsParams {
  page?: number;
  size?: number;
  search?: string;
  category?: string;
}

export function useMaterials(params: UseMaterialsParams = {}) {
  const [data, setData] = useState<PaginatedResponse<Material> | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMaterials();
  }, [params.page, params.size, params.search, params.category]);

  async function fetchMaterials() {
    setIsLoading(true);
    setError(null);

    try {
      const queryParams = new URLSearchParams();
      if (params.page) queryParams.set('page', params.page.toString());
      if (params.size) queryParams.set('size', params.size.toString());
      if (params.search) queryParams.set('search_query', params.search);
      if (params.category) queryParams.set('category', params.category);

      const response = await api.get<PaginatedResponse<Material>>(
        `/materials?${queryParams.toString()}`
      );
      setData(response);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch materials');
    } finally {
      setIsLoading(false);
    }
  }

  return { data, isLoading, error, refetch: fetchMaterials };
}
