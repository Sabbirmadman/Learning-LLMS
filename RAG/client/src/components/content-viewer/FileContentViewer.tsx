import { Card, CardContent } from '@/components/ui/card';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { FileDetails } from '@/lib/redux/api/fileApi';
import { FileText } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface FileContentViewerProps {
  fileDetails: FileDetails;
}

export function FileContentViewer({ fileDetails }: FileContentViewerProps) {

  const formatDate = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch (e) {
      return dateString;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-md bg-primary/10">
            <FileText className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">{fileDetails.filename}</h1>
            <p className="text-sm text-muted-foreground">
              {fileDetails.content_type} • {(fileDetails.file_size / 1024).toFixed(2)} KB • 
              Uploaded {formatDate(fileDetails.upload_date)}
            </p>
          </div>
        </div>
      </div>

      <Card>
        <CardContent className="p-6">
          <div className="prose prose-sm md:prose-base dark:prose-invert max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {fileDetails.markdown_content}
            </ReactMarkdown>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}