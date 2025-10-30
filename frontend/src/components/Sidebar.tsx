import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Server, Database, AlertCircle } from 'lucide-react';
import { k8sAPI, docsAPI } from '../services/api';

interface SidebarProps {
  selectedNamespace: string;
  onNamespaceChange: (namespace: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ selectedNamespace, onNamespaceChange }) => {
  const { data: namespaces, isLoading: namespacesLoading } = useQuery({
    queryKey: ['namespaces'],
    queryFn: k8sAPI.getNamespaces,
    refetchInterval: 30000, // Refresh every 30s
  });

  const { data: clusterInfo, isLoading: clusterLoading } = useQuery({
    queryKey: ['cluster-info'],
    queryFn: k8sAPI.getClusterInfo,
    refetchInterval: 60000, // Refresh every 60s
  });

  const { data: docStats } = useQuery({
    queryKey: ['doc-stats'],
    queryFn: docsAPI.getStats,
    refetchInterval: 60000,
  });

  return (
    <div className="w-64 bg-gray-900 text-white p-4 flex flex-col h-screen">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-1">SRE AI Agent</h1>
        <p className="text-gray-400 text-sm">Kubernetes Assistant</p>
      </div>

      {/* Cluster Info */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <Server className="w-4 h-4" />
          <h2 className="font-semibold">Cluster Info</h2>
        </div>
        {clusterLoading ? (
          <div className="text-sm text-gray-400">Loading...</div>
        ) : clusterInfo ? (
          <div className="text-sm space-y-1">
            <div className="text-gray-400">
              Version: <span className="text-white">{clusterInfo.version.git_version}</span>
            </div>
            <div className="text-gray-400">
              Nodes: <span className="text-white">{clusterInfo.node_count}</span>
            </div>
          </div>
        ) : (
          <div className="text-sm text-red-400 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            <span>Unable to connect</span>
          </div>
        )}
      </div>

      {/* Namespace Selector */}
      <div className="mb-6">
        <label className="block mb-2 font-semibold text-sm">Namespace</label>
        {namespacesLoading ? (
          <div className="text-sm text-gray-400">Loading...</div>
        ) : (
          <select
            value={selectedNamespace}
            onChange={(e) => onNamespaceChange(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {namespaces?.namespaces.map((ns) => (
              <option key={ns.name} value={ns.name}>
                {ns.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Documentation Stats */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <Database className="w-4 h-4" />
          <h2 className="font-semibold">Documentation</h2>
        </div>
        {docStats ? (
          <div className="text-sm text-gray-400">
            <div>{docStats.document_count} runbooks indexed</div>
          </div>
        ) : (
          <div className="text-sm text-gray-400">No documents indexed</div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="mt-auto">
        <div className="text-xs text-gray-500 mb-2">Quick Commands</div>
        <div className="space-y-1 text-sm text-gray-400">
          <div>• Show all pods</div>
          <div>• List deployments</div>
          <div>• Check cluster health</div>
          <div>• Show recent events</div>
        </div>
      </div>
    </div>
  );
};
