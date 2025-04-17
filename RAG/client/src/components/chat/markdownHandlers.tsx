/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */
import React from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { atomDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { InlineMath, BlockMath } from "react-katex";

// Helper function to process text with inline math
export const processInlineMath = (text: string) => {
  if (!text || !text.includes('$')) return text;
  
  // Split the text into parts: math and non-math
  const parts: React.ReactNode[] = [];
  let currentText = '';
  let inMath = false;
  let mathContent = '';
  
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    
    if (char === '$') {
      if (inMath) {
        // End of a math expression
        parts.push(currentText);
        currentText = '';
        parts.push(
          <InlineMath key={`math-${parts.length}`} math={mathContent} />
        );
        mathContent = '';
        inMath = false;
      } else {
        // Start of a math expression
        parts.push(currentText);
        currentText = '';
        mathContent = '';
        inMath = true;
      }
    } else {
      if (inMath) {
        mathContent += char;
      } else {
        currentText += char;
      }
    }
  }
  
  // Add any remaining text
  if (currentText) {
    parts.push(currentText);
  }
  
  // If we're still in math mode (unmatched $), add it as text
  if (inMath && mathContent) {
    parts.push('$' + mathContent);
  }
  
  return parts;
};

// Preprocessing for LaTeX blocks
// Preprocessing for LaTeX blocks
export const preprocessLatex = (markdown: string) => {
  // Check if there's a ```math block and convert it to LaTeX
  const mathCodeBlockRegex = /```math\n([\s\S]*?)```/g;
  markdown = markdown.replace(mathCodeBlockRegex, (_, expression) => {
    return `$$${expression}$$`;
  });
  
  // Replace all $$ ... $$ blocks with a placeholder that won't be affected by markdown
  const blockMathPlaceholder = "BLOCK_MATH_PLACEHOLDER_";
  const blockMathRegex = /\$\$([\s\S]*?)\$\$/g;
  const blockMathExpressions: string[] = [];
  
  const processedMarkdown = markdown.replace(blockMathRegex, (_, expression) => {
    blockMathExpressions.push(expression);
    return blockMathPlaceholder + (blockMathExpressions.length - 1);
  });
  
  return { 
    processedMarkdown, 
    blockMathExpressions,
    blockMathPlaceholder
  };
};

// Table cell handler that processes math
export const tableCellHandler = ({ node, children, ...props }: any) => {
  const childContent = String(children);
  if (childContent.includes('$')) {
    return <td className="border border-gray-700 px-4 py-2" {...props}>{processInlineMath(childContent)}</td>;
  }
  return <td className="border border-gray-700 px-4 py-2" {...props}>{children}</td>;
};

// Table header cell handler that processes math
export const tableHeaderHandler = ({ node, children, ...props }: any) => {
  const childContent = String(children);
  if (childContent.includes('$')) {
    return <th className="border border-gray-700 px-4 py-2 text-left" {...props}>{processInlineMath(childContent)}</th>;
  }
  return <th className="border border-gray-700 px-4 py-2 text-left" {...props}>{children}</th>;
};

// Table components handler
export const tableComponents = {
  table: ({ node, ...props }: any) => (
    <div className="my-6 overflow-x-auto max-w-full">
      <table className="border-collapse bg-black text-white border border-gray-700" {...props} />
    </div>
  ),
  thead: (props: any) => <thead className="bg-gray-800" {...props} />,
  tbody: (props: any) => <tbody {...props} />, // Explicitly define tbody handler
  th: tableHeaderHandler,
  td: tableCellHandler,
  tr: (props: any) => <tr className="border-b border-gray-700" {...props} />
};

// Code block handler
export const codeBlockHandler = ({ node, inline, className, children, ...props }: any) => {
  const match = /language-(\w+)/.exec(className || '');
  const language = match?.[1] || 'text';
  
  // Special handling for math code blocks
  if (language === 'math') {
    const mathContent = String(children).replace(/\n$/, '');
    return (
      <div className="my-4 flex justify-center">
        <BlockMath math={mathContent} />
      </div>
    );
  }
  
  // Process any inline math expressions in code blocks
  const codeContent = String(children).replace(/\n$/, '');
  if (codeContent.includes('$') && language !== 'math') {
    // Use a different styling for code blocks that might contain math
    return !inline ? (
      <div className="my-4 relative">
        <div className="code-with-math">
          <SyntaxHighlighter
            style={atomDark}
            language={language}
            PreTag="div"
            {...props}
          >
            {codeContent.replace(/\$([^$]+)\$/g, (_, mathExpr) => {
              // Replace math expressions with visible placeholders
              return `[math: ${mathExpr}]`;
            })}
          </SyntaxHighlighter>
        </div>
      </div>
    ) : (
      <code className={className} {...props}>
        {processInlineMath(codeContent)}
      </code>
    );
  }
  
  return !inline ? (
    <div className="my-4">
      <SyntaxHighlighter
        style={atomDark}
        language={language}
        PreTag="div"
        {...props}
      >
        {codeContent}
      </SyntaxHighlighter>
    </div>
  ) : (
    <code className={className} {...props}>
      {children}
    </code>
  );
};
export const headingHandler = ({ node, level, children, ...props }: any) => {
  const childContent = String(children);
  if (childContent.includes('$')) {
    return React.createElement(
      `h${level}`,
      props,
      processInlineMath(childContent)
    );
  }
  return React.createElement(`h${level}`, props, children);
};

// Improve list handling
export const listHandler = ({ ordered, children, ...props }: any) => {
  const Component = ordered ? 'ol' : 'ul';
  const listStyle = ordered ? "list-decimal" : "list-disc"; 
  return <Component className={`pl-6 my-4 ${listStyle} ml-5 space-y-2`} {...props}>{children}</Component>;
};

// Enhanced list item handler for better spacing and bullet points
export const listItemHandler = ({ node, children, ...props }: any) => {
  const childContent = String(children);
  if (childContent.includes('$')) {
    return <li className="my-1 pl-1 marker:text-gray-400" {...props}>{processInlineMath(childContent)}</li>;
  }
  return <li className="my-1 pl-1 marker:text-gray-400" {...props}>{children}</li>;
};


export const paragraphHandler = (blockMathExpressions: string[], blockMathPlaceholder: string) => {
  return ({ node, children, ...props }: any) => {
    const childContent = String(children);
    
    // Check for block math placeholders and replace them
    if (childContent.includes(blockMathPlaceholder)) {
      const parts: React.ReactNode[] = [];
      let lastIndex = 0;
      const placeholderRegex = new RegExp(`${blockMathPlaceholder}(\\d+)`, 'g');
      let match;
      
      while ((match = placeholderRegex.exec(childContent)) !== null) {
        // Add text before the placeholder
        if (match.index > lastIndex) {
          const textBefore = childContent.substring(lastIndex, match.index);
          // Process any inline math in the text before
          if (textBefore.includes('$')) {
            parts.push(...processInlineMath(textBefore));
          } else {
            parts.push(textBefore);
          }
        }
        
        // Add the math component
        const mathIndex = parseInt(match[1], 10);
        if (mathIndex >= 0 && mathIndex < blockMathExpressions.length) {
          parts.push(
            <div key={`block-math-${mathIndex}`} className="my-4 flex justify-center">
              <BlockMath math={blockMathExpressions[mathIndex]} />
            </div>
          );
        }
        
        lastIndex = match.index + match[0].length;
      }
      
      // Add any remaining text
      if (lastIndex < childContent.length) {
        const textAfter = childContent.substring(lastIndex);
        // Process any inline math in the text after
        if (textAfter.includes('$')) {
          parts.push(...processInlineMath(textAfter));
        } else {
          parts.push(textAfter);
        }
      }
      
      return <div className="text-wrap break-words whitespace-normal" {...props}>{parts}</div>;
    }
    
    // Handle inline math expressions with single $ symbols
    if (childContent.includes('$')) {
      return <p className="text-wrap break-words whitespace-normal" {...props}>{processInlineMath(childContent)}</p>;
    }
    
    // Ensure normal paragraphs flow properly without preserving markdown newlines
    return <p className="text-wrap break-words whitespace-normal" {...props}>{children}</p>;
  };
};

// Get all markdown components
export const getMarkdownComponents = (blockMathExpressions: string[], blockMathPlaceholder: string) => {
  return {
    table: tableComponents.table,
    thead: tableComponents.thead,
    tbody: tableComponents.tbody,
    tr: tableComponents.tr,
    th: tableComponents.th,
    td: tableComponents.td,
    code: codeBlockHandler,
    h1: (props: any) => headingHandler({ ...props, level: 1 }),
    h2: (props: any) => headingHandler({ ...props, level: 2 }),
    h3: (props: any) => headingHandler({ ...props, level: 3 }),
    h4: (props: any) => headingHandler({ ...props, level: 4 }),
    h5: (props: any) => headingHandler({ ...props, level: 5 }),
    h6: (props: any) => headingHandler({ ...props, level: 6 }),
    ul: listHandler,
    ol: (props: any) => listHandler({ ...props, ordered: true }),
    li: listItemHandler,
    p: paragraphHandler(blockMathExpressions, blockMathPlaceholder),
    // Add better fallback list item handling
    a: (props: any) => <a className="text-blue-400 hover:underline" target="_blank" rel="noopener noreferrer" {...props} />
  };
};