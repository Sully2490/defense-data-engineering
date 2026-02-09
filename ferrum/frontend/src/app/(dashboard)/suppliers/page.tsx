'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useSuppliers } from '@/hooks/useSuppliers';
import { Card, CardBody } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { SupplierTable } from '@/components/suppliers/SupplierTable';
import { SupplierFilters } from '@/components/suppliers/SupplierFilters';
import { Pagination } from '@/components/ui/Pagination';

export default function SuppliersPage() {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState<{ state: string; isSmallBusiness?: boolean }>({
    state: '',
  });

  const { data, isLoading, error } = useSuppliers({
    page,
    size: 20,
    search,
    ...filters,
  });

  function handleSupplierClick(id: string) {
    router.push(`/suppliers/${id}`);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Suppliers</h1>
        <p className="mt-2 text-gray-600">Browse and manage supplier information</p>
      </div>

      <Card>
        <CardBody>
          <div className="space-y-4">
            <Input
              placeholder="Search suppliers..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />

            <SupplierFilters
              filters={filters}
              onFiltersChange={setFilters}
            />
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardBody className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-gray-600">Loading suppliers...</div>
          ) : error ? (
            <div className="p-8 text-center text-red-600">{error}</div>
          ) : data && data.items.length > 0 ? (
            <>
              <SupplierTable
                suppliers={data.items}
                onSupplierClick={handleSupplierClick}
              />

              {data.pages > 1 && (
                <div className="p-6 border-t border-gray-200">
                  <Pagination
                    currentPage={page}
                    totalPages={data.pages}
                    onPageChange={setPage}
                  />
                </div>
              )}
            </>
          ) : (
            <div className="p-8 text-center text-gray-600">No suppliers found</div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
