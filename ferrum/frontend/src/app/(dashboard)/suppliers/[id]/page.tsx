'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { Supplier } from '@/lib/types';
import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui/Card';
import { Tabs } from '@/components/ui/Tabs';
import { Badge } from '@/components/ui/Badge';
import { Building2, Mail, Phone, Globe } from 'lucide-react';

export default function SupplierDetailPage() {
  const params = useParams();
  const [supplier, setSupplier] = useState<Supplier | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSupplier();
  }, [params.id]);

  async function fetchSupplier() {
    try {
      const data = await api.get<Supplier>(`/suppliers/${params.id}`);
      setSupplier(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch supplier');
    } finally {
      setIsLoading(false);
    }
  }

  if (isLoading) {
    return <div className="p-8 text-center">Loading supplier details...</div>;
  }

  if (error || !supplier) {
    return <div className="p-8 text-center text-red-600">{error || 'Supplier not found'}</div>;
  }

  const tabs = [
    {
      id: 'overview',
      label: 'Overview',
      content: (
        <div className="space-y-6">
          {supplier.description && (
            <p className="text-gray-700">{supplier.description}</p>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">CAGE Code</p>
              <p className="mt-1 font-medium">{supplier.cage_code || '-'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">DUNS Number</p>
              <p className="mt-1 font-medium">{supplier.duns_number || '-'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">NAICS Codes</p>
              <p className="mt-1 font-medium">{supplier.naics_codes?.join(', ') || '-'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Risk Score</p>
              <p className="mt-1">
                {supplier.risk_score ? (
                  <Badge
                    variant={
                      supplier.risk_score < 30 ? 'success' :
                      supplier.risk_score < 70 ? 'warning' : 'danger'
                    }
                  >
                    {supplier.risk_score}
                  </Badge>
                ) : '-'}
              </p>
            </div>
          </div>

          {(supplier.address || supplier.city) && (
            <div>
              <p className="text-sm text-gray-600 mb-2">Address</p>
              <p className="font-medium">
                {supplier.address && <>{supplier.address}<br /></>}
                {supplier.city && supplier.state && (
                  <>{supplier.city}, {supplier.state} {supplier.zip_code}<br /></>
                )}
                {supplier.country || 'USA'}
              </p>
            </div>
          )}

          <div className="space-y-2">
            {supplier.contact_email && (
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-gray-400" />
                <a href={`mailto:${supplier.contact_email}`} className="text-steel-blue hover:underline">
                  {supplier.contact_email}
                </a>
              </div>
            )}
            {supplier.contact_phone && (
              <div className="flex items-center gap-2">
                <Phone className="w-4 h-4 text-gray-400" />
                <span>{supplier.contact_phone}</span>
              </div>
            )}
            {supplier.website && (
              <div className="flex items-center gap-2">
                <Globe className="w-4 h-4 text-gray-400" />
                <a href={supplier.website} target="_blank" rel="noopener noreferrer" className="text-steel-blue hover:underline">
                  {supplier.website}
                </a>
              </div>
            )}
          </div>

          <div>
            <p className="text-sm text-gray-600 mb-2">Business Status</p>
            <div className="flex flex-wrap gap-2">
              {supplier.small_business && <Badge variant="info">Small Business</Badge>}
              {supplier.woman_owned && <Badge variant="info">Woman Owned</Badge>}
              {supplier.veteran_owned && <Badge variant="info">Veteran Owned</Badge>}
              {supplier.hub_zone && <Badge variant="info">HUBZone</Badge>}
              {!supplier.small_business && !supplier.woman_owned && !supplier.veteran_owned && !supplier.hub_zone && (
                <span className="text-gray-400">None</span>
              )}
            </div>
          </div>
        </div>
      ),
    },
    {
      id: 'capabilities',
      label: 'Capabilities',
      content: (
        <div className="space-y-4">
          {supplier.capabilities && supplier.capabilities.length > 0 ? (
            supplier.capabilities.map((cap) => (
              <div key={cap.id} className="border-b border-gray-200 pb-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900">{cap.name}</h4>
                    {cap.category && (
                      <p className="mt-1 text-sm text-gray-600">{cap.category}</p>
                    )}
                  </div>
                  {cap.proficiency && (
                    <Badge variant={
                      cap.proficiency === 'expert' ? 'success' :
                      cap.proficiency === 'advanced' ? 'info' :
                      cap.proficiency === 'intermediate' ? 'warning' : 'default'
                    }>
                      {cap.proficiency}
                    </Badge>
                  )}
                </div>
              </div>
            ))
          ) : (
            <p className="text-gray-600">No capabilities listed</p>
          )}
        </div>
      ),
    },
    {
      id: 'certifications',
      label: 'Certifications',
      content: (
        <div className="space-y-4">
          {supplier.certifications && supplier.certifications.length > 0 ? (
            supplier.certifications.map((cert) => (
              <div key={cert.id} className="border-b border-gray-200 pb-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900">{cert.name}</h4>
                    <p className="text-sm text-gray-600">{cert.cert_number || 'No number'}</p>
                    {cert.body && (
                      <p className="text-sm text-gray-600">Issued by: {cert.body}</p>
                    )}
                  </div>
                  {cert.status && (
                    <Badge variant={
                      cert.status === 'active' ? 'success' :
                      cert.status === 'expired' ? 'danger' :
                      cert.status === 'pending' ? 'warning' : 'default'
                    }>
                      {cert.status}
                    </Badge>
                  )}
                </div>
                <div className="mt-2 flex gap-4 text-sm text-gray-600">
                  {cert.issued_date && <span>Issued: {new Date(cert.issued_date).toLocaleDateString()}</span>}
                  {cert.expiry_date && <span>Expires: {new Date(cert.expiry_date).toLocaleDateString()}</span>}
                </div>
              </div>
            ))
          ) : (
            <p className="text-gray-600">No certifications listed</p>
          )}
        </div>
      ),
    },
    {
      id: 'materials',
      label: 'Materials',
      content: (
        <div className="space-y-4">
          {supplier.materials && supplier.materials.length > 0 ? (
            supplier.materials.map((mat) => (
              <div key={mat.id} className="border-b border-gray-200 pb-4">
                <h4 className="font-medium text-gray-900">{mat.name}</h4>
                {mat.specification && (
                  <p className="mt-1 text-sm text-gray-600">Spec: {mat.specification}</p>
                )}
              </div>
            ))
          ) : (
            <p className="text-gray-600">No materials listed</p>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-4">
        <Building2 className="w-12 h-12 text-steel-blue" />
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{supplier.name}</h1>
          <p className="mt-1 text-gray-600">
            {supplier.cage_code ? `CAGE: ${supplier.cage_code}` : ''}
            {supplier.cage_code && supplier.country ? ' | ' : ''}
            {supplier.country || ''}
          </p>
        </div>
      </div>

      <Card>
        <CardBody>
          <Tabs tabs={tabs} />
        </CardBody>
      </Card>
    </div>
  );
}
