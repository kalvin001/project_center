import React, { useState, useEffect } from 'react';
import { Table, Button, Tag, Space, Tooltip, Empty, Card, Typography, message } from 'antd';
import { 
  ReloadOutlined, PlayCircleOutlined, StopOutlined, 
  EyeOutlined, DeleteOutlined, SyncOutlined, CodeOutlined,
  PlusOutlined 
} from '@ant-design/icons';
import api from '../../utils/api';
import { useNavigate } from 'react-router-dom';
import { useStore } from '../../stores';
import { DeployedProject } from '../../types/machine';
import { formatDate } from '../../utils/dateUtils';
import ProjectDeployDetail from './ProjectDeployDetail';

const { Title } = Typography;

interface DeployedProjectsListProps {
  machineId: number;
  onPasswordRequired?: (operation: string, projectId: number) => void;
}

const DeployedProjectsList: React.FC<DeployedProjectsListProps> = ({ 
  machineId, 
  onPasswordRequired 
}) => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<DeployedProject[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const { token } = useStore();
  const [selectedProject, setSelectedProject] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchProjects = async () => {
    if (!machineId) return;
    
    try {
      setLoading(true);
      const response = await api.get(`/machines/${machineId}/projects`);
      setProjects(response.data || []);
      setError(null);
    } catch (error: any) {
      console.error('获取部署项目列表失败:', error);
      setError(error.response?.data?.detail || '获取部署项目列表失败');
      
      // 处理认证错误
      if (error.response?.status === 401 && onPasswordRequired) {
        onPasswordRequired('fetch', 0);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [machineId]);

  const handleOperation = (operation: string, projectId: number) => {
    if (onPasswordRequired) {
      onPasswordRequired(operation, projectId);
    }
  };

  const handleViewProject = (projectId: number) => {
    navigate(`/projects/${projectId}`);
  };

  const handleViewDeployDetail = (deployId: number) => {
    setSelectedProject(deployId);
  };

  const getStatusTag = (status: string) => {
    switch (status) {
      case 'running':
        return <Tag color="success">运行中</Tag>;
      case 'stopped':
        return <Tag color="default">已停止</Tag>;
      case 'error':
        return <Tag color="error">错误</Tag>;
      default:
        return <Tag color="processing">未知</Tag>;
    }
  };

  // 如果选择了项目，显示项目部署详情
  if (selectedProject !== null) {
    return (
      <ProjectDeployDetail 
        machineId={machineId}
        projectId={selectedProject}
        onBack={() => setSelectedProject(null)}
        onPasswordRequired={handleOperation}
      />
    );
  }

  const columns = [
    {
      title: '项目名称',
      dataIndex: 'project_name',
      key: 'project_name',
    },
    {
      title: '部署路径',
      dataIndex: 'deploy_path',
      key: 'deploy_path',
    },
    {
      title: '状态',
      key: 'status',
      render: (_: any, record: DeployedProject) => getStatusTag(record.status),
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      render: (version: string) => version || '-',
    },
    {
      title: '部署时间',
      key: 'deployed_at',
      render: (_: any, record: DeployedProject) => formatDate(record.deployed_at),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: DeployedProject) => (
        <Space size="small">
          <Tooltip title="查看项目">
            <Button 
              type="link" 
              icon={<EyeOutlined />} 
              size="small"
              onClick={() => handleViewProject(record.project_id)} 
            />
          </Tooltip>
          <Tooltip title="查看部署详情">
            <Button 
              type="link" 
              icon={<CodeOutlined />} 
              size="small"
              onClick={() => handleViewDeployDetail(record.id)} 
            />
          </Tooltip>
          <Tooltip title="重新部署">
            <Button 
              type="link" 
              icon={<SyncOutlined />} 
              size="small"
              onClick={() => handleOperation('redeploy', record.id)} 
            />
          </Tooltip>
          {record.status === 'running' ? (
            <Tooltip title="停止">
              <Button 
                type="link" 
                icon={<StopOutlined />} 
                size="small"
                onClick={() => handleOperation('stop_project', record.id)} 
              />
            </Tooltip>
          ) : (
            <Tooltip title="启动">
              <Button 
                type="link" 
                icon={<PlayCircleOutlined />} 
                size="small"
                onClick={() => handleOperation('start_project', record.id)} 
              />
            </Tooltip>
          )}
          <Tooltip title="移除部署">
            <Button 
              type="link" 
              danger
              icon={<DeleteOutlined />} 
              size="small"
              onClick={() => handleOperation('remove_deploy', record.id)} 
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4}>已部署项目</Title>
        <Space>
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={() => navigate(`/machines/${machineId}/deploy`)}
          >
            新增部署
          </Button>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={fetchProjects}
            loading={loading}
          >
            刷新
          </Button>
        </Space>
      </div>
      
      <Card>
        {projects.length > 0 ? (
          <Table 
            columns={columns} 
            dataSource={projects} 
            rowKey="id" 
            loading={loading}
            pagination={false}
          />
        ) : (
          <Empty description="该机器上暂无部署的项目" />
        )}
      </Card>
    </div>
  );
};

export default DeployedProjectsList; 