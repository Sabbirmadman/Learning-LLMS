import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '@/store/store';
import { 
  useGetFilesQuery, 
  useUploadFileMutation, 
  useDeleteFileMutation,
  useGetFileByIdQuery
} from '../lib/redux/api/fileApi';
import { 
  toggleFileSelection, 
  selectFiles, 
  clearFileSelection,
  SelectedFile 
} from '../store/slices/selectionSlice';

export const useFiles = () => {
  const dispatch = useDispatch();
  const selectedFiles = useSelector((state: RootState) => state.selection.selectedFileIds);
  
  const {
    data: files,
    isLoading: isLoadingFiles,
    error: filesError,
    refetch: refetchFiles
  } = useGetFilesQuery();
  
  const [uploadFile, { isLoading: isUploading }] = useUploadFileMutation();
  const [deleteFile, { isLoading: isDeleting }] = useDeleteFileMutation();
  
  const isLoading = isLoadingFiles || isUploading || isDeleting;
  
  const toggleSelection = (fileId: string) => {
    const file = files?.find(f => f.id === fileId);
    if (file) {
      const selectedFile: SelectedFile = {
        id: file.id,
        filename: file.filename,
        size: file.file_size,
        type: file.content_type,
        createdAt: file.upload_date
      };
      dispatch(toggleFileSelection(selectedFile));
    }
  };
  
  const setSelectedFiles = (fileIds: string[]) => {
    if (files) {
      const selectedFilesData = files
        .filter(file => fileIds.includes(file.id))
        .map(file => ({
          id: file.id,
          filename: file.filename,
          size: file.file_size,
          type: file.content_type,
          createdAt: file.upload_date
        }));
      dispatch(selectFiles(selectedFilesData));
    }
  };
  
  const clearSelection = () => {
    dispatch(clearFileSelection());
  };
  
  const isSelected = (fileId: string) => {
    return selectedFiles.some(file => file.id === fileId);
  };
  
  // Get just the IDs of selected files for easier passing to other components
  const selectedFileIds = selectedFiles.map(file => file.id);
  
  return {
    files,
    selectedFileIds,
    isLoading,
    filesError,
    uploadFile,
    deleteFile,
    refetchFiles,
    toggleSelection,
    setSelectedFiles,
    clearSelection,
    isSelected
  };
};

// Create a separate hook for file details
export const useFileDetails = (id: string) => {
  return useGetFileByIdQuery(id);
};