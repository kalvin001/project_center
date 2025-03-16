import React, { useState, useEffect } from 'react';
import { Typography, Button, message, Tabs, Modal, Input, Breadcrumb } from 'antd';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { HomeOutlined, LaptopOutlined, DeploymentUnitOutlined } from '@ant-design/icons';
import axios from 'axios';
import { useStore } from '../stores';
import { Machine, DeployParams } from '../types/machine';
import MachineDetailComponent from '../components/machine/MachineDetail';
import MachineMonitor from '../components/machine/MachineMonitor';
import DeployedProjectsList from '../components/machine/DeployedProjectsList';
import PasswordModal from '../components/machine/PasswordModal';
import DeploymentForm from '../components/DeploymentForm';
import MachineDeployments from '../components/machine/MachineDeployments';

const { Title } = Typography;
const { TabPane } = Tabs;

const MachineDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [machine, setMachine] = useState<Machine | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const { token } = useStore();
  const [activeTab, setActiveTab] = useState<string>('info');
  
  // 操作相关状态
  const [passwordModalVisible, setPasswordModalVisible] = useState<boolean>(false);
  const [currentOperation, setCurrentOperation] = useState<string>('');
  const [operationLoading, setOperationLoading] = useState<boolean>(false);
  const [currentProjectId, setCurrentProjectId] = useState<number | null>(null);
  const [currentDeploymentId, setCurrentDeploymentId] = useState<number | null>(null);
  
  // 部署相关状态
  const [deployModalVisible, setDeployModalVisible] = useState<boolean>(false);
  
  const fetchMachine = async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      const response = await axios.get(`/api/machines/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMachine(response.data);
    } catch (error) {
      console.error('获取机器详情失败:', error);
      message.error('获取机器详情失败');
      navigate('/machines');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMachine();
  }, [id]);

  const handleCheck = async (id: number, password?: string) => {
    try {
      setOperationLoading(true);
      
      // 确保当密码为空字符串时转为null
      const cleanPassword = password && password.trim() !== '' ? password : null;
      
      await axios.post(
        `/api/machines/${id}/check`, 
        { password: cleanPassword }, 
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      message.success('检查状态成功');
      fetchMachine();
    } catch (error: any) {
      console.error('检查状态失败:', error);
      // 显示详细错误信息
      message.error(error.response?.data?.detail || '检查状态失败');
    } finally {
      setOperationLoading(false);
      setPasswordModalVisible(false);
    }
  };

  const handleOperation = (operation: string, machine: Machine) => {
    setCurrentOperation(operation);
    setCurrentProjectId(null);
    setCurrentDeploymentId(null);
    setPasswordModalVisible(true);
  };

  const handleProjectOperation = (operation: string, projectId: number) => {
    setCurrentOperation(operation);
    setCurrentProjectId(projectId);
    setCurrentDeploymentId(null);
    setPasswordModalVisible(true);
  };

  const handleDeploymentOperation = (operation: string, deploymentId: number) => {
    setCurrentOperation(operation);
    setCurrentDeploymentId(deploymentId);
    setCurrentProjectId(null);
    setPasswordModalVisible(true);
  };

  const executeOperation = async (password: string) => {
    if (!machine) return;
    
    try {
      setOperationLoading(true);
      
      let response;
      let url = '';
      let data = { password };
      
      // 处理机器操作
      if (!currentProjectId && !currentDeploymentId) {
        switch (currentOperation) {
          case 'check':
            await handleCheck(machine.id, password);
            return;
          case 'deploy':
            url = `/api/machines/${machine.id}/deploy`;
            data = { password, show_logs: false } as DeployParams;
            break;
          case 'start':
            url = `/api/machines/${machine.id}/start`;
            break;
          case 'stop':
            url = `/api/machines/${machine.id}/stop`;
            break;
          default:
            return;
        }
      } 
      // 处理项目操作
      else if (currentProjectId) {
        switch (currentOperation) {
          case 'redeploy':
            url = `/api/machines/${machine.id}/projects/${currentProjectId}/redeploy`;
            break;
          case 'start_project':
            url = `/api/machines/${machine.id}/projects/${currentProjectId}/start`;
            break;
          case 'stop_project':
            url = `/api/machines/${machine.id}/projects/${currentProjectId}/stop`;
            break;
          case 'remove_deploy':
            url = `/api/machines/${machine.id}/projects/${currentProjectId}`;
            // 使用DELETE方法
            await axios.delete(url, {
              headers: { Authorization: `Bearer ${token}` },
              data: { password }
            });
            message.success('项目部署已移除');
            // 刷新页面
            fetchMachine();
            setActiveTab('deployments');
            return;
          default:
            return;
        }
      }
      // 处理部署操作
      else if (currentDeploymentId) {
        switch (currentOperation) {
          case 'deploy':
            url = `/api/deployments/${currentDeploymentId}/deploy`;
            break;
          case 'redeploy':
            url = `/api/deployments/${currentDeploymentId}/redeploy`;
            break;
          case 'delete_deployment':
            try {
              await axios.delete(`/api/deployments/${currentDeploymentId}`);
              message.success('部署已删除');
              fetchMachine();
              setActiveTab('deployments');
              setOperationLoading(false);
              setPasswordModalVisible(false);
              return;
            } catch (error: any) {
              console.error('删除部署失败:', error);
              message.error(error.response?.data?.detail || '删除部署失败');
              setOperationLoading(false);
              setPasswordModalVisible(false);
              return;
            }
          default:
            return;
        }
      }
      
      // 执行操作
      response = await axios.post(
        url,
        data,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // 显示成功消息
      let successMsg = '操作成功';
      if (response?.data?.message) {
        successMsg = response.data.message;
      } else {
        switch (currentOperation) {
          case 'deploy':
            successMsg = '部署任务已启动';
            break;
          case 'start':
          case 'start_project':
            successMsg = '服务已启动';
            break;
          case 'stop':
          case 'stop_project':
            successMsg = '服务已停止';
            break;
          case 'redeploy':
            successMsg = '重新部署任务已启动';
            break;
        }
      }
      
      message.success(successMsg);
      
      // 刷新机器详情
      fetchMachine();
      
      // 如果是项目操作，切换到项目Tab
      if (currentProjectId) {
        setActiveTab('projects');
      }
    } catch (error: any) {
      console.error(`操作失败:`, error);
      message.error(`操作失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setOperationLoading(false);
      setPasswordModalVisible(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await axios.delete(`/api/machines/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      message.success('机器删除成功');
      navigate('/machines');
    } catch (error) {
      console.error('删除失败:', error);
      message.error('删除失败');
    }
  };

  const handleEdit = (machine: Machine) => {
    navigate(`/machines/edit/${machine.id}`);
  };

  // 部署成功回调
  const handleDeploymentSuccess = () => {
    setDeployModalVisible(false);
    message.success('部署任务已提交，请稍后查看部署状态');
    // 刷新机器详情，更新项目列表
    fetchMachine();
    // 切换到项目Tab
    setActiveTab('projects');
  };

  const handleMonitorPasswordRequired = () => {
    Modal.confirm({
      title: '需要SSH密码',
      content: (
        <div>
          <p>获取监控数据需要SSH连接到机器。请提供SSH密码：</p>
          <Input.Password id="monitor-password" placeholder="输入SSH密码" />
        </div>
      ),
      onOk: async () => {
        const password = (document.getElementById('monitor-password') as HTMLInputElement)?.value;
        if (machine) {
          await handleCheck(machine.id, password);
          setActiveTab('monitor');
        }
      }
    });
  };

  if (!machine && !loading) {
    return (
      <div>
        <Title level={3}>机器详情</Title>
        <div>未找到机器信息</div>
        <Button type="primary" onClick={() => navigate('/machines')}>
          返回列表
        </Button>
      </div>
    );
  }

  return (
    <div>
      <Breadcrumb style={{ marginBottom: 16 }}>
        <Breadcrumb.Item>
          <Link to="/">
            <HomeOutlined /> 首页
          </Link>
        </Breadcrumb.Item>
        <Breadcrumb.Item>
          <Link to="/machines">
            <LaptopOutlined /> 机器管理
          </Link>
        </Breadcrumb.Item>
        <Breadcrumb.Item>{machine?.name || '机器详情'}</Breadcrumb.Item>
      </Breadcrumb>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={3}>{machine?.name} 详情</Title>
        <div>
          <Button 
            type="primary" 
            style={{ marginRight: 8 }} 
            onClick={() => setDeployModalVisible(true)}
            icon={<DeploymentUnitOutlined />}
          >
            部署项目
          </Button>
          <Button 
            onClick={() => machine && handleEdit(machine)} 
            style={{ marginRight: 8 }}
          >
            编辑
          </Button>
          <Button 
            danger 
            onClick={() => machine && handleDelete(machine.id)}
          >
            删除
          </Button>
        </div>
      </div>

      <Tabs 
        activeKey={activeTab}
        onChange={setActiveTab}
      >
        <TabPane tab="基本信息" key="info">
          {machine && (
            <MachineDetailComponent 
              machine={machine}
              onOperation={handleOperation}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          )}
        </TabPane>
        <TabPane tab="部署" key="deployments">
          {machine && (
            <MachineDeployments 
              machineId={machine.id}
              onOperation={handleDeploymentOperation}
            />
          )}
        </TabPane>
        <TabPane tab="已部署项目" key="projects">
          {machine && (
            <DeployedProjectsList 
              machineId={machine.id}
              onPasswordRequired={handleProjectOperation}
            />
          )}
        </TabPane>
        <TabPane tab="系统监控" key="monitor">
          {machine && (
            <MachineMonitor 
              machineId={machine.id} 
              onPasswordRequired={handleMonitorPasswordRequired}
            />
          )}
        </TabPane>
      </Tabs>

      {machine && (
        <PasswordModal
          title={`请输入 ${machine.name} 的SSH密码`}
          visible={passwordModalVisible}
          confirmLoading={operationLoading}
          onOk={executeOperation}
          onCancel={() => setPasswordModalVisible(false)}
        />
      )}

      <Modal
        title="部署项目到此机器"
        open={deployModalVisible}
        onCancel={() => setDeployModalVisible(false)}
        footer={null}
        width={700}
      >
        {machine && (
          <DeploymentForm
            initialMachineId={machine.id ? Number(machine.id) : undefined}
            onSuccess={handleDeploymentSuccess}
            inCard={false}
          />
        )}
      </Modal>
    </div>
  );
};

export default MachineDetailPage; 