import React from 'react';
import { Table, Button, Space, Badge, Tooltip, Popconfirm } from 'antd';
import { 
  PlusOutlined, ReloadOutlined, SyncOutlined, DeploymentUnitOutlined,
  PlayCircleOutlined, StopOutlined, EditOutlined, DeleteOutlined, EyeOutlined
} from '@ant-design/icons';
import { Machine } from '../../types/machine';
import { formatDate } from '../../utils/dateUtils';

interface MachineListProps {
  machines: Machine[];
  loading: boolean;
  onAdd: () => void;
  onRefresh: () => void;
  onView: (machine: Machine) => void;
  onEdit: (machine: Machine) => void;
  onDelete: (id: number) => void;
  onOperation: (operation: string, machine: Machine) => void;
}

const MachineList: React.FC<MachineListProps> = ({
  machines,
  loading,
  onAdd,
  onRefresh,
  onView,
  onEdit,
  onDelete,
  onOperation
}) => {
  const columns = [
    {
      title: '名称',
      key: 'name',
      render: (_: any, record: Machine) => (
        <Button 
          type="link" 
          onClick={() => onView(record)}
        >
          {record.name}
        </Button>
      ),
    },
    {
      title: '地址',
      key: 'address',
      render: (_: any, record: Machine) => `${record.host}:${record.port}`,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '状态',
      key: 'status',
      render: (_: any, record: Machine) => (
        <Space>
          <Badge 
            status={record.is_online ? "success" : "error"} 
            text={record.is_online ? "在线" : "离线"} 
          />
          {record.is_online && (
            <>
              <Badge 
                status={record.backend_running ? "success" : "default"} 
                text="后端" 
              />
              <Badge 
                status={record.frontend_running ? "success" : "default"} 
                text="前端" 
              />
            </>
          )}
        </Space>
      ),
    },
    {
      title: '最后检查',
      key: 'last_check',
      render: (_: any, record: Machine) => record.last_check 
        ? formatDate(record.last_check) 
        : '未检查',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Machine) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button 
              type="link" 
              icon={<EyeOutlined />} 
              size="small"
              onClick={() => onView(record)} 
            />
          </Tooltip>
          <Tooltip title="检查状态">
            <Button 
              type="link" 
              icon={<SyncOutlined />} 
              size="small"
              onClick={() => onOperation('check', record)} 
            />
          </Tooltip>
          <Tooltip title="部署项目">
            <Button 
              type="link" 
              icon={<DeploymentUnitOutlined />} 
              size="small"
              onClick={() => onOperation('deploy', record)} 
            />
          </Tooltip>
          <Tooltip title="启动服务">
            <Button 
              type="link" 
              icon={<PlayCircleOutlined />} 
              size="small"
              onClick={() => onOperation('start', record)} 
              disabled={!record.is_online}
            />
          </Tooltip>
          <Tooltip title="停止服务">
            <Button 
              type="link" 
              icon={<StopOutlined />} 
              size="small"
              onClick={() => onOperation('stop', record)} 
              disabled={!record.is_online}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button 
              type="link" 
              icon={<EditOutlined />} 
              size="small"
              onClick={() => onEdit(record)} 
            />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确定要删除这台机器吗?"
              onConfirm={() => onDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button 
                type="link" 
                danger 
                icon={<DeleteOutlined />} 
                size="small"
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={onAdd}
          >
            添加机器
          </Button>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={onRefresh}
            loading={loading}
          >
            刷新列表
          </Button>
        </Space>
      </div>
      
      <Table 
        columns={columns} 
        dataSource={machines} 
        rowKey="id" 
        loading={loading}
        pagination={{ pageSize: 10 }}
      />
    </>
  );
};

export default MachineList; 