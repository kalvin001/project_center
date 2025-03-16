import React from 'react';
import { Modal, Form, Input, InputNumber } from 'antd';
import { Machine, MachineForm as MachineFormType } from '../../types/machine';

const { TextArea } = Input;

interface MachineFormProps {
  visible: boolean;
  editingMachine: Machine | null;
  onCancel: () => void;
  onSave: () => void;
  form: any;
  confirmLoading?: boolean;
  inPage?: boolean; // 是否在页面内显示，而不是在模态框中
}

const MachineForm: React.FC<MachineFormProps> = ({
  visible,
  editingMachine,
  onCancel,
  onSave,
  form,
  confirmLoading = false,
  inPage = false
}) => {
  const formContent = (
    <Form form={form} layout="vertical">
      <Form.Item
        name="name"
        label="机器名称"
        rules={[{ required: true, message: '请输入机器名称' }]}
      >
        <Input placeholder="如: 生产服务器" />
      </Form.Item>
      
      <Form.Item
        name="host"
        label="主机地址"
        rules={[{ required: true, message: '请输入主机地址' }]}
      >
        <Input placeholder="如: 192.168.1.100" />
      </Form.Item>
      
      <Form.Item
        name="port"
        label="SSH端口"
        rules={[{ required: true, message: '请输入SSH端口' }]}
        initialValue={22}
      >
        <InputNumber min={1} max={65535} style={{ width: '100%' }} />
      </Form.Item>
      
      <Form.Item
        name="username"
        label="用户名"
        rules={[{ required: true, message: '请输入用户名' }]}
        initialValue="root"
      >
        <Input placeholder="如: root" />
      </Form.Item>
      
      {!editingMachine && (
        <Form.Item
          name="password"
          label="密码"
          extra="密码仅用于初始连接验证，不会保存到服务器"
        >
          <Input.Password placeholder="可选，如果使用密钥认证可不填" />
        </Form.Item>
      )}
      
      <Form.Item
        name="key_file"
        label="SSH密钥文件"
        extra="可选，指定SSH密钥文件路径"
      >
        <Input placeholder="如: /path/to/id_rsa" />
      </Form.Item>
      
      <Form.Item
        name="description"
        label="描述"
      >
        <TextArea rows={3} placeholder="可选，填写机器的用途或备注信息" />
      </Form.Item>
    </Form>
  );

  // 如果是页面内表单，直接返回表单内容
  if (inPage) {
    return formContent;
  }

  // 否则返回模态框包装的表单
  return (
    <Modal
      title={editingMachine ? '编辑机器' : '添加机器'}
      open={visible}
      onOk={onSave}
      onCancel={onCancel}
      okText="保存"
      cancelText="取消"
      confirmLoading={confirmLoading}
    >
      {formContent}
    </Modal>
  );
};

export default MachineForm; 