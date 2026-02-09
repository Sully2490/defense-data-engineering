'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import { Organization } from '@/lib/types';
import { Card, CardHeader, CardBody, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';

export default function SettingsPage() {
  const { user } = useAuth();
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchOrganization();
  }, []);

  async function fetchOrganization() {
    try {
      if (user?.org_id) {
        const data = await api.get<Organization>(`/organizations/${user.org_id}`);
        setOrganization(data);
      }
    } catch (error) {
      console.error('Failed to fetch organization:', error);
    } finally {
      setIsLoading(false);
    }
  }

  if (isLoading) {
    return <div className="p-8 text-center">Loading settings...</div>;
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="mt-2 text-gray-600">Manage your account and organization settings</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
        </CardHeader>
        <CardBody>
          <div className="space-y-4">
            <Input
              label="Email"
              type="email"
              value={user?.email || ''}
              readOnly
              disabled
            />
            <Input
              label="Name"
              type="text"
              value={user?.name || ''}
              readOnly
              disabled
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Role
              </label>
              <Badge variant="info" className="uppercase">
                {user?.role || 'N/A'}
              </Badge>
            </div>
          </div>
        </CardBody>
      </Card>

      {organization && (
        <Card>
          <CardHeader>
            <CardTitle>Organization</CardTitle>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              <Input
                label="Organization Name"
                type="text"
                value={organization.name}
                readOnly
                disabled
              />
              {organization.tier && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tier
                  </label>
                  <Badge variant="info" className="uppercase">
                    {organization.tier}
                  </Badge>
                </div>
              )}
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
