import React, { useState, useEffect } from 'react';
import { Typography, Space, Button, message, Row, Col, Breadcrumb, Modal, Card } from 'antd';
import { ReloadOutlined, HomeOutlined, PlusOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { deploymentApi } from '../utils/api';
import { Deployment } from '../types';
import DeploymentForm from '../components/DeploymentForm';
import DeploymentTable from '../components/DeploymentTable';
import { formatDate } from '../utils/dateUtils';

const { Title } = Typography;

const DeploymentPage: React.FC = () => {
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);

  const fetchDeployments = async () => {
    setLoading(true);
    try {
      const data = await deploymentApi.getDeployments();
      setDeployments(data);
    } catch (error) {
      message.error('无法加载部署记录，请稍后再试');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDeployments();
  }, []);

  const showModal = () => {
    setIsModalVisible(true);
  };

  const handleCancel = () => {
    setIsModalVisible(false);
  };

  const handleDeploySuccess = () => {
    setIsModalVisible(false);
    fetchDeployments();
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

  const redeployProject = async (deployment: Deployment) => {
    try {
      await deploymentApi.redeployProject(deployment.id);
      message.success('重新部署请求已提交，系统正在处理您的请求');
      
      // 延迟一下再刷新数据
      setTimeout(() => {
        fetchDeployments();
      }, 1000);
    } catch (error: any) {
      console.error('重新部署错误：', error);
      
      if (error.response?.status === 400) {
        // 如果是400错误，可能是缺少部署路径
        message.error('部署失败：缺少部署路径或其他参数');
      } else {
        message.error('提交重新部署请求时发生错误，请稍后再试');
      }
    }
  };

  return (
    <div>
      <Breadcrumb style={{ marginBottom: 16 }}>
        <Breadcrumb.Item>
          <Link to="/">
            <HomeOutlined />
          </Link>
        </Breadcrumb.Item>
        <Breadcrumb.Item>项目部署</Breadcrumb.Item>
      </Breadcrumb>

      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2}>项目部署</Title>
        </Col>
        <Col>
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={showModal}
            >
              新建部署
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchDeployments}
              loading={loading}
            >
              刷新
            </Button>
          </Space>
        </Col>
      </Row>

      <Card title="部署记录" bordered={false}>
        <DeploymentTable 
          deployments={deployments} 
          loading={loading}
          onViewLogs={viewLogs}
          onRedeploy={redeployProject}
          highlightClickable={true}
        />
      </Card>

      <Modal
        title="新建部署"
        open={isModalVisible}
        onCancel={handleCancel}
        footer={null}
        width={700}
        destroyOnClose={true}
      >
        <DeploymentForm onSuccess={handleDeploySuccess} />
      </Modal>
    </div>
  );
};

export default DeploymentPage; 