import React, { useEffect, useState } from 'react';
import { 
  Row, Col, Card, List, Empty, Button, Spin, 
  Breadcrumb, Divider 
} from 'antd';
import { 
  HomeOutlined, FolderOutlined, UploadOutlined, 
  GithubOutlined, FileOutlined, FileMarkdownOutlined, FileImageOutlined, 
  FileZipOutlined, FileExcelOutlined, FilePdfOutlined, FileWordOutlined, CodeOutlined
} from '@ant-design/icons';
import { useProjectStore } from '../../stores/projectStore';
import FileViewer from './FileViewer';
import { ProjectFile } from '../../types';

// 引入文件大小格式化函数
import { formatFileSize } from '../../utils/fileUtils-ts';

// 获取文件图标的函数
const getFileIcon = (extension: string): JSX.Element => {
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

interface ProjectFileBrowserProps {
  projectId: number;
  onOpenGitModal: () => void;
  onOpenUploadModal: () => void;
}

const ProjectFileBrowser: React.FC<ProjectFileBrowserProps> = ({ 
  projectId, 
  onOpenGitModal,
  onOpenUploadModal
}) => {
  const { 
    projectFiles, currentFileContent,
    fetchProjectFiles, fetchFileContent
  } = useProjectStore();
  
  const [isLoading, setIsLoading] = useState(false);
  const [currentPath, setCurrentPath] = useState('');
  const [selectedFile, setSelectedFile] = useState<string | null>(null);

  // 初始加载文件列表
  useEffect(() => {
    fetchFileList();
  }, [projectId]);

  // 处理文件夹导航
  const handleNavigateFolder = (path: string) => {
    console.log(`导航到文件夹: ${path}`);
    setCurrentPath(path);
    setSelectedFile(null);
    fetchProjectFiles(projectId, path)
      .then(data => {
        console.log('获取文件列表成功:', data);
      })
      .catch(error => {
        console.error('获取文件列表失败:', error);
      });
  };
  
  // 处理打开文件
  const handleOpenFile = (path: string) => {
    console.log(`打开文件: ${path}`);
    setSelectedFile(path);
    fetchFileContent(projectId, path)
      .then(data => {
        console.log('获取文件内容成功:', data);
      })
      .catch(error => {
        console.error('获取文件内容失败:', error);
      });
  };
  
  // 处理返回上级目录
  const handleGoBack = () => {
    if (!currentPath) return;
    
    const pathParts = currentPath.split('/');
    pathParts.pop();
    const parentPath = pathParts.join('/');
    handleNavigateFolder(parentPath);
  };

  // 更新fetchProjectFiles函数
  const fetchFileList = async () => {
    setIsLoading(true);
    try {
      console.log('获取项目文件列表', projectId, currentPath);
      await fetchProjectFiles(projectId, currentPath);
    } catch (error) {
      console.error('获取项目文件列表失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <Spin tip="加载中..." />;
  }

  if (!projectFiles) {
    return (
      <Empty 
        description="无法加载文件列表" 
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      />
    );
  }

  // 检查目录是否为空
  if (projectFiles.is_empty || 
      (projectFiles.directories.length === 0 && projectFiles.files.length === 0)) {
    return (
      <Empty 
        description={
          <div>
            <p>项目目录为空</p>
            <p>请上传文件或从Git仓库克隆</p>
            <div style={{ marginTop: '20px' }}>
              <Button 
                type="primary" 
                icon={<UploadOutlined />}
                onClick={onOpenUploadModal}
                style={{ marginRight: '10px' }}
              >
                上传文件
              </Button>
              <Button 
                icon={<GithubOutlined />}
                onClick={onOpenGitModal}
              >
                从Git克隆
              </Button>
            </div>
          </div>
        }
      />
    );
  }

  return (
    <div>
      {/* 导航区域 */}
      <div style={{ marginBottom: '16px' }}>
        <Breadcrumb>
          <Breadcrumb.Item>
            <a onClick={() => handleNavigateFolder("")}>
              <HomeOutlined /> 根目录
            </a>
          </Breadcrumb.Item>
          {currentPath.split('/').filter(Boolean).map((segment, index, array) => {
            const path = array.slice(0, index + 1).join('/');
            return (
              <Breadcrumb.Item key={path}>
                <a onClick={() => handleNavigateFolder(path)}>{segment}</a>
              </Breadcrumb.Item>
            );
          })}
        </Breadcrumb>
      </div>

      <Row gutter={16}>
        {/* 文件列表区域 */}
        <Col span={selectedFile ? 12 : 24}>
          {/* 目录列表 */}
          {projectFiles.directories.length > 0 && (
            <div>
              <Divider orientation="left">目录</Divider>
              <List
                grid={{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 3, xl: 4, xxl: 4 }}
                dataSource={projectFiles.directories}
                renderItem={(directory: ProjectFile) => (
                  <List.Item>
                    <Card
                      hoverable
                      size="small"
                      onClick={() => handleNavigateFolder(directory.path)}
                    >
                      <Card.Meta
                        avatar={<FolderOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
                        title={directory.name}
                      />
                    </Card>
                  </List.Item>
                )}
              />
            </div>
          )}

          {/* 文件列表 */}
          <div>
            <Divider orientation="left">文件</Divider>
            <List
              grid={{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 3, xl: 4, xxl: 4 }}
              dataSource={projectFiles.files}
              renderItem={(file: ProjectFile) => (
                <List.Item>
                  <Card
                    hoverable
                    size="small"
                    onClick={() => handleOpenFile(file.path)}
                    style={selectedFile === file.path ? { borderColor: '#1890ff', boxShadow: '0 0 0 2px rgba(24,144,255,0.2)' } : {}}
                  >
                    <Card.Meta
                      avatar={getFileIcon(file.extension || '')}
                      title={file.name}
                      description={
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span>{file.extension ? `.${file.extension}` : ''}</span>
                          <span>{formatFileSize(file.size)}</span>
                        </div>
                      }
                    />
                  </Card>
                </List.Item>
              )}
            />
          </div>
        </Col>
        
        {/* 文件内容区域 */}
        {selectedFile && (
          <Col span={12}>
            <FileViewer
              fileContent={currentFileContent}
              onClose={() => setSelectedFile(null)}
              projectId={projectId}
            />
          </Col>
        )}
      </Row>
    </div>
  );
};

export default ProjectFileBrowser; 