export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  message: string;
  namespace?: string;
  conversation_history?: Array<{ role: string; content: string }>;
}

export interface ToolCall {
  tool: string;
  arguments: Record<string, unknown>;
  result: unknown;
}

export interface ChatResponse {
  response: string;
  tool_calls: ToolCall[];
  model: string;
}

export interface Pod {
  name: string;
  namespace: string;
  status: string;
  conditions: Array<{
    type: string;
    status: string;
    reason?: string;
    message?: string;
  }>;
  containers: Array<{
    name: string;
    image: string;
    ready: boolean;
    restart_count: number;
  }>;
  node: string;
  created_at: string;
}

export interface PodsResponse {
  pods: Pod[];
  count: number;
}

export interface Deployment {
  name: string;
  namespace: string;
  replicas: {
    desired: number;
    current: number;
    ready: number;
    updated: number;
    available: number;
  };
  conditions: Array<{
    type: string;
    status: string;
    reason?: string;
    message?: string;
  }>;
  strategy: string;
  created_at: string;
}

export interface DeploymentsResponse {
  deployments: Deployment[];
  count: number;
}

export interface K8sEvent {
  name: string;
  namespace: string;
  type: string;
  reason: string;
  message: string;
  involved_object: {
    kind: string;
    name: string;
    namespace: string;
  };
  count: number;
  first_timestamp: string | null;
  last_timestamp: string | null;
}

export interface EventsResponse {
  events: K8sEvent[];
  count: number;
}

export interface Namespace {
  name: string;
  status: string;
  created_at: string;
  labels: Record<string, string>;
}

export interface NamespacesResponse {
  namespaces: Namespace[];
  count: number;
}

export interface ClusterNode {
  name: string;
  status: string;
  roles: string[];
  version: string;
  os: string;
  kernel: string;
}

export interface ClusterInfo {
  nodes: ClusterNode[];
  node_count: number;
  version: {
    major: string;
    minor: string;
    git_version: string;
  };
}

export interface DocumentStats {
  collection_name: string;
  document_count: number;
}

export interface SearchResult {
  content: string;
  metadata: Record<string, unknown>;
  distance: number;
  id: string;
}

export interface SearchResponse {
  results: SearchResult[];
  count: number;
}
