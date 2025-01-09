# Angel Framework Development Guide

## Development Environment Setup

### Required Tools
- Python 3.8+
- Git
- Virtual Environment (recommended)

### Setup Steps
1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Architecture Overview

The Angel framework is built with a focus on autonomy, intelligence, and stealth. The architecture is designed to be modular, extensible, and resilient.

### Core Components

#### Brain (core/brain.py)
The autonomous decision-making engine that:
- Analyzes environment and system state
- Manages risk assessment and stealth levels
- Controls operation timing based on conditions
- Learns from past decisions and outcomes
- Adapts behavior based on environmental factors

Key classes:
- `AngelBrain`: Main brain implementation
  - Environment analysis
  - Decision making
  - Risk assessment
  - Learning capabilities

#### Router (modules/router.py)
Mesh network routing system that:
- Manages P2P communication
- Handles dynamic route discovery
- Distributes commands across the network
- Implements optimal path calculation

Key classes:
- `CommandRouter`: Core routing implementation
  - Node management
  - Route calculation
  - Command distribution
  - Network resilience

#### Collector (modules/collector.py)
Advanced data collection module supporting:
- Browser password recovery
- Screen and webcam capture
- Keylogging capabilities
- System information gathering
- Browser cookie collection

#### Network (modules/network.py)
Network operations module handling:
- Network scanning
- P2P connection establishment
- Payload propagation
- Protocol-specific deployment (SMB/HTTP/DNS)

#### Comms (modules/comms.py)
Secure communications module implementing:
- Tor network integration
- I2P network support
- DNS tunneling capabilities
- Channel rotation
- Identity management

## Project Structure

```plaintext
angeling/
├── core/
│   ├── __init__.py
│   ├── brain.py
│   ├── crypter.py
│   ├── obfuscator.py
│   └── stealth.py
├── modules/
│   ├── __init__.py
│   ├── router.py
│   ├── collector.py
│   ├── network.py
│   ├── comms.py
│   ├── polyglot.py
│   ├── persistence.py
│   └── communication.py
├── docs/
│   ├── README.md
│   └── DEVELOPMENT.md
├── main.py
├── builder.py
└── requirements.txt
```

## Component Development Guidelines

### Adding New Components

1. Create new component file in appropriate directory
2. Implement required interfaces
3. Update documentation
4. Add tests
5. Update builder if needed

### Code Style
- Follow PEP 8 guidelines
- Use type hints for function parameters
- Include docstrings for classes and functions
- Keep functions focused and modular

### Security Practices
- Implement proper encryption for all communications
- Use secure random number generation
- Clean up sensitive data from memory
- Implement anti-debugging measures
- Use timing-based detection evasion

### Error Handling
- Implement graceful error recovery
- Use try/except blocks appropriately
- Log errors without exposing sensitive information
- Maintain stealth even during errors

### Testing
- Write unit tests for core functionality
- Test network operations in isolated environments
- Verify stealth capabilities
- Test error recovery mechanisms

## Adding New Features

### Brain Enhancements
1. Add new decision factors in `AngelBrain.analyze_environment()`
2. Implement new decision rules in `AngelBrain.make_decision()`
3. Update learning mechanisms in `AngelBrain._learn_from_decision()`

### Network Capabilities
1. Add new protocols in `NetworkOperations`
2. Implement new propagation methods
3. Update routing algorithms in `CommandRouter`

### Data Collection
1. Add new collection methods in `Collector`
2. Implement new browser support
3. Add system information gathering capabilities

### Communication Channels
1. Implement new transport protocols in `SecureComms`
2. Add new channel types
3. Enhance channel rotation logic

## Building New Modules

### Module Structure
```python
class NewModule:
    def __init__(self, config=None):
        self.config = config or {}
        self.initialize_components()

    def initialize_components(self):
        # Setup required components
        pass

    def cleanup(self):
        # Cleanup resources
        pass
```

### Integration Steps
1. Create new module file in `modules/`
2. Implement required interfaces
3. Add to main Angel class
4. Update documentation
5. Add test cases

## Debugging and Testing

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing Environment
- Use virtual machines for testing
- Setup isolated network environments
- Test against different security solutions
- Verify stealth capabilities

### Performance Testing
- Test memory usage
- Verify network efficiency
- Check CPU utilization
- Monitor stealth effectiveness

## Contributing

### Pull Request Process
1. Create feature branch
2. Implement changes
3. Add/update tests
4. Update documentation
5. Submit pull request

### Code Review Guidelines
- Verify security measures
- Check error handling
- Review stealth capabilities
- Validate performance impact
- Ensure documentation updates

## Deployment

### Building
1. Update version numbers
2. Run test suite
3. Build distribution packages
4. Test in isolated environment

### Distribution
- Create obfuscated builds
- Test in target environments
- Verify stealth capabilities
- Check communication channels

## Security Considerations

### Development Security
- Use secure development environment
- Implement proper access controls
- Secure source code storage
- Clean build environments

### Runtime Security
- Implement memory protection
- Use secure communication
- Implement anti-analysis features
- Maintain stealth capabilities

### Testing Security
- Use isolated test environments
- Implement secure test data
- Clean test environments
- Verify security measures

## Performance Optimization

### Guidelines
1. Minimize file size
2. Optimize memory usage
3. Reduce network traffic
4. Handle errors efficiently

### Example Optimization
```python
# Before
def process_data(data):
    return ''.join([str(x) for x in data])

# After
def process_data(data):
    return ''.join(map(str, data))
```

## Documentation

### Component Documentation
```python
class Component:
    """
    Component description.
    
    Attributes:
        attr1 (type): description
        attr2 (type): description
    
    Example:
        >>> component = Component()
        >>> result = component.method()
    """
```

### Update Process
1. Update README.md
2. Update DEVELOPMENT.md
3. Update docstrings
4. Update version history

---

**Note**: Keep this document updated with any architectural or development process changes.
