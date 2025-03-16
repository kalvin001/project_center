import React from 'react';
import { 
  Card, Button, Form, Input, 
  Select, Space, message
} from 'antd';
import { RollbackOutlined } from '@ant-design/icons';
import { useProjectStore } from '../../stores/projectStore';

const { Item: FormItem } = Form;
const { Option } = Select;

interface ProjectEditFormProps {
  project: any;
  projectId: number;
  onCancel: () => void;
}

const ProjectEditForm: React.FC<ProjectEditFormProps> = ({ 
  project, 
  projectId,
  onCancel 
}) => {
  const [form] = Form.useForm();
  const { updateProject } = useProjectStore();

  // 处理项目更新
  const handleUpdateProject = async (values: any) => {
    try {
      await updateProject(projectId, values);
      message.success('项目更新成功');
      onCancel();
    } catch (error) {
      message.error('更新项目失败');
    }
  };

  return (
    <Card 
      title="编辑项目" 
      extra={
        <Button icon={<RollbackOutlined />} onClick={onCancel}>
          取消编辑
        </Button>
      }
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleUpdateProject}
        initialValues={{
          name: project.name,
          description: project.description,
          project_type: project.project_type,
          repository_url: project.repository_url,
          is_active: project.is_active,
        }}
      >
        <FormItem
          name="name"
          label="项目名称"
          rules={[{ required: true, message: '请输入项目名称' }]}
        >
          <Input />
        </FormItem>
        
        <FormItem
          name="description"
          label="项目描述"
        >
          <Input.TextArea rows={4} />
        </FormItem>
        
        <FormItem
          name="project_type"
          label="项目类型"
          rules={[{ required: true, message: '请选择项目类型' }]}
        >
          <Select>
            <Option value="frontend">前端</Option>
            <Option value="backend">后端</Option>
            <Option value="fullstack">全栈</Option>
            <Option value="mobile">移动端</Option>
            <Option value="other">其他</Option>
          </Select>
        </FormItem>
        
        <FormItem
          name="repository_url"
          label="代码仓库"
        >
          <Input placeholder="如: https://github.com/username/repo" />
        </FormItem>
        
        <FormItem
          name="is_active"
          label="项目状态"
        >
          <Select>
            <Option value={true}>活跃</Option>
            <Option value={false}>非活跃</Option>
          </Select>
        </FormItem>
        
        <FormItem>
          <Space>
            <Button type="primary" htmlType="submit">
              保存
            </Button>
            <Button onClick={onCancel}>
              取消
            </Button>
          </Space>
        </FormItem>
      </Form>
    </Card>
  );
};

export default ProjectEditForm; 