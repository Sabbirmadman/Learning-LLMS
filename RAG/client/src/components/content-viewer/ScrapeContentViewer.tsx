import { ScrapeJobDetails, ScrapeContent } from '@/lib/redux/api/scrapeApi';
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { formatDistanceToNow } from 'date-fns';

interface ScrapeContentViewerProps {
  scrapeDetails: ScrapeJobDetails;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  filteredContents: ScrapeContent[];
}

export function ScrapeContentViewer({
  scrapeDetails,
  searchQuery,
  setSearchQuery,
  filteredContents
}: ScrapeContentViewerProps) {
  const formatDate = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch (e) {
      return dateString;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold mb-2">{scrapeDetails.url}</h1>
        <p className="text-sm text-muted-foreground">
          Status: <span className="font-medium">{scrapeDetails.status}</span> • 
          Created {formatDate(scrapeDetails.created_at)} • 
          Last updated {formatDate(scrapeDetails.updated_at)}
        </p>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search content..."
          className="pl-10"
        />
      </div>

      {filteredContents && filteredContents.length > 0 ? (
        <Accordion type="multiple" className="space-y-4">
          {filteredContents.map((content) => (
            <Card key={content.id}>
              <AccordionItem value={`content-${content.id}`} className="border-none">
                <AccordionTrigger className="px-4 py-3 hover:no-underline">
                  <div className="text-left">
                    <div className="font-medium">{content.link}</div>
                    <div className="text-xs text-muted-foreground">
                      {content.content_type} • {formatDate(content.created_at)}
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-4 pb-4">
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {content.content}
                    </ReactMarkdown>
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Card>
          ))}
        </Accordion>
      ) : (
        <div className="text-center py-12 text-muted-foreground">
          {searchQuery ? "No results found" : "No content available"}
        </div>
      )}
    </div>
  );
}