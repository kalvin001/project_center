import React, { useState, useEffect } from 'react';
import { Modal, Input, Button, message } from 'antd';
import { Typography } from 'antd';
import { useProjectStore } from '../../stores/projectStore';

const { Text } = Typography;

interface ProjectIgnoreModalProps {
  projectId: number;
  project: any;
  isOpen: boolean;
  onClose: () => void;
}

const ProjectIgnoreModal: React.FC<ProjectIgnoreModalProps> = ({
  projectId,
  project,
  isOpen,
  onClose
}) => {
  const [ignoreContent, setIgnoreContent] = useState('');
  const { fetchProjectFiles, fetchFileContent, createIgnoreFile, fetchProject } = useProjectStore();

  // 当模态框打开时，尝试加载.ignore文件内容
  useEffect(() => {
    if (isOpen) {
      loadIgnoreFileContent();
    }
  }, [isOpen, projectId]);

  // 加载.ignore文件内容
  const loadIgnoreFileContent = async () => {
    try {
      const ignoreFileExists = project.stats?.ignore_file_exists;
      
      if (ignoreFileExists) {
        // 尝试在文件列表中查找.ignore文件
        const fileList = await fetchProjectFiles(projectId, '');
        const ignoreFile = fileList.files.find(f => f.name === '.ignore');
        
        if (ignoreFile) {
          await fetchFileContent(projectId, ignoreFile.path);
          const fileContent = useProjectStore.getState().currentFileContent;
          if (fileContent) {
            setIgnoreContent(fileContent.content);
          }
        }
      } else {
        // 如果文件不存在，显示默认模板
        setIgnoreContent(`# .ignore文件
# 在此文件中指定要忽略的文件和目录模式
# 支持的格式：
# - 精确匹配: file.txt
# - 目录匹配: node_modules/
# - 扩展名匹配: *.log
# - 通配符: temp*
# 
# 常见示例:
node_modules/
.DS_Store
*.log
*.tmp
.env
.vscode/
dist/
build/
*.pyc
__pycache__/`);
      }
    } catch (error) {
      console.error('加载.ignore文件失败:', error);
      message.error('加载.ignore文件失败');
    }
  };

  // 保存.ignore文件
  const handleSaveIgnoreFile = async () => {
    try {
      await createIgnoreFile(projectId, ignoreContent);
      message.success('保存.ignore文件成功');
      // 刷新项目以获取最新统计
      await fetchProject(projectId);
      onClose();
    } catch (error) {
      console.error('保存.ignore文件失败:', error);
      message.error('保存.ignore文件失败');
    }
  };

  return (
    <Modal
      title={project.stats?.ignore_file_exists ? "编辑.ignore文件" : "创建.ignore文件"}
      open={isOpen}
      onCancel={onClose}
      width={700}
      footer={[
        <Button key="cancel" onClick={onClose}>
          取消
        </Button>,
        <Button 
          key="submit" 
          type="primary" 
          onClick={handleSaveIgnoreFile}
        >
          保存
        </Button>
      ]}
    >
      <div style={{ marginBottom: 16 }}>
        <Text>
          指定要在项目同步和上传时忽略的文件和目录。每行一个模式。
        </Text>
      </div>
      <Input.TextArea
        value={ignoreContent}
        onChange={(e) => setIgnoreContent(e.target.value)}
        style={{ height: 300, fontFamily: 'monospace' }}
        placeholder="# 输入要忽略的文件或目录模式，每行一个"
      />
    </Modal>
  );
};

export default ProjectIgnoreModal; 