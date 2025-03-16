import React from 'react';
import { 
  FileMarkdownOutlined, FileImageOutlined, FileZipOutlined,
  FileExcelOutlined, FilePdfOutlined, FileWordOutlined,
  CodeOutlined, FileOutlined
} from '@ant-design/icons';

// 获取文件图标
export const getFileIcon = (extension: string): React.ReactNode => {
  switch (extension) {
    case 'md':
      return <FileMarkdownOutlined />;
    case 'jpg':
    case 'jpeg':
    case 'png':
    case 'gif':
    case 'svg':
      return <FileImageOutlined />;
    case 'zip':
    case 'rar':
    case 'tar':
    case 'gz':
      return <FileZipOutlined />;
    case 'xls':
    case 'xlsx':
    case 'csv':
      return <FileExcelOutlined />;
    case 'pdf':
      return <FilePdfOutlined />;
    case 'doc':
    case 'docx':
      return <FileWordOutlined />;
    case 'js':
    case 'jsx':
    case 'ts':
    case 'tsx':
    case 'html':
    case 'css':
    case 'py':
    case 'java':
    case 'c':
    case 'cpp':
    case 'php':
    case 'rb':
    case 'go':
    case 'rs':
      return <CodeOutlined />;
    default:
      return <FileOutlined />;
  }
};

// 格式化文件大小
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}; 