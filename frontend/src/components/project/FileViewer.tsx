import React from 'react';
import { Card, Button, Empty } from 'antd';
import { 
  CodeOutlined, FileOutlined, DownloadOutlined,
  CloseOutlined
} from '@ant-design/icons';
import { FileContent } from '../../types';

interface FileViewerProps {
  fileContent: FileContent | null;
  onClose: () => void;
  projectId: number;
}

const FileViewer: React.FC<FileViewerProps> = ({ 
  fileContent, 
  onClose,
  projectId
}) => {
  if (!fileContent) {
    return (
      <Empty description="选择一个文件以查看内容" />
    );
  }

  // 处理文件下载
  const handleDownloadFile = (filePath: string) => {
    // 构建下载URL
    const token = localStorage.getItem('token');
    const downloadUrl = `http://localhost:8011/api/projects/${projectId}/files/download?file_path=${encodeURIComponent(filePath)}&token=${token}`;
    
    // 创建一个隐藏的a标签并触发下载
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = filePath.split('/').pop() || 'download';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const { extension, content, is_binary, name, path } = fileContent;
      
  // 如果是二进制文件
  if (is_binary) {
    return (
      <div style={{ padding: '20px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
        <p style={{ textAlign: 'center' }}>
          <FileOutlined style={{ fontSize: '48px', color: '#1890ff', marginBottom: '10px' }} />
        </p>
        <p style={{ textAlign: 'center' }}>{content}</p>
        <p style={{ textAlign: 'center' }}>
          <Button 
            type="primary" 
            onClick={() => handleDownloadFile(path)}
            icon={<DownloadOutlined />}
          >
            下载文件
          </Button>
        </p>
      </div>
    );
  }
  
  // 处理各种代码文件类型
  const isCodeFile = [
    'js', 'jsx', 'ts', 'tsx', 'html', 'css', 'scss', 'less',
    'py', 'java', 'c', 'cpp', 'cs', 'go', 'php', 'rb', 'rs',
    'swift', 'kt', 'json', 'xml', 'yaml', 'yml', 'sql',
    'sh', 'bat', 'ps1', 'ini', 'conf', 'cfg', 'config',
    'md', 'txt'
  ].includes(extension);
  
  // 图片文件特殊处理
  if (['jpg', 'jpeg', 'png', 'gif', 'svg'].includes(extension)) {
    return (
      <div>
        <p>图片文件需要使用下载功能查看</p>
        <Button 
          type="primary" 
          onClick={() => handleDownloadFile(path)}
          icon={<DownloadOutlined />}
        >
          下载图片
        </Button>
      </div>
    );
  }
  
  // 获取代码语言
  const getLanguage = (ext: string): string => {
    const languageMap: Record<string, string> = {
      'js': 'javascript',
      'jsx': 'jsx',
      'ts': 'typescript',
      'tsx': 'tsx',
      'html': 'html',
      'css': 'css',
      'scss': 'scss',
      'less': 'less',
      'py': 'python',
      'java': 'java',
      'c': 'c',
      'cpp': 'cpp',
      'cs': 'csharp',
      'go': 'go',
      'php': 'php',
      'rb': 'ruby',
      'rs': 'rust',
      'swift': 'swift',
      'kt': 'kotlin',
      'json': 'json',
      'xml': 'xml',
      'yaml': 'yaml',
      'yml': 'yaml',
      'sql': 'sql',
      'sh': 'bash',
      'bat': 'batch',
      'ps1': 'powershell',
      'ini': 'ini',
      'conf': 'apache',
      'cfg': 'ini',
      'config': 'xml',
    };
    return languageMap[ext] || '';
  };
  
  // 代码文件使用PrismJS高亮
  if (isCodeFile) {
    // 确保在组件加载后运行高亮
    React.useEffect(() => {
      if (window.Prism) {
        setTimeout(() => window.Prism.highlightAll(), 0);
      }
    }, [content]);

    return (
      <Card 
        style={{ maxHeight: '600px', overflow: 'auto' }}
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>
              <CodeOutlined /> {name}
            </span>
            <Button 
              icon={<CloseOutlined />} 
              size="small" 
              onClick={onClose}
              type="text"
            />
          </div>
        }
      >
        <pre className={`language-${getLanguage(extension)}`}>
          <code className={`language-${getLanguage(extension)}`}>
            {content}
          </code>
        </pre>
      </Card>
    );
  }
  
  // 默认文本显示
  return (
    <Card 
      style={{ maxHeight: '600px', overflow: 'auto' }}
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>
            <FileOutlined /> {name}
          </span>
          <Button 
            icon={<CloseOutlined />} 
            size="small" 
            onClick={onClose}
            type="text"
          />
        </div>
      }
    >
      <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
        {content}
      </pre>
    </Card>
  );
};

export default FileViewer; 