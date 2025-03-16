import React, { useEffect, useState } from 'react'
import { 
  Card, Typography, Button, Breadcrumb, Tabs, Spin,
  Space, Tag
} from 'antd'
import { 
  EditOutlined, DeleteOutlined, DownloadOutlined,
  SyncOutlined, HomeOutlined
} from '@ant-design/icons'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useProjectStore } from '../stores/projectStore'

// 导入子组件
import ProjectInfoTab from '../components/project/ProjectInfoTab'
import ProjectFileBrowser from '../components/project/ProjectFileBrowser'
import ProjectDeploymentTab from '../components/project/ProjectDeploymentTab'
import ProjectSyncProgress from '../components/project/ProjectSyncProgress'
import ProjectEditForm from '../components/project/ProjectEditForm'
import ProjectGitModal from '../components/project/ProjectGitModal'
import ProjectUploadModal from '../components/project/ProjectUploadModal'
import ProjectIgnoreModal from '../components/project/ProjectIgnoreModal'

const { TabPane } = Tabs

const ProjectDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const projectId = parseInt(id || '0')
  
  const { 
    currentProject, loading: storeLoading, 
    fetchProject, deleteProject, downloadProject,
    syncProject
  } = useProjectStore()
  
  const [isEditing, setIsEditing] = useState(false)
  const [activeTab, setActiveTab] = useState('info')
  const [isGitModalOpen, setIsGitModalOpen] = useState(false)
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [isIgnoreModalOpen, setIsIgnoreModalOpen] = useState(false)
  
  // 添加调试日志
  useEffect(() => {
    console.log('项目详情页渲染状态:', {
      projectId,
      currentProject,
      loading: storeLoading,
      activeTab
    });
  }, [projectId, currentProject, storeLoading, activeTab]);
  
  // 修改useEffect依赖，添加强制刷新逻辑
  useEffect(() => {
    if (projectId) {
      console.log(`项目ID变化为${projectId}，重新获取项目数据`);
      // 先清空当前项目数据，防止显示旧数据
      useProjectStore.setState({ currentProject: null });
      // 获取新项目数据
      fetchProject(projectId);
    }
  }, [projectId]); // 只依赖projectId，移除fetchProject依赖
  
  if (storeLoading && !currentProject) {
    return (
      <div style={{ textAlign: 'center', margin: '50px 0' }}>
        <Spin size="large" />
      </div>
    )
  }
  
  if (!currentProject) {
    return (
      <Card>
        <Typography.Title level={4}>项目不存在或已被删除</Typography.Title>
        <Button type="primary" onClick={() => navigate('/projects')}>
          返回项目列表
        </Button>
      </Card>
    )
  }
  
  // 处理项目删除
  const handleDeleteProject = async () => {
    try {
      await deleteProject(projectId)
      navigate('/projects')
    } catch (error) {
      console.error('删除项目失败:', error)
    }
  }
  
  // 处理项目下载
  const handleDownload = async () => {
    try {
      await downloadProject(projectId)
    } catch (error) {
      console.error('下载项目文件失败:', error)
    }
  }
  
  // 处理项目同步
  const handleSyncProject = async () => {
    try {
      await syncProject(projectId);
    } catch (error) {
      console.error('同步失败:', error);
    }
  }
  
  const handleTabChange = (key: string) => {
    setActiveTab(key)
  }

  // 编辑模式
  if (isEditing) {
    return (
      <ProjectEditForm 
        project={currentProject} 
        projectId={projectId}
        onCancel={() => setIsEditing(false)}
      />
    )
  }
  
  return (
    <div>
      <Breadcrumb style={{ marginBottom: 16 }}>
        <Breadcrumb.Item>
          <Link to="/projects"><HomeOutlined /> 项目列表</Link>
        </Breadcrumb.Item>
        <Breadcrumb.Item>{currentProject.name}</Breadcrumb.Item>
      </Breadcrumb>
      
      {/* 在项目信息卡片上方显示同步进度 */}
      <ProjectSyncProgress />
      
      <Card
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Space>
              <Typography.Title level={4} style={{ margin: 0 }}>{currentProject.name}</Typography.Title>
              <Tag color={
                currentProject.project_type === 'frontend' ? 'blue' : 
                currentProject.project_type === 'backend' ? 'green' : 
                currentProject.project_type === 'fullstack' ? 'purple' : 
                'default'
              }>
                {currentProject.project_type}
              </Tag>
              <Tag color={currentProject.is_active ? 'success' : 'default'}>
                {currentProject.is_active ? '活跃' : '非活跃'}
              </Tag>
            </Space>
            <Button
              type="primary"
              icon={<EditOutlined />}
              onClick={() => setIsEditing(true)}
              style={{ marginRight: 10 }}
            >
              编辑项目
            </Button>
          </div>
        }
        extra={
          <Space>
            <Button 
              icon={<SyncOutlined />} 
              onClick={handleSyncProject}
            >
              同步项目
            </Button>
            <Button 
              icon={<DownloadOutlined />} 
              onClick={handleDownload}
            >
              下载
            </Button>
            <Button 
              danger 
              icon={<DeleteOutlined />} 
              onClick={handleDeleteProject}
            >
              删除
            </Button>
          </Space>
        }
      >
        <Tabs activeKey={activeTab} onChange={handleTabChange}>
          <TabPane tab="项目信息" key="info">
            {activeTab === 'info' && (
              <ProjectInfoTab 
                project={currentProject} 
                onOpenIgnoreModal={() => setIsIgnoreModalOpen(true)}
              />
            )}
          </TabPane>
          
          <TabPane tab="文件浏览" key="files">
            {activeTab === 'files' && (
              <ProjectFileBrowser 
                projectId={projectId}
                onOpenGitModal={() => setIsGitModalOpen(true)}
                onOpenUploadModal={() => setIsUploadModalOpen(true)}
              />
            )}
          </TabPane>
          
          <TabPane tab="部署管理" key="deployment">
            {activeTab === 'deployment' && (
              <ProjectDeploymentTab projectId={projectId} />
            )}
          </TabPane>
        </Tabs>
      </Card>
      
      {/* 子组件模态框 */}
      <ProjectGitModal
        projectId={projectId}
        isOpen={isGitModalOpen}
        onClose={() => setIsGitModalOpen(false)}
      />
      
      <ProjectUploadModal
        projectId={projectId}
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
      />
      
      <ProjectIgnoreModal
        projectId={projectId}
        project={currentProject}
        isOpen={isIgnoreModalOpen}
        onClose={() => setIsIgnoreModalOpen(false)}
      />
    </div>
  )
}

export default ProjectDetail 