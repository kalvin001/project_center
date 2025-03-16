import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  Typography, 
  Row, 
  Col, 
  Card, 
  Button, 
  Space, 
  Tag, 
  Descriptions, 
  Divider, 
  message, 
  Tabs,
  Spin,
  List,
  Timeline,
  Result,
  Breadcrumb,
  Modal,
  Tooltip,
  Progress,
  Table,
  Empty,
  Input,
  Select
} from 'antd';
import { 
  ArrowLeftOutlined, 
  CheckCircleOutlined, 
  CloseCircleOutlined, 
  ClockCircleOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  StopOutlined,
  SettingOutlined,
  CodeOutlined,
  FolderOutlined,
  EnvironmentOutlined,
  HomeOutlined,
  SyncOutlined,
  UploadOutlined,
  ExclamationCircleOutlined,
  FileOutlined,
  FolderOpenOutlined,
  FileTextOutlined,
  EyeOutlined,
  LeftOutlined,
  FileMarkdownOutlined,
  FileImageOutlined,
  FileZipOutlined
} from '@ant-design/icons';
import { deploymentApi } from '../utils/api';
import { Deployment } from '../types';
import { formatDate } from '../utils/dateUtils';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

// 状态颜色映射
const statusColors = {
  pending: 'blue',
  success: 'green',
  failed: 'red',
  not_deployed: 'default',
  running: 'green',
  stopped: 'orange',
  syncing: 'blue',
  sync_failed: 'red',
  starting: 'blue',
  start_failed: 'red',
  stopping: 'blue',
  stop_failed: 'red'
};

// 状态图标映射
const statusIcons = {
  pending: <ClockCircleOutlined />,
  success: <CheckCircleOutlined />,
  failed: <CloseCircleOutlined />,
  not_deployed: <ClockCircleOutlined />,
  running: <CheckCircleOutlined />,
  stopped: <StopOutlined />,
  syncing: <SyncOutlined spin />,
  sync_failed: <CloseCircleOutlined />,
  starting: <ClockCircleOutlined spin />,
  start_failed: <CloseCircleOutlined />,
  stopping: <ClockCircleOutlined spin />,
  stop_failed: <CloseCircleOutlined />
};

// 环境名称映射
const envLabels = {
  development: '开发环境',
  staging: '测试环境',
  production: '生产环境'
};

// 文件类型图标
const getFileIcon = (fileType: string, fileName: string) => {
  if (fileType === 'directory') return <FolderOutlined style={{ color: '#faad14' }} />;
  
  const extension = fileName.split('.').pop()?.toLowerCase();
  
  switch (fileType) {
    case 'code':
      return <FileOutlined style={{ color: '#1890ff' }} />;
    case 'image':
      return <FileImageOutlined style={{ color: '#52c41a' }} />;
    case 'plain':
    case 'text':
      return <FileTextOutlined style={{ color: '#8c8c8c' }} />;
    case 'config':
      return <FileOutlined style={{ color: '#722ed1' }} />;
    case 'archive':
      return <FileZipOutlined style={{ color: '#eb2f96' }} />;
    default:
      return <FileOutlined />;
  }
};

// 格式化文件大小
const formatFileSize = (size: number): string => {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(2)} KB`;
  if (size < 1024 * 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(2)} MB`;
  return `${(size / (1024 * 1024 * 1024)).toFixed(2)} GB`;
};

const DeploymentDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [deployment, setDeployment] = useState<Deployment | null>(null);
  const [loading, setLoading] = useState(true);
  const [deployLogs, setDeployLogs] = useState<string>('');
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [activeTab, setActiveTab] = useState('info');
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);
  const [actionInProgress, setActionInProgress] = useState(false);
  const [fileList, setFileList] = useState<any>({ directories: [], files: [] });
  const [currentPath, setCurrentPath] = useState<string>("");
  const [filePathHistory, setFilePathHistory] = useState<string[]>([]);
  const [loadingFiles, setLoadingFiles] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [fileContent, setFileContent] = useState<string>("");
  const [loadingFileContent, setLoadingFileContent] = useState<boolean>(false);

  // 获取部署详情
  const fetchDeployment = async () => {
    if (!id) return;
    
    try {
      const data = await deploymentApi.getDeployment(parseInt(id));
      setDeployment(data);
      
      // 如果状态是进行中的状态，自动刷新
      const isProgressStatus = ['pending', 'syncing', 'starting', 'stopping'].includes(data.status);
      if (isProgressStatus && !refreshInterval) {
        const interval = setInterval(() => {
          fetchDeployment();
        }, 3000);
        setRefreshInterval(interval);
      } else if (!isProgressStatus && refreshInterval) {
        clearInterval(refreshInterval);
        setRefreshInterval(null);
      }
      
    } catch (error) {
      message.error('获取部署详情失败，请稍后再试。');
    } finally {
      setLoading(false);
    }
  };

  // 获取部署日志
  const fetchDeploymentLogs = async () => {
    if (!id) return;
    
    setLoadingLogs(true);
    try {
      const data = await deploymentApi.getDeploymentLogs(parseInt(id));
      setDeployLogs(data.log || '没有可用的部署日志');
    } catch (error) {
      message.error('获取部署日志失败，请稍后再试。');
      setDeployLogs('加载日志失败');
    } finally {
      setLoadingLogs(false);
    }
  };

  // 同步项目代码
  const handleSyncProject = async () => {
    if (!id || !deployment) return;
    
    Modal.confirm({
      title: '同步项目代码',
      content: '确定要同步项目代码吗？这将从代码仓库拉取最新代码但不会重新部署或重启应用。',
      icon: <SyncOutlined />,
      okText: '确认同步',
      cancelText: '取消',
      onOk: async () => {
        try {
          setActionInProgress(true);
          await deploymentApi.syncProject(parseInt(id));
          message.success('同步项目请求已提交，系统正在处理同步请求。');
          fetchDeployment();
        } catch (error: any) {
          console.error('同步项目错误：', error);
          
          if (error.response?.status === 400) {
            message.error('同步失败：' + (error.response.data.detail || '缺少部署路径或其他参数'));
          } else {
            message.error('同步项目代码时发生错误，请稍后再试。');
          }
        } finally {
          setActionInProgress(false);
        }
      }
    });
  };

  // 重新部署
  const handleRedeploy = async () => {
    if (!id) return;
    
    Modal.confirm({
      title: '重新部署项目',
      content: '确定要重新部署项目吗？这将从代码仓库拉取最新代码并重新部署。',
      icon: <UploadOutlined />,
      okText: '确认部署',
      cancelText: '取消',
      onOk: async () => {
        try {
          setActionInProgress(true);
          await deploymentApi.redeployProject(parseInt(id));
          message.success('重新部署请求已提交，系统正在处理您的重新部署请求。');
          
          // 延迟一下再刷新，给后端一些处理时间
          setTimeout(() => {
            fetchDeployment();
          }, 1000);
        } catch (error: any) {
          console.error('重新部署错误：', error);
          
          if (error.response?.status === 400) {
            // 如果是400错误，可能是缺少部署路径，询问用户是否要设置默认路径
            Modal.confirm({
              title: '部署路径问题',
              content: '部署需要设置部署路径。您想使用默认路径继续吗？',
              okText: '使用默认路径',
              cancelText: '取消',
              onOk: async () => {
                try {
                  // 第二次尝试，后端会设置默认路径
                  await deploymentApi.redeployProject(parseInt(id));
                  message.success('使用默认路径的重新部署请求已提交');
                  fetchDeployment();
                } catch (secondError) {
                  message.error('即使使用默认路径，重新部署仍然失败');
                }
              }
            });
          } else {
            message.error('提交重新部署请求时发生错误，请稍后再试。');
          }
        } finally {
          setActionInProgress(false);
        }
      }
    });
  };

  // 启动应用
  const handleStartApplication = async () => {
    if (!id || !deployment) return;
    
    Modal.confirm({
      title: '启动应用',
      content: '确定要启动应用吗？',
      icon: <PlayCircleOutlined />,
      okText: '确认启动',
      cancelText: '取消',
      onOk: async () => {
        try {
          setActionInProgress(true);
          await deploymentApi.startApplication(parseInt(id));
          message.success('应用启动请求已提交，系统正在处理应用启动请求。');
          fetchDeployment();
        } catch (error) {
          message.error('处理应用启动请求时发生错误，请稍后再试。');
        } finally {
          setActionInProgress(false);
        }
      }
    });
  };

  // 停止应用
  const handleStopApplication = async () => {
    if (!id || !deployment) return;
    
    Modal.confirm({
      title: '停止应用',
      content: '确定要停止应用吗？',
      icon: <StopOutlined />,
      okText: '确认停止',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          setActionInProgress(true);
          await deploymentApi.stopApplication(parseInt(id));
          message.success('应用停止请求已提交，系统正在处理应用停止请求。');
          fetchDeployment();
        } catch (error) {
          message.error('处理应用停止请求时发生错误，请稍后再试。');
        } finally {
          setActionInProgress(false);
        }
      }
    });
  };

  // 删除部署
  const handleDeleteDeployment = async () => {
    if (!id) return;
    
    Modal.confirm({
      title: '删除部署',
      content: '确定要删除此部署记录吗？此操作不可撤销，但不会删除已部署的代码。',
      icon: <ExclamationCircleOutlined />,
      okText: '确认删除',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          await deploymentApi.deleteDeployment(parseInt(id));
          message.success('部署记录已成功删除。');
          navigate('/deployment');
        } catch (error) {
          message.error('删除部署记录时发生错误，请稍后再试。');
        }
      }
    });
  };

  // 获取部署文件列表
  const fetchDeploymentFiles = async (path: string = "") => {
    if (!deployment?.id) return;
    
    setLoadingFiles(true);
    try {
      const filesData = await deploymentApi.getDeploymentFiles(parseInt(id!), path);
      setFileList(filesData);
      setCurrentPath(path);
    } catch (error: any) {
      console.error('获取文件列表失败:', error);
      message.error('获取文件列表失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoadingFiles(false);
    }
  };
  
  // 获取文件内容
  const fetchFileContent = async (filePath: string) => {
    if (!deployment?.id) return;
    
    setLoadingFileContent(true);
    try {
      const fileData = await deploymentApi.getFileContent(parseInt(id!), filePath);
      setSelectedFile(fileData);
      setFileContent(fileData.content);
    } catch (error: any) {
      console.error('获取文件内容失败:', error);
      message.error('获取文件内容失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoadingFileContent(false);
    }
  };
  
  // 处理目录导航
  const handleNavigate = (path: string) => {
    // 保存当前路径到历史
    if (currentPath) {
      setFilePathHistory([...filePathHistory, currentPath]);
    }
    
    // 导航到新路径
    fetchDeploymentFiles(path);
  };
  
  // 返回上级目录
  const handleGoBack = () => {
    // 从历史中获取上一个路径
    if (filePathHistory.length > 0) {
      const previousPath = filePathHistory[filePathHistory.length - 1];
      
      // 更新历史和当前路径
      setFilePathHistory(filePathHistory.slice(0, -1));
      fetchDeploymentFiles(previousPath);
    } else {
      // 如果没有历史，回到根目录
      fetchDeploymentFiles("");
    }
  };

  // 初始加载
  useEffect(() => {
    fetchDeployment();
    
    // 清理函数
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [id]);

  // 当切换到日志选项卡时，加载日志
  useEffect(() => {
    if (activeTab === 'logs') {
      fetchDeploymentLogs();
    }
  }, [activeTab]);

  // 初始化时加载文件列表
  useEffect(() => {
    if (deployment?.id && activeTab === 'files') {
      fetchDeploymentFiles();
    }
  }, [deployment?.id, activeTab]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px 0' }}>
        <Spin size="large" />
        <p>加载部署详情...</p>
      </div>
    );
  }

  if (!deployment) {
    return (
      <Result
        status="404"
        title="找不到部署"
        subTitle="抱歉，您要查看的部署不存在或已被删除。"
        extra={
          <Button type="primary" onClick={() => navigate('/deployment')}>
            返回部署列表
          </Button>
        }
      />
    );
  }

  // 渲染部署状态标签
  const renderStatusTag = (status: string) => (
    <Tag color={statusColors[status as keyof typeof statusColors] || 'default'}>
      {statusIcons[status as keyof typeof statusIcons]} 
      {status === 'pending' ? '部署中' : 
       status === 'success' ? '部署成功' : 
       status === 'failed' ? '部署失败' :
       status === 'not_deployed' ? '未部署' :
       status === 'running' ? '运行中' :
       status === 'stopped' ? '已停止' :
       status === 'syncing' ? '同步中' :
       status === 'sync_failed' ? '同步失败' :
       status === 'starting' ? '启动中' :
       status === 'start_failed' ? '启动失败' :
       status === 'stopping' ? '停止中' :
       status === 'stop_failed' ? '停止失败' : 
       status}
    </Tag>
  );

  // 渲染部署进度指示器
  const renderProgressIndicator = () => {
    const progressStatuses = {
      pending: '部署中',
      syncing: '同步中',
      starting: '启动中',
      stopping: '停止中'
    };
    
    if (Object.keys(progressStatuses).includes(deployment.status)) {
      return (
        <Card style={{ marginBottom: 16 }}>
          <Row gutter={16} align="middle">
            <Col span={18}>
              <Progress 
                status="active" 
                percent={75} 
                strokeColor={{ 
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
              />
            </Col>
            <Col span={6}>
              <Text>正在{progressStatuses[deployment.status as keyof typeof progressStatuses]}，请稍候...</Text>
            </Col>
          </Row>
        </Card>
      );
    }
    
    return null;
  };

  return (
    <div className="deployment-detail-page">
      {/* 添加面包屑导航 */}
      <Breadcrumb style={{ marginBottom: 16 }}>
        <Breadcrumb.Item>
          <Link to="/">
            <HomeOutlined />
          </Link>
        </Breadcrumb.Item>
        <Breadcrumb.Item>
          <Link to="/deployment">项目部署</Link>
        </Breadcrumb.Item>
        <Breadcrumb.Item>部署详情</Breadcrumb.Item>
      </Breadcrumb>

      {/* 显示进度指示器（如果有） */}
      {renderProgressIndicator()}

      {/* 页面头部 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={24}>
          <Card>
            <Row justify="space-between" align="middle">
              <Col>
                <Title level={3} style={{ marginBottom: 0 }}>
                  {deployment.project?.name || `项目 #${deployment.project_id}`} 
                  <span style={{ marginLeft: 8, fontSize: '16px', fontWeight: 'normal' }}>
                    {renderStatusTag(deployment.status)}
                  </span>
                </Title>
                <Text type="secondary">
                  部署到 {deployment.machine?.name || `机器 #${deployment.machine_id}`} ({deployment.machine?.host})
                </Text>
              </Col>
              <Col>
                <Space>
                  <Tooltip title="同步项目代码">
                    <Button 
                      type="default" 
                      onClick={handleSyncProject}
                      icon={<SyncOutlined />}
                      loading={actionInProgress && deployment.status === 'syncing'}
                      disabled={(['syncing', 'pending', 'starting', 'stopping'] as Array<typeof deployment.status>).includes(deployment.status)}
                    >
                      同步代码
                    </Button>
                  </Tooltip>
                  <Tooltip title="重新部署项目">
                    <Button 
                      type="primary" 
                      onClick={handleRedeploy}
                      icon={<ReloadOutlined />}
                      loading={actionInProgress && deployment.status === 'pending'}
                      disabled={(['pending', 'syncing', 'starting', 'stopping'] as Array<typeof deployment.status>).includes(deployment.status)}
                    >
                      重新部署
                    </Button>
                  </Tooltip>
                  {(['success', 'stopped'] as Array<typeof deployment.status>).includes(deployment.status) && (
                    <Tooltip title="启动应用">
                      <Button 
                        type="primary" 
                        onClick={handleStartApplication}
                        icon={<PlayCircleOutlined />}
                        loading={actionInProgress && deployment.status === 'starting'}
                        disabled={(['pending', 'syncing', 'starting', 'stopping', 'running'] as Array<typeof deployment.status>).includes(deployment.status)}
                      >
                        启动应用
                      </Button>
                    </Tooltip>
                  )}
                  {(['success', 'running'] as Array<typeof deployment.status>).includes(deployment.status) && (
                    <Tooltip title="停止应用">
                      <Button 
                        danger 
                        onClick={handleStopApplication}
                        icon={<StopOutlined />}
                        loading={actionInProgress && deployment.status === 'stopping'}
                        disabled={(['pending', 'syncing', 'starting', 'stopping', 'stopped'] as Array<typeof deployment.status>).includes(deployment.status)}
                      >
                        停止应用
                      </Button>
                    </Tooltip>
                  )}
                  <Tooltip title="删除部署">
                    <Button 
                      danger 
                      onClick={handleDeleteDeployment}
                      disabled={(['pending', 'syncing', 'starting', 'stopping'] as Array<typeof deployment.status>).includes(deployment.status)}
                    >
                      删除
                    </Button>
                  </Tooltip>
                </Space>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* 主要内容区域 */}
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="基本信息" key="info">
          <Card>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="项目名称">
                <Link to={`/projects/${deployment.project_id}`}>
                  {deployment.project?.name || `项目 #${deployment.project_id}`}
                </Link>
              </Descriptions.Item>
              <Descriptions.Item label="部署机器">
                <Link to={`/machines/${deployment.machine_id}`}>
                  {deployment.machine?.name || `机器 #${deployment.machine_id}`} ({deployment.machine?.host})
                </Link>
              </Descriptions.Item>
              <Descriptions.Item label="部署环境">
                <Tag icon={<EnvironmentOutlined />}>
                  {envLabels[deployment.environment as keyof typeof envLabels] || deployment.environment}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="部署路径">
                <Tag icon={<FolderOutlined />}>
                  {deployment.deploy_path || '未设置部署路径'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="部署状态">{renderStatusTag(deployment.status)}</Descriptions.Item>
              <Descriptions.Item label="部署时间">{formatDate(deployment.deployed_at, '未部署')}</Descriptions.Item>
              <Descriptions.Item label="部署ID" span={2}>{deployment.id}</Descriptions.Item>
            </Descriptions>
          </Card>

          {deployment.project && (
            <Card title="项目详情" style={{ marginTop: 16 }}>
              <Descriptions bordered column={2}>
                <Descriptions.Item label="项目类型">{deployment.project.project_type}</Descriptions.Item>
                <Descriptions.Item label="仓库类型">{deployment.project.repository_type}</Descriptions.Item>
                <Descriptions.Item label="仓库地址" span={2}>{deployment.project.repository_url}</Descriptions.Item>
                <Descriptions.Item label="项目描述" span={2}>{deployment.project.description || '无描述'}</Descriptions.Item>
              </Descriptions>
            </Card>
          )}

          {deployment.machine && (
            <Card title="机器详情" style={{ marginTop: 16 }}>
              <Descriptions bordered column={2}>
                <Descriptions.Item label="机器名称">{deployment.machine.name}</Descriptions.Item>
                <Descriptions.Item label="IP地址">{deployment.machine.host}</Descriptions.Item>
                <Descriptions.Item label="SSH端口">{deployment.machine.port}</Descriptions.Item>
                <Descriptions.Item label="用户名">{deployment.machine.username}</Descriptions.Item>
                <Descriptions.Item label="CPU使用率">{deployment.machine.cpu_usage || '未知'}</Descriptions.Item>
                <Descriptions.Item label="内存使用率">{deployment.machine.memory_usage || '未知'}</Descriptions.Item>
                <Descriptions.Item label="磁盘使用率">{deployment.machine.disk_usage || '未知'}</Descriptions.Item>
                <Descriptions.Item label="在线状态">
                  <Tag color={deployment.machine.is_online ? 'green' : 'red'}>
                    {deployment.machine.is_online ? '在线' : '离线'}
                  </Tag>
                </Descriptions.Item>
              </Descriptions>
            </Card>
          )}
        </TabPane>

        <TabPane tab="部署日志" key="logs">
          <Card>
            {loadingLogs ? (
              <div style={{ textAlign: 'center', padding: '20px 0' }}>
                <Spin />
                <p>加载日志中...</p>
              </div>
            ) : (
              <div className="log-container">
                <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
                  <Col>
                    <Text strong>部署日志</Text>
                  </Col>
                  <Col>
                    <Button 
                      type="primary" 
                      onClick={fetchDeploymentLogs} 
                      icon={<ReloadOutlined />}
                    >
                      刷新日志
                    </Button>
                  </Col>
                </Row>
                
                <pre style={{ 
                  backgroundColor: '#f5f5f5', 
                  padding: 16, 
                  borderRadius: 4, 
                  maxHeight: '500px', 
                  overflowY: 'auto',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all'
                }}>
                  {deployLogs}
                </pre>
              </div>
            )}
          </Card>
        </TabPane>

        <TabPane tab="操作" key="actions">
          <Card>
            <List
              itemLayout="horizontal"
              dataSource={[
                {
                  title: '同步项目代码',
                  description: '从代码仓库拉取最新代码，但不会部署或重启应用。',
                  action: handleSyncProject,
                  icon: <SyncOutlined />,
                  buttonText: '同步代码',
                  disabled: (['syncing', 'pending', 'starting', 'stopping'] as Array<typeof deployment.status>).includes(deployment.status)
                },
                {
                  title: '重新部署',
                  description: '重新执行部署流程，将项目代码重新部署到目标机器上。',
                  action: handleRedeploy,
                  icon: <ReloadOutlined />,
                  buttonText: '立即重新部署',
                  disabled: (['pending', 'syncing', 'starting', 'stopping'] as Array<typeof deployment.status>).includes(deployment.status)
                },
                {
                  title: '启动应用',
                  description: '在目标机器上启动已部署的应用。',
                  action: handleStartApplication,
                  icon: <PlayCircleOutlined />,
                  buttonText: '启动应用',
                  disabled: (['pending', 'syncing', 'starting', 'stopping', 'running'] as Array<typeof deployment.status>).includes(deployment.status)
                },
                {
                  title: '停止应用',
                  description: '停止目标机器上运行的应用。',
                  action: handleStopApplication,
                  icon: <StopOutlined />,
                  buttonText: '停止应用',
                  disabled: (['pending', 'syncing', 'starting', 'stopping', 'stopped'] as Array<typeof deployment.status>).includes(deployment.status)
                },
                {
                  title: '查看项目详情',
                  description: '查看项目的详细信息和文件结构。',
                  action: () => navigate(`/projects/${deployment.project_id}`),
                  icon: <CodeOutlined />,
                  buttonText: '前往项目详情'
                },
                {
                  title: '查看机器详情',
                  description: '查看目标机器的详细信息和状态。',
                  action: () => navigate(`/machines/${deployment.machine_id}`),
                  icon: <SettingOutlined />,
                  buttonText: '前往机器详情'
                },
                {
                  title: '删除部署',
                  description: '删除此部署记录。注意：此操作不会删除已部署的代码。',
                  action: handleDeleteDeployment,
                  icon: <CloseCircleOutlined />,
                  buttonText: '删除部署',
                  danger: true,
                  disabled: (['pending', 'syncing', 'starting', 'stopping'] as Array<typeof deployment.status>).includes(deployment.status)
                }
              ]}
              renderItem={item => (
                <List.Item
                  actions={[
                    <Button 
                      type={item.danger ? 'primary' : 'default'}
                      danger={item.danger}
                      onClick={item.action}
                      icon={item.icon}
                      disabled={item.disabled}
                    >
                      {item.buttonText}
                    </Button>
                  ]}
                >
                  <List.Item.Meta
                    title={item.title}
                    description={item.description}
                  />
                </List.Item>
              )}
            />
          </Card>
        </TabPane>

        <TabPane tab="文件列表" key="files">
          <Card>
            <Row gutter={16}>
              <Col span={24}>
                <Space style={{ marginBottom: 16 }}>
                  <Button 
                    icon={<LeftOutlined />} 
                    onClick={handleGoBack}
                    disabled={filePathHistory.length === 0 && currentPath === ""}
                  >
                    返回上级
                  </Button>
                  <Breadcrumb separator="/">
                    <Breadcrumb.Item>
                      <a onClick={() => fetchDeploymentFiles("")}>根目录</a>
                    </Breadcrumb.Item>
                    {currentPath.split('/').filter(Boolean).map((segment, index, array) => {
                      // 构建到当前段的路径
                      const pathToHere = array.slice(0, index + 1).join('/');
                      return (
                        <Breadcrumb.Item key={index}>
                          {index === array.length - 1 ? (
                            segment
                          ) : (
                            <a onClick={() => fetchDeploymentFiles(pathToHere)}>{segment}</a>
                          )}
                        </Breadcrumb.Item>
                      );
                    })}
                  </Breadcrumb>
                </Space>
              </Col>
              
              {selectedFile ? (
                // 文件内容展示
                <Col span={24}>
                  <Card 
                    title={
                      <Space>
                        {getFileIcon(selectedFile.file_type, selectedFile.file_name)}
                        <span>{selectedFile.file_name}</span>
                        <Tag color="blue">{formatFileSize(selectedFile.file_size)}</Tag>
                      </Space>
                    }
                    extra={
                      <Button onClick={() => setSelectedFile(null)}>
                        返回文件列表
                      </Button>
                    }
                  >
                    {loadingFileContent ? (
                      <div style={{ textAlign: 'center', padding: '20px' }}>
                        <Spin tip="加载文件内容..." />
                      </div>
                    ) : (
                      <div>
                        {selectedFile.file_type === 'image' ? (
                          <div style={{ textAlign: 'center' }}>
                            <img 
                              src={`data:image/${selectedFile.file_name.split('.').pop()};base64,${btoa(selectedFile.content)}`} 
                              alt={selectedFile.file_name}
                              style={{ maxWidth: '100%' }}
                            />
                          </div>
                        ) : (
                          <pre style={{ 
                            maxHeight: '500px', 
                            overflow: 'auto', 
                            padding: '16px',
                            backgroundColor: '#f5f5f5',
                            borderRadius: '4px'
                          }}>
                            {fileContent}
                          </pre>
                        )}
                      </div>
                    )}
                  </Card>
                </Col>
              ) : (
                // 文件列表展示
                <Col span={24}>
                  {loadingFiles ? (
                    <div style={{ textAlign: 'center', padding: '20px' }}>
                      <Spin tip="加载文件列表..." />
                    </div>
                  ) : (
                    <>
                      {fileList.directories.length === 0 && fileList.files.length === 0 ? (
                        <Empty description="目录为空" />
                      ) : (
                        <List
                          bordered
                          dataSource={[
                            ...fileList.directories.map((dir: any) => ({
                              ...dir,
                              isDirectory: true
                            })),
                            ...fileList.files.map((file: any) => ({
                              ...file,
                              isDirectory: false
                            }))
                          ]}
                          renderItem={(item: any) => (
                            <List.Item
                              actions={[
                                item.isDirectory ? (
                                  <Button 
                                    type="link" 
                                    onClick={() => handleNavigate(currentPath ? `${currentPath}/${item.name}` : item.name)}
                                  >
                                    打开
                                  </Button>
                                ) : (
                                  <Button 
                                    type="link" 
                                    onClick={() => fetchFileContent(currentPath ? `${currentPath}/${item.name}` : item.name)}
                                  >
                                    查看
                                  </Button>
                                )
                              ]}
                            >
                              <List.Item.Meta
                                avatar={item.isDirectory 
                                  ? <FolderOpenOutlined style={{ fontSize: '20px', color: '#faad14' }} /> 
                                  : getFileIcon('file', item.name)
                                }
                                title={item.name}
                                description={
                                  <Space>
                                    {item.isDirectory 
                                      ? '目录' 
                                      : (
                                        <>
                                          <span>文件</span>
                                          <span>{formatFileSize(item.size)}</span>
                                        </>
                                      )
                                    }
                                    {item.last_modified && (
                                      <span>
                                        {new Date(item.last_modified * 1000).toLocaleString()}
                                      </span>
                                    )}
                                  </Space>
                                }
                              />
                            </List.Item>
                          )}
                        />
                      )}
                    </>
                  )}
                </Col>
              )}
            </Row>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default DeploymentDetail; 