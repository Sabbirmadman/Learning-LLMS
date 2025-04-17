import React, { useState } from "react";
import { useFiles } from "@/hooks/useFiles";
import { useUrls } from "@/hooks/useUrls";
import { useNavigate } from "react-router-dom";
import { FilesSection } from "@/components/files/FilesSection";
import { UrlsSection } from "@/components/files/UrlsSection";
import { SearchBar } from "@/components/files/SearchBar";

const MyFilesPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");

  const {
    files,
    isLoading: isFilesLoading,
    uploadFile,
    deleteFile,
    toggleSelection: toggleFileSelection,
    isSelected: isFileSelected,
    selectedFileIds,
  } = useFiles();

  const {
    urls,
    isLoading: isUrlsLoading,
    createScrape,
    deleteScrape,
    toggleSelection: toggleUrlSelection,
    isSelected: isUrlSelected,
    selectedUrlIds,
  } = useUrls();

  const hasSelections = selectedFileIds.length > 0 || selectedUrlIds.length > 0;

  const handleStartChat = () => {
    navigate("/chat", {
      state: {
        selectedFileIds,
        selectedUrlIds,
      },
    });
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">My Files</h1>

      <SearchBar
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        hasSelections={hasSelections}
        onStartChat={handleStartChat}
      />

      <FilesSection
        files={files}
        isLoading={isFilesLoading}
        uploadFile={uploadFile}
        deleteFile={deleteFile}
        isSelected={isFileSelected}
        toggleSelection={toggleFileSelection}
        searchQuery={searchQuery}
      />

      <UrlsSection
        urls={urls}
        isLoading={isUrlsLoading}
        createScrape={createScrape}
        deleteScrape={deleteScrape}
        isSelected={isUrlSelected}
        toggleSelection={toggleUrlSelection}
        searchQuery={searchQuery}
      />
    </div>
  );
};

export default MyFilesPage;
