import os
import json
import time
import random
import threading
from queue import Queue
from uuid import uuid4
from typing import Dict, List, Optional

class CommandRouter:
    def __init__(self):
        self.node_id = str(uuid4())
        self.nodes: Dict[str, dict] = {}  # {node_id: node_info}
        self.routes: Dict[str, Dict[str, List[str]]] = {}  # {source: {target: [route]}}
        self.command_queue = Queue()
        self.response_queues: Dict[str, Queue] = {}
        self.active = True
        
        # Start routing thread
        self.router_thread = threading.Thread(target=self._route_processor)
        self.router_thread.daemon = True
        self.router_thread.start()
        
    def add_node(self, node_id: str, node_info: dict):
        """Add a new node to the network"""
        self.nodes[node_id] = node_info
        self._update_routes()
        
    def remove_node(self, node_id: str):
        """Remove a node from the network"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            self._update_routes()
            
    def _update_routes(self):
        """Update routing table using mesh network topology"""
        for source in self.nodes:
            self.routes[source] = {}
            for target in self.nodes:
                if source != target:
                    route = self._calculate_route(source, target)
                    if route:
                        self.routes[source][target] = route
                        
    def _calculate_route(self, source: str, target: str) -> Optional[List[str]]:
        """Calculate optimal route between nodes using modified Dijkstra's algorithm"""
        if source not in self.nodes or target not in self.nodes:
            return None
            
        distances = {node: float('infinity') for node in self.nodes}
        distances[source] = 0
        previous = {node: None for node in self.nodes}
        unvisited = set(self.nodes.keys())
        
        while unvisited:
            current = min(unvisited, key=lambda x: distances[x])
            if current == target:
                break
                
            unvisited.remove(current)
            
            for neighbor in self._get_neighbors(current):
                if neighbor in unvisited:
                    distance = distances[current] + self._get_distance(current, neighbor)
                    if distance < distances[neighbor]:
                        distances[neighbor] = distance
                        previous[neighbor] = current
                        
        if distances[target] == float('infinity'):
            return None
            
        # Reconstruct path
        path = []
        current = target
        while current is not None:
            path.append(current)
            current = previous[current]
        return list(reversed(path))
        
    def _get_neighbors(self, node_id: str) -> List[str]:
        """Get directly connected neighbors of a node"""
        # In a mesh network, consider all nodes within range as neighbors
        return [n for n in self.nodes if n != node_id]
        
    def _get_distance(self, node1: str, node2: str) -> float:
        """Calculate distance/cost between nodes"""
        # Could be based on various metrics: latency, hop count, bandwidth, etc.
        return 1.0  # For now, assume uniform cost
        
    def route_command(self, command: dict, target_id: Optional[str] = None):
        """Route a command to specific target or broadcast"""
        command_id = str(uuid4())
        routing_info = {
            'command_id': command_id,
            'source': self.node_id,
            'target': target_id,
            'timestamp': time.time(),
            'ttl': 10,  # Time To Live in hops
            'path': [],  # Track path taken
            'command': command
        }
        
        self.command_queue.put(routing_info)
        return command_id
        
    def _route_processor(self):
        """Process and route commands in background"""
        while self.active:
            try:
                if not self.command_queue.empty():
                    routing_info = self.command_queue.get()
                    
                    # Check TTL
                    if routing_info['ttl'] <= 0:
                        continue
                        
                    # Update path
                    routing_info['path'].append(self.node_id)
                    routing_info['ttl'] -= 1
                    
                    # Handle command
                    if routing_info['target'] is None:
                        # Broadcast to all nodes
                        self._broadcast_command(routing_info)
                    else:
                        # Route to specific target
                        self._route_to_target(routing_info)
                        
                time.sleep(0.1)  # Prevent CPU overuse
            except Exception as e:
                continue
                
    def _broadcast_command(self, routing_info: dict):
        """Broadcast command to all nodes"""
        for node_id in self.nodes:
            if node_id not in routing_info['path']:
                self._forward_command(routing_info, node_id)
                
    def _route_to_target(self, routing_info: dict):
        """Route command to specific target"""
        target = routing_info['target']
        if target in self.nodes:
            route = self._calculate_route(self.node_id, target)
            if route and len(route) > 1:
                next_hop = route[1]  # First hop after current node
                self._forward_command(routing_info, next_hop)
                
    def _forward_command(self, routing_info: dict, next_hop: str):
        """Forward command to next hop"""
        try:
            # In real implementation, this would use network communication
            # For now, we'll simulate by adding to target's queue
            if next_hop in self.nodes:
                routing_info['path'].append(next_hop)
                self.command_queue.put(routing_info)
        except:
            pass
            
    def get_network_status(self) -> dict:
        """Get current network status"""
        return {
            'node_id': self.node_id,
            'nodes': len(self.nodes),
            'routes': {k: len(v) for k, v in self.routes.items()},
            'queue_size': self.command_queue.qsize()
        }
        
    def shutdown(self):
        """Shutdown router"""
        self.active = False
        if hasattr(self, 'router_thread'):
            self.router_thread.join()
