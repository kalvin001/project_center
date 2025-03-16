import React, { useState, useEffect } from 'react';
import { 
  Button, Modal, Space, message, Spin, Input
} from 'antd';
import { useProjectStore } from '../../stores/projectStore';
import { Deployment } from '../../types';
import { deploymentApi } from '../../utils/api';
import DeploymentForm from '../DeploymentForm';
import DeploymentTable from '../DeploymentTable';

interface ProjectDeploymentTabProps {
  projectId: number;
}

const ProjectDeploymentTab: React.FC<ProjectDeploymentTabProps> = ({ projectId }) => {
  const [isDeployModalOpen, setIsDeployModalOpen] = useState(false);
  const { currentProject } = useProjectStore();
  const [loading, setLoading] = useState(false);
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [deployPath, setDeployPath] = useState('');
  const [deploymentToModify, setDeploymentToModify] = useState<Deployment | null>(null);
  const [isDeployPathModalVisible, setIsDeployPathModalVisible] = useState(false);

  useEffect(() => {
    fetchProjectDeployments();
  }, [projectId]);

  // 获取项目的部署记录
  const fetchProjectDeployments = async () => {
    setLoading(true);
    try {
      const data = await deploymentApi.getProjectDeployments(projectId);
      setDeployments(data);
    } catch (error) {
      message.error('获取部署记录失败');
    } finally {
      setLoading(false);
    }
  };

  // 部署成功回调
  const handleDeploymentSuccess = () => {
    setIsDeployModalOpen(false);
    fetchProjectDeployments();
  };

  // 查看部署日志
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

  // 启动部署
  const startDeploy = async (deployment: Deployment, path: string) => {
    try {
      await deploymentApi.deployApplication(deployment.id, {
        deploy_path: path,
        environment: deployment.environment
      });
      message.success('部署请求已提交');
      setIsDeployPathModalVisible(false);
      setDeploymentToModify(null);
      fetchProjectDeployments();
    } catch (error) {
      message.error('部署失败');
    }
  };

  // 显示部署路径确认对话框
  const showDeployPathModal = (deployment: Deployment) => {
    setDeploymentToModify(deployment);
    setDeployPath(deployment.deploy_path || '/root/projects');
    setIsDeployPathModalVisible(true);
  };

  // 重新部署项目
  const redeployProject = async (deployment: Deployment) => {
    try {
      await deploymentApi.redeployProject(deployment.id);
      message.success('重新部署请求已提交');
      fetchProjectDeployments();
    } catch (error) {
      message.error('重新部署失败');
    }
  };

  // 删除部署
  const deleteDeployment = async (deploymentId: number) => {
    try {
      await deploymentApi.deleteDeployment(deploymentId);
      message.success('部署记录已删除');
      fetchProjectDeployments();
    } catch (error) {
      message.error('删除部署记录失败');
    }
  };

  if (loading && deployments.length === 0) {
    return <Spin tip="加载中..." />;
  }

  return (
    <>
      <div style={{ marginBottom: '16px' }}>
        <Button type="primary" onClick={() => setIsDeployModalOpen(true)}>
          添加新机器部署
        </Button>
        <Button 
          style={{ marginLeft: '8px' }} 
          onClick={fetchProjectDeployments}
        >
          刷新部署记录
        </Button>
      </div>
      
      <DeploymentTable
        deployments={deployments}
        loading={loading}
        onViewLogs={viewLogs}
        onRedeploy={redeployProject}
        highlightClickable={true}
      />

      {/* 添加新机器部署模态框 */}
      <Modal
        title="添加新机器部署"
        open={isDeployModalOpen}
        footer={null}
        onCancel={() => setIsDeployModalOpen(false)}
        width={700}
      >
        <DeploymentForm 
          initialProjectId={projectId}
          onSuccess={handleDeploymentSuccess}
          inCard={false}
        />
      </Modal>

      {/* 设置部署路径模态框 */}
      {deploymentToModify && (
        <Modal
          title="设置部署路径"
          open={isDeployPathModalVisible}
          onOk={() => startDeploy(deploymentToModify, deployPath)}
          onCancel={() => {
            setIsDeployPathModalVisible(false);
            setDeploymentToModify(null);
          }}
        >
          <p>请输入项目在机器 {deploymentToModify.machine?.name || deploymentToModify.machine_id} 上的部署路径：</p>
          <p style={{ color: '#888', fontSize: '13px' }}>此路径将作为项目的部署目标目录，如果不确定可以稍后设置</p>
          <Input
            placeholder="/root/projects"
            value={deployPath}
            onChange={(e) => setDeployPath(e.target.value)}
          />
        </Modal>
      )}
    </>
  );
};

export default ProjectDeploymentTab; 