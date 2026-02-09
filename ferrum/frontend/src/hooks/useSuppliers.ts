'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Supplier, PaginatedResponse } from '@/lib/types';

interface UseSuppliersParams {
  page?: number;
  size?: number;
  search?: string;
  state?: string;
  isSmallBusiness?: boolean;
}

export function useSuppliers(params: UseSuppliersParams = {}) {
  const [data, setData] = useState<PaginatedResponse<Supplier> | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSuppliers();
  }, [params.page, params.size, params.search, params.state, params.isSmallBusiness]);

  async function fetchSuppliers() {
    setIsLoading(true);
    setError(null);

    try {
      const queryParams = new URLSearchParams();
      if (params.page) queryParams.set('page', params.page.toString());
      if (params.size) queryParams.set('size', params.size.toString());
      if (params.search) queryParams.set('search_query', params.search);
      if (params.state) queryParams.set('state', params.state);
      if (params.isSmallBusiness !== undefined) {
        queryParams.set('small_business', params.isSmallBusiness.toString());
      }

      const response = await api.get<PaginatedResponse<Supplier>>(
        `/suppliers?${queryParams.toString()}`
      );
      setData(response);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch suppliers');
    } finally {
      setIsLoading(false);
    }
  }

  return { data, isLoading, error, refetch: fetchSuppliers };
}
