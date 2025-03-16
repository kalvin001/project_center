import React from 'react';
import { Card, Typography, Progress } from 'antd';
import { useProjectStore } from '../../stores/projectStore';

const { Text } = Typography;

const ProjectSyncProgress: React.FC = () => {
  const { syncProgress } = useProjectStore();

  if (syncProgress.status === '') {
    return null;
  }
  
  // 确定进度条状态
  let status: "success" | "exception" | "normal" | "active" | undefined = 'normal';
  if (syncProgress.status === 'complete') {
    status = 'success';
  } else if (syncProgress.status === 'error') {
    status = 'exception';
  }
  
  return (
    <div style={{ marginTop: 16, marginBottom: 16 }}>
      <Card>
        <div style={{ marginBottom: 16 }}>
          <Text strong>同步进度: </Text>
          <Text type={syncProgress.status === 'error' ? 'danger' : undefined}>
            {syncProgress.message}
          </Text>
        </div>
        <Progress 
          percent={syncProgress.progress} 
          status={status}
          strokeColor={{
            from: '#108ee9',
            to: '#87d068',
          }}
        />
      </Card>
    </div>
  );
};

export default ProjectSyncProgress; 