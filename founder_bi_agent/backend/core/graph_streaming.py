"""
Integration Guide for Real-time Graph Execution with WebSocket Streaming

This module shows how to integrate the WebSocket streaming infrastructure
with your existing LangGraph workflow to enable real-time visualization.
"""

from typing import Any, Dict, Optional
from founder_bi_agent.backend.core.logger import EnhancedTraceLogger
from founder_bi_agent.backend.core.data_lineage import DataLineageTracker, DataType
from founder_bi_agent.backend.graph.state import BIState
import asyncio


class StreamingGraphWrapper:
    """
    Wrapper for LangGraph that instruments it with real-time streaming.
    
    Usage:
        wrapper = StreamingGraphWrapper(graph, trace_logger, lineage_tracker)
        result = await wrapper.invoke(state)
    """

    def __init__(
        self,
        graph,
        trace_logger: EnhancedTraceLogger,
        lineage_tracker: DataLineageTracker,
    ):
        self.graph = graph
        self.trace_logger = trace_logger
        self.lineage_tracker = lineage_tracker

    async def invoke(self, state: BIState) -> BIState:
        """Execute graph with streaming instrumentation"""
        try:
            # Emit start event
            await self.trace_logger.emit_node_start(
                "graph_execution",
                input_data={"question": state.get("question")},
                metadata={"session_id": self.trace_logger.session_id},
            )

            # Run the graph
            # Note: You'll need to adapt this based on your actual graph.invoke() implementation
            result = await asyncio.to_thread(
                self._run_sync_graph, state
            )

            # Emit completion event
            await self.trace_logger.emit_node_end(
                "graph_execution",
                output_data={"answer": result.get("answer")},
            )

            return result

        except Exception as e:
            await self.trace_logger.emit_node_error(
                "graph_execution",
                str(e),
            )
            raise

    def _run_sync_graph(self, state: BIState) -> BIState:
        """Run the synchronous graph and track each node"""
        # This is the bridge between async WebSocket and sync graph execution
        # Subgraph nodes will emit their own events
        return self.graph.invoke(state)


class NodeTrackingDecorator:
    """
    Decorator to add tracing to individual node functions.
    
    Usage:
        @NodeTrackingDecorator(trace_logger, lineage_tracker)
        def memory_retriever(state: dict) -> dict:
            # Node implementation
            return state
    """

    def __init__(
        self,
        trace_logger: EnhancedTraceLogger,
        lineage_tracker: DataLineageTracker,
        node_name: Optional[str] = None,
    ):
        self.trace_logger = trace_logger
        self.lineage_tracker = lineage_tracker
        self.node_name = node_name

    def __call__(self, func):
        async def async_wrapper(state: dict) -> dict:
            node_name = self.node_name or func.__name__
            
            # Emit node start
            input_summary = self._summarize_state(state)
            
            # Track input data
            input_data_id = self.lineage_tracker.track_data_input(
                node_name,
                DataType.CONTEXT if "question" in state else DataType.DATA_TABLE,
                value=state,
                metadata={"keys": list(state.keys())},
            )

            try:
                # Call the wrapped function
                result = func(state) if not asyncio.iscoroutinefunction(func) else await func(state)

                # Track output data
                output_data_id = self.lineage_tracker.track_data_output(
                    node_name,
                    DataType.RESULT_SET,
                    value=result,
                    metadata={"keys": list(result.keys())},
                )

                # Track transformation
                self.lineage_tracker.track_transformation(
                    "previous_node",  # You'll need to track this
                    node_name,
                    [input_data_id],
                    [output_data_id],
                    transformation_type="processing",
                )

                # Emit node end event
                output_summary = self._summarize_state(result)
                await self.trace_logger.emit_node_end(
                    node_name,
                    output_data=output_summary,
                )

                return result

            except Exception as e:
                await self.trace_logger.emit_node_error(
                    node_name,
                    str(e),
                )
                raise

        return async_wrapper

    @staticmethod
    def _summarize_state(state: dict, max_depth: int = 1, key_limit: int = 5) -> dict:
        """Create a safe summary of state for logging"""
        if not isinstance(state, dict):
            return {}

        summary = {}
        for i, (key, value) in enumerate(state.items()):
            if i >= key_limit:
                break

            if isinstance(value, (str, int, float, bool, type(None))):
                summary[key] = value
            elif isinstance(value, dict):
                summary[key] = f"<dict[{len(value)}]>"
            elif isinstance(value, (list, tuple)):
                summary[key] = f"<{type(value).__name__}[{len(value)}]>"
            else:
                summary[key] = f"<{type(value).__name__}>"

        return summary


# ============================================================================
# INTEGRATION STEPS
# ============================================================================

"""
To integrate real-time streaming with your existing graph:

1. In your FastAPI main.py, modify the WebSocket handler to import and use:

    from founder_bi_agent.backend.core.graph_streaming import NodeTrackingDecorator

2. Update your graph nodes to use the decorator:

    @NodeTrackingDecorator(trace_logger, lineage_tracker, "memory_retriever")
    def memory_retriever(state: dict) -> dict:
        # Existing implementation
        return updated_state

3. Add WeSocket initialization to your FastAPI app:

    from founder_bi_agent.backend.api.ws import router as ws_router, manager
    from founder_bi_agent.backend.core.session_manager import SessionManager
    
    # Initialize session manager
    session_manager = SessionManager(redis_client=redis, db_connection=db)
    
    # Attach to WebSocket module
    import founder_bi_agent.backend.api.ws as ws_module
    ws_module.session_manager = session_manager
    
    # Include WebSocket routes
    app.include_router(ws_router)

4. In your graph execution handler (handle_graph_execution in ws.py):

    async def handle_graph_execution(session_id: str, data: Dict[str, Any]):
        trace_logger = manager.get_trace_logger(session_id)
        lineage_tracker = DataLineageTracker(session_id)
        
        wrapper = StreamingGraphWrapper(
            your_graph,
            trace_logger,
            lineage_tracker
        )
        
        result = await wrapper.invoke(state)
        # Result will have streaming events emitted via WebSocket

5. Frontend integration:

    import { useWebSocket } from './hooks/useWebSocket';
    import { NodeGraphVisualization } from './components/NodeGraphVisualization';
    import { DataLineageVisualization } from './components/DataLineageVisualization';

    function App() {
        const session_id = generateSessionId();
        const [graphNodes, setGraphNodes] = useState([]);
        
        const { connected, executeQuery } = useWebSocket({
            sessionId: session_id,
            onNodeStart: (event) => {
                setGraphNodes(prev => ({
                    ...prev,
                    [event.node_name]: { status: 'running' }
                }));
            },
            onNodeEnd: (event) => {
                setGraphNodes(prev => ({
                    ...prev,
                    [event.node_name]: { 
                        status: 'completed',
                        executionTime: event.execution_time_ms
                    }
                }));
            }
        });
        
        return (
            <NodeGraphVisualization 
                nodes={Object.values(graphNodes)}
                edges={[]}
            />
        );
    }
"""

# Example node implementation with tracing
def create_traced_memory_retriever(
    trace_logger: EnhancedTraceLogger,
    lineage_tracker: DataLineageTracker,
    foundation_llm: Any,
    vector_store: Any,
) -> any:
    """Create memory retriever node with tracing"""

    def memory_retriever(state: dict) -> dict:
        session_id = state.get("session_id", "default_session")
        question = state.get("question", "")
        
        # Track input
        lineage_tracker.track_data_input(
            "memory_retriever",
            DataType.QUESTION,
            {"question": question, "session_id": session_id},
        )

        # Retrieve context
        context = vector_store.get_relevant_context(session_id, question)

        # Track output
        lineage_tracker.track_data_output(
            "memory_retriever",
            DataType.CONTEXT,
            {"context": context},
        )

        return {
            "long_term_context": context,
            "traces": state.get("traces", []) + [{
                "ts": __import__('datetime').datetime.utcnow().isoformat() + "Z",
                "node": "memory_retriever",
                "status": "completed",
            }],
        }

    return memory_retriever
