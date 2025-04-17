import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '@/store/store';
import { 
  useGetScrapesQuery, 
  useCreateScrapeMutation, 
  useDeleteScrapeMutation,
  useGetScrapeByIdQuery
} from '../lib/redux/api/scrapeApi';
import { 
  toggleUrlSelection, 
  selectUrls, 
  clearUrlSelection,
  SelectedUrl
} from '../store/slices/selectionSlice';

export const useUrls = () => {
  const dispatch = useDispatch();
  const selectedUrls = useSelector((state: RootState) => state.selection.selectedUrlIds);
  
  const {
    data: urls,
    isLoading: isLoadingUrls,
    error: urlsError,
    refetch: refetchUrls
  } = useGetScrapesQuery();
  
  const [createScrape, { isLoading: isCreating }] = useCreateScrapeMutation();
  const [deleteScrape, { isLoading: isDeleting }] = useDeleteScrapeMutation();
  
  const isLoading = isLoadingUrls || isCreating || isDeleting;
  
  const toggleSelection = (urlId: string) => {
    const url = urls?.find(u => u.id === urlId);
    if (url) {
      const selectedUrl: SelectedUrl = {
        id: url.id,
        url: url.url,
        createdAt: url.created_at || new Date().toISOString()
      };
      dispatch(toggleUrlSelection(selectedUrl));
    }
  };
  
  const setSelectedUrls = (urlIds: string[]) => {
    if (urls) {
      const selectedUrlsData = urls
        .filter(url => urlIds.includes(url.id))
        .map(url => ({
          id: url.id,
          url: url.url,
          createdAt: url.created_at || new Date().toISOString()
        }));
      dispatch(selectUrls(selectedUrlsData));
    }
  };
  
  const clearSelection = () => {
    dispatch(clearUrlSelection());
  };
  
  const isSelected = (urlId: string) => {
    return selectedUrls.some(url => url.id === urlId);
  };
  
  // Get just the IDs of selected URLs for easier passing to other components
  const selectedUrlIds = selectedUrls.map(url => url.id);
  
  return {
    urls,
    selectedUrlIds,
    isLoading,
    urlsError,
    createScrape,
    deleteScrape,
    refetchUrls,
    toggleSelection,
    setSelectedUrls,
    clearSelection,
    isSelected
  };
};

// Create a separate hook for URL details
export const useUrlDetails = (id: string) => {
  return useGetScrapeByIdQuery(id);
};