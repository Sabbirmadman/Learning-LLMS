/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useRef } from "react";
import { ChevronDown, ChevronUp, Upload, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { FileCard } from "./FileCard";
import { FileItem } from "@/types/files";

interface FilesSectionProps {
  files: FileItem[] | undefined;
  isLoading: boolean;
  uploadFile: ({ files }: { files: File[] }) => Promise<any>;
  deleteFile: (id: string) => Promise<any>;
  isSelected: (id: string) => boolean;
  toggleSelection: (id: string) => void;
  searchQuery: string;
}

export const FilesSection: React.FC<FilesSectionProps> = ({
  files,
  isLoading,
  uploadFile,
  deleteFile,
  isSelected,
  toggleSelection,
  searchQuery,
}) => {
  const [isOpen, setIsOpen] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const filteredFiles = files?.filter((file) =>
    file.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;

    setIsUploading(true);
    try {
      // Convert FileList to array for easier handling
      const filesArray = Array.from(e.target.files);
      setUploadProgress(`Uploading ${filesArray.length} file(s)...`);
      
      console.log("Uploading files:", filesArray.map(f => f.name));
      const response = await uploadFile({ files: filesArray });
      console.log("Upload response:", response);

      // Reset the file input to allow uploading the same file again
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (error) {
      console.error("File upload failed:", error);
    } finally {
      setIsUploading(false);
      setUploadProgress(null);
    }
  };

  const handleDeleteFile = async (id: string) => {
    try {
      await deleteFile(id);
    } catch (error) {
      console.error("Failed to delete file:", error);
    }
  };

  return (
    <Card className="mb-6">
      <Collapsible open={isOpen} onOpenChange={setIsOpen} className="w-full">
        <CollapsibleTrigger className="w-full bg-muted p-4 flex justify-between items-center cursor-pointer">
          <div className="flex items-center">
            <FileText className="w-5 h-5 mr-2" />
            <h2 className="text-xl font-semibold">Files</h2>
          </div>
          {isOpen ? <ChevronUp /> : <ChevronDown />}
        </CollapsibleTrigger>

        <CollapsibleContent className="p-4">
          <div className="mb-4">
            <Button
              variant="outline"
              className="w-full flex items-center justify-center gap-2"
              disabled={isUploading}
              onClick={() => fileInputRef.current?.click()}
            >
              {isUploading ? (
                uploadProgress || "Uploading..."
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Upload Files
                </>
              )}
            </Button>
            <input
              ref={fileInputRef}
              id="fileUpload"
              type="file"
              className="hidden"
              onChange={handleFileUpload}
              disabled={isUploading}
              accept="*/*"
              multiple
            />
          </div>

          {isLoading ? (
            <div className="text-center py-8">Loading files...</div>
          ) : filteredFiles && filteredFiles.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filteredFiles.map((file) => (
                <FileCard
                  key={file.id}
                  file={file}
                  isSelected={isSelected(file.id)}
                  toggleSelection={toggleSelection}
                  onDelete={handleDeleteFile}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              No files found. Upload some files to get started.
            </div>
          )}
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
};