import React, { useEffect, useState } from 'react'
import { 
  Table, Button, Space, Tag, Input, Typography, 
  Popconfirm, message, Card, Select 
} from 'antd'
import { 
  PlusOutlined, SearchOutlined, DeleteOutlined, 
  EditOutlined, EyeOutlined, DownloadOutlined 
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useProjectStore } from '../stores/projectStore'

const { Title } = Typography
const { Option } = Select

const ProjectList: React.FC = () => {
  const navigate = useNavigate()
  const { projects, loading, fetchProjects, deleteProject, downloadProject } = useProjectStore()
  
  const [searchText, setSearchText] = useState('')
  const [filterType, setFilterType] = useState<string | null>(null)
  
  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])
  
  // 处理搜索和筛选
  const filteredProjects = projects.filter(project => {
    const matchesSearch = !searchText || 
      project.name.toLowerCase().includes(searchText.toLowerCase()) ||
      (project.description && project.description.toLowerCase().includes(searchText.toLowerCase()))
    
    const matchesType = !filterType || project.project_type === filterType
    
    return matchesSearch && matchesType
  })
  
  // 获取所有项目类型
  const projectTypes = Array.from(new Set(projects.map(p => p.project_type)))
  
  // 处理删除项目
  const handleDelete = async (id: number) => {
    try {
      await deleteProject(id)
    } catch (error) {
      message.error('删除项目失败')
    }
  }
  
  // 处理下载项目
  const handleDownload = async (id: number) => {
    try {
      await downloadProject(id)
    } catch (error) {
      message.error('下载项目失败')
    }
  }
  
  const columns = [
    {
      title: '项目名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: any) => (
        <a onClick={() => navigate(`/projects/${record.id}`)}>{text}</a>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '类型',
      dataIndex: 'project_type',
      key: 'project_type',
      render: (type: string) => (
        <Tag color={
          type === 'frontend' ? 'blue' : 
          type === 'backend' ? 'green' : 
          type === 'fullstack' ? 'purple' : 
          'default'
        }>
          {type}
        </Tag>
      ),
    },
    {
      title: '最后更新',
      dataIndex: 'last_updated',
      key: 'last_updated',
      render: (date: string) => new Date(date).toLocaleString(),
      sorter: (a: any, b: any) => new Date(b.last_updated).getTime() - new Date(a.last_updated).getTime(),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Tag color={active ? 'success' : 'default'}>
          {active ? '活跃' : '非活跃'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space size="small">
          <Button 
            type="text" 
            icon={<EyeOutlined />} 
            onClick={() => navigate(`/projects/${record.id}`)}
          />
          <Button 
            type="text" 
            icon={<EditOutlined />} 
            onClick={() => navigate(`/projects/${record.id}`, { state: { edit: true } })}
          />
          <Button 
            type="text" 
            icon={<DownloadOutlined />} 
            onClick={() => handleDownload(record.id)}
          />
          <Popconfirm
            title="确定要删除这个项目吗？"
            description="删除后将无法恢复，项目文件也会被删除。"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]
  
  return (
    <div>
      <Title level={2}>项目列表</Title>
      
      <Card style={{ marginBottom: 16 }}>
        <Space style={{ marginBottom: 16 }}>
          <Input
            placeholder="搜索项目"
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
            style={{ width: 200 }}
            prefix={<SearchOutlined />}
            allowClear
          />
          
          <Select
            placeholder="项目类型"
            style={{ width: 150 }}
            allowClear
            onChange={(value) => setFilterType(value)}
          >
            {projectTypes.map(type => (
              <Option key={type} value={type}>{type}</Option>
            ))}
          </Select>
          
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={() => navigate('/projects/create')}
          >
            创建项目
          </Button>
        </Space>
        
        <Table
          columns={columns}
          dataSource={filteredProjects.map(p => ({ ...p, key: p.id }))}
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  )
}

export default ProjectList 