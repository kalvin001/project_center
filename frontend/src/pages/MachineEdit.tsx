import React, { useState, useEffect } from 'react';
import { Typography, Form, message, Button, Space } from 'antd';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import { useStore } from '../stores';
import { Machine } from '../types/machine';
import MachineForm from '../components/machine/MachineForm';

const { Title } = Typography;

const MachineEditPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [machine, setMachine] = useState<Machine | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [form] = Form.useForm();
  const { token } = useStore();
  
  const isEdit = !!id;
  
  const fetchMachine = async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      const response = await axios.get(`/api/machines/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMachine(response.data);
      
      // 设置表单初始值
      form.setFieldsValue({
        name: response.data.name,
        host: response.data.host,
        port: response.data.port,
        username: response.data.username,
        description: response.data.description
      });
    } catch (error) {
      console.error('获取机器详情失败:', error);
      message.error('获取机器详情失败');
      navigate('/machines');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isEdit) {
      fetchMachine();
    }
  }, [id]);

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      
      if (isEdit && machine) {
        // 更新机器
        await axios.put(`/api/machines/${id}`, values, {
          headers: { Authorization: `Bearer ${token}` }
        });
        message.success('机器更新成功');
      } else {
        // 创建新机器
        await axios.post('/api/machines/', values, {
          headers: { Authorization: `Bearer ${token}` }
        });
        message.success('机器添加成功');
      }
      
      navigate('/machines');
    } catch (error) {
      console.error('保存失败:', error);
      message.error('保存失败');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    navigate('/machines');
  };

  return (
    <div>
      <Title level={3}>{isEdit ? '编辑机器' : '添加机器'}</Title>
      
      <div style={{ maxWidth: 800, margin: '0 auto' }}>
        <MachineForm 
          visible={true}
          editingMachine={machine}
          onCancel={handleCancel}
          onSave={handleSave}
          form={form}
          confirmLoading={saving}
          inPage={true}
        />
        
        <div style={{ marginTop: 24, textAlign: 'right' }}>
          <Space>
            <Button onClick={handleCancel}>
              取消
            </Button>
            <Button type="primary" onClick={handleSave} loading={saving}>
              保存
            </Button>
          </Space>
        </div>
      </div>
    </div>
  );
};

export default MachineEditPage; 