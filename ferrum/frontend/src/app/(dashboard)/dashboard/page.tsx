'use client';

import { useState, useEffect } from 'react';
import { Card, CardBody, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Building2, Package, ShieldCheck, AlertTriangle } from 'lucide-react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { PaginatedResponse, Supplier, Material } from '@/lib/types';

export default function DashboardPage() {
  const [supplierCount, setSupplierCount] = useState<number | null>(null);
  const [materialCount, setMaterialCount] = useState<number | null>(null);

  useEffect(() => {
    async function fetchCounts() {
      try {
        const [suppliers, materials] = await Promise.all([
          api.get<PaginatedResponse<Supplier>>('/suppliers?size=1'),
          api.get<PaginatedResponse<Material>>('/materials?size=1'),
        ]);
        setSupplierCount(suppliers.total);
        setMaterialCount(materials.total);
      } catch (err) {
        console.error('Failed to fetch counts:', err);
      }
    }
    fetchCounts();
  }, []);

  const stats = [
    { name: 'Total Suppliers', value: supplierCount !== null ? supplierCount.toLocaleString() : '...', icon: Building2, color: 'text-steel-blue' },
    { name: 'Materials', value: materialCount !== null ? materialCount.toLocaleString() : '...', icon: Package, color: 'text-green-600' },
    { name: 'Active Certifications', value: '-', icon: ShieldCheck, color: 'text-blue-600' },
    { name: 'Risk Alerts', value: '-', icon: AlertTriangle, color: 'text-forge-orange' },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">Supply chain overview and quick actions</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.name}>
              <CardBody className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                  <p className="mt-2 text-3xl font-bold text-gray-900">{stat.value}</p>
                </div>
                <Icon className={`w-12 h-12 ${stat.color}`} />
              </CardBody>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardBody>
          <CardTitle>Quick Search</CardTitle>
          <div className="mt-4">
            <Link href="/search">
              <Input
                placeholder="Search your supply chain..."
                className="cursor-pointer"
                readOnly
              />
            </Link>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
