import React, { useState, useEffect } from 'react';
import { Button, Card, message, Tooltip, Empty, Modal, Input } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { deploymentApi } from '../../utils/api';
import { useNavigate } from 'react-router-dom';
import type { Deployment } from '../../types';
import DeploymentTable from '../DeploymentTable';

interface MachineDeploymentsProps {
  machineId: number;
  onOperation: (operation: string, deploymentId: number) => void;
}

const MachineDeployments: React.FC<MachineDeploymentsProps> = ({ 
  machineId, 
  onOperation 
}) => {
  const navigate = useNavigate();
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [loading, setLoading] = useState(false);
  const [deployPath, setDeployPath] = useState('');
  const [currentDeployment, setCurrentDeployment] = useState<Deployment | null>(null);
  const [isDeployPathModalVisible, setIsDeployPathModalVisible] = useState(false);

  useEffect(() => {
    fetchDeployments();
  }, [machineId]);

  const fetchDeployments = async () => {
    setLoading(true);
    try {
      const data = await deploymentApi.getMachineDeployments(machineId);
      setDeployments(data);
    } catch (error) {
      message.error('获取机器部署列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleViewProject = (projectId: number) => {
    navigate(`/projects/${projectId}`);
  };

  const viewLogs = (deployment: Deployment) => {
    Modal.info({
      title: '部署日志',
      width: 800,
      content: (
        <div style={{ maxHeight: '400px', overflow: 'auto', whiteSpace: 'pre-wrap' }}>
          {deployment.log || '无部署日志'}
        </div>
      ),
      okText: '关闭'
    });
  };

  const showDeployPathModal = (deployment: Deployment) => {
    setCurrentDeployment(deployment);
    setDeployPath(deployment.deploy_path || '');
    setIsDeployPathModalVisible(true);
  };

  const startDeploy = async (deployment: Deployment) => {
    if (!deployPath.trim()) {
      message.error('部署路径不能为空');
      return;
    }
    
    try {
      await deploymentApi.deployApplication(deployment.id, {
        deploy_path: deployPath,
        environment: deployment.environment
      });
      message.success('部署请求已提交');
      setIsDeployPathModalVisible(false);
      setCurrentDeployment(null);
      onOperation('refresh', deployment.id);
    } catch (error) {
      message.error('部署失败');
    }
  };

  const handleRedeploy = (deployment: Deployment) => {
    onOperation('redeploy', deployment.id);
  };

  const handleDeleteDeployment = (deployment: Deployment) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除此部署记录吗？',
      onOk: () => onOperation('delete_deployment', deployment.id)
    });
  };

  return (
    <Card 
      title="机器部署" 
      extra={
        <Button 
          icon={<ReloadOutlined />} 
          onClick={fetchDeployments}
          loading={loading}
        >
          刷新
        </Button>
      }
    >
      {deployments.length > 0 ? (
        <DeploymentTable 
          deployments={deployments}
          loading={loading}
          onViewLogs={viewLogs}
          onRedeploy={handleRedeploy}
          highlightClickable={true}
        />
      ) : (
        <Empty description="该机器上暂无部署记录" />
      )}

      {currentDeployment && (
        <Modal
          title="设置部署路径"
          open={isDeployPathModalVisible}
          onOk={() => startDeploy(currentDeployment)}
          onCancel={() => {
            setIsDeployPathModalVisible(false);
            setCurrentDeployment(null);
          }}
        >
          <p>请输入部署路径：</p>
          <Input
            placeholder="/root/projects"
            value={deployPath}
            onChange={(e) => setDeployPath(e.target.value)}
          />
        </Modal>
      )}
    </Card>
  );
};

export default MachineDeployments; 