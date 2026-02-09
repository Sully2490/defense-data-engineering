import { Card, CardBody } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Building2, Package } from 'lucide-react';
import Link from 'next/link';

interface SearchResultsProps {
  results: Record<string, any>[];
  total: number;
}

export function SearchResults({ results, total }: SearchResultsProps) {
  if (results.length === 0) {
    return (
      <Card>
        <CardBody className="text-center py-8">
          <p className="text-gray-600">No results found</p>
        </CardBody>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">
          {total} {total === 1 ? 'result' : 'results'}
        </h2>
      </div>

      {results.map((result, index) => {
        const isSupplier = 'cage_code' in result || 'small_business' in result;
        const id = result.id || index;

        return (
          <Link
            key={id}
            href={isSupplier ? `/suppliers/${id}` : `/materials/${id}`}
          >
            <Card className="hover:shadow-md transition-shadow cursor-pointer">
              <CardBody>
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0">
                    {isSupplier ? (
                      <Building2 className="w-8 h-8 text-steel-blue" />
                    ) : (
                      <Package className="w-8 h-8 text-green-600" />
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-lg font-medium text-gray-900">
                          {result.name}
                        </h3>
                        <p className="mt-1 text-sm text-gray-600">
                          {isSupplier ? (
                            <>CAGE: {result.cage_code || 'N/A'}</>
                          ) : (
                            <>NSN: {result.nsn || 'N/A'}</>
                          )}
                        </p>
                      </div>
                    </div>

                    {result.description && (
                      <p className="mt-2 text-sm text-gray-700 line-clamp-2">
                        {result.description}
                      </p>
                    )}

                    {isSupplier && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {result.small_business && <Badge variant="info">Small Business</Badge>}
                        {result.city && result.state && (
                          <Badge variant="default">{result.city}, {result.state}</Badge>
                        )}
                      </div>
                    )}

                    {!isSupplier && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {result.specialty_metal && <Badge variant="info">Specialty Metal</Badge>}
                        {result.export_controlled && <Badge variant="danger">Export Controlled</Badge>}
                        {result.domestic_required && <Badge variant="warning">Domestic Req.</Badge>}
                      </div>
                    )}
                  </div>
                </div>
              </CardBody>
            </Card>
          </Link>
        );
      })}
    </div>
  );
}
