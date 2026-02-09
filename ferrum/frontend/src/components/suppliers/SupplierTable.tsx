import { Supplier } from '@/lib/types';
import { Table, TableHead, TableBody, TableRow, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';

interface SupplierTableProps {
  suppliers: Supplier[];
  onSupplierClick: (id: string) => void;
}

export function SupplierTable({ suppliers, onSupplierClick }: SupplierTableProps) {
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableCell header>Name</TableCell>
          <TableCell header>CAGE Code</TableCell>
          <TableCell header>Location</TableCell>
          <TableCell header>NAICS</TableCell>
          <TableCell header>Risk Score</TableCell>
          <TableCell header>Certifications</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {suppliers.map((supplier) => (
          <TableRow
            key={supplier.id}
            onClick={() => onSupplierClick(supplier.id)}
          >
            <TableCell>
              <div className="font-medium text-gray-900">{supplier.name}</div>
              {supplier.small_business && (
                <Badge variant="info" className="mt-1">Small Business</Badge>
              )}
            </TableCell>
            <TableCell>{supplier.cage_code || '-'}</TableCell>
            <TableCell>
              {supplier.city && supplier.state ? (
                `${supplier.city}, ${supplier.state}`
              ) : (
                <span className="text-gray-400">-</span>
              )}
            </TableCell>
            <TableCell>{supplier.naics_codes?.join(', ') || '-'}</TableCell>
            <TableCell>
              {supplier.risk_score ? (
                <Badge
                  variant={
                    supplier.risk_score < 30 ? 'success' :
                    supplier.risk_score < 70 ? 'warning' : 'danger'
                  }
                >
                  {supplier.risk_score}
                </Badge>
              ) : (
                <span className="text-gray-400">-</span>
              )}
            </TableCell>
            <TableCell>
              {supplier.certifications?.length || 0}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
