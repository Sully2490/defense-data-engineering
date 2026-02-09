import { Button } from '@/components/ui/Button';
import { X } from 'lucide-react';

interface FilterState {
  state: string;
  isSmallBusiness?: boolean;
}

interface SupplierFiltersProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
}

export function SupplierFilters({ filters, onFiltersChange }: SupplierFiltersProps) {
  function toggleSmallBusiness() {
    onFiltersChange({
      ...filters,
      isSmallBusiness: filters.isSmallBusiness ? undefined : true,
    });
  }

  function clearFilters() {
    onFiltersChange({ state: '', isSmallBusiness: undefined });
  }

  const hasActiveFilters = filters.isSmallBusiness !== undefined;

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="text-sm text-gray-600 mr-2">Filters:</span>

      <Button
        variant={filters.isSmallBusiness ? 'primary' : 'outline'}
        size="sm"
        onClick={toggleSmallBusiness}
      >
        Small Business
      </Button>

      {hasActiveFilters && (
        <Button
          variant="ghost"
          size="sm"
          onClick={clearFilters}
          className="flex items-center gap-1"
        >
          <X className="w-4 h-4" />
          Clear
        </Button>
      )}
    </div>
  );
}
