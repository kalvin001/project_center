import React, { useEffect, useState } from 'react'
import { 
  Card, Typography, Button, Descriptions, Tag, Tabs, 
  Upload, message, Spin, Form, Input, Select, Space, Table, Modal, 
  List, Breadcrumb, Divider, Tooltip, Row, Col, Radio, Empty, Progress,
  Statistic
} from 'antd'
import { 
  UploadOutlined, DownloadOutlined, EditOutlined,
  DeleteOutlined, CloudUploadOutlined, RollbackOutlined,
  FolderOutlined, FileOutlined, GithubOutlined, 
  FileTextOutlined, FileMarkdownOutlined, FileImageOutlined,
  FileZipOutlined, FileExcelOutlined, FilePdfOutlined,
  FileWordOutlined, CodeOutlined, ArrowLeftOutlined,
  FolderOpenOutlined, HomeOutlined, InboxOutlined,
  SyncOutlined, FileExclamationOutlined, CloseOutlined
} from '@ant-design/icons'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import type { UploadFile, UploadProps } from 'antd/es/upload/interface'
import { useProjectStore } from '../stores/projectStore'
import { ProjectFileList, ProjectFile, FileContent } from '../types'
import { Link } from 'react-router-dom'

const { Title, Paragraph, Text } = Typography
const { TabPane } = Tabs
const { Item: FormItem } = Form
const { Option } = Select

interface DeploymentFormValues {
  environment: string
  server_host: string
  server_port: number | null
  deploy_path: string
}

// 获取文件图标
const getFileIcon = (extension: string) => {
  switch (extension) {
    case 'md':
      return <FileMarkdownOutlined />
    case 'jpg':
    case 'jpeg':
    case 'png':
    case 'gif':
    case 'svg':
      return <FileImageOutlined />
    case 'zip':
    case 'rar':
    case 'tar':
    case 'gz':
      return <FileZipOutlined />
    case 'xls':
    case 'xlsx':
    case 'csv':
      return <FileExcelOutlined />
    case 'pdf':
      return <FilePdfOutlined />
    case 'doc':
    case 'docx':
      return <FileWordOutlined />
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
      return <CodeOutlined />
    default:
      return <FileOutlined />
  }
}

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const ProjectDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const projectId = parseInt(id || '0')
  
  const { 
    currentProject, loading: storeLoading, 
    fetchProject, updateProject, deleteProject, 
    uploadProject, downloadProject, createDeployment,
    projectFiles, currentFileContent,
    fetchProjectFiles, fetchFileContent, cloneFromGit,
    syncProject, syncProgress
  } = useProjectStore()
  
  const [isEditing, setIsEditing] = useState(location.state?.edit || false)
  const [form] = Form.useForm()
  const [deployForm] = Form.useForm()
  const [isDeployModalOpen, setIsDeployModalOpen] = useState(false)
  const [isGitModalOpen, setIsGitModalOpen] = useState(false)
  const [gitForm] = Form.useForm()
  const [uploadFileList, setUploadFileList] = useState<UploadFile[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('info')
  const [currentPath, setCurrentPath] = useState('')
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadMode, setUploadMode] = useState<'replace' | 'increment'>('replace')
  const [gitUrl, setGitUrl] = useState('')
  const [gitBranch, setGitBranch] = useState('')
  const [gitCloning, setGitCloning] = useState(false)
  const [uploadVisible, setUploadVisible] = useState(false)
  const [gitVisible, setGitVisible] = useState(false)
  const [isIgnoreModalOpen, setIsIgnoreModalOpen] = useState(false)
  const [ignoreContent, setIgnoreContent] = useState('')
  
  // 添加调试日志
  useEffect(() => {
    console.log('项目详情页渲染状态:', {
      projectId,
      currentProject,
      loading: storeLoading,
      activeTab
    });
  }, [projectId, currentProject, storeLoading, activeTab]);
  
  useEffect(() => {
    if (projectId) {
      fetchProject(projectId)
      if (activeTab === 'files') {
        fetchProjectFiles(projectId, currentPath)
      }
    }
  }, [projectId, fetchProject, activeTab])
  
  useEffect(() => {
    if (currentProject && isEditing) {
      form.setFieldsValue({
        name: currentProject.name,
        description: currentProject.description,
        project_type: currentProject.project_type,
        repository_url: currentProject.repository_url,
        is_active: currentProject.is_active,
      })
    }
  }, [currentProject, form, isEditing])
  
  // 将useEffect从条件语句移到组件顶层
  useEffect(() => {
    // 只有当有选中的文件，且文件是代码文件时才高亮
    if (currentFileContent && selectedFile) {
      const { extension, content } = currentFileContent;
      const isCodeFile = [
        'js', 'jsx', 'ts', 'tsx', 'html', 'css', 'scss', 'less',
        'py', 'java', 'c', 'cpp', 'cs', 'go', 'php', 'rb', 'rs',
        'swift', 'kt', 'json', 'xml', 'yaml', 'yml', 'sql',
        'sh', 'bat', 'ps1', 'ini', 'conf', 'cfg', 'config',
        'md', 'txt'
      ].includes(extension);
      
      if (isCodeFile && window.Prism) {
        // 这里添加一个延迟，确保DOM已更新
        setTimeout(() => {
          window.Prism.highlightAll();
        }, 0);
      }
    }
  }, [currentFileContent, selectedFile]);
  
  // 渲染.ignore文件编辑模态框
  const renderIgnoreModal = () => {
    if (!currentProject) return null;
    
    return (
      <Modal
        title={currentProject.stats?.ignore_file_exists ? "编辑.ignore文件" : "创建.ignore文件"}
        open={isIgnoreModalOpen}
        onCancel={() => setIsIgnoreModalOpen(false)}
        width={700}
        footer={[
          <Button key="cancel" onClick={() => setIsIgnoreModalOpen(false)}>
            取消
          </Button>,
          <Button 
            key="submit" 
            type="primary" 
            onClick={() => {
              // 保存.ignore文件
              useProjectStore.getState().createIgnoreFile(projectId, ignoreContent)
                .then(() => {
                  setIsIgnoreModalOpen(false);
                  // 刷新项目以获取最新统计
                  fetchProject(projectId);
                })
                .catch(error => {
                  message.error('保存.ignore文件失败');
                });
            }}
          >
            保存
          </Button>
        ]}
      >
        <div style={{ marginBottom: 16 }}>
          <Text>
            指定要在项目同步和上传时忽略的文件和目录。每行一个模式。
          </Text>
        </div>
        <Input.TextArea
          value={ignoreContent}
          onChange={(e) => setIgnoreContent(e.target.value)}
          style={{ height: 300, fontFamily: 'monospace' }}
          placeholder="# 输入要忽略的文件或目录模式，每行一个"
        />
      </Modal>
    );
  };
  
  if (storeLoading && !currentProject) {
    return (
      <div style={{ textAlign: 'center', margin: '50px 0' }}>
        <Spin size="large" />
      </div>
    )
  }
  
  if (!currentProject) {
    return (
      <Card>
        <Title level={4}>项目不存在或已被删除</Title>
        <Button type="primary" onClick={() => navigate('/projects')}>
          返回项目列表
        </Button>
      </Card>
    )
  }
  
  // 处理项目更新
  const handleUpdateProject = async (values: any) => {
    try {
      await updateProject(projectId, values)
      setIsEditing(false)
      message.success('项目更新成功')
    } catch (error) {
      message.error('更新项目失败')
    }
  }
  
  // 处理项目删除
  const handleDeleteProject = async () => {
    try {
      await deleteProject(projectId)
      message.success('项目删除成功')
      navigate('/projects')
    } catch (error) {
      message.error('删除项目失败')
    }
  }
  
  // 处理项目同步
  const handleSyncProject = async () => {
    try {
      await syncProject(projectId);
      // 同步完成后的处理已经移到store中
      
      // 如果当前在文件浏览标签页，刷新文件列表
      if (activeTab === 'files') {
        fetchProjectFiles(projectId, currentPath);
      }
    } catch (error) {
      // 错误处理已经移到store中
      console.error('同步失败:', error);
    }
  }
  
  // 处理文件上传
  const handleUpload = async () => {
    if (!uploadFile) {
      message.error('请选择要上传的文件')
      return
    }

    if (!uploadFile.name.endsWith('.zip')) {
      message.error('只支持上传ZIP格式的文件')
      return
    }

    setIsLoading(true)
    try {
      console.log('开始上传文件:', uploadFile.name)
      await uploadProject(projectId, uploadFile, uploadMode)
      message.success('文件上传成功')
      // 重新加载文件列表
      fetchProjectFiles(projectId, currentPath)
      setUploadFile(null)
    } catch (error: any) {
      console.error('文件上传失败:', error)
      message.error(error?.response?.data?.detail || '文件上传失败，请检查文件格式或权限')
    } finally {
      setIsLoading(false)
      setUploadFile(null)
    }
  }
  
  // 处理文件下载
  const handleDownload = async () => {
    try {
      await downloadProject(projectId)
    } catch (error) {
      message.error('下载项目文件失败')
    }
  }
  
  // 上传配置
  const uploadProps: UploadProps = {
    onRemove: file => {
      setUploadFileList([])
    },
    beforeUpload: file => {
      if (!file.name.endsWith('.zip')) {
        message.error('只支持上传 ZIP 格式的文件')
        return Upload.LIST_IGNORE
      }
      
      setUploadFileList([file])
      return false
    },
    fileList: uploadFileList,
    accept: '.zip',
    maxCount: 1,
  }
  
  // 处理部署创建
  const handleCreateDeployment = async (values: DeploymentFormValues) => {
    try {
      await createDeployment(projectId, values)
      setIsDeployModalOpen(false)
      deployForm.resetFields()
    } catch (error) {
      message.error('创建部署任务失败')
    }
  }
  
  // 渲染部署列表
  const deploymentColumns = [
    {
      title: '环境',
      dataIndex: 'environment',
      key: 'environment',
      render: (env: string) => (
        <Tag color={
          env === 'production' ? 'red' : 
          env === 'staging' ? 'orange' : 
          'green'
        }>
          {env}
        </Tag>
      ),
    },
    {
      title: '服务器',
      dataIndex: 'server_host',
      key: 'server_host',
      render: (host: string, record: any) => (
        <span>{host}{record.server_port ? `:${record.server_port}` : ''}</span>
      ),
    },
    {
      title: '部署路径',
      dataIndex: 'deploy_path',
      key: 'deploy_path',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={
          status === 'success' ? 'success' : 
          status === 'pending' ? 'warning' : 
          status === 'deploying' ? 'processing' :
          'error'
        }>
          {status}
        </Tag>
      ),
    },
    {
      title: '部署时间',
      dataIndex: 'deployed_at',
      key: 'deployed_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
  ]
  
  const handleTabChange = (key: string) => {
    setActiveTab(key)
    if (key === 'files' && projectId) {
      fetchProjectFiles(projectId, currentPath)
    }
  }
  
  // 处理文件夹导航
  const handleNavigateFolder = (path: string) => {
    console.log(`导航到文件夹: ${path}`)
    setCurrentPath(path)
    setSelectedFile(null)
    fetchProjectFiles(projectId, path)
      .then(data => {
        console.log('获取文件列表成功:', data)
      })
      .catch(error => {
        console.error('获取文件列表失败:', error)
      })
  }
  
  // 处理打开文件
  const handleOpenFile = (path: string) => {
    console.log(`打开文件: ${path}`)
    setSelectedFile(path)
    fetchFileContent(projectId, path)
      .then(data => {
        console.log('获取文件内容成功:', data)
      })
      .catch(error => {
        console.error('获取文件内容失败:', error)
      })
  }
  
  // 处理返回上级目录
  const handleGoBack = () => {
    if (!currentPath) return
    
    const pathParts = currentPath.split('/')
    pathParts.pop()
    const parentPath = pathParts.join('/')
    handleNavigateFolder(parentPath)
  }
  
  // 渲染面包屑导航
  const renderBreadcrumb = () => {
    const paths = currentPath ? ['', ...currentPath.split('/')] : ['']
    const items = paths.map((path, index) => {
      const pathTo = paths.slice(1, index + 1).join('/')
      return {
        title: index === 0 ? (
          <a onClick={() => handleNavigateFolder('')}><FolderOutlined /> 根目录</a>
        ) : (
          <a onClick={() => handleNavigateFolder(pathTo)}>{path || '/'}</a>
        ),
        key: index
      }
    })
    
    return <Breadcrumb items={items} />
  }
  
  // 从Git克隆
  const handleCloneFromGit = async (values: { repository_url: string, branch?: string }) => {
    if (!values.repository_url) {
      message.error('请输入Git仓库地址')
      return
    }

    setGitCloning(true)
    try {
      console.log('开始克隆Git仓库:', values.repository_url)
      
      await cloneFromGit(projectId, values.repository_url, values.branch)
      setIsGitModalOpen(false)
      gitForm.resetFields()
      setActiveTab('files')
      message.success('Git仓库克隆成功')
    } catch (error: any) {
      console.error('Git克隆失败:', error)
      message.error(error?.response?.data?.detail || 'Git仓库克隆失败，请检查仓库地址和权限')
    } finally {
      setGitCloning(false)
      setGitUrl('')
      setGitBranch('')
    }
  }
  
  // 更新fetchProjectFiles函数
  const fetchFileList = async () => {
    setIsLoading(true)
    try {
      console.log('获取项目文件列表', projectId, currentPath)
      await fetchProjectFiles(projectId, currentPath)
      console.log('文件列表结果:', projectFiles)
    } catch (error) {
      console.error('获取项目文件列表失败:', error)
      message.error('获取项目文件列表失败')
    } finally {
      setIsLoading(false)
    }
  }
  
  // 添加渲染文件内容的函数
  const renderFileContent = () => {
    if (!currentFileContent) {
      return (
        <Empty description="选择一个文件以查看内容" />
      );
    }

    // 针对特殊文件类型处理
    const renderSpecialContent = () => {
      const { extension, content, is_binary, name, path } = currentFileContent;
      
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
        // 这里需要一个图片预览功能
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
                  onClick={() => setSelectedFile(null)}
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
                onClick={() => setSelectedFile(null)}
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
    
    return renderSpecialContent();
  }

  // 添加新的下载文件函数
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
  }

  // 修改渲染文件浏览器组件，添加文件内容显示
  const renderFileBrowser = () => {
    if (isLoading || storeLoading) {
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
                  onClick={() => setUploadVisible(true)}
                  style={{ marginRight: '10px' }}
                >
                  上传文件
                </Button>
                <Button 
                  icon={<GithubOutlined />}
                  onClick={() => setGitVisible(true)}
                >
                  从Git克隆
                </Button>
              </div>
            </div>
          }
        />
      );
    }

    // 渲染文件列表和文件内容（两栏布局）
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
                  renderItem={directory => (
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
                renderItem={file => (
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
              {renderFileContent()}
            </Col>
          )}
        </Row>
      </div>
    );
  }
  
  // Git仓库克隆模态框
  const renderGitModal = () => {
    return (
      <Modal
        title="从Git仓库克隆"
        open={gitVisible}
        footer={null}
        onCancel={() => setGitVisible(false)}
      >
        <Form
          layout="vertical"
          onFinish={(values) => {
            setGitCloning(true);
            cloneFromGit(projectId, values.repository_url, values.branch)
              .then(() => {
                setGitVisible(false);
                message.success('Git仓库克隆成功');
                fetchProjectFiles(projectId, currentPath);
              })
              .catch((error) => {
                message.error('Git仓库克隆失败: ' + (error.response?.data?.detail || error.message));
              })
              .finally(() => {
                setGitCloning(false);
              });
          }}
        >
          <FormItem
            name="repository_url"
            label="Git仓库地址"
            rules={[{ required: true, message: '请输入Git仓库地址' }]}
          >
            <Input placeholder="例如: https://github.com/user/repo.git" />
          </FormItem>
          
          <FormItem
            name="branch"
            label="分支 (可选)"
          >
            <Input placeholder="默认: main" />
          </FormItem>
          
          <FormItem
            name="mode"
            label="克隆模式"
            initialValue="replace"
          >
            <Radio.Group>
              <Radio value="replace">替换所有文件（将删除项目中现有的所有文件）</Radio>
              <Radio value="increment">增量更新（保留项目中现有的文件）</Radio>
            </Radio.Group>
          </FormItem>
          
          <FormItem>
            <Space>
              <Button type="primary" htmlType="submit" loading={gitCloning}>
                开始克隆
              </Button>
              <Button onClick={() => setGitVisible(false)}>
                取消
              </Button>
            </Space>
          </FormItem>
        </Form>
      </Modal>
    );
  };
  
  // 添加文件上传对话框渲染函数
  const renderUploadModal = () => {
    return (
      <Modal
        title="上传项目文件"
        open={uploadVisible}
        footer={null}
        onCancel={() => setUploadVisible(false)}
      >
        <div style={{ marginBottom: '16px' }}>
          <Upload.Dragger
            beforeUpload={(file) => {
              if (!file.name.endsWith('.zip')) {
                message.error('只支持上传 ZIP 格式的文件');
                return Upload.LIST_IGNORE;
              }
              setUploadFile(file);
              return false;
            }}
            onRemove={() => setUploadFile(null)}
            fileList={uploadFile ? [{
              uid: '-1',
              name: uploadFile.name,
              status: 'done',
              size: uploadFile.size,
              type: uploadFile.type,
              originFileObj: uploadFile,
            } as UploadFile] : []}
            accept=".zip"
            maxCount={1}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">只支持 ZIP 格式的文件</p>
          </Upload.Dragger>
        </div>
        
        <div style={{ marginBottom: '16px' }}>
          <Radio.Group 
            value={uploadMode} 
            onChange={(e) => setUploadMode(e.target.value)}
          >
            <Radio value="replace">替换所有文件（将删除项目中现有的所有文件）</Radio>
            <Radio value="increment">增量更新（保留项目中现有的文件）</Radio>
          </Radio.Group>
        </div>
        
        <div style={{ textAlign: 'right' }}>
          <Space>
            <Button 
              type="primary" 
              onClick={handleUpload} 
              disabled={!uploadFile}
              loading={isLoading}
            >
              上传文件
            </Button>
            <Button onClick={() => setUploadVisible(false)}>
              取消
            </Button>
          </Space>
        </div>
      </Modal>
    );
  };
  
  // 渲染同步进度组件
  const renderSyncProgress = () => {
    if (syncProgress.status === '') {
      return null;
    }
    
    // 确定进度条状态
    let status = 'normal';
    if (syncProgress.status === 'complete') {
      status = 'success';
    } else if (syncProgress.status === 'error') {
      status = 'exception';
    }
    
    return (
      <div style={{ marginTop: 16, marginBottom: 16 }}>
        <Card>
          <div style={{ marginBottom: 16 }}>
            <Text strong>同步进度: </Text>
            <Text type={syncProgress.status === 'error' ? 'danger' : undefined}>
              {syncProgress.message}
            </Text>
          </div>
          <Progress 
            percent={syncProgress.progress} 
            status={status as any}
            strokeColor={{
              from: '#108ee9',
              to: '#87d068',
            }}
          />
        </Card>
      </div>
    );
  };
  
  // 编辑模式
  if (isEditing) {
    return (
      <Card 
        title="编辑项目" 
        extra={
          <Button icon={<RollbackOutlined />} onClick={() => setIsEditing(false)}>
            取消编辑
          </Button>
        }
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleUpdateProject}
          initialValues={{
            name: currentProject.name,
            description: currentProject.description,
            project_type: currentProject.project_type,
            repository_url: currentProject.repository_url,
            is_active: currentProject.is_active,
          }}
        >
          <FormItem
            name="name"
            label="项目名称"
            rules={[{ required: true, message: '请输入项目名称' }]}
          >
            <Input />
          </FormItem>
          
          <FormItem
            name="description"
            label="项目描述"
          >
            <Input.TextArea rows={4} />
          </FormItem>
          
          <FormItem
            name="project_type"
            label="项目类型"
            rules={[{ required: true, message: '请选择项目类型' }]}
          >
            <Select>
              <Option value="frontend">前端</Option>
              <Option value="backend">后端</Option>
              <Option value="fullstack">全栈</Option>
              <Option value="mobile">移动端</Option>
              <Option value="other">其他</Option>
            </Select>
          </FormItem>
          
          <FormItem
            name="repository_url"
            label="代码仓库"
          >
            <Input placeholder="如: https://github.com/username/repo" />
          </FormItem>
          
          <FormItem
            name="is_active"
            label="项目状态"
            valuePropName="checked"
          >
            <Select>
              <Option value={true}>活跃</Option>
              <Option value={false}>非活跃</Option>
            </Select>
          </FormItem>
          
          <FormItem>
            <Space>
              <Button type="primary" htmlType="submit">
                保存
              </Button>
              <Button onClick={() => setIsEditing(false)}>
                取消
              </Button>
            </Space>
          </FormItem>
        </Form>
      </Card>
    )
  }
  
  // 移除这里的提前返回，改为渲染不同的内容
  const renderInfoTab = () => {
    return (
      <div>
        <Descriptions bordered column={2}>
          <Descriptions.Item label="项目类型">
            {currentProject.project_type}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {new Date(currentProject.created_at).toLocaleString()}
          </Descriptions.Item>
          <Descriptions.Item label="最后更新">
            {new Date(currentProject.last_updated).toLocaleString()}
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={currentProject.is_active ? 'green' : 'red'}>
              {currentProject.is_active ? '活跃' : '非活跃'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="仓库URL" span={2}>
            {currentProject.repository_url || '无'}
          </Descriptions.Item>
          <Descriptions.Item label="项目描述" span={2}>
            {currentProject.description || '无描述'}
          </Descriptions.Item>
        </Descriptions>
        
        {/* 项目统计信息卡片 */}
        {currentProject.stats && (
          <Card title="项目统计" style={{ marginTop: 16 }}>
            <Row gutter={16}>
              <Col span={6}>
                <Statistic 
                  title="文件数量" 
                  value={currentProject.stats.file_count} 
                  suffix="个文件"
                />
              </Col>
              <Col span={6}>
                <Statistic 
                  title="项目大小" 
                  value={currentProject.stats.total_size_human}
                />
              </Col>
              <Col span={6}>
                <Statistic 
                  title="代码行数" 
                  value={currentProject.stats.code_lines} 
                  suffix="行"
                />
              </Col>
              <Col span={6}>
                <Button 
                  icon={<FileExclamationOutlined />}
                  onClick={() => {
                    // 尝试读取现有.ignore文件内容
                    const ignoreFileExists = currentProject.stats?.ignore_file_exists;
                    if (ignoreFileExists) {
                      // 这里可以通过API获取.ignore文件内容
                      // 简化版本：在文件浏览器中查找.ignore文件
                      fetchProjectFiles(projectId, '')
                        .then(() => {
                          const ignoreFile = projectFiles?.files.find(f => f.name === '.ignore');
                          if (ignoreFile) {
                            fetchFileContent(projectId, ignoreFile.path)
                              .then(() => {
                                if (currentFileContent) {
                                  setIgnoreContent(currentFileContent.content);
                                  setIsIgnoreModalOpen(true);
                                }
                              });
                          } else {
                            setIgnoreContent('');
                            setIsIgnoreModalOpen(true);
                          }
                        });
                    } else {
                      // 如果文件不存在，显示空编辑器
                      setIgnoreContent(`# .ignore文件
# 在此文件中指定要忽略的文件和目录模式
# 支持的格式：
# - 精确匹配: file.txt
# - 目录匹配: node_modules/
# - 扩展名匹配: *.log
# - 通配符: temp*
# 
# 常见示例:
node_modules/
.DS_Store
*.log
*.tmp
.env
.vscode/
dist/
build/
*.pyc
__pycache__/`);
                      setIsIgnoreModalOpen(true);
                    }
                  }}
                >
                  {currentProject.stats?.ignore_file_exists ? '编辑忽略文件' : '创建忽略文件'}
                </Button>
              </Col>
            </Row>
          </Card>
        )}
      </div>
    );
  };
  
  return (
    <div>
      <Breadcrumb style={{ marginBottom: 16 }}>
        <Breadcrumb.Item>
          <Link to="/projects">项目列表</Link>
        </Breadcrumb.Item>
        <Breadcrumb.Item>{currentProject.name}</Breadcrumb.Item>
      </Breadcrumb>
      
      {/* 在项目信息卡片上方显示同步进度 */}
      {renderSyncProgress()}
      
      <Card
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Space>
              <Title level={4} style={{ margin: 0 }}>{currentProject.name}</Title>
              <Tag color={
                currentProject.project_type === 'frontend' ? 'blue' : 
                currentProject.project_type === 'backend' ? 'green' : 
                currentProject.project_type === 'fullstack' ? 'purple' : 
                'default'
              }>
                {currentProject.project_type}
              </Tag>
              <Tag color={currentProject.is_active ? 'success' : 'default'}>
                {currentProject.is_active ? '活跃' : '非活跃'}
              </Tag>
            </Space>
            <Button
              type="primary"
              icon={<EditOutlined />}
              onClick={() => setIsEditing(true)}
            >
              编辑项目
            </Button>
          </div>
        }
        extra={
          <Space>
            <Button 
              icon={<SyncOutlined />} 
              onClick={handleSyncProject}
            >
              同步项目
            </Button>
            <Button 
              icon={<DownloadOutlined />} 
              onClick={handleDownload}
            >
              下载
            </Button>
            <Button 
              danger 
              icon={<DeleteOutlined />} 
              onClick={handleDeleteProject}
            >
              删除
            </Button>
          </Space>
        }
      >
        <Tabs activeKey={activeTab} onChange={handleTabChange}>
          <TabPane tab="项目信息" key="info">
            {activeTab === 'info' && renderInfoTab()}
          </TabPane>
          
          <TabPane tab="文件浏览" key="files">
            {activeTab === 'files' && renderFileBrowser()}
          </TabPane>
          
          <TabPane tab="部署管理" key="deployment">
            {activeTab === 'deployment' && (
              <>
                <div style={{ marginBottom: '16px' }}>
                  <Button type="primary" onClick={() => setIsDeployModalOpen(true)}>
                    创建部署任务
                  </Button>
                </div>
                
                <Table
                  dataSource={currentProject.deployments}
                  columns={deploymentColumns}
                  rowKey="id"
                  pagination={false}
                />
              </>
            )}
          </TabPane>
        </Tabs>
      </Card>
      
      <Modal
        title="创建部署任务"
        open={isDeployModalOpen}
        footer={null}
        onCancel={() => setIsDeployModalOpen(false)}
      >
        <Form
          form={deployForm}
          layout="vertical"
          onFinish={handleCreateDeployment}
        >
          <FormItem
            name="environment"
            label="部署环境"
            rules={[{ required: true, message: '请选择部署环境' }]}
            initialValue="development"
          >
            <Select>
              <Option value="development">开发环境</Option>
              <Option value="staging">测试环境</Option>
              <Option value="production">生产环境</Option>
            </Select>
          </FormItem>
          
          <FormItem
            name="server_host"
            label="服务器地址"
            rules={[{ required: true, message: '请输入服务器地址' }]}
          >
            <Input placeholder="如: 192.168.1.100 或 example.com" />
          </FormItem>
          
          <FormItem
            name="server_port"
            label="服务器端口"
          >
            <Input type="number" placeholder="如: 22 (可选)" />
          </FormItem>
          
          <FormItem
            name="deploy_path"
            label="部署路径"
            rules={[{ required: true, message: '请输入部署路径' }]}
          >
            <Input placeholder="如: /var/www/html/myapp" />
          </FormItem>
          
          <FormItem>
            <Space>
              <Button type="primary" htmlType="submit">
                创建部署任务
              </Button>
              <Button onClick={() => setIsDeployModalOpen(false)}>
                取消
              </Button>
            </Space>
          </FormItem>
        </Form>
      </Modal>
      
      {renderGitModal()}
      {renderUploadModal()}
      {renderIgnoreModal()}
    </div>
  )
}

export default ProjectDetailPage 