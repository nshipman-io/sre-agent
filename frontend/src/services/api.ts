import axios from 'axios';
import type {
  ChatRequest,
  ChatResponse,
  PodsResponse,
  DeploymentsResponse,
  EventsResponse,
  NamespacesResponse,
  ClusterInfo,
  DocumentStats,
  SearchResponse,
} from '../types/api';

const API_BASE_URL = '/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Chat API
export const chatAPI = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await apiClient.post<ChatResponse>('/chat/message', request);
    return response.data;
  },

  analyzePods: async (namespace: string = 'default', labelSelector?: string) => {
    const response = await apiClient.post('/chat/analyze-pods', null, {
      params: { namespace, label_selector: labelSelector },
    });
    return response.data;
  },
};

// Kubernetes API
export const k8sAPI = {
  getNamespaces: async (): Promise<NamespacesResponse> => {
    const response = await apiClient.get<NamespacesResponse>('/k8s/namespaces');
    return response.data;
  },

  getClusterInfo: async (): Promise<ClusterInfo> => {
    const response = await apiClient.get<ClusterInfo>('/k8s/cluster-info');
    return response.data;
  },

  getPods: async (namespace: string = 'default', labelSelector?: string): Promise<PodsResponse> => {
    const response = await apiClient.get<PodsResponse>('/k8s/pods', {
      params: { namespace, label_selector: labelSelector },
    });
    return response.data;
  },

  getPodLogs: async (
    podName: string,
    namespace: string = 'default',
    container?: string,
    tailLines: number = 100
  ): Promise<{ logs: string }> => {
    const response = await apiClient.get(`/k8s/pods/${podName}/logs`, {
      params: { namespace, container, tail_lines: tailLines },
    });
    return response.data;
  },

  getDeployments: async (
    namespace: string = 'default',
    labelSelector?: string
  ): Promise<DeploymentsResponse> => {
    const response = await apiClient.get<DeploymentsResponse>('/k8s/deployments', {
      params: { namespace, label_selector: labelSelector },
    });
    return response.data;
  },

  getEvents: async (
    namespace: string = 'default',
    fieldSelector?: string,
    limit: number = 50
  ): Promise<EventsResponse> => {
    const response = await apiClient.get<EventsResponse>('/k8s/events', {
      params: { namespace, field_selector: fieldSelector, limit },
    });
    return response.data;
  },
};

// Documents API
export const docsAPI = {
  getStats: async (): Promise<DocumentStats> => {
    const response = await apiClient.get<DocumentStats>('/docs/stats');
    return response.data;
  },

  search: async (query: string, nResults: number = 5): Promise<SearchResponse> => {
    const response = await apiClient.post<SearchResponse>('/docs/search', {
      query,
      n_results: nResults,
    });
    return response.data;
  },

  indexDirectory: async (directoryPath: string, fileExtensions?: string[]) => {
    const response = await apiClient.post('/docs/index-directory', {
      directory_path: directoryPath,
      file_extensions: fileExtensions,
    });
    return response.data;
  },
};

export default apiClient;
