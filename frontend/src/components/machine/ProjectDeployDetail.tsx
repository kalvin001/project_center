import React, { useState, useEffect } from 'react';
import { 
  Card, Descriptions, Button, Space, Tabs, Tag, 
  Typography, Spin, message, Modal, Divider 
} from 'antd';
import { 
  PlayCircleOutlined, StopOutlined, SyncOutlined, 
  DeleteOutlined, CodeOutlined, RollbackOutlined 
} from '@ant-design/icons';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useStore } from '../../stores';
import { DeployedProject } from '../../types/machine';
import { formatDate } from '../../utils/dateUtils';
import LogsViewer from './LogsViewer';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

interface ProjectDeployDetailProps {
  machineId: number;
  projectId: number;
  onBack: () => void;
  onPasswordRequired: (operation: string, projectId: number) => void;
}

const ProjectDeployDetail: React.FC<ProjectDeployDetailProps> = ({
  machineId,
  projectId,
  onBack,
  onPasswordRequired
}) => {
  const navigate = useNavigate();
  const [project, setProject] = useState<DeployedProject | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const { token } = useStore();
  const [activeTab, setActiveTab] = useState<string>('info');

  const fetchProject = async () => {
    try {
      setLoading(true);
      const response = await axios.get(
        `/api/machines/${machineId}/projects/${projectId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setProject(response.data);
    } catch (error) {
      console.error('获取项目部署详情失败:', error);
      message.error('获取项目部署详情失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProject();
  }, [machineId, projectId]);

  const handleOperation = (operation: string) => {
    onPasswordRequired(operation, projectId);
  };

  const handleViewProject = () => {
    if (project) {
      navigate(`/projects/${project.project_id}`);
    }
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

  if (loading && !project) {
    return (
      <div style={{ textAlign: 'center', padding: '50px 0' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>加载项目部署详情...</div>
      </div>
    );
  }

  if (!project) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <Text type="danger">未找到项目部署信息</Text>
          <div style={{ marginTop: 16 }}>
            <Button type="primary" onClick={onBack}>
              返回列表
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button 
          type="link" 
          icon={<RollbackOutlined />} 
          onClick={onBack}
        >
          返回部署列表
        </Button>
      </div>
      
      <Title level={4}>项目部署详情: {project.project_name}</Title>
      
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="基本信息" key="info">
          <Card>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="项目ID">{project.project_id}</Descriptions.Item>
              <Descriptions.Item label="项目名称">{project.project_name}</Descriptions.Item>
              <Descriptions.Item label="部署路径">{project.deploy_path}</Descriptions.Item>
              <Descriptions.Item label="状态">{getStatusTag(project.status)}</Descriptions.Item>
              <Descriptions.Item label="版本">{project.version || '-'}</Descriptions.Item>
              <Descriptions.Item label="部署时间">{formatDate(project.deployed_at)}</Descriptions.Item>
            </Descriptions>
            
            <Divider />
            
            <div style={{ marginTop: 16 }}>
              <Space>
                <Button 
                  type="primary" 
                  onClick={handleViewProject}
                >
                  查看项目详情
                </Button>
                
                <Button 
                  icon={<SyncOutlined />} 
                  onClick={() => handleOperation('redeploy')}
                >
                  重新部署
                </Button>
                
                {project.status === 'running' ? (
                  <Button 
                    danger
                    icon={<StopOutlined />} 
                    onClick={() => handleOperation('stop_project')}
                  >
                    停止服务
                  </Button>
                ) : (
                  <Button 
                    type="primary"
                    icon={<PlayCircleOutlined />} 
                    onClick={() => handleOperation('start_project')}
                    style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
                  >
                    启动服务
                  </Button>
                )}
                
                <Button 
                  danger
                  icon={<DeleteOutlined />} 
                  onClick={() => {
                    Modal.confirm({
                      title: '确认移除部署',
                      content: '确定要移除此项目部署吗？此操作不可恢复。',
                      okText: '确认',
                      cancelText: '取消',
                      onOk: () => handleOperation('remove_deploy')
                    });
                  }}
                >
                  移除部署
                </Button>
              </Space>
            </div>
          </Card>
        </TabPane>
        
        <TabPane 
          tab={
            <span>
              <CodeOutlined />
              日志查看
            </span>
          } 
          key="logs"
        >
          <Card>
            <LogsViewer 
              machineId={machineId} 
              projectId={project.project_id}
            />
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default ProjectDeployDetail; 