import React from 'react';
import { Table, Space, Tag, Button } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined, StopOutlined, SyncOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { Deployment } from '../types';
import { formatDate } from '../utils/dateUtils';

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

interface DeploymentTableProps {
  deployments: Deployment[];
  loading: boolean;
  onViewLogs?: (deployment: Deployment) => void;
  onRedeploy?: (deployment: Deployment) => void;
  highlightClickable?: boolean;
}

const DeploymentTable: React.FC<DeploymentTableProps> = ({ 
  deployments,
  loading,
  onViewLogs,
  onRedeploy,
  highlightClickable = true
}) => {
  const navigate = useNavigate();

  const goToDeploymentDetail = (id: number) => {
    navigate(`/deployments/${id}`);
  };

  const goToProjectDetail = (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    navigate(`/projects/${id}`);
  };

  const goToMachineDetail = (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    navigate(`/machines/${id}`);
  };

  const handleViewLogs = (deployment: Deployment, e: React.MouseEvent) => {
    e.stopPropagation();
    if (onViewLogs) {
      onViewLogs(deployment);
    }
  };

  const handleRedeploy = (deployment: Deployment, e: React.MouseEvent) => {
    e.stopPropagation();
    if (onRedeploy) {
      onRedeploy(deployment);
    }
  };

  const columns = [
    {
      title: '项目',
      dataIndex: ['project', 'name'],
      key: 'project_name',
      render: (text: string, record: Deployment) => (
        <Button 
          type="link" 
          onClick={(e) => goToProjectDetail(record.project_id, e)}
          style={{ padding: 0 }}
        >
          {text || `项目 #${record.project_id}`}
        </Button>
      )
    },
    {
      title: '机器',
      dataIndex: ['machine', 'name'],
      key: 'machine_name',
      render: (text: string, record: Deployment) => {
        if (text) {
          return (
            <Button 
              type="link" 
              onClick={(e) => goToMachineDetail(record.machine_id, e)}
              style={{ padding: 0 }}
            >
              {text} ({record.machine?.host})
            </Button>
          );
        }
        return (
          <Button 
            type="link" 
            onClick={(e) => goToMachineDetail(record.machine_id, e)}
            style={{ padding: 0 }}
          >
            机器 #{record.machine_id}
          </Button>
        );
      }
    },
    {
      title: '环境',
      dataIndex: 'environment',
      key: 'environment',
      render: (text: string) => {
        const envLabels = {
          development: '开发环境',
          staging: '测试环境',
          production: '生产环境'
        };
        return envLabels[text as keyof typeof envLabels] || text;
      }
    },
    {
      title: '部署路径',
      dataIndex: 'deploy_path',
      key: 'deploy_path'
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
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
      )
    },
    {
      title: '部署时间',
      dataIndex: 'deployed_at',
      key: 'deployed_at',
      render: (text: string) => formatDate(text, '未部署')
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: Deployment) => (
        <Space size="middle">
          <Button 
            size="small" 
            onClick={(e) => {
              e.stopPropagation();
              goToDeploymentDetail(record.id);
            }}
          >
            详情
          </Button>
          {onViewLogs && (
            <Button 
              size="small" 
              onClick={(e) => handleViewLogs(record, e)}
            >
              查看日志
            </Button>
          )}
          {onRedeploy && record.status === 'failed' && (
            <Button 
              size="small" 
              type="primary" 
              onClick={(e) => handleRedeploy(record, e)}
            >
              重新部署
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={deployments}
      rowKey="id"
      loading={loading}
      pagination={{ pageSize: 10 }}
      onRow={(record) => ({
        onClick: () => goToDeploymentDetail(record.id),
        style: highlightClickable ? { 
          cursor: 'pointer',
          transition: 'background-color 0.3s',
          ':hover': {
            backgroundColor: '#f5f5f5'
          }
        } : { cursor: 'pointer' }
      })}
    />
  );
};

export default DeploymentTable; 