'use client';

import { useState } from 'react';
import { useMaterials } from '@/hooks/useMaterials';
import { Card, CardBody } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Table, TableHead, TableBody, TableRow, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { Pagination } from '@/components/ui/Pagination';

export default function MaterialsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');

  const { data, isLoading, error } = useMaterials({
    page,
    size: 20,
    search,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Materials</h1>
        <p className="mt-2 text-gray-600">Browse material catalog</p>
      </div>

      <Card>
        <CardBody>
          <Input
            placeholder="Search materials..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </CardBody>
      </Card>

      <Card>
        <CardBody className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-gray-600">Loading materials...</div>
          ) : error ? (
            <div className="p-8 text-center text-red-600">{error}</div>
          ) : data && data.items.length > 0 ? (
            <>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell header>Name</TableCell>
                    <TableCell header>NSN</TableCell>
                    <TableCell header>Specification</TableCell>
                    <TableCell header>Grade / Form</TableCell>
                    <TableCell header>Type</TableCell>
                    <TableCell header>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.items.map((material) => (
                    <TableRow key={material.id}>
                      <TableCell>
                        <div className="font-medium text-gray-900">{material.name}</div>
                        {material.description && (
                          <div className="text-sm text-gray-600">{material.description}</div>
                        )}
                      </TableCell>
                      <TableCell>{material.nsn || '-'}</TableCell>
                      <TableCell>{material.specification || '-'}</TableCell>
                      <TableCell>
                        {material.grade || material.form
                          ? [material.grade, material.form].filter(Boolean).join(' / ')
                          : '-'}
                      </TableCell>
                      <TableCell>{material.material_type || '-'}</TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          {material.specialty_metal && <Badge variant="info">Specialty Metal</Badge>}
                          {material.export_controlled && <Badge variant="danger">Export Controlled</Badge>}
                          {material.domestic_required && <Badge variant="warning">Domestic Req.</Badge>}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

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
            <div className="p-8 text-center text-gray-600">No materials found</div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
