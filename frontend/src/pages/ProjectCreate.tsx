import React, { useState } from 'react'
import { Card, Typography, Form, Input, Button, Select, message, Radio, Modal, Tree, Spin } from 'antd'
import { useNavigate } from 'react-router-dom'
import { useProjectStore } from '../stores/projectStore'
import { FolderOutlined, FileOutlined } from '@ant-design/icons'
import axios from 'axios'

const { Title } = Typography
const { Item: FormItem } = Form
const { Option } = Select
const { TextArea } = Input
const { DirectoryTree } = Tree

interface ProjectFormValues {
  name: string
  description?: string
  project_type: string
  repository_url: string
  repository_type: 'git' | 'local'
  tech_stack?: Record<string, any> | null
  is_active?: boolean
}

interface DirectoryItem {
  title: string
  key: string
  path: string
  isLeaf: boolean
  children?: DirectoryItem[]
}

const ProjectCreate: React.FC = () => {
  const navigate = useNavigate()
  const { createProject, loading } = useProjectStore()
  const [form] = Form.useForm()
  const [repositoryType, setRepositoryType] = useState<'git' | 'local'>('local') // 默认为本地文件
  const [folderPickerVisible, setFolderPickerVisible] = useState(false)
  const [directories, setDirectories] = useState<DirectoryItem[]>([])
  const [selectedPath, setSelectedPath] = useState('')
  const [loadingDirectories, setLoadingDirectories] = useState(false)
  
  // 根目录列表
  const rootDirectories = ['C:\\', 'D:\\']

  // 加载目录内容
  const loadDirectories = async (path: string) => {
    setLoadingDirectories(true)
    try {
      // 这里应该调用后端API获取目录列表
      // 由于安全限制，前端不能直接访问文件系统
      // 假设有API: /api/files/directories?path=xxx
      const token = localStorage.getItem('token')
      const response = await axios.get(`http://localhost:8011/api/files/directories?path=${encodeURIComponent(path)}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      return response.data
    } catch (error) {
      console.error('加载目录失败:', error)
      message.error('加载目录失败')
      return []
    } finally {
      setLoadingDirectories(false)
    }
  }
  
  // 打开目录选择对话框
  const openFolderPicker = async () => {
    setFolderPickerVisible(true)
    if (directories.length === 0) {
      try {
        const roots = await Promise.all(
          rootDirectories.map(async (dir) => {
            const children = await loadDirectories(dir)
            return {
              title: dir,
              key: dir,
              path: dir,
              isLeaf: false,
              children
            }
          })
        )
        setDirectories(roots)
      } catch (error) {
        console.error('加载根目录失败:', error)
      }
    }
  }
  
  // 处理目录展开事件
  const onLoadData = async ({ key, children, path }: any) => {
    if (children) return
    
    const items = await loadDirectories(path)
    const newDirectories = [...directories]
    
    // 更新目录树
    const updateTreeNodes = (nodes: DirectoryItem[], targetKey: string, items: DirectoryItem[]): DirectoryItem[] => {
      return nodes.map(node => {
        if (node.key === targetKey) {
          return {
            ...node,
            children: items
          }
        }
        if (node.children) {
          return {
            ...node,
            children: updateTreeNodes(node.children, targetKey, items)
          }
        }
        return node
      })
    }
    
    setDirectories(updateTreeNodes(newDirectories, key, items))
  }
  
  // 选择目录
  const selectFolder = (selectedKeys: React.Key[], info: any) => {
    if (selectedKeys.length > 0) {
      setSelectedPath(info.node.path)
    }
  }
  
  // 确认选择目录
  const confirmFolderSelection = () => {
    if (selectedPath) {
      form.setFieldValue('repository_url', selectedPath)
      setFolderPickerVisible(false)
    } else {
      message.warning('请选择一个文件夹')
    }
  }
  
  const handleCreateProject = async (values: ProjectFormValues) => {
    try {
      // 补充默认值
      const projectData = {
        ...values,
        tech_stack: values.tech_stack || null,
        is_active: values.is_active !== false // 默认为true
      }
      
      console.log('创建项目:', projectData)
      const projectId = await createProject(projectData)
      message.success('项目创建成功')
      // 跳转到项目详情页
      navigate(`/projects/${projectId}`)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '创建项目失败')
    }
  }
  
  return (
    <Card>
      <Title level={2}>创建新项目</Title>
      
      <Form
        form={form}
        layout="vertical"
        onFinish={handleCreateProject}
        initialValues={{
          project_type: 'fullstack',
          repository_type: 'local' // 默认为本地文件
        }}
      >
        <FormItem
          name="name"
          label="项目名称"
          rules={[{ required: true, message: '请输入项目名称' }]}
        >
          <Input placeholder="输入项目名称" />
        </FormItem>
        
        <FormItem
          name="description"
          label="项目描述"
        >
          <TextArea rows={4} placeholder="输入项目描述(可选)" />
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
          name="repository_type"
          label="仓库类型"
          rules={[{ required: true, message: '请选择仓库类型' }]}
        >
          <Radio.Group 
            onChange={(e) => setRepositoryType(e.target.value)}
            value={repositoryType}
          >
            <Radio value="git">Git 仓库</Radio>
            <Radio value="local">本地文件夹</Radio>
          </Radio.Group>
        </FormItem>
        
        <FormItem
          name="repository_url"
          label={repositoryType === 'git' ? "Git 仓库地址" : "本地文件夹路径"}
          rules={[{ required: true, message: repositoryType === 'git' ? '请输入Git仓库地址' : '请输入本地文件夹路径' }]}
        >
          <Input 
            placeholder={repositoryType === 'git' 
              ? "如: https://github.com/username/repo" 
              : "如: D:\\Projects\\MyProject"}
            addonAfter={
              repositoryType === 'local' ? (
                <Button type="link" size="small" onClick={openFolderPicker}>
                  浏览...
                </Button>
              ) : null
            }
          />
        </FormItem>
        
        <FormItem>
          <Button type="primary" htmlType="submit" loading={loading}>
            创建项目
          </Button>
          <Button 
            style={{ marginLeft: 8 }} 
            onClick={() => navigate('/projects')}
          >
            取消
          </Button>
        </FormItem>
      </Form>
      
      {/* 文件夹选择对话框 */}
      <Modal
        title="选择本地文件夹"
        open={folderPickerVisible}
        onOk={confirmFolderSelection}
        onCancel={() => setFolderPickerVisible(false)}
        width={600}
      >
        {loadingDirectories ? (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Spin tip="加载目录..." />
          </div>
        ) : (
          <DirectoryTree
            treeData={directories}
            loadData={onLoadData}
            onSelect={selectFolder}
            height={400}
          />
        )}
      </Modal>
    </Card>
  )
}

export default ProjectCreate 