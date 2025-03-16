export interface Machine {
  id: number;
  name: string;
  host: string;
  port: number;
  username: string;
  description?: string;
  is_online: boolean;
  backend_running: boolean;
  frontend_running: boolean;
  cpu_usage?: string;
  memory_usage?: string;
  disk_usage?: string;
  last_check?: string;
  created_at: string;
  updated_at?: string;
  deployed_projects?: DeployedProject[];
}

export interface DeployedProject {
  id: number;
  project_id: number;
  project_name: string;
  deploy_path: string;
  status: 'running' | 'stopped' | 'error';
  version?: string;
  deployed_at: string;
}

export interface MachineMetrics {
  timestamp: string;
  cpu: {
    cores: number;
    usage_percent: number;
    load_avg: number[];
  };
  memory: {
    total: number;
    used: number;
    free: number;
    usage_percent: number;
  };
  disk: {
    total: number;
    used: number;
    free: number;
    usage_percent: number;
  };
  network: {
    rx_bytes: number;
    tx_bytes: number;
    rx_packets: number;
    tx_packets: number;
  };
  processes: {
    total: number;
    running: number;
    sleeping: number;
  };
}

export interface MachineForm {
  name: string;
  host: string;
  port: number;
  username: string;
  password?: string;
  key_file?: string;
  description?: string;
}

export interface OperationModalProps {
  title: string;
  visible: boolean;
  onCancel: () => void;
  onOk: (password: string) => Promise<void>;
  confirmLoading: boolean;
}

export interface DeployParams {
  password: string;
  show_logs?: boolean;
} 