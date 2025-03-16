import React, { useState, useEffect } from 'react';
import { 
  Card, Row, Col, Statistic, Progress, Spin, Empty, Button, 
  Divider, Typography, Alert, Result 
} from 'antd';
import { 
  ReloadOutlined, DashboardOutlined, WarningOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import api from '../../utils/api';
import { useStore } from '../../stores';
import { MachineMetrics } from '../../types/machine';
import { formatBytes } from '../../utils/formatUtils';

const { Title, Text, Paragraph } = Typography;

interface MachineMonitorProps {
  machineId: number;
  onPasswordRequired?: () => void;
}

const MachineMonitor: React.FC<MachineMonitorProps> = ({ machineId, onPasswordRequired }) => {
  const [metrics, setMetrics] = useState<MachineMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [apiNotImplemented, setApiNotImplemented] = useState<boolean>(false);
  const { token } = useStore();

  const fetchMetrics = async () => {
    if (!machineId) return;
    
    try {
      setLoading(true);
      setError(null);
      setApiNotImplemented(false);
      
      const response = await api.get(`/machines/${machineId}/metrics`);
      
      setMetrics(response.data);
    } catch (error: any) {
      console.error('获取监控指标失败:', error);
      
      // 检查是否是API未实现的错误
      if (error.response?.status === 404 && 
          error.response?.data?.detail === "Not Found") {
        setApiNotImplemented(true);
      } else {
        setError(error.response?.data?.detail || '获取监控指标失败');
        
        // 如果是认证错误，可能需要密码
        if (error.response?.status === 401 && onPasswordRequired) {
          onPasswordRequired();
        }
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    
    // 设置自动刷新，每30秒
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, [machineId]);

  if (loading && !metrics && !apiNotImplemented) {
    return (
      <div style={{ textAlign: 'center', padding: '50px 0' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>加载监控数据...</div>
      </div>
    );
  }

  if (apiNotImplemented) {
    return (
      <Result
        icon={<ExclamationCircleOutlined />}
        status="warning"
        title="监控功能尚未实现"
        subTitle="后端API接口 /api/machines/{id}/metrics 尚未实现"
        extra={
          <div>
            <Paragraph>
              需要在后端实现以下功能：
            </Paragraph>
            <ul>
              <li>创建监控数据收集接口</li>
              <li>实现CPU、内存、磁盘等系统资源监控</li>
              <li>实现网络流量监控</li>
              <li>实现进程监控</li>
            </ul>
            <Button 
              type="primary" 
              icon={<ReloadOutlined />} 
              onClick={fetchMetrics}
            >
              重试
            </Button>
          </div>
        }
      />
    );
  }

  if (error) {
    return (
      <Card>
        <Alert
          message="获取监控数据失败"
          description={error}
          type="error"
          showIcon
          action={
            <Button 
              type="primary" 
              size="small" 
              icon={<ReloadOutlined />} 
              onClick={fetchMetrics}
            >
              重试
            </Button>
          }
        />
      </Card>
    );
  }

  if (!metrics) {
    return (
      <Card>
        <Empty 
          description="暂无监控数据" 
          image={Empty.PRESENTED_IMAGE_SIMPLE} 
        />
      </Card>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4}>
          <DashboardOutlined /> 实时监控
        </Title>
        <Button 
          icon={<ReloadOutlined />} 
          onClick={fetchMetrics}
          loading={loading}
        >
          刷新
        </Button>
      </div>
      
      <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>
        最后更新: {new Date(metrics.timestamp).toLocaleString('zh-CN')}
      </Text>
      
      <Row gutter={[16, 16]}>
        {/* CPU 卡片 */}
        <Col xs={24} sm={12} lg={8}>
          <Card title="CPU" bordered={false}>
            <Progress 
              type="dashboard" 
              percent={Math.round(metrics.cpu.usage_percent)} 
              status={metrics.cpu.usage_percent > 90 ? "exception" : "normal"}
            />
            <Divider />
            <Row gutter={16}>
              <Col span={12}>
                <Statistic title="核心数" value={metrics.cpu.cores} />
              </Col>
              <Col span={12}>
                <Statistic 
                  title="平均负载" 
                  value={metrics.cpu.load_avg[0].toFixed(2)} 
                  suffix={`/${metrics.cpu.cores}`}
                />
              </Col>
            </Row>
          </Card>
        </Col>
        
        {/* 内存卡片 */}
        <Col xs={24} sm={12} lg={8}>
          <Card title="内存" bordered={false}>
            <Progress 
              type="dashboard" 
              percent={Math.round(metrics.memory.usage_percent)} 
              status={metrics.memory.usage_percent > 90 ? "exception" : "normal"}
            />
            <Divider />
            <Row gutter={16}>
              <Col span={12}>
                <Statistic 
                  title="已用" 
                  value={formatBytes(metrics.memory.used)} 
                />
              </Col>
              <Col span={12}>
                <Statistic 
                  title="总计" 
                  value={formatBytes(metrics.memory.total)} 
                />
              </Col>
            </Row>
          </Card>
        </Col>
        
        {/* 磁盘卡片 */}
        <Col xs={24} sm={12} lg={8}>
          <Card title="磁盘" bordered={false}>
            <Progress 
              type="dashboard" 
              percent={Math.round(metrics.disk.usage_percent)} 
              status={metrics.disk.usage_percent > 90 ? "exception" : "normal"}
            />
            <Divider />
            <Row gutter={16}>
              <Col span={12}>
                <Statistic 
                  title="已用" 
                  value={formatBytes(metrics.disk.used)} 
                />
              </Col>
              <Col span={12}>
                <Statistic 
                  title="总计" 
                  value={formatBytes(metrics.disk.total)} 
                />
              </Col>
            </Row>
          </Card>
        </Col>
        
        {/* 网络卡片 */}
        <Col xs={24} sm={12} lg={12}>
          <Card title="网络" bordered={false}>
            <Row gutter={16}>
              <Col span={12}>
                <Statistic 
                  title="接收" 
                  value={formatBytes(metrics.network.rx_bytes)} 
                  suffix="/s"
                />
              </Col>
              <Col span={12}>
                <Statistic 
                  title="发送" 
                  value={formatBytes(metrics.network.tx_bytes)} 
                  suffix="/s"
                />
              </Col>
            </Row>
            <Divider />
            <Row gutter={16}>
              <Col span={12}>
                <Statistic 
                  title="接收包" 
                  value={metrics.network.rx_packets} 
                  suffix="/s"
                />
              </Col>
              <Col span={12}>
                <Statistic 
                  title="发送包" 
                  value={metrics.network.tx_packets} 
                  suffix="/s"
                />
              </Col>
            </Row>
          </Card>
        </Col>
        
        {/* 进程卡片 */}
        <Col xs={24} sm={12} lg={12}>
          <Card title="进程" bordered={false}>
            <Row gutter={16}>
              <Col span={8}>
                <Statistic 
                  title="总计" 
                  value={metrics.processes.total} 
                />
              </Col>
              <Col span={8}>
                <Statistic 
                  title="运行中" 
                  value={metrics.processes.running} 
                />
              </Col>
              <Col span={8}>
                <Statistic 
                  title="休眠" 
                  value={metrics.processes.sleeping} 
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default MachineMonitor; 