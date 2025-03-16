import React from 'react';
import { Modal, Form, Input } from 'antd';
import { OperationModalProps } from '../../types/machine';

const PasswordModal: React.FC<OperationModalProps> = ({ 
  title, visible, onCancel, onOk, confirmLoading 
}) => {
  const [form] = Form.useForm();

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      await onOk(values.password);
      form.resetFields();
    } catch (error) {
      console.error('验证表单失败:', error);
    }
  };

  return (
    <Modal
      title={title}
      open={visible}
      onOk={handleOk}
      confirmLoading={confirmLoading}
      onCancel={() => {
        form.resetFields();
        onCancel();
      }}
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="password"
          label="SSH密码"
          rules={[{ required: false, message: '请输入密码用于SSH连接' }]}
        >
          <Input.Password placeholder="如果使用密钥认证可以不填" />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default PasswordModal; 