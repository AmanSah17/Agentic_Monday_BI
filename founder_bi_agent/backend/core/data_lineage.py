"""Data Lineage & Flow Tracking System"""
from typing import Any, Dict, List, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DataType(str, Enum):
    """Data types that flow through the system"""
    QUESTION = "question"
    CONTEXT = "context"
    SCHEMA = "schema"
    DATA_TABLE = "data_table"
    SQL_QUERY = "sql_query"
    RESULT_SET = "result_set"
    INSIGHT = "insight"
    CHART_SPEC = "chart_spec"
    ANSWER = "answer"


@dataclass
class DataNode:
    """Represents a piece of data flowing through the graph"""
    id: str
    data_type: DataType
    timestamp: str
    source_node: str
    value: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    size_bytes: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "data_type": self.data_type.value,
            "timestamp": self.timestamp,
            "source_node": self.source_node,
            "metadata": self.metadata,
            "size_bytes": self.size_bytes,
        }


@dataclass
class DataTransformation:
    """Represents transformation between nodes"""
    id: str
    from_node: str
    to_node: str
    data_ids: List[str]  # IDs of data flowing
    transformation_type: str  # e.g., "filter", "aggregate", "join"
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "from_node": self.from_node,
            "to_node": self.to_node,
            "data_count": len(self.data_ids),
            "transformation_type": self.transformation_type,
            "timestamp": self.timestamp,
        }


class DataLineageTracker:
    """Tracks complete data lineage through execution"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.data_nodes: Dict[str, DataNode] = {}
        self.transformations: Dict[str, DataTransformation] = {}
        self.node_outputs: Dict[str, List[str]] = {}  # node_name -> [data_id]
        self.node_inputs: Dict[str, List[str]] = {}   # node_name -> [data_id]

    def track_data_input(
        self,
        node_name: str,
        data_type: DataType,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track data entering a node"""
        import uuid
        data_id = f"{node_name}_{uuid.uuid4().hex[:8]}"

        data_node = DataNode(
            id=data_id,
            data_type=data_type,
            timestamp=datetime.utcnow().isoformat() + "Z",
            source_node=node_name,
            value=value,
            metadata=metadata or {},
            size_bytes=self._estimate_size(value),
        )

        self.data_nodes[data_id] = data_node

        if node_name not in self.node_inputs:
            self.node_inputs[node_name] = []
        self.node_inputs[node_name].append(data_id)

        return data_id

    def track_data_output(
        self,
        node_name: str,
        data_type: DataType,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track data leaving a node"""
        import uuid
        data_id = f"{node_name}_out_{uuid.uuid4().hex[:8]}"

        data_node = DataNode(
            id=data_id,
            data_type=data_type,
            timestamp=datetime.utcnow().isoformat() + "Z",
            source_node=node_name,
            value=value,
            metadata=metadata or {},
            size_bytes=self._estimate_size(value),
        )

        self.data_nodes[data_id] = data_node

        if node_name not in self.node_outputs:
            self.node_outputs[node_name] = []
        self.node_outputs[node_name].append(data_id)

        return data_id

    def track_transformation(
        self,
        from_node: str,
        to_node: str,
        input_data_ids: List[str],
        output_data_ids: List[str],
        transformation_type: str = "data_flow"
    ) -> str:
        """Track data transformation between nodes"""
        import uuid
        transform_id = f"transform_{uuid.uuid4().hex[:8]}"

        # Combine all data ids
        all_data_ids = input_data_ids + output_data_ids

        transformation = DataTransformation(
            id=transform_id,
            from_node=from_node,
            to_node=to_node,
            data_ids=all_data_ids,
            transformation_type=transformation_type,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

        self.transformations[transform_id] = transformation
        return transform_id

    def get_data_lineage_graph(self) -> Dict[str, Any]:
        """Generate complete lineage graph"""
        # Build node connectivity
        node_graph: Dict[str, Any] = {}

        for transform_id, transform in self.transformations.items():
            if transform.from_node not in node_graph:
                node_graph[transform.from_node] = {
                    "outputs": [],
                    "inputs": [],
                }
            if transform.to_node not in node_graph:
                node_graph[transform.to_node] = {
                    "outputs": [],
                    "inputs": [],
                }

            node_graph[transform.from_node]["outputs"].append({
                "target": transform.to_node,
                "transform_id": transform_id,
                "type": transform.transformation_type,
            })
            node_graph[transform.to_node]["inputs"].append({
                "source": transform.from_node,
                "transform_id": transform_id,
                "type": transform.transformation_type,
            })

        return {
            "session_id": self.session_id,
            "nodes": node_graph,
            "data_nodes_count": len(self.data_nodes),
            "transformations_count": len(self.transformations),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    def get_node_lineage(self, node_name: str) -> Dict[str, Any]:
        """Get lineage for specific node"""
        inputs = []
        outputs = []

        # Find inputs
        for transform in self.transformations.values():
            if transform.to_node == node_name:
                inputs.append({
                    "from": transform.from_node,
                    "data_count": len(transform.data_ids),
                    "type": transform.transformation_type,
                })

        # Find outputs
        for transform in self.transformations.values():
            if transform.from_node == node_name:
                outputs.append({
                    "to": transform.to_node,
                    "data_count": len(transform.data_ids),
                    "type": transform.transformation_type,
                })

        return {
            "node": node_name,
            "inputs": inputs,
            "outputs": outputs,
            "upstream_nodes": list(set(i["from"] for i in inputs)),
            "downstream_nodes": list(set(o["to"] for o in outputs)),
        }

    def trace_data_path(self, data_id: str) -> List[Dict[str, Any]]:
        """Trace specific data through system"""
        path = []
        current_data_id = data_id

        # Find source
        if current_data_id not in self.data_nodes:
            return []

        data_node = self.data_nodes[current_data_id]
        path.append({
            "data_id": current_data_id,
            "node": data_node.source_node,
            "type": data_node.data_type.value,
            "timestamp": data_node.timestamp,
        })

        # Follow transformations
        visited = {current_data_id}
        for transform in self.transformations.values():
            if current_data_id in transform.data_ids:
                for output_id in transform.data_ids:
                    if output_id not in visited and output_id in self.data_nodes:
                        output_node = self.data_nodes[output_id]
                        path.append({
                            "data_id": output_id,
                            "node": output_node.source_node,
                            "type": output_node.data_type.value,
                            "timestamp": output_node.timestamp,
                        })
                        visited.add(output_id)

        return path

    @staticmethod
    def _estimate_size(value: Any) -> int:
        """Estimate data size in bytes"""
        import sys
        try:
            return sys.getsizeof(value)
        except:
            return 0

    def get_summary(self) -> Dict[str, Any]:
        """Get lineage summary"""
        node_names = set(
            list(self.node_inputs.keys()) + list(self.node_outputs.keys())
        )

        return {
            "session_id": self.session_id,
            "total_nodes": len(node_names),
            "total_data_pieces": len(self.data_nodes),
            "total_transformations": len(self.transformations),
            "nodes": sorted(list(node_names)),
            "data_types": list(set(
                dn.data_type.value for dn in self.data_nodes.values()
            )),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
