export interface FileItem {
  id: string;
  filename: string;
  content_type: string;
  file_size: number;
  upload_date: string;
  file: string;
}

export interface ScrapeJob {
  id: string;
  url: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
  created_at: string;
  updated_at: string;
}
