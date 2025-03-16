import React, { useState, useEffect, useRef } from 'react';
import { 
  Table, Card, Button, Space, Tag, Input, Select, 
  DatePicker, Form, Drawer, Typography, Divider, message, Tooltip
} from 'antd';
import { SearchOutlined, ReloadOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { logApi } from '../utils/api';
import { Log, LogFilter, LogStatusColors, LogCategoryMap, LogOperationMap } from '../types/log';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

// 扩展LogFilter类型，添加dateRange字段
interface ExtendedLogFilter extends LogFilter {
  dateRange?: any;
}

const LogsPage: React.FC = () => {
  const [logs, setLogs] = useState<Log[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentLog, setCurrentLog] = useState<Log | null>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
  });
  
  const [form] = Form.useForm();
  const formRef = useRef(null);
  
  // 加载日志数据
  const fetchLogs = async (filter: ExtendedLogFilter = {}) => {
    try {
      setLoading(true);
      
      const params = {
        ...filter,
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
      };
      
      const [data, count] = await Promise.all([
        logApi.getLogs(params),
        logApi.getLogsCount(filter)
      ]);
      
      setLogs(data);
      setTotal(count);
    } catch (error) {
      console.error('获取日志失败:', error);
      message.error('获取日志失败');
    } finally {
      setLoading(false);
    }
  };
  
  // 初始加载
  useEffect(() => {
    fetchLogs();
  }, [pagination.current, pagination.pageSize]);
  
  // 处理表格分页变化
  const handleTableChange = (pagination: any) => {
    setPagination(pagination);
  };
  
  // 处理过滤表单提交
  const handleFilterSubmit = (values: any) => {
    const filter: ExtendedLogFilter = { ...values };
    
    // 处理日期范围
    if (values.dateRange && values.dateRange.length === 2) {
      filter.start_date = values.dateRange[0].format('YYYY-MM-DD');
      filter.end_date = values.dateRange[1].format('YYYY-MM-DD');
      delete filter.dateRange;
    }
    
    // 重置分页到第一页
    setPagination({
      ...pagination,
      current: 1,
    });
    
    fetchLogs(filter);
  };
  
  // 重置过滤条件
  const handleReset = () => {
    form.resetFields();
    setPagination({
      ...pagination,
      current: 1,
    });
    fetchLogs();
  };
  
  // 查看日志详情
  const handleViewLog = async (record: Log) => {
    try {
      setLoading(true);
      const data = await logApi.getLog(record.id);
      setCurrentLog(data);
      setDrawerVisible(true);
    } catch (error) {
      console.error('获取日志详情失败:', error);
      message.error('获取日志详情失败');
    } finally {
      setLoading(false);
    }
  };
  
  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      render: (text: string) => {
        const label = (LogCategoryMap as Record<string, string>)[text];
        return label || text;
      },
      width: 100,
    },
    {
      title: '操作类型',
      dataIndex: 'operation',
      key: 'operation',
      render: (text: string) => LogOperationMap[text] || text,
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (text: string) => {
        if (!text) return '-';
        const color = (LogStatusColors as Record<string, string>)[text] || 'default';
        return <Tag color={color}>{text}</Tag>;
      },
      width: 100,
    },
    {
      title: '关联对象',
      key: 'entity',
      render: (_: any, record: Log) => (
        record.entity_type ? `${record.entity_type}:${record.entity_id}` : '-'
      ),
      width: 120,
    },
    {
      title: '操作用户',
      dataIndex: 'username',
      key: 'username',
      render: (text: string, record: Log) => text || '系统',
      width: 120,
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
      width: 180,
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Log) => (
        <Space size="middle">
          <Button 
            type="link" 
            icon={<InfoCircleOutlined />} 
            onClick={() => handleViewLog(record)}
          >
            详情
          </Button>
        </Space>
      ),
      width: 100,
    },
  ];
  
  // 日志详情抽屉
  const renderLogDrawer = () => {
    if (!currentLog) return null;
    
    return (
      <Drawer
        title="日志详情"
        placement="right"
        width={600}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        <div style={{ marginBottom: 16 }}>
          <Title level={4}>{currentLog.title}</Title>
          <Tag color={(LogStatusColors as Record<string, string>)[currentLog.status || 'info'] || 'default'}>
            {currentLog.status || '未知'}
          </Tag>
          <Text type="secondary" style={{ marginLeft: 8 }}>
            {dayjs(currentLog.created_at).format('YYYY-MM-DD HH:mm:ss')}
          </Text>
        </div>
        
        <Divider orientation="left">基本信息</Divider>
        <div style={{ marginBottom: 16 }}>
          <p><Text strong>分类：</Text> {(LogCategoryMap as Record<string, string>)[currentLog.category] || currentLog.category}</p>
          <p><Text strong>操作：</Text> {LogOperationMap[currentLog.operation] || currentLog.operation}</p>
          {currentLog.entity_type && (
            <p><Text strong>关联对象：</Text> {currentLog.entity_type}:{currentLog.entity_id}</p>
          )}
          <p><Text strong>操作用户：</Text> {currentLog.username || '系统'}</p>
          {currentLog.user_ip && <p><Text strong>IP地址：</Text> {currentLog.user_ip}</p>}
        </div>
        
        {currentLog.content && (
          <>
            <Divider orientation="left">详细内容</Divider>
            <div style={{ marginBottom: 16, whiteSpace: 'pre-wrap' }}>
              {currentLog.content}
            </div>
          </>
        )}
        
        {currentLog.data && (
          <>
            <Divider orientation="left">额外数据</Divider>
            <div style={{ marginBottom: 16, whiteSpace: 'pre-wrap', overflow: 'auto' }}>
              <pre>{JSON.stringify(currentLog.data, null, 2)}</pre>
            </div>
          </>
        )}
      </Drawer>
    );
  };
  
  return (
    <div>
      <Card title="系统日志" style={{ marginBottom: 16 }}>
        <Form
          layout="inline"
          form={form}
          ref={formRef}
          onFinish={handleFilterSubmit}
          style={{ marginBottom: 16 }}
        >
          <Form.Item name="category" label="分类">
            <Select style={{ width: 120 }} allowClear placeholder="选择分类">
              {Object.entries(LogCategoryMap).map(([value, label]) => (
                <Option key={value} value={value}>{label}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item name="operation" label="操作类型">
            <Select style={{ width: 120 }} allowClear placeholder="操作类型">
              {Object.entries(LogOperationMap).map(([value, label]) => (
                <Option key={value} value={value}>{label}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item name="entity_type" label="对象类型">
            <Select style={{ width: 120 }} allowClear placeholder="对象类型">
              <Option value="machine">机器</Option>
              <Option value="project">项目</Option>
              <Option value="user">用户</Option>
              <Option value="system">系统</Option>
            </Select>
          </Form.Item>
          
          <Form.Item name="status" label="状态">
            <Select style={{ width: 120 }} allowClear placeholder="状态">
              <Option value="success">成功</Option>
              <Option value="failed">失败</Option>
              <Option value="warning">警告</Option>
              <Option value="info">信息</Option>
            </Select>
          </Form.Item>
          
          <Form.Item name="dateRange" label="时间范围">
            <RangePicker />
          </Form.Item>
          
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" icon={<SearchOutlined />}>
                查询
              </Button>
              <Button onClick={handleReset} icon={<ReloadOutlined />}>
                重置
              </Button>
            </Space>
          </Form.Item>
        </Form>
        
        <Table
          columns={columns}
          dataSource={logs}
          rowKey="id"
          pagination={{
            ...pagination,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条日志`,
          }}
          loading={loading}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
        />
      </Card>
      
      {renderLogDrawer()}
    </div>
  );
};

export default LogsPage; 