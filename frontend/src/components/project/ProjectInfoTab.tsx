import React from 'react'
import { 
  Descriptions, Tag, Card, Row, Col, Button,
  Statistic
} from 'antd'
import { FileExclamationOutlined } from '@ant-design/icons'

interface ProjectInfoTabProps {
  project: any; // 这里可以替换为具体的项目类型
  onOpenIgnoreModal: () => void;
}

const ProjectInfoTab: React.FC<ProjectInfoTabProps> = ({ 
  project, 
  onOpenIgnoreModal 
}) => {
  return (
    <div>
      <Descriptions bordered column={2}>
        <Descriptions.Item label="项目类型">
          {project.project_type}
        </Descriptions.Item>
        <Descriptions.Item label="创建时间">
          {new Date(project.created_at).toLocaleString()}
        </Descriptions.Item>
        <Descriptions.Item label="最后更新">
          {new Date(project.last_updated).toLocaleString()}
        </Descriptions.Item>
        <Descriptions.Item label="状态">
          <Tag color={project.is_active ? 'green' : 'red'}>
            {project.is_active ? '活跃' : '非活跃'}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="仓库URL" span={2}>
          {project.repository_url || '无'}
        </Descriptions.Item>
        <Descriptions.Item label="项目描述" span={2}>
          {project.description || '无描述'}
        </Descriptions.Item>
      </Descriptions>
      
      {/* 项目统计信息卡片 */}
      {project.stats && (
        <Card title="项目统计" style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col span={6}>
              <Statistic 
                title="文件数量" 
                value={project.stats.file_count} 
                suffix="个文件"
              />
            </Col>
            <Col span={6}>
              <Statistic 
                title="项目大小" 
                value={project.stats.total_size_human}
              />
            </Col>
            <Col span={6}>
              <Statistic 
                title="代码行数" 
                value={project.stats.code_lines} 
                suffix="行"
              />
            </Col>
            <Col span={6}>
              <Button 
                icon={<FileExclamationOutlined />}
                onClick={onOpenIgnoreModal}
              >
                {project.stats?.ignore_file_exists ? '编辑忽略文件' : '创建忽略文件'}
              </Button>
            </Col>
          </Row>
        </Card>
      )}
    </div>
  );
};

export default ProjectInfoTab; 