declare module 'react-katex' {
    import { ReactNode } from 'react';
  
    interface KatexProps {
      math: string;
      block?: boolean;
      errorColor?: string;
      renderError?: (error: Error) => ReactNode;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      settings?: any;
      children?: string;
    }
  
    export const InlineMath: React.FC<KatexProps>;
    export const BlockMath: React.FC<KatexProps>;
  }