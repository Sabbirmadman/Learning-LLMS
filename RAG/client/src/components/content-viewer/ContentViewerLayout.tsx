import { Button } from '@/components/ui/button';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { FileContentViewer } from './FileContentViewer';
import { ScrapeContentViewer } from './ScrapeContentViewer';
import { useContentViewer } from '@/hooks/useContentViewer';

export function ContentViewerLayout() {
  const {
    type,
    fileDetails,
    scrapeDetails,
    isLoading,
    error,
    searchQuery,
    setSearchQuery,
    filteredContents,
    goBack
  } = useContentViewer();

  // Handle loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[50vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // Handle error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-[50vh]">
        <h2 className="text-xl font-bold text-destructive mb-2">Error</h2>
        <p className="text-muted-foreground mb-6">Failed to load content. Please try again later.</p>
        <Button onClick={goBack}>Go Back</Button>
      </div>
    );
  }

  // Handle not found state
  if ((type === 'file' && !fileDetails) || (type === 'scrape' && !scrapeDetails)) {
    return (
      <div className="flex flex-col items-center justify-center h-[50vh]">
        <h2 className="text-xl font-bold mb-2">Content Not Found</h2>
        <p className="text-muted-foreground mb-6">The requested content could not be found</p>
        <Button onClick={goBack}>Go Back</Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 space-y-6">
      <Button 
        variant="outline" 
        onClick={goBack}
        className="flex items-center gap-2"
      >
        <ArrowLeft className="h-4 w-4" />
        Back
      </Button>

      {type === 'file' && fileDetails && (
        <FileContentViewer fileDetails={fileDetails} />
      )}
      
      {type === 'scrape' && scrapeDetails && (
        <ScrapeContentViewer 
          scrapeDetails={scrapeDetails}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          filteredContents={filteredContents || []}
        />
      )}
    </div>
  );
}