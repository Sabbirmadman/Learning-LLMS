import React, { useMemo } from "react";
import { ChevronLeft, PanelLeftClose, PanelRightClose, FileText, FileImage, FileCode, File } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useSelector } from "react-redux";
import { RootState } from "@/store/store";
import { Badge } from "@/components/ui/badge";

interface FilesPanelProps {
  onClose: () => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  isMobile: boolean;
}

const FilesPanel: React.FC<FilesPanelProps> = ({ 
  onClose, 
  collapsed, 
  onToggleCollapse,
  isMobile 
}) => {
  const selectedFiles = useSelector((state: RootState) => state.selection.selectedFileIds);
  const selectedUrls = useSelector((state: RootState) => state.selection.selectedUrlIds);

  // Group files by type
  const groupedFiles = useMemo(() => {
    const groups = {
      images: [] as typeof selectedFiles,
      documents: [] as typeof selectedFiles,
      code: [] as typeof selectedFiles,
      other: [] as typeof selectedFiles
    };

    selectedFiles.forEach(file => {
      if (file.type.startsWith('image/')) {
        groups.images.push(file);
      } else if (file.type === 'application/pdf' || file.type.includes('word') || file.type.includes('text/plain')) {
        groups.documents.push(file);
      } else if (
        file.type.includes('javascript') || 
        file.type.includes('json') || 
        file.type.includes('html') || 
        file.type.includes('css') ||
        file.type.includes('code')
      ) {
        groups.code.push(file);
      } else {
        groups.other.push(file);
      }
    });

    return groups;
  }, [selectedFiles]);

  const getFileIcon = (contentType: string) => {
    if (contentType.startsWith("image/")) {
      return <FileImage className="h-4 w-4 text-blue-500" />;
    } else if (contentType === "application/pdf" || contentType.includes('text/plain')) {
      return <FileText className="h-4 w-4 text-red-500" />;
    } else if (
      contentType.includes("javascript") ||
      contentType.includes("json") ||
      contentType.includes("html") ||
      contentType.includes("css")
    ) {
      return <FileCode className="h-4 w-4 text-yellow-500" />;
    } else {
      return <File className="h-4 w-4 text-gray-400" />;
    }
  };

  if (collapsed) {
    return (
      <Button 
        variant="ghost" 
        size="sm" 
        className="flex justify-center items-center py-1 border-t"
        onClick={onToggleCollapse}
      >
        <PanelLeftClose className="h-4 w-4" />
      </Button>
    );
  }

  return (
    <>
      {isMobile && (
        <div className="flex items-center p-3 border-b">
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="mr-2"
          >
            <ChevronLeft className="h-5 w-5" />
          </Button>
          <h2 className="font-semibold">Files</h2>
        </div>
      )}

      <div className="flex-1 overflow-auto p-3">
        <h3 className="font-medium mb-2">Context Files</h3>
        
        {selectedFiles.length === 0 && selectedUrls.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No files or URLs selected for context.
          </p>
        ) : (
          <div className="space-y-4">
            {/* URLs Section */}
            {selectedUrls.length > 0 && (
              <div>
                <h4 className="text-sm font-medium mb-2 flex items-center">
                  <Badge variant="outline" className="mr-2">{selectedUrls.length}</Badge>
                  URLs
                </h4>
                <div className="space-y-1">
                  {selectedUrls.map(url => (
                    <div key={url.id} className="text-xs bg-muted p-2 rounded flex gap-2 items-start">
                      <div className="shrink-0 mt-0.5">
                        <FileText className="h-3.5 w-3.5 text-blue-500" />
                      </div>
                      <div className="truncate" title={url.url}>
                        {url.url}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Documents Section */}
            {groupedFiles.documents.length > 0 && (
              <div>
                <h4 className="text-sm font-medium mb-2 flex items-center">
                  <Badge variant="outline" className="mr-2">{groupedFiles.documents.length}</Badge>
                  Documents
                </h4>
                <div className="space-y-1">
                  {groupedFiles.documents.map(file => (
                    <div key={file.id} className="text-xs bg-muted p-2 rounded flex gap-2 items-start">
                      <div className="shrink-0 mt-0.5">
                        {getFileIcon(file.type)}
                      </div>
                      <div className="truncate" title={file.filename}>
                        {file.filename}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Images Section */}
            {groupedFiles.images.length > 0 && (
              <div>
                <h4 className="text-sm font-medium mb-2 flex items-center">
                  <Badge variant="outline" className="mr-2">{groupedFiles.images.length}</Badge>
                  Images
                </h4>
                <div className="space-y-1">
                  {groupedFiles.images.map(file => (
                    <div key={file.id} className="text-xs bg-muted p-2 rounded flex gap-2 items-start">
                      <div className="shrink-0 mt-0.5">
                        {getFileIcon(file.type)}
                      </div>
                      <div className="truncate" title={file.filename}>
                        {file.filename}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Code Files Section */}
            {groupedFiles.code.length > 0 && (
              <div>
                <h4 className="text-sm font-medium mb-2 flex items-center">
                  <Badge variant="outline" className="mr-2">{groupedFiles.code.length}</Badge>
                  Code Files
                </h4>
                <div className="space-y-1">
                  {groupedFiles.code.map(file => (
                    <div key={file.id} className="text-xs bg-muted p-2 rounded flex gap-2 items-start">
                      <div className="shrink-0 mt-0.5">
                        {getFileIcon(file.type)}
                      </div>
                      <div className="truncate" title={file.filename}>
                        {file.filename}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Other Files Section */}
            {groupedFiles.other.length > 0 && (
              <div>
                <h4 className="text-sm font-medium mb-2 flex items-center">
                  <Badge variant="outline" className="mr-2">{groupedFiles.other.length}</Badge>
                  Other Files
                </h4>
                <div className="space-y-1">
                  {groupedFiles.other.map(file => (
                    <div key={file.id} className="text-xs bg-muted p-2 rounded flex gap-2 items-start">
                      <div className="shrink-0 mt-0.5">
                        {getFileIcon(file.type)}
                      </div>
                      <div className="truncate" title={file.filename}>
                        {file.filename}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {!isMobile && (
        <Button 
          variant="ghost" 
          size="sm" 
          className="flex justify-center items-center py-1 border-t"
          onClick={onToggleCollapse}
        >
          <PanelRightClose className="h-4 w-4" />
        </Button>
      )}
    </>
  );
};

export default FilesPanel;