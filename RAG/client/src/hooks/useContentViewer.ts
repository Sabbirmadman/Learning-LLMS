import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useFileDetails } from './useFiles';
import { useUrlDetails } from './useUrls';

type ContentType = 'file' | 'scrape';

export function useContentViewer() {
  const { type, id } = useParams<{ type: ContentType; id: string }>();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  
  // Fetch file details if type is 'file'
  const {
    data: fileDetails,
    isLoading: isFileLoading,
    error: fileError
  } = useFileDetails(type === 'file' ? id ?? '' : '');
  
  // Fetch URL/scrape details if type is 'scrape'
  const {
    data: scrapeDetails,
    isLoading: isScrapeLoading,
    error: scrapeError
  } = useUrlDetails(type === 'scrape' ? id ?? '' : '');
  
  const isLoading = type === 'file' ? isFileLoading : isScrapeLoading;
  const error = type === 'file' ? fileError : scrapeError;
  
  // Filter scrape contents by search query
  const filteredContents = scrapeDetails?.contents?.filter(content => 
    content.link.toLowerCase().includes(searchQuery.toLowerCase()) || 
    content.content.toLowerCase().includes(searchQuery.toLowerCase())
  );
  
  const goBack = () => {
    navigate(-1);
  };
  
  return {
    type,
    fileDetails,
    scrapeDetails,
    isLoading,
    error,
    searchQuery,
    setSearchQuery,
    filteredContents,
    goBack
  };
}