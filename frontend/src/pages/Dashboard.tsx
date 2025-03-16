import React, { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, List, Typography, Spin, Progress, Tabs, Badge, Table, Tag, Button } from 'antd'
import { 
  ProjectOutlined, 
  CloudServerOutlined, 
  ClockCircleOutlined, 
  DeploymentUnitOutlined, 
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LoadingOutlined,
  EyeOutlined,
  LineChartOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useProjectStore } from '../stores/projectStore'
import { useAuthStore } from '../stores/authStore'
import api from '../utils/api'
import { Machine, Deployment, Project } from '../types'

const { Title, Text } = Typography
const { TabPane } = Tabs

const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  const { projects, loading: projectsLoading, fetchProjects } = useProjectStore()
  const { user } = useAuthStore()
  const [machines, setMachines] = useState<Machine[]>([])
  const [deployments, setDeployments] = useState<Deployment[]>([])
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    // 获取项目数据
    fetchProjects()
    
    // 获取机器数据
    const fetchMachines = async () => {
      try {
        const response = await api.get('/machines/')
        setMachines(response.data)
      } catch (error) {
        console.error('获取机器列表失败:', error)
      }
    }
    
    // 获取部署数据
    const fetchDeployments = async () => {
      try {
        const response = await api.get('/deployments/')
        setDeployments(response.data)
      } catch (error) {
        console.error('获取部署列表失败:', error)
      }
    }
    
    // 并行获取所有数据
    Promise.all([
      fetchProjects(),
      fetchMachines(),
      fetchDeployments()
    ]).finally(() => {
      setLoading(false)
    })
  }, [fetchProjects])
  
  // 获取最近更新的项目
  const recentProjects = [...projects]
    .sort((a, b) => new Date(b.last_updated).getTime() - new Date(a.last_updated).getTime())
    .slice(0, 5)
  
  // 获取最近的部署
  const recentDeployments = [...deployments]
    .sort((a, b) => new Date(b.deployed_at).getTime() - new Date(a.deployed_at).getTime())
    .slice(0, 5)
  
  // 项目统计数据
  const projectStats = {
    total: projects.length,
    active: projects.filter(p => p.is_active).length,
    inactive: projects.filter(p => !p.is_active).length
  }
  
  // 机器统计数据
  const machineStats = {
    total: machines.length,
    online: machines.filter(m => m.is_online).length,
    offline: machines.filter(m => !m.is_online).length
  }
  
  // 部署统计数据
  const deploymentStats = {
    total: deployments.length,
    success: deployments.filter(d => d.status === 'success').length,
    failed: deployments.filter(d => d.status === 'failed').length,
    pending: deployments.filter(d => d.status === 'pending').length
  }
  
  // 按类型统计项目数量
  const projectTypeCount: Record<string, number> = {}
  projects.forEach(project => {
    const type = project.project_type || 'other'
    projectTypeCount[type] = (projectTypeCount[type] || 0) + 1
  })
  
  // 渲染部署状态标签
  const renderDeploymentStatus = (status: string) => {
    switch(status) {
      case 'success':
        return <Tag color="success">成功</Tag>
      case 'failed':
        return <Tag color="error">失败</Tag>
      case 'pending':
        return <Tag color="processing">进行中</Tag>
      case 'running':
        return <Tag color="blue">运行中</Tag>
      case 'stopped':
        return <Tag color="default">已停止</Tag>
      default:
        return <Tag>{status}</Tag>
    }
  }

  // 部署表格列
  const deploymentColumns = [
    {
      title: '项目',
      dataIndex: 'project',
      key: 'project',
      render: (project: Project) => project?.name || '-'
    },
    {
      title: '环境',
      dataIndex: 'environment',
      key: 'environment'
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => renderDeploymentStatus(status)
    },
    {
      title: '部署时间',
      dataIndex: 'deployed_at',
      key: 'deployed_at',
      render: (time: string) => new Date(time).toLocaleString()
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Deployment) => (
        <Button 
          type="link" 
          icon={<EyeOutlined />} 
          onClick={() => navigate(`/deployments/${record.id}`)}
        >
          查看
        </Button>
      )
    }
  ]
  
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <Title level={2}>首页</Title>
          <Text>欢迎回来，{user?.username || '用户'}！</Text>
        </div>
        <Button 
          type="primary" 
          icon={<LineChartOutlined />}
          onClick={() => navigate('/logs')}
        >
          监控详情
        </Button>
      </div>
      
      {loading ? (
        <div style={{ textAlign: 'center', margin: '100px 0' }}>
          <Spin size="large" />
        </div>
      ) : (
        <>
          {/* 统计卡片区域 */}
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12} md={8} lg={6}>
              <Card hoverable onClick={() => navigate('/projects')} className="stat-card">
                <Statistic
                  title="项目总数"
                  value={projectStats.total}
                  prefix={<ProjectOutlined />}
                  suffix={
                    <div style={{ fontSize: '14px', marginLeft: '8px' }}>
                      <Badge status="success" text={`活跃: ${projectStats.active}`} />
                      <br />
                      <Badge status="default" text={`非活跃: ${projectStats.inactive}`} />
                    </div>
                  }
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={8} lg={6}>
              <Card hoverable onClick={() => navigate('/machines')} className="stat-card">
                <Statistic
                  title="机器总数"
                  value={machineStats.total}
                  prefix={<CloudServerOutlined />}
                  suffix={
                    <div style={{ fontSize: '14px', marginLeft: '8px' }}>
                      <Badge status="success" text={`在线: ${machineStats.online}`} />
                      <br />
                      <Badge status="error" text={`离线: ${machineStats.offline}`} />
                    </div>
                  }
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={8} lg={6}>
              <Card hoverable onClick={() => navigate('/deployment')} className="stat-card">
                <Statistic
                  title="部署总数"
                  value={deploymentStats.total}
                  prefix={<DeploymentUnitOutlined />}
                  suffix={
                    <div style={{ fontSize: '14px', marginLeft: '8px' }}>
                      <Badge status="success" text={`成功: ${deploymentStats.success}`} />
                      <br />
                      <Badge status="error" text={`失败: ${deploymentStats.failed}`} />
                    </div>
                  }
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={8} lg={6}>
              <Card hoverable className="stat-card">
                <Statistic
                  title="资源利用率"
                  value={machines.length > 0 ? 
                    Math.round(machines.filter(m => m.is_online).length / machines.length * 100) : 0
                  }
                  suffix="%"
                  prefix={<LineChartOutlined />}
                  valueStyle={{ color: '#3f8600' }}
                />
                <Progress 
                  percent={machines.length > 0 ? 
                    Math.round(machines.filter(m => m.is_online).length / machines.length * 100) : 0
                  } 
                  showInfo={false} 
                  status="active" 
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                />
              </Card>
            </Col>
          </Row>
          
          {/* 详细数据展示区域 */}
          <Tabs defaultActiveKey="recent" className="dashboard-tabs">
            <TabPane tab="最近活动" key="recent">
              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Card 
                    title="最近更新的项目" 
                    extra={<Button type="link" onClick={() => navigate('/projects')}>查看全部</Button>}
                  >
                    <List
                      dataSource={recentProjects}
                      renderItem={item => (
                        <List.Item
                          key={item.id}
                          actions={[
                            <Button 
                              key="view" 
                              type="link" 
                              onClick={() => navigate(`/projects/${item.id}`)}
                            >
                              查看
                            </Button>,
                          ]}
                        >
                          <List.Item.Meta
                            title={item.name}
                            description={`${item.description || '无描述'} | 类型: ${item.project_type}`}
                          />
                          <div>更新于: {new Date(item.last_updated).toLocaleString()}</div>
                        </List.Item>
                      )}
                      locale={{ emptyText: '暂无项目数据' }}
                    />
                  </Card>
                </Col>
                <Col xs={24} md={12}>
                  <Card 
                    title="最近部署记录" 
                    extra={<Button type="link" onClick={() => navigate('/deployment')}>查看全部</Button>}
                  >
                    <List
                      dataSource={recentDeployments}
                      renderItem={item => (
                        <List.Item
                          key={item.id}
                          actions={[
                            <Button 
                              key="view" 
                              type="link" 
                              onClick={() => navigate(`/deployments/${item.id}`)}
                            >
                              查看
                            </Button>,
                          ]}
                        >
                          <List.Item.Meta
                            title={item.project?.name || `项目ID: ${item.project_id}`}
                            description={`环境: ${item.environment} | 路径: ${item.deploy_path}`}
                          />
                          {renderDeploymentStatus(item.status)}
                        </List.Item>
                      )}
                      locale={{ emptyText: '暂无部署记录' }}
                    />
                  </Card>
                </Col>
              </Row>
            </TabPane>
            <TabPane tab="机器状态" key="machines">
              <Card>
                <Row gutter={16}>
                  {machines.slice(0, 6).map(machine => (
                    <Col xs={24} sm={12} md={8} key={machine.id} style={{ marginBottom: 16 }}>
                      <Card 
                        hoverable 
                        title={machine.name}
                        extra={
                          <Badge 
                            status={machine.is_online ? "success" : "error"} 
                            text={machine.is_online ? "在线" : "离线"} 
                          />
                        }
                        onClick={() => navigate(`/machines/${machine.id}`)}
                      >
                        <p><strong>主机:</strong> {machine.host}</p>
                        {machine.is_online && (
                          <>
                            <Row gutter={16}>
                              <Col span={12}>
                                <Statistic 
                                  title="CPU" 
                                  value={machine.cpu_usage || '0%'} 
                                  valueStyle={{ fontSize: '14px' }} 
                                />
                              </Col>
                              <Col span={12}>
                                <Statistic 
                                  title="内存" 
                                  value={machine.memory_usage || '0%'} 
                                  valueStyle={{ fontSize: '14px' }} 
                                />
                              </Col>
                            </Row>
                            <Progress 
                              percent={parseInt(machine.cpu_usage || '0')} 
                              size="small" 
                              status="active"
                              showInfo={false}
                              style={{ marginTop: 8 }}
                            />
                          </>
                        )}
                      </Card>
                    </Col>
                  ))}
                </Row>
                {machines.length > 6 && (
                  <div style={{ textAlign: 'center', marginTop: 16 }}>
                    <Button type="primary" onClick={() => navigate('/machines')}>
                      查看全部机器
                    </Button>
                  </div>
                )}
              </Card>
            </TabPane>
            <TabPane tab="部署情况" key="deployments">
              <Card>
                <Table 
                  dataSource={deployments.slice(0, 10)} 
                  columns={deploymentColumns} 
                  rowKey="id"
                  pagination={false}
                  size="middle"
                />
                {deployments.length > 10 && (
                  <div style={{ textAlign: 'right', marginTop: 16 }}>
                    <Button type="primary" onClick={() => navigate('/deployment')}>
                      查看全部部署
                    </Button>
                  </div>
                )}
              </Card>
            </TabPane>
          </Tabs>
        </>
      )}
      
      {/* 添加CSS样式 */}
      <style>{`
        .stat-card {
          transition: all 0.3s;
        }
        .stat-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .dashboard-tabs {
          margin-top: 24px;
        }
        .ant-table-wrapper {
          background: white;
        }
      `}</style>
    </div>
  )
}

export default Dashboard 