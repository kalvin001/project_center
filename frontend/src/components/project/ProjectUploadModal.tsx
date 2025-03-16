import React, { useState } from 'react';
import { Modal, Upload, Button, Radio, Space, message } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { useProjectStore } from '../../stores/projectStore';
import type { UploadFile } from 'antd/es/upload/interface';

interface ProjectUploadModalProps {
  projectId: number;
  isOpen: boolean;
  onClose: () => void;
}

const ProjectUploadModal: React.FC<ProjectUploadModalProps> = ({ 
  projectId, 
  isOpen, 
  onClose 
}) => {
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadMode, setUploadMode] = useState<'replace' | 'increment'>('replace');
  const [isLoading, setIsLoading] = useState(false);
  const { uploadProject, fetchProjectFiles } = useProjectStore();

  const handleUpload = async () => {
    if (!uploadFile) {
      message.error('请选择要上传的文件');
      return;
    }

    if (!uploadFile.name.endsWith('.zip')) {
      message.error('只支持上传ZIP格式的文件');
      return;
    }

    setIsLoading(true);
    try {
      console.log('开始上传文件:', uploadFile.name);
      await uploadProject(projectId, uploadFile, uploadMode);
      message.success('文件上传成功');
      // 重新加载文件列表
      fetchProjectFiles(projectId, '');
      setUploadFile(null);
      onClose();
    } catch (error: any) {
      console.error('文件上传失败:', error);
      message.error(error?.response?.data?.detail || '文件上传失败，请检查文件格式或权限');
    } finally {
      setIsLoading(false);
      setUploadFile(null);
    }
  };

  return (
    <Modal
      title="上传项目文件"
      open={isOpen}
      footer={null}
      onCancel={onClose}
    >
      <div style={{ marginBottom: '16px' }}>
        <Upload.Dragger
          beforeUpload={(file) => {
            if (!file.name.endsWith('.zip')) {
              message.error('只支持上传 ZIP 格式的文件');
              return Upload.LIST_IGNORE;
            }
            setUploadFile(file);
            return false;
          }}
          onRemove={() => setUploadFile(null)}
          fileList={uploadFile ? [{
            uid: '-1',
            name: uploadFile.name,
            status: 'done',
            size: uploadFile.size,
            type: uploadFile.type,
            originFileObj: uploadFile,
          } as UploadFile] : []}
          accept=".zip"
          maxCount={1}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">只支持 ZIP 格式的文件</p>
        </Upload.Dragger>
      </div>
      
      <div style={{ marginBottom: '16px' }}>
        <Radio.Group 
          value={uploadMode} 
          onChange={(e) => setUploadMode(e.target.value)}
        >
          <Radio value="replace">替换所有文件（将删除项目中现有的所有文件）</Radio>
          <Radio value="increment">增量更新（保留项目中现有的文件）</Radio>
        </Radio.Group>
      </div>
      
      <div style={{ textAlign: 'right' }}>
        <Space>
          <Button 
            type="primary" 
            onClick={handleUpload} 
            disabled={!uploadFile}
            loading={isLoading}
          >
            上传文件
          </Button>
          <Button onClick={onClose}>
            取消
          </Button>
        </Space>
      </div>
    </Modal>
  );
};

export default ProjectUploadModal; 