import React, { useState, useEffect } from 'react';
import { Typography, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useStore } from '../stores';
import { Machine } from '../types/machine';
import MachineList from '../components/machine/MachineList';
import PasswordModal from '../components/machine/PasswordModal';

const { Title } = Typography;

const MachineManagement: React.FC = () => {
  const navigate = useNavigate();
  const [machines, setMachines] = useState<Machine[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const { token } = useStore();
  
  // 操作相关状态
  const [selectedMachine, setSelectedMachine] = useState<Machine | null>(null);
  const [passwordModalVisible, setPasswordModalVisible] = useState<boolean>(false);
  const [currentOperation, setCurrentOperation] = useState<string>('');
  const [operationLoading, setOperationLoading] = useState<boolean>(false);
  
  const fetchMachines = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/machines/', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMachines(response.data);
    } catch (error) {
      console.error('获取机器列表失败:', error);
      message.error('获取机器列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMachines();
  }, []);

  const handleDelete = async (id: number) => {
    try {
      await axios.delete(`/api/machines/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      message.success('机器删除成功');
      fetchMachines();
    } catch (error) {
      console.error('删除失败:', error);
      message.error('删除失败');
    }
  };

  const handleCheck = async (id: number, password?: string) => {
    try {
      setOperationLoading(true);
      
      // 确保当密码为空字符串时转为null
      const cleanPassword = password && password.trim() !== '' ? password : null;
      
      const response = await axios.post(
        `/api/machines/${id}/check`, 
        { password: cleanPassword }, 
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      message.success('检查状态成功');
      fetchMachines();
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
    setSelectedMachine(machine);
    setCurrentOperation(operation);
    setPasswordModalVisible(true);
  };

  const executeOperation = async (password: string) => {
    if (!selectedMachine) return;
    
    try {
      setOperationLoading(true);
      
      let response;
      switch (currentOperation) {
        case 'check':
          await handleCheck(selectedMachine.id, password);
          break;
        case 'deploy':
          response = await axios.post(
            `/api/machines/${selectedMachine.id}/deploy`,
            { password, show_logs: false },
            { headers: { Authorization: `Bearer ${token}` } }
          );
          message.success(response?.data?.message || '部署任务已启动');
          break;
        case 'start':
          response = await axios.post(
            `/api/machines/${selectedMachine.id}/start`,
            { password },
            { headers: { Authorization: `Bearer ${token}` } }
          );
          message.success(response?.data?.message || '服务已启动');
          break;
        case 'stop':
          response = await axios.post(
            `/api/machines/${selectedMachine.id}/stop`,
            { password },
            { headers: { Authorization: `Bearer ${token}` } }
          );
          message.success(response?.data?.message || '服务已停止');
          break;
        default:
          break;
      }
      
      // 刷新机器列表
      fetchMachines();
    } catch (error: any) {
      console.error(`操作失败:`, error);
      message.error(`操作失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setOperationLoading(false);
      setPasswordModalVisible(false);
    }
  };

  const handleView = (machine: Machine) => {
    navigate(`/machines/${machine.id}`);
  };

  const handleAdd = () => {
    navigate('/machines/add');
  };

  const handleEdit = (machine: Machine) => {
    navigate(`/machines/edit/${machine.id}`);
  };

  return (
    <div>
      <Title level={3}>机器管理</Title>
      
      <MachineList 
        machines={machines}
        loading={loading}
        onAdd={handleAdd}
        onRefresh={fetchMachines}
        onView={handleView}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onOperation={handleOperation}
      />
      
      <PasswordModal
        title={`请输入${selectedMachine?.name || ''}的SSH密码`}
        visible={passwordModalVisible}
        onCancel={() => setPasswordModalVisible(false)}
        onOk={executeOperation}
        confirmLoading={operationLoading}
      />
    </div>
  );
};

export default MachineManagement; 