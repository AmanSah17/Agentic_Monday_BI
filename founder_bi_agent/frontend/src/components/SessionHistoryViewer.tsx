/**
 * Session History Component
 * Displays conversation history, traces, and execution details
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface NodeTrace {
  node_name: string;
  status: 'completed' | 'failed' | 'running' | 'skipped';
  execution_time_ms?: number;
  timestamp: string;
  input_data?: Record<string, any>;
  output_data?: Record<string, any>;
  error_message?: string;
}

interface SessionHistoryProps {
  messages: Message[];
  traces: NodeTrace[];
  sessionId: string;
  onExport?: () => void;
  onClear?: () => void;
}

const roleIcons: Record<string, string> = {
  user: '👤',
  assistant: '🤖',
};

const statusIcons: Record<string, string> = {
  completed: '✓',
  failed: '✗',
  running: '⏳',
  skipped: '⊝',
};

const statusColors: Record<string, string> = {
  completed: 'text-green-600 bg-green-50',
  failed: 'text-red-600 bg-red-50',
  running: 'text-blue-600 bg-blue-50',
  skipped: 'text-gray-600 bg-gray-50',
};

export const SessionHistoryViewer: React.FC<SessionHistoryProps> = ({
  messages,
  traces,
  sessionId,
  onExport,
  onClear,
}) => {
  const [expandedMessages, setExpandedMessages] = useState<Set<string>>(
    new Set()
  );
  const [expandedTraces, setExpandedTraces] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<'messages' | 'traces'>(
    'messages'
  );

  const toggleMessageExpand = (id: string) => {
    const expanded = new Set(expandedMessages);
    if (expanded.has(id)) {
      expanded.delete(id);
    } else {
      expanded.add(id);
    }
    setExpandedMessages(expanded);
  };

  const toggleTraceExpand = (nodeName: string) => {
    const expanded = new Set(expandedTraces);
    if (expanded.has(nodeName)) {
      expanded.delete(nodeName);
    } else {
      expanded.add(nodeName);
    }
    setExpandedTraces(expanded);
  };

  const formatJson = (obj: any): string => {
    try {
      return JSON.stringify(obj, null, 2);
    } catch {
      return String(obj);
    }
  };

  return (
    <div className="w-full bg-white rounded-lg border border-slate-200 overflow-hidden flex flex-col">
      {/* Header */}
      <div className="px-6 py-4 bg-gradient-to-r from-slate-50 to-slate-100 border-b border-slate-200 flex justify-between items-center">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Session History</h3>
          <p className="text-xs text-slate-600 mt-1">Session: {sessionId}</p>
        </div>

        <div className="flex gap-2">
          {onExport && (
            <button
              onClick={onExport}
              className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
            >
              📥 Export
            </button>
          )}
          {onClear && (
            <button
              onClick={onClear}
              className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
            >
              🗑️ Clear
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 bg-slate-50">
        <button
          onClick={() => setActiveTab('messages')}
          className={`flex-1 px-4 py-3 text-sm font-semibold transition-colors ${
            activeTab === 'messages'
              ? 'border-b-2 border-blue-500 text-blue-600 bg-white'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          💬 Messages ({messages.length})
        </button>
        <button
          onClick={() => setActiveTab('traces')}
          className={`flex-1 px-4 py-3 text-sm font-semibold transition-colors ${
            activeTab === 'traces'
              ? 'border-b-2 border-blue-500 text-blue-600 bg-white'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          📊 Node Traces ({traces.length})
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <AnimatePresence mode="wait">
          {activeTab === 'messages' ? (
            <motion.div
              key="messages"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="divide-y divide-slate-200"
            >
              {messages.length > 0 ? (
                messages.map((message, index) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="p-4 hover:bg-slate-50 transition-colors"
                  >
                    <div
                      className="flex gap-3 cursor-pointer"
                      onClick={() => toggleMessageExpand(message.id)}
                    >
                      <div className="text-2xl flex-shrink-0">
                        {roleIcons[message.role]}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-start gap-2">
                          <div>
                            <div className="font-semibold text-sm text-slate-900 capitalize">
                              {message.role}
                            </div>
                            <div className="text-xs text-slate-500 mt-1">
                              {new Date(message.timestamp).toLocaleString()}
                            </div>
                          </div>
                          <motion.div
                            animate={{
                              rotate: expandedMessages.has(message.id)
                                ? 180
                                : 0,
                            }}
                            className="text-slate-400"
                          >
                            ▼
                          </motion.div>
                        </div>

                        <motion.div
                          initial={false}
                          animate={{
                            height: expandedMessages.has(message.id)
                              ? 'auto'
                              : 0,
                          }}
                          className="overflow-hidden"
                        >
                          <p className="text-sm text-slate-700 mt-3 whitespace-pre-wrap">
                            {message.content}
                          </p>

                          {message.metadata && (
                            <div className="mt-3 p-2 bg-slate-100 rounded text-xs font-mono text-slate-600 overflow-x-auto">
                              <pre>
                                {formatJson(message.metadata)}
                              </pre>
                            </div>
                          )}
                        </motion.div>
                      </div>
                    </div>
                  </motion.div>
                ))
              ) : (
                <div className="p-8 text-center text-slate-400">
                  <div className="text-3xl mb-2">💬</div>
                  <p>No messages yet. Start a conversation to see history.</p>
                </div>
              )}
            </motion.div>
          ) : (
            <motion.div
              key="traces"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="divide-y divide-slate-200"
            >
              {traces.length > 0 ? (
                traces.map((trace, index) => (
                  <motion.div
                    key={`${trace.node_name}-${index}`}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="p-4 hover:bg-slate-50 transition-colors"
                  >
                    <div
                      className="flex gap-3 cursor-pointer"
                      onClick={() =>
                        toggleTraceExpand(`${trace.node_name}-${index}`)
                      }
                    >
                      <div
                        className={`text-lg flex-shrink-0 ${
                          statusColors[trace.status]
                        }`}
                      >
                        {statusIcons[trace.status]}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-start gap-2">
                          <div>
                            <div className="font-semibold text-sm text-slate-900">
                              {trace.node_name}
                            </div>
                            <div className="text-xs text-slate-500 mt-1">
                              {new Date(trace.timestamp).toLocaleString()}
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <span
                              className={`text-xs px-2 py-1 rounded capitalize font-semibold ${
                                statusColors[trace.status]
                              }`}
                            >
                              {trace.status}
                            </span>
                            {trace.execution_time_ms && (
                              <span className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded">
                                {trace.execution_time_ms.toFixed(0)}ms
                              </span>
                            )}
                            <motion.div
                              animate={{
                                rotate: expandedTraces.has(
                                  `${trace.node_name}-${index}`
                                )
                                  ? 180
                                  : 0,
                              }}
                              className="text-slate-400"
                            >
                              ▼
                            </motion.div>
                          </div>
                        </div>

                        <motion.div
                          initial={false}
                          animate={{
                            height: expandedTraces.has(
                              `${trace.node_name}-${index}`
                            )
                              ? 'auto'
                              : 0,
                          }}
                          className="overflow-hidden"
                        >
                          <div className="mt-3 space-y-2">
                            {trace.error_message && (
                              <div className="p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                                <strong>Error:</strong> {trace.error_message}
                              </div>
                            )}

                            {trace.input_data && (
                              <div className="p-2 bg-blue-50 rounded text-xs font-mono text-slate-600 overflow-x-auto">
                                <strong className="text-blue-900">
                                  Input:
                                </strong>
                                <pre className="mt-1">
                                  {formatJson(trace.input_data)}
                                </pre>
                              </div>
                            )}

                            {trace.output_data && (
                              <div className="p-2 bg-green-50 rounded text-xs font-mono text-slate-600 overflow-x-auto">
                                <strong className="text-green-900">
                                  Output:
                                </strong>
                                <pre className="mt-1">
                                  {formatJson(trace.output_data)}
                                </pre>
                              </div>
                            )}
                          </div>
                        </motion.div>
                      </div>
                    </div>
                  </motion.div>
                ))
              ) : (
                <div className="p-8 text-center text-slate-400">
                  <div className="text-3xl mb-2">📊</div>
                  <p>
                    No execution traces yet. Node traces will appear here
                    during execution.
                  </p>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Stats */}
      {(messages.length > 0 || traces.length > 0) && (
        <div className="grid grid-cols-2 gap-3 p-4 bg-slate-50 border-t border-slate-200">
          <div className="text-xs">
            <div className="text-slate-600">Total Messages</div>
            <div className="text-lg font-bold text-slate-900">
              {messages.length}
            </div>
          </div>
          <div className="text-xs">
            <div className="text-slate-600">Total Node Executions</div>
            <div className="text-lg font-bold text-slate-900">
              {traces.length}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SessionHistoryViewer;
