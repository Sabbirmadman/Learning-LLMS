/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState } from "react";
import { ChevronDown, ChevronUp, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ScrapeJobCard } from "./ScrapeJobCard";
import { ScrapeJob } from "@/types/files";

interface UrlsSectionProps {
  urls: ScrapeJob[] | undefined;
  isLoading: boolean;
  createScrape: ({ url }: { url: string }) => Promise<any>;
  deleteScrape: (id: string) => Promise<any>;
  isSelected: (id: string) => boolean;
  toggleSelection: (id: string) => void;
  searchQuery: string;
}

export const UrlsSection: React.FC<UrlsSectionProps> = ({
  urls,
  isLoading,
  createScrape,
  deleteScrape,
  isSelected,
  toggleSelection,
  searchQuery,
}) => {
  const [isOpen, setIsOpen] = useState(true);
  const [newUrl, setNewUrl] = useState("");

  const filteredUrls = urls?.filter((url) =>
    url.url.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleCreateScrape = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUrl) return;

    try {
      await createScrape({ url: newUrl });
      setNewUrl("");
    } catch (error) {
      console.error("Failed to create scrape job:", error);
    }
  };

  const handleDeleteScrape = async (id: string) => {
    try {
      await deleteScrape(id);
    } catch (error) {
      console.error("Failed to delete scrape job:", error);
    }
  };

  return (
    <Card>
      <Collapsible open={isOpen} onOpenChange={setIsOpen} className="w-full">
        <CollapsibleTrigger className="w-full bg-muted p-4 flex justify-between items-center cursor-pointer">
          <div className="flex items-center">
            <Globe className="w-5 h-5 mr-2" />
            <h2 className="text-xl font-semibold">URLs / Scraping Jobs</h2>
          </div>
          {isOpen ? <ChevronUp /> : <ChevronDown />}
        </CollapsibleTrigger>

        <CollapsibleContent className="p-4">
          <form onSubmit={handleCreateScrape} className="mb-4 flex gap-2">
            <Input
              type="url"
              value={newUrl}
              onChange={(e) => setNewUrl(e.target.value)}
              placeholder="Enter URL to scrape..."
              required
              className="flex-1"
            />
            <Button type="submit">Add URL</Button>
          </form>

          {isLoading ? (
            <div className="text-center py-8">Loading scrape jobs...</div>
          ) : filteredUrls && filteredUrls.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filteredUrls.map((url) => (
                <ScrapeJobCard
                  key={url.id}
                  url={url}
                  isSelected={isSelected(url.id)}
                  toggleSelection={toggleSelection}
                  onDelete={handleDeleteScrape}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              No scraping jobs found. Add a URL to start scraping.
            </div>
          )}
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
};
