import React, { useState, useEffect } from 'react';
import { Form, Select, Input, Button, Card, message, Spin } from 'antd';
import { Project, Machine, DeploymentFormValues } from '../types';
import api from '../utils/api';
import { deploymentApi } from '../utils/api';

interface DeploymentFormProps {
  initialProjectId?: number;
  initialMachineId?: number;
  onSuccess?: () => void;
  inCard?: boolean;
}

const DeploymentForm: React.FC<DeploymentFormProps> = ({
  initialProjectId,
  initialMachineId,
  onSuccess,
  inCard = true
}) => {
  const [form] = Form.useForm();
  const [projects, setProjects] = useState<Project[]>([]);
  const [machines, setMachines] = useState<Machine[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [deploymentCreated, setDeploymentCreated] = useState(false);
  const [deploymentId, setDeploymentId] = useState<number | null>(null);

  useEffect(() => {
    fetchProjects();
    fetchMachines();
  }, []);

  // 设置初始值
  useEffect(() => {
    if (initialProjectId || initialMachineId) {
      const initialValues: Partial<DeploymentFormValues> = {
        environment: 'development'
      };
      
      if (initialProjectId) {
        initialValues.project_id = initialProjectId;
      }
      
      if (initialMachineId) {
        initialValues.machine_id = initialMachineId;
      }
      
      form.setFieldsValue(initialValues);
    }
  }, [initialProjectId, initialMachineId, form]);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const response = await api.get('/projects');
      setProjects(response.data);
    } catch (error: any) {
      if (error.response?.status === 401) {
        console.warn('获取项目列表需要授权，请确保已登录');
        // 不显示错误消息，避免重复显示
      } else {
        message.error('获取项目列表失败');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchMachines = async () => {
    try {
      setLoading(true);
      const response = await api.get('/machines');
      setMachines(response.data);
    } catch (error: any) {
      if (error.response?.status === 401) {
        console.warn('获取机器列表需要授权，请确保已登录');
        // 不显示错误消息，避免重复显示
      } else {
        message.error('获取机器列表失败');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (values: DeploymentFormValues) => {
    try {
      setSubmitting(true);
      
      // 创建部署关联，使用新的deploymentApi
      const responseData = await deploymentApi.createDeployment({
        project_id: values.project_id,
        machine_id: values.machine_id,
        environment: values.environment,
        deploy_path: values.deploy_path || null
      });
      
      setDeploymentCreated(true);
      setDeploymentId(responseData.id);
      
      message.success('部署关联创建成功');
      
      if (values.deploy_path) {
        // 如果提供了部署路径，直接开始部署
        await startDeployment(responseData.id, values);
      }
      
      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      message.error('创建部署失败');
      console.error('创建部署失败:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const startDeployment = async (id: number, values: DeploymentFormValues) => {
    try {
      setSubmitting(true);
      await api.post(`/deployments/${id}/deploy`, {
        deploy_path: values.deploy_path,
        environment: values.environment
      });
      message.success('部署任务已提交');
      
      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      message.error('开始部署失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleStartDeploy = async () => {
    if (!deploymentId) return;
    
    try {
      const values = form.getFieldsValue();
      await startDeployment(deploymentId, values);
    } catch (error) {
      message.error('开始部署失败');
    }
  };

  const formContent = (
    <>
      {loading ? (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <Spin tip="加载中..." />
        </div>
      ) : (
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{ environment: 'development' }}
        >
          <Form.Item
            name="project_id"
            label="项目"
            rules={[{ required: true, message: '请选择项目' }]}
          >
            <Select
              placeholder="请选择项目"
              disabled={!!initialProjectId || submitting}
              showSearch
              optionFilterProp="children"
            >
              {projects.map(project => (
                <Select.Option key={project.id} value={project.id}>
                  {project.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item
            name="machine_id"
            label="部署机器"
            rules={[{ required: true, message: '请选择部署机器' }]}
          >
            <Select
              placeholder="请选择部署机器"
              disabled={!!initialMachineId || submitting}
              showSearch
              optionFilterProp="children"
            >
              {machines.map(machine => (
                <Select.Option key={machine.id} value={machine.id}>
                  {machine.name} ({machine.host})
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item
            name="environment"
            label="部署环境"
            rules={[{ required: true, message: '请选择部署环境' }]}
          >
            <Select placeholder="请选择部署环境" disabled={submitting}>
              <Select.Option value="development">开发环境</Select.Option>
              <Select.Option value="staging">测试环境</Select.Option>
              <Select.Option value="production">生产环境</Select.Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="deploy_path"
            label="部署路径"
            help="此路径将作为项目的部署目标目录，如果不确定可以稍后设置"
          >
            <Input placeholder="/root/projects" disabled={submitting} />
          </Form.Item>
          
          <Form.Item>
            {!deploymentCreated ? (
              <Button 
                type="primary" 
                htmlType="submit" 
                loading={submitting}
                block
              >
                部署项目
              </Button>
            ) : (
              <Button 
                type="primary" 
                onClick={handleStartDeploy} 
                loading={submitting}
                block
              >
                {form.getFieldValue('deploy_path') ? '开始部署' : '输入部署路径并开始部署'}
              </Button>
            )}
          </Form.Item>
        </Form>
      )}
    </>
  );

  if (inCard) {
    return <Card title="部署配置">{formContent}</Card>;
  }
  
  return formContent;
};

export default DeploymentForm; 