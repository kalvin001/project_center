import React, { useState } from 'react';
import { Modal, Form, Input, Radio, Button, Space, message } from 'antd';
import { useProjectStore } from '../../stores/projectStore';

const { Item: FormItem } = Form;

interface ProjectGitModalProps {
  projectId: number;
  isOpen: boolean;
  onClose: () => void;
}

const ProjectGitModal: React.FC<ProjectGitModalProps> = ({ 
  projectId, 
  isOpen, 
  onClose 
}) => {
  const [form] = Form.useForm();
  const [gitCloning, setGitCloning] = useState(false);
  const { cloneFromGit, fetchProjectFiles } = useProjectStore();

  const handleCloneFromGit = async (values: { 
    repository_url: string; 
    branch?: string;
    mode: 'replace' | 'increment';
  }) => {
    if (!values.repository_url) {
      message.error('请输入Git仓库地址');
      return;
    }

    setGitCloning(true);
    try {
      console.log('开始克隆Git仓库:', values.repository_url);
      
      await cloneFromGit(projectId, values.repository_url, values.branch);
      onClose();
      form.resetFields();
      message.success('Git仓库克隆成功');
      // 刷新文件列表
      fetchProjectFiles(projectId, '');
    } catch (error: any) {
      console.error('Git克隆失败:', error);
      message.error(error?.response?.data?.detail || 'Git仓库克隆失败，请检查仓库地址和权限');
    } finally {
      setGitCloning(false);
    }
  };

  return (
    <Modal
      title="从Git仓库克隆"
      open={isOpen}
      footer={null}
      onCancel={onClose}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleCloneFromGit}
      >
        <FormItem
          name="repository_url"
          label="Git仓库地址"
          rules={[{ required: true, message: '请输入Git仓库地址' }]}
        >
          <Input placeholder="例如: https://github.com/user/repo.git" />
        </FormItem>
        
        <FormItem
          name="branch"
          label="分支 (可选)"
        >
          <Input placeholder="默认: main" />
        </FormItem>
        
        <FormItem
          name="mode"
          label="克隆模式"
          initialValue="replace"
        >
          <Radio.Group>
            <Radio value="replace">替换所有文件（将删除项目中现有的所有文件）</Radio>
            <Radio value="increment">增量更新（保留项目中现有的文件）</Radio>
          </Radio.Group>
        </FormItem>
        
        <FormItem>
          <Space>
            <Button type="primary" htmlType="submit" loading={gitCloning}>
              开始克隆
            </Button>
            <Button onClick={onClose}>
              取消
            </Button>
          </Space>
        </FormItem>
      </Form>
    </Modal>
  );
};

export default ProjectGitModal; 