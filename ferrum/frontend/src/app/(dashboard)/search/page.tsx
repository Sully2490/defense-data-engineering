'use client';

import { useState } from 'react';
import { useSearch } from '@/hooks/useSearch';
import { Card, CardBody } from '@/components/ui/Card';
import { SearchBar } from '@/components/search/SearchBar';
import { SearchResults } from '@/components/search/SearchResults';
import { QueryInterpretation } from '@/components/search/QueryInterpretation';
import { SkeletonCard } from '@/components/ui/Skeleton';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const { data, isLoading, error, search } = useSearch();

  function handleSearch(searchQuery: string) {
    setQuery(searchQuery);
    search(searchQuery, true);
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Search</h1>
        <p className="mt-2 text-gray-600">AI-powered supply chain search</p>
      </div>

      <SearchBar onSearch={handleSearch} />

      {isLoading && (
        <div className="space-y-4">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      )}

      {error && (
        <Card>
          <CardBody>
            <p className="text-red-600">{error}</p>
          </CardBody>
        </Card>
      )}

      {data && (
        <div className="space-y-6">
          {data.query_interpretation && (
            <QueryInterpretation
              query={query}
              interpretation={data.query_interpretation}
              searchType={data.search_type}
            />
          )}

          <SearchResults results={data.results} total={data.total} />
        </div>
      )}

      {!data && !isLoading && (
        <Card>
          <CardBody className="text-center py-12">
            <p className="text-gray-600">
              Enter a natural language query to search your supply chain
            </p>
            <p className="mt-2 text-sm text-gray-500">
              Example: &quot;Find small business suppliers in California with ISO 9001 certification&quot;
            </p>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
