/**
 * Node Graph Visualization Component
 * Uses React Flow to display the execution graph with real-time node status updates
 */

import React, { useCallback, useState, useEffect } from 'react';
import { motion } from 'framer-motion';

export interface GraphNode {
  id: string;
  label: string;
  status: 'idle' | 'running' | 'completed' | 'failed' | 'skipped';
  executionTime?: number;
  description?: string;
  inputCount?: number;
  outputCount?: number;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  animated: boolean;
  type?: string;
}

interface NodeGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick?: (nodeId: string) => void;
  onReset?: () => void;
  isExecuting?: boolean;
}

const statusColors = {
  idle: '#6B7280',
  running: '#3B82F6',
  completed: '#10B981',
  failed: '#EF4444',
  skipped: '#9CA3AF',
};

const statusGlows = {
  idle: 'none',
  running: '0 0 20px rgba(59, 130, 246, 0.6)',
  completed: '0 0 20px rgba(16, 185, 129, 0.6)',
  failed: '0 0 20px rgba(239, 68, 68, 0.6)',
  skipped: 'none',
};

const GraphNode: React.FC<{
  node: GraphNode;
  onClick: (id: string) => void;
}> = ({ node, onClick }) => {
  const isRunning = node.status === 'running';
  const isFailed = node.status === 'failed';
  const isCompleted = node.status === 'completed';

  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      onClick={() => onClick(node.id)}
      className="relative cursor-pointer"
    >
      <motion.div
        animate={{
          boxShadow: statusGlows[node.status],
          scale: isRunning ? [1, 1.05, 1] : 1,
        }}
        transition={{
          boxShadow: { duration: 0.3 },
          scale: isRunning ? { duration: 1.5, repeat: Infinity } : undefined,
        }}
        className="w-32 h-20 rounded-lg border-2 flex flex-col items-center justify-center p-2 bg-slate-50 transition-all"
        style={{
          borderColor: statusColors[node.status],
          boxShadow: statusGlows[node.status],
        }}
      >
        <div className="font-semibold text-sm text-center truncate text-slate-900">
          {node.label}
        </div>

        <div className="text-xs text-slate-600 mt-1">
          {node.status === 'running' && (
            <motion.span
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              ⏳ Running
            </motion.span>
          )}
          {node.status === 'completed' && `✓ ${node.executionTime?.toFixed(0)}ms`}
          {node.status === 'failed' && '✗ Failed'}
          {node.status === 'skipped' && 'Skipped'}
          {node.status === 'idle' && 'Pending'}
        </div>
      </motion.div>

      {/* Status indicator badge */}
      <motion.div
        animate={{
          scale: isRunning ? [0.8, 1.2, 0.8] : 1,
        }}
        transition={{
          duration: 1,
          repeat: isRunning ? Infinity : 0,
        }}
        className="absolute -top-2 -right-2 w-5 h-5 rounded-full border-2 border-white"
        style={{
          backgroundColor: statusColors[node.status],
        }}
      />
    </motion.div>
  );
};

const GraphEdge: React.FC<{
  edge: GraphEdge;
  sourcePos: [number, number];
  targetPos: [number, number];
}> = ({ edge, sourcePos, targetPos }) => {
  const isAnimated = edge.animated;

  return (
    <svg
      className="absolute top-0 left-0 pointer-events-none"
      style={{
        width: '100%',
        height: '100%',
        zIndex: 0,
      }}
    >
      <defs>
        <marker
          id="arrowhead"
          markerWidth="10"
          markerHeight="10"
          refX="9"
          refY="3"
          orient="auto"
        >
          <polygon points="0 0, 10 3, 0 6" fill="#94A3B8" />
        </marker>
      </defs>
      <line
        x1={sourcePos[0]}
        y1={sourcePos[1]}
        x2={targetPos[0]}
        y2={targetPos[1]}
        stroke="#94A3B8"
        strokeWidth="2"
        markerEnd="url(#arrowhead)"
        strokeDasharray={isAnimated ? '5,5' : '0'}
        className={isAnimated ? "animate-pulse" : ""}
        style={{
          stroke: isAnimated ? "#3B82F6" : "#94A3B8",
          strokeWidth: isAnimated ? "3" : "2",
          animation: isAnimated ? 'dash 20s linear infinite' : 'none',
        }}
      />
    </svg>
  );
};

export const NodeGraphVisualization: React.FC<NodeGraphProps> = ({
  nodes,
  edges,
  onNodeClick,
  onReset,
  isExecuting = false,
}) => {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const [nodePositions, setNodePositions] = useState<
    Record<string, [number, number]>
  >({});

  // Calculate node positions
  useEffect(() => {
    if (nodes.length === 0) return;

    const positions: Record<string, [number, number]> = {};
    const itemsPerRow = Math.ceil(Math.sqrt(nodes.length));
    const horizontalSpacing = 200;
    const verticalSpacing = 150;

    nodes.forEach((node, idx) => {
      const row = Math.floor(idx / itemsPerRow);
      const col = idx % itemsPerRow;
      positions[node.id] = [
        col * horizontalSpacing + 50,
        row * verticalSpacing + 50,
      ];
    });

    setNodePositions(positions);
  }, [nodes]);

  return (
    <div className="w-full h-full bg-gradient-to-br from-slate-50 to-slate-100 rounded-lg border border-slate-200 p-6 overflow-auto relative">
      <style>{`
        @keyframes dash {
          to {
            stroke-dashoffset: -10;
          }
        }
      `}</style>

      {/* Header */}
      <div className="flex justify-between items-center mb-4 sticky top-0 z-10 bg-white bg-opacity-90 p-2 rounded">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-bold text-slate-900">Graph Execution</h3>
          {isExecuting && (
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity }}
              className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"
            />
          )}
        </div>

        {onReset && (
          <button
            onClick={onReset}
            disabled={isExecuting}
            className="px-3 py-1 text-sm bg-slate-200 text-slate-900 rounded hover:bg-slate-300 disabled:opacity-50 transition-colors"
          >
            Reset
          </button>
        )}
      </div>

      {/* Legend */}
      <div className="flex gap-4 mb-4 text-xs text-slate-600 p-2 bg-white rounded border border-slate-200">
        {(Object.entries(statusColors) as Array<[keyof typeof statusColors, string]>).map(
          ([status, color]) => (
            <div key={status} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded"
                style={{ backgroundColor: color }}
              />
              <span className="capitalize">{status}</span>
            </div>
          )
        )}
      </div>

      {/* Graph container */}
      <div
        ref={containerRef}
        className="relative"
        style={{
          minHeight: '600px',
          background: 'white',
          borderRadius: '8px',
          border: '1px solid #E2E8F0',
        }}
      >
        {/* Edges (SVG background) */}
        {edges.map((edge) => (
          <GraphEdge
            key={edge.id}
            edge={edge}
            sourcePos={nodePositions[edge.source] || [0, 0]}
            targetPos={nodePositions[edge.target] || [0, 0]}
          />
        ))}

        {/* Nodes */}
        {nodes.map((node) => (
          <motion.div
            key={node.id}
            initial={{
              x: nodePositions[node.id]?.[0] || 0,
              y: nodePositions[node.id]?.[1] || 0,
            }}
            animate={{
              x: nodePositions[node.id]?.[0] || 0,
              y: nodePositions[node.id]?.[1] || 0,
            }}
            className="absolute"
          >
            <GraphNode
              node={node}
              onClick={() => onNodeClick?.(node.id)}
            />
          </motion.div>
        ))}

        {/* Empty state */}
        {nodes.length === 0 && (
          <div className="flex items-center justify-center h-96 text-slate-400">
            <div className="text-center">
              <div className="text-4xl mb-2">📊</div>
              <p>No nodes to display. Ready for execution.</p>
            </div>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mt-4">
        <div className="p-3 bg-slate-100 rounded text-sm">
          <div className="text-slate-600">Total Nodes</div>
          <div className="text-xl font-bold text-slate-900">{nodes.length}</div>
        </div>
        <div className="p-3 bg-blue-50 rounded text-sm border border-blue-200">
          <div className="text-blue-600">Running</div>
          <div className="text-xl font-bold text-blue-900">
            {nodes.filter((n) => n.status === 'running').length}
          </div>
        </div>
        <div className="p-3 bg-green-50 rounded text-sm border border-green-200">
          <div className="text-green-600">Completed</div>
          <div className="text-xl font-bold text-green-900">
            {nodes.filter((n) => n.status === 'completed').length}
          </div>
        </div>
        <div className="p-3 bg-red-50 rounded text-sm border border-red-200">
          <div className="text-red-600">Failed</div>
          <div className="text-xl font-bold text-red-900">
            {nodes.filter((n) => n.status === 'failed').length}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NodeGraphVisualization;
