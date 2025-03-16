import React from 'react';
import { Button, Card, Descriptions, Badge, Space, Popconfirm } from 'antd';
import { 
  SyncOutlined, DeploymentUnitOutlined, PlayCircleOutlined, 
  StopOutlined, EditOutlined, DeleteOutlined
} from '@ant-design/icons';
import { Machine } from '../../types/machine';
import { formatDate } from '../../utils/dateUtils';

interface MachineDetailProps {
  machine: Machine;
  onOperation: (operation: string, machine: Machine) => void;
  onEdit: (machine: Machine) => void;
  onDelete: (id: number) => void;
}

const MachineDetail: React.FC<MachineDetailProps> = ({
  machine,
  onOperation,
  onEdit,
  onDelete
}) => {
  return (
    <Card title={`机器详情: ${machine.name}`}>
      <Descriptions bordered column={2}>
        <Descriptions.Item label="ID">{machine.id}</Descriptions.Item>
        <Descriptions.Item label="名称">{machine.name}</Descriptions.Item>
        <Descriptions.Item label="主机地址">{machine.host}</Descriptions.Item>
        <Descriptions.Item label="SSH端口">{machine.port}</Descriptions.Item>
        <Descriptions.Item label="用户名">{machine.username}</Descriptions.Item>
        <Descriptions.Item label="状态">
          <Badge 
            status={machine.is_online ? "success" : "error"} 
            text={machine.is_online ? "在线" : "离线"} 
          />
        </Descriptions.Item>
        <Descriptions.Item label="后端服务">
          <Badge 
            status={machine.backend_running ? "success" : "default"} 
            text={machine.backend_running ? "运行中" : "已停止"} 
          />
        </Descriptions.Item>
        <Descriptions.Item label="前端服务">
          <Badge 
            status={machine.frontend_running ? "success" : "default"} 
            text={machine.frontend_running ? "运行中" : "已停止"} 
          />
        </Descriptions.Item>
        {machine.cpu_usage && (
          <Descriptions.Item label="CPU使用情况">
            {machine.cpu_usage}
          </Descriptions.Item>
        )}
        {machine.memory_usage && (
          <Descriptions.Item label="内存使用情况">
            {machine.memory_usage}
          </Descriptions.Item>
        )}
        {machine.disk_usage && (
          <Descriptions.Item label="磁盘使用情况">
            {machine.disk_usage}
          </Descriptions.Item>
        )}
        <Descriptions.Item label="最后检查时间">
          {machine.last_check 
            ? formatDate(machine.last_check)
            : '未检查'}
        </Descriptions.Item>
        <Descriptions.Item label="创建时间">
          {formatDate(machine.created_at)}
        </Descriptions.Item>
        {machine.description && (
          <Descriptions.Item label="描述" span={2}>
            {machine.description}
          </Descriptions.Item>
        )}
      </Descriptions>
      
      <div style={{ marginTop: 16 }}>
        <Space>
          <Button 
            type="primary" 
            icon={<SyncOutlined />}
            onClick={() => onOperation('check', machine)}
          >
            检查状态
          </Button>
          <Button 
            icon={<DeploymentUnitOutlined />}
            onClick={() => onOperation('deploy', machine)}
          >
            部署项目
          </Button>
          <Button 
            type="primary" 
            icon={<PlayCircleOutlined />}
            onClick={() => onOperation('start', machine)}
            disabled={!machine.is_online}
            style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
          >
            启动服务
          </Button>
          <Button 
            danger 
            icon={<StopOutlined />}
            onClick={() => onOperation('stop', machine)}
            disabled={!machine.is_online}
          >
            停止服务
          </Button>
          <Button 
            icon={<EditOutlined />}
            onClick={() => onEdit(machine)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这台机器吗?"
            onConfirm={() => onDelete(machine.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              danger 
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      </div>
    </Card>
  );
};

export default MachineDetail; 