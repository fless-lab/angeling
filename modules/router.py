import os
import json
import time
import random
import threading
import hashlib
import base64
from queue import Queue, PriorityQueue
from uuid import uuid4
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum, auto
import logging
from concurrent.futures import ThreadPoolExecutor

class CommandPriority(Enum):
    """Priority levels for commands"""
    CRITICAL = auto()
    HIGH = auto()
    NORMAL = auto()
    LOW = auto()
    
    def to_value(self) -> int:
        """Convert priority to numeric value for queue"""
        priority_values = {
            CommandPriority.CRITICAL: 0,
            CommandPriority.HIGH: 1,
            CommandPriority.NORMAL: 2,
            CommandPriority.LOW: 3
        }
        return priority_values[self]

@dataclass
class RoutingMetrics:
    """Metrics for route calculation"""
    latency: float = 0.0
    bandwidth: float = 0.0
    reliability: float = 0.0
    hop_count: int = 0
    load: float = 0.0
    
    def calculate_cost(self) -> float:
        """Calculate total cost for routing decisions"""
        weights = {
            'latency': 0.3,
            'bandwidth': 0.2,
            'reliability': 0.2,
            'hop_count': 0.15,
            'load': 0.15
        }
        
        normalized_metrics = {
            'latency': min(self.latency / 1000.0, 1.0),
            'bandwidth': 1.0 - min(self.bandwidth / 100.0, 1.0),
            'reliability': 1.0 - self.reliability,
            'hop_count': min(self.hop_count / 10.0, 1.0),
            'load': self.load
        }
        
        return sum(weights[k] * normalized_metrics[k] for k in weights)

class NetworkTopology:
    """Manages network topology and route calculations"""
    def __init__(self):
        self.nodes: Dict[str, dict] = {}
        self.links: Dict[str, Dict[str, RoutingMetrics]] = {}
        self.routes: Dict[str, Dict[str, List[str]]] = {}
        
    def add_node(self, node_id: str, node_info: dict):
        """Add a node to the network"""
        self.nodes[node_id] = node_info
        if node_id not in self.links:
            self.links[node_id] = {}
        self._update_topology()
        
    def remove_node(self, node_id: str):
        """Remove a node from the network"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            del self.links[node_id]
            for node in self.links:
                if node_id in self.links[node]:
                    del self.links[node][node_id]
        self._update_topology()
        
    def update_link_metrics(self, source: str, target: str, metrics: RoutingMetrics):
        """Update metrics for a link between nodes"""
        if source in self.nodes and target in self.nodes:
            self.links[source][target] = metrics
            self._update_topology()
            
    def _update_topology(self):
        """Update network topology and recalculate all routes"""
        for source in self.nodes:
            self.routes[source] = {}
            for target in self.nodes:
                if source != target:
                    route = self._calculate_optimal_route(source, target)
                    if route:
                        self.routes[source][target] = route
                        
    def _calculate_optimal_route(self, source: str, target: str) -> Optional[List[str]]:
        """Calculate optimal route using modified Dijkstra with multiple metrics"""
        if source not in self.nodes or target not in self.nodes:
            return None
            
        costs = {node: float('infinity') for node in self.nodes}
        costs[source] = 0
        previous = {node: None for node in self.nodes}
        visited = set()
        
        while len(visited) < len(self.nodes):
            # Find node with minimum cost
            current = min(
                (node for node in self.nodes if node not in visited),
                key=lambda x: costs[x]
            )
            
            if current == target:
                break
                
            visited.add(current)
            
            # Update costs to neighbors
            for neighbor, metrics in self.links[current].items():
                if neighbor not in visited:
                    cost = costs[current] + metrics.calculate_cost()
                    if cost < costs[neighbor]:
                        costs[neighbor] = cost
                        previous[neighbor] = current
                        
        if costs[target] == float('infinity'):
            return None
            
        # Reconstruct path
        path = []
        current = target
        while current is not None:
            path.append(current)
            current = previous[current]
        return list(reversed(path))

class CommandRouter:
    def __init__(self, max_workers: int = 4):
        self.node_id = str(uuid4())
        self.topology = NetworkTopology()
        self.command_queues: Dict[CommandPriority, PriorityQueue] = {
            priority: PriorityQueue() for priority in CommandPriority
        }
        self.response_queues: Dict[str, Queue] = {}
        self.active = True
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.logger = logging.getLogger('CommandRouter')
        
        # Start routing threads
        self.router_threads = [
            threading.Thread(target=self._route_processor, args=(priority,))
            for priority in CommandPriority
        ]
        for thread in self.router_threads:
            thread.daemon = True
            thread.start()
            
    def add_node(self, node_id: str, node_info: dict):
        """Add a new node to the network"""
        self.topology.add_node(node_id, node_info)
        self._update_node_metrics(node_id)
        
    def remove_node(self, node_id: str):
        """Remove a node from the network"""
        self.topology.remove_node(node_id)
        
    def _update_node_metrics(self, node_id: str):
        """Update metrics for links to a node"""
        if node_id in self.topology.nodes:
            for other_node in self.topology.nodes:
                if other_node != node_id:
                    metrics = self._measure_link_metrics(node_id, other_node)
                    self.topology.update_link_metrics(node_id, other_node, metrics)
                    
    def _measure_link_metrics(self, source: str, target: str) -> RoutingMetrics:
        """Measure metrics for a link between nodes"""
        # In real implementation, this would measure actual network metrics
        # For now, we'll simulate with random values
        return RoutingMetrics(
            latency=random.uniform(10, 1000),  # ms
            bandwidth=random.uniform(1, 100),   # Mbps
            reliability=random.uniform(0.8, 1.0),
            hop_count=1,
            load=random.uniform(0, 1.0)
        )
        
    def route_command(self, command: dict, target_id: Optional[str] = None,
                     priority: CommandPriority = CommandPriority.NORMAL) -> str:
        """Route a command with specified priority"""
        command_id = str(uuid4())
        routing_info = {
            'command_id': command_id,
            'source': self.node_id,
            'target': target_id,
            'timestamp': time.time(),
            'ttl': 10,
            'path': [],
            'command': command,
            'priority': priority,
            'signature': self._sign_command(command)
        }
        
        # Add to appropriate priority queue
        self.command_queues[priority].put(
            (priority.to_value(), routing_info)
        )
        return command_id
        
    def _sign_command(self, command: dict) -> str:
        """Create signature for command verification"""
        command_str = json.dumps(command, sort_keys=True)
        return base64.b64encode(
            hashlib.sha256(command_str.encode()).digest()
        ).decode()
        
    def _route_processor(self, priority: CommandPriority):
        """Process and route commands for a specific priority level"""
        while self.active:
            try:
                if not self.command_queues[priority].empty():
                    _, routing_info = self.command_queues[priority].get()
                    
                    if routing_info['ttl'] <= 0:
                        continue
                        
                    routing_info['path'].append(self.node_id)
                    routing_info['ttl'] -= 1
                    
                    # Submit routing task to thread pool
                    self.executor.submit(
                        self._process_routing,
                        routing_info
                    )
                    
                time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Error in route processor: {str(e)}")
                continue
                
    def _process_routing(self, routing_info: dict):
        """Process routing in thread pool"""
        try:
            if routing_info['target'] is None:
                self._broadcast_command(routing_info)
            else:
                self._route_to_target(routing_info)
        except Exception as e:
            self.logger.error(f"Error processing route: {str(e)}")
            
    def _broadcast_command(self, routing_info: dict):
        """Broadcast command to all nodes"""
        for node_id in self.topology.nodes:
            if node_id not in routing_info['path']:
                self._forward_command(routing_info, node_id)
                
    def _route_to_target(self, routing_info: dict):
        """Route command to specific target"""
        target = routing_info['target']
        if target in self.topology.nodes:
            route = self.topology.routes.get(self.node_id, {}).get(target)
            if route and len(route) > 1:
                next_hop = route[1]
                self._forward_command(routing_info, next_hop)
                
    def _forward_command(self, routing_info: dict, next_hop: str):
        """Forward command to next hop with verification"""
        try:
            if next_hop in self.topology.nodes:
                # Verify command hasn't been tampered with
                if self._verify_command(routing_info['command'],
                                     routing_info['signature']):
                    routing_info['path'].append(next_hop)
                    self.command_queues[routing_info['priority']].put(
                        (routing_info['priority'].to_value(), routing_info)
                    )
                else:
                    self.logger.warning(
                        f"Command verification failed: {routing_info['command_id']}"
                    )
        except Exception as e:
            self.logger.error(f"Error forwarding command: {str(e)}")
            
    def _verify_command(self, command: dict, signature: str) -> bool:
        """Verify command signature"""
        command_str = json.dumps(command, sort_keys=True)
        expected_signature = base64.b64encode(
            hashlib.sha256(command_str.encode()).digest()
        ).decode()
        return signature == expected_signature
        
    def get_network_status(self) -> dict:
        """Get detailed network status"""
        return {
            'node_id': self.node_id,
            'nodes': len(self.topology.nodes),
            'routes': {
                k: {
                    'route_count': len(v),
                    'metrics': {
                        target: self.topology.links[k][target].__dict__
                        for target in v
                        if k in self.topology.links
                        and target in self.topology.links[k]
                    }
                }
                for k, v in self.topology.routes.items()
            },
            'queue_sizes': {
                priority.name: queue.qsize()
                for priority, queue in self.command_queues.items()
            }
        }
        
    def shutdown(self):
        """Graceful shutdown of router"""
        self.active = False
        self.executor.shutdown(wait=True)
        for thread in self.router_threads:
            thread.join()
