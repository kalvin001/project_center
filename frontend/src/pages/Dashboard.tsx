import React, { useEffect } from 'react'
import { Row, Col, Card, Statistic, List, Typography, Spin } from 'antd'
import { ProjectOutlined, CloudServerOutlined, ClockCircleOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useProjectStore } from '../stores/projectStore'
import { useAuthStore } from '../stores/authStore'

const { Title, Text } = Typography

const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  const { projects, loading, fetchProjects } = useProjectStore()
  const { user } = useAuthStore()
  
  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])
  
  // 获取最近更新的项目
  const recentProjects = [...projects]
    .sort((a, b) => new Date(b.last_updated).getTime() - new Date(a.last_updated).getTime())
    .slice(0, 5)
  
  // 按类型统计项目数量
  const projectTypeCount: Record<string, number> = {}
  projects.forEach(project => {
    const type = project.project_type || 'other'
    projectTypeCount[type] = (projectTypeCount[type] || 0) + 1
  })
  
  return (
    <div>
      <Title level={2}>仪表盘</Title>
      <Text>欢迎回来，{user?.username || '用户'}！</Text>
      
      {loading ? (
        <div style={{ textAlign: 'center', margin: '50px 0' }}>
          <Spin size="large" />
        </div>
      ) : (
        <>
          <Row gutter={16} style={{ marginTop: 24 }}>
            <Col span={8}>
              <Card>
                <Statistic
                  title="项目总数"
                  value={projects.length}
                  prefix={<ProjectOutlined />}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="活跃项目"
                  value={projects.filter(p => p.is_active).length}
                  prefix={<CloudServerOutlined />}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="最近更新"
                  value={recentProjects.length > 0 ? recentProjects[0].name : '无'}
                  prefix={<ClockCircleOutlined />}
                />
              </Card>
            </Col>
          </Row>
          
          <Card title="最近更新的项目" style={{ marginTop: 24 }}>
            <List
              dataSource={recentProjects}
              renderItem={item => (
                <List.Item
                  key={item.id}
                  actions={[
                    <a key="view" onClick={() => navigate(`/projects/${item.id}`)}>
                      查看
                    </a>,
                  ]}
                >
                  <List.Item.Meta
                    title={item.name}
                    description={`${item.description || '无描述'} | 类型: ${item.project_type}`}
                  />
                  <div>更新于: {new Date(item.last_updated).toLocaleString()}</div>
                </List.Item>
              )}
            />
          </Card>
          
          <Card title="项目类型统计" style={{ marginTop: 24 }}>
            <List
              dataSource={Object.entries(projectTypeCount)}
              renderItem={([type, count]) => (
                <List.Item key={type}>
                  <List.Item.Meta
                    title={type}
                    description={`共 ${count} 个项目`}
                  />
                </List.Item>
              )}
            />
          </Card>
        </>
      )}
    </div>
  )
}

export default Dashboard 