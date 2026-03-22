/**
 * Data Lineage Visualization Component
 * Shows data flow and transformations between nodes
 */

import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';

export interface DataFlowEdge {
  id: string;
  from: string;
  to: string;
  dataCount: number;
  transformationType: string;
}

export interface DataFlowNode {
  id: string;
  name: string;
  dataType: string;
  timestamp: string;
}

interface DataLineageProps {
  nodes: DataFlowNode[];
  edges: DataFlowEdge[];
  onNodeClick?: (nodeId: string) => void;
  title?: string;
}

const dataTypeColors: Record<string, string> = {
  question: '#F59E0B',
  context: '#8B5CF6',
  schema: '#EC4899',
  data_table: '#06B6D4',
  sql_query: '#10B981',
  result_set: '#3B82F6',
  insight: '#F97316',
  chart_spec: '#6366F1',
  answer: '#14B8A6',
};

const transformationIcons: Record<string, string> = {
  filter: '🔍',
  aggregate: '📊',
  join: '🔗',
  select: '✂️',
  data_flow: '→',
  transform: '⚙️',
};

export const DataLineageVisualization: React.FC<DataLineageProps> = ({
  nodes,
  edges,
  onNodeClick,
  title = 'Data Lineage',
}) => {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [highlightedPath, setHighlightedPath] = useState<Set<string>>(
    new Set()
  );

  // Group nodes by data type
  const nodesByType = useMemo(() => {
    const grouped: Record<string, DataFlowNode[]> = {};
    nodes.forEach((node) => {
      if (!grouped[node.dataType]) {
        grouped[node.dataType] = [];
      }
      grouped[node.dataType].push(node);
    });
    return grouped;
  }, [nodes]);

  // Find path through graph
  const findPath = (nodeId: string): Set<string> => {
    const visited = new Set<string>();
    const queue: string[] = [nodeId];

    while (queue.length > 0) {
      const current = queue.shift()!;
      if (visited.has(current)) continue;
      visited.add(current);

      // Find connected edges
      edges.forEach((edge) => {
        if (edge.from === current && !visited.has(edge.to)) {
          queue.push(edge.to);
        }
        if (edge.to === current && !visited.has(edge.from)) {
          queue.push(edge.from);
        }
      });
    }

    return visited;
  };

  const handleNodeClick = (nodeId: string) => {
    setSelectedNode(nodeId);
    setHighlightedPath(findPath(nodeId));
    onNodeClick?.(nodeId);
  };

  return (
    <div className="w-full bg-gradient-to-br from-slate-50 to-slate-100 rounded-lg border border-slate-200 p-6">
      <style>{`
        @keyframes flowAnimation {
          0% { stroke-dashoffset: 20; }
          100% { stroke-dashoffset: 0; }
        }
        
        .animate-flow {
          animation: flowAnimation 2s linear infinite;
        }
      `}</style>

      {/* Header */}
      <div className="mb-6">
        <h3 className="text-lg font-bold text-slate-900">{title}</h3>
        <p className="text-sm text-slate-600 mt-1">
          Shows data transformations through {nodes.length} data pieces across{' '}
          {edges.length} transformations
        </p>
      </div>

      {/* Legend */}
      <div className="mb-6 p-4 bg-white rounded-lg border border-slate-200">
        <h4 className="text-sm font-semibold text-slate-900 mb-3">Data Types</h4>
        <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
          {Object.entries(dataTypeColors).map(([type, color]) => (
            <div key={type} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: color }}
              />
              <span className="text-xs text-slate-700 capitalize">{type}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Data Flow Timeline */}
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        {Object.entries(nodesByType).length > 0 ? (
          <div className="space-y-1 divide-y divide-slate-200">
            {Object.entries(nodesByType).map(([dataType, typeNodes]) => (
              <motion.div
                key={dataType}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="p-4 hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div
                    className="w-4 h-4 rounded-full flex-shrink-0"
                    style={{
                      backgroundColor: dataTypeColors[dataType],
                    }}
                  />
                  <h4 className="font-semibold text-sm text-slate-900 capitalize">
                    {dataType}
                  </h4>
                  <span className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded">
                    {typeNodes.length}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 ml-7">
                  {typeNodes.map((node) => (
                    <motion.div
                      key={node.id}
                      whileHover={{ scale: 1.02 }}
                      onClick={() => handleNodeClick(node.id)}
                      className={`p-3 rounded border cursor-pointer transition-all ${
                        selectedNode === node.id
                          ? 'border-blue-500 bg-blue-50'
                          : highlightedPath.has(node.id)
                          ? 'border-amber-300 bg-amber-50'
                          : 'border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <div className="text-xs font-mono text-slate-600 truncate">
                        {node.name}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        {new Date(node.timestamp).toLocaleTimeString()}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center text-slate-400">
            <div className="text-3xl mb-2">📁</div>
            <p>No data pieces tracked yet. Data lineage will appear here during execution.</p>
          </div>
        )}
      </div>

      {/* Transformations */}
      {edges.length > 0 && (
        <div className="mt-6 bg-white rounded-lg border border-slate-200 p-4">
          <h4 className="font-semibold text-sm text-slate-900 mb-4">
            Data Transformations
          </h4>

          <div className="space-y-2">
            {edges.map((edge) => {
              const isHighlighted =
                highlightedPath.has(edge.from) ||
                highlightedPath.has(edge.to);

              return (
                <motion.div
                  key={edge.id}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`p-3 rounded border flex items-center justify-between transition-all ${
                    isHighlighted
                      ? 'border-amber-300 bg-amber-50'
                      : 'border-slate-200 bg-slate-50'
                  }`}
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <span className="text-lg flex-shrink-0">
                      {transformationIcons[edge.transformationType] || '→'}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="text-xs text-slate-600 truncate">
                        <span className="font-semibold text-slate-900">
                          {edge.from}
                        </span>
                        {' → '}
                        <span className="font-semibold text-slate-900">
                          {edge.to}
                        </span>
                      </div>
                      <div className="text-xs text-slate-500 mt-1 capitalize">
                        {edge.transformationType}
                      </div>
                    </div>
                  </div>
                  <span className="text-xs bg-slate-200 text-slate-700 px-2 py-1 rounded flex-shrink-0 ml-2">
                    {edge.dataCount} items
                  </span>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}

      {/* Stats */}
      {nodes.length > 0 && (
        <div className="mt-4 grid grid-cols-3 gap-3">
          <div className="p-3 bg-blue-50 rounded border border-blue-200">
            <div className="text-xs text-blue-600">Data Pieces</div>
            <div className="text-lg font-bold text-blue-900">{nodes.length}</div>
          </div>
          <div className="p-3 bg-purple-50 rounded border border-purple-200">
            <div className="text-xs text-purple-600">Transformations</div>
            <div className="text-lg font-bold text-purple-900">{edges.length}</div>
          </div>
          <div className="p-3 bg-green-50 rounded border border-green-200">
            <div className="text-xs text-green-600">Data Types</div>
            <div className="text-lg font-bold text-green-900">
              {Object.keys(nodesByType).length}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataLineageVisualization;
