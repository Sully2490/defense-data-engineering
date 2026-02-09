import { Card, CardBody } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Sparkles } from 'lucide-react';

interface QueryInterpretationProps {
  query: string;
  interpretation: string;
  searchType: string;
}

export function QueryInterpretation({ query, interpretation, searchType }: QueryInterpretationProps) {
  const isAI = searchType === 'sql' || searchType === 'rag';

  return (
    <Card className="border-l-4 border-l-steel-blue">
      <CardBody>
        <div className="flex items-start gap-3">
          <Sparkles className="w-5 h-5 text-steel-blue flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-semibold text-gray-900">Query Interpretation</h3>
              <Badge variant={isAI ? 'info' : 'default'}>
                {isAI ? 'AI Search' : 'Full-text Search'}
              </Badge>
            </div>
            <p className="text-sm text-gray-700 mb-2">
              <span className="font-medium">Your query:</span> &quot;{query}&quot;
            </p>
            <p className="text-sm text-gray-700">
              <span className="font-medium">Understood as:</span> {interpretation}
            </p>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
