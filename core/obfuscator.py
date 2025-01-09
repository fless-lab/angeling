import random
import string
import base64
import zlib
import ast
import astor
import marshal
import types
import builtins
import sys
import hashlib
import struct
import itertools
from typing import Dict, List, Set, Optional
import logging
from datetime import datetime, timedelta

class ObfuscationType:
    RENAME = 'rename'
    JUNK = 'junk'
    FLOW = 'flow'
    ENCODE = 'encode'
    STRING = 'string'
    TIMING = 'timing'

class CodeObfuscator:
    def __init__(self):
        self.logger = logging.getLogger('CodeObfuscator')
        self.var_mapping: Dict[str, str] = {}
        self.string_mapping: Dict[str, str] = {}
        self.used_names: Set[str] = set()
        self.junk_functions: List[str] = []
        self._init_reserved_names()
        
    def _init_reserved_names(self):
        """Initialize reserved names that shouldn't be renamed"""
        self.reserved_names = set(dir(builtins))
        self.reserved_names.update([
            'self', 'cls', 'args', 'kwargs', 'super',
            'yield', 'return', 'print', 'True', 'False', 'None'
        ])
        
    def _generate_random_name(self, length: int = None) -> str:
        """Generate a random, unique variable name"""
        if length is None:
            length = random.randint(8, 16)
            
        while True:
            # Use confusing character combinations
            chars = 'OoIlL1' + string.ascii_letters + string.digits
            name = ''.join(random.choice(chars) for _ in range(length))
            
            # Ensure name starts with a letter and is unique
            if name[0].isalpha() and name not in self.used_names:
                self.used_names.add(name)
                return name
                
    def _generate_junk_expression(self) -> str:
        """Generate complex mathematical expressions"""
        operators = ['+', '-', '*', '/', '//', '%', '**']
        values = list(range(1, 100)) + [0.1, 0.01, 0.001]
        
        def _gen_expr(depth=0):
            if depth > 3 or random.random() < 0.3:
                return str(random.choice(values))
            op = random.choice(operators)
            left = _gen_expr(depth + 1)
            right = _gen_expr(depth + 1)
            return f"({left} {op} {right})"
            
        return _gen_expr()
        
    def _generate_junk_condition(self) -> str:
        """Generate complex conditional expressions"""
        comparisons = ['==', '!=', '<', '>', '<=', '>=']
        logic_ops = ['and', 'or']
        
        def _gen_cond(depth=0):
            if depth > 2 or random.random() < 0.3:
                return f"{self._generate_junk_expression()} {random.choice(comparisons)} {self._generate_junk_expression()}"
            op = random.choice(logic_ops)
            left = _gen_cond(depth + 1)
            right = _gen_cond(depth + 1)
            return f"({left} {op} {right})"
            
        return _gen_cond()
        
    def _rename_variables(self, node: ast.AST) -> None:
        """Rename variables and functions to obfuscated names"""
        if isinstance(node, ast.Name):
            if node.id not in self.reserved_names:
                if isinstance(node.ctx, ast.Store):
                    if node.id not in self.var_mapping:
                        self.var_mapping[node.id] = self._generate_random_name()
                if node.id in self.var_mapping:
                    node.id = self.var_mapping[node.id]
                    
        elif isinstance(node, ast.FunctionDef):
            if node.name not in self.reserved_names:
                if node.name not in self.var_mapping:
                    self.var_mapping[node.name] = self._generate_random_name()
                node.name = self.var_mapping[node.name]
                
        elif isinstance(node, ast.ClassDef):
            if node.name not in self.reserved_names:
                if node.name not in self.var_mapping:
                    self.var_mapping[node.name] = self._generate_random_name()
                node.name = self.var_mapping[node.name]
                
        for child in ast.iter_child_nodes(node):
            self._rename_variables(child)
            
    def _obfuscate_strings(self, node: ast.AST) -> None:
        """Obfuscate string literals"""
        if isinstance(node, ast.Str):
            if node.s not in self.string_mapping:
                # XOR encode with random key
                key = random.randint(1, 255)
                encoded = bytes(b ^ key for b in node.s.encode())
                encoded_str = base64.b85encode(encoded).decode()
                decode_expr = f"''.join(chr(x ^ {key}) for x in base64.b85decode('{encoded_str}'))"
                self.string_mapping[node.s] = decode_expr
            node.s = self.string_mapping[node.s]
            
        for child in ast.iter_child_nodes(node):
            self._obfuscate_strings(child)
            
    def _add_control_flow(self, node: ast.AST) -> None:
        """Add complex control flow obfuscation"""
        if isinstance(node, ast.FunctionDef):
            # Add complex conditions and loops
            junk_cond = self._generate_junk_condition()
            junk_body = [
                ast.parse(f"if {junk_cond}:").body[0],
                ast.parse(f"while {junk_cond} and False:").body[0]
            ]
            node.body = junk_body + node.body
            
        for child in ast.iter_child_nodes(node):
            self._add_control_flow(child)
            
    def _add_junk_code(self, code: str) -> str:
        """Add sophisticated junk code"""
        junk_templates = [
            # Complex mathematical calculations
            '''
def {name}():
    x = {expr1}
    y = {expr2}
    if {condition}:
        return x
    return y
''',
            # Fake encryption operations
            '''
def {name}():
    data = bytes([{bytes}])
    key = {key}
    return bytes(x ^ key for x in data)
''',
            # Network-like operations
            '''
def {name}():
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.001)
        s.connect(('127.0.0.1', {port}))
        s.close()
    except:
        pass
    return {expr1}
'''
        ]
        
        lines = code.split('\n')
        num_junks = random.randint(5, 10)
        
        for _ in range(num_junks):
            template = random.choice(junk_templates)
            junk = template.format(
                name=self._generate_random_name(),
                expr1=self._generate_junk_expression(),
                expr2=self._generate_junk_expression(),
                condition=self._generate_junk_condition(),
                bytes=','.join(str(random.randint(0, 255)) for _ in range(32)),
                key=random.randint(1, 255),
                port=random.randint(1024, 65535)
            )
            pos = random.randint(0, len(lines))
            lines.insert(pos, junk)
            
        return '\n'.join(lines)
        
    def _add_timing_evasion(self, code: str) -> str:
        """Add sophisticated timing-based evasion"""
        timing_code = '''
import time
import random
import threading
from datetime import datetime, timedelta

def _timing_check():
    start = datetime.now()
    time.sleep(random.uniform(0.1, 0.3))
    end = datetime.now()
    
    # Check if time diff is suspicious
    if (end - start) < timedelta(milliseconds=50):
        sys.exit()
        
    # Start background timing checks
    def _background_check():
        while True:
            time.sleep(random.uniform(10, 30))
            _timing_check()
            
    t = threading.Thread(target=_background_check, daemon=True)
    t.start()

_timing_check()
'''
        return timing_code + code
        
    def _encode_code(self, code: str) -> str:
        """Apply multiple layers of encoding"""
        # First layer: marshal
        code_obj = compile(code, '<string>', 'exec')
        marshalled = marshal.dumps(code_obj)
        
        # Second layer: custom encoding
        key = bytes(random.randint(0, 255) for _ in range(16))
        encoded = bytes(x ^ y for x, y in zip(marshalled, itertools.cycle(key)))
        
        # Third layer: compression
        compressed = zlib.compress(encoded, level=9)
        
        # Final layer: base85 encoding
        final = base64.b85encode(compressed)
        
        # Create sophisticated loader
        loader = f'''
import base64
import zlib
import marshal
import itertools
import sys
import random
import time

def _load(key, data):
    # Decode layers
    decoded = base64.b85decode(data)
    decompressed = zlib.decompress(decoded)
    decoded = bytes(x ^ y for x, y in zip(decompressed, itertools.cycle(key)))
    code = marshal.loads(decoded)
    
    # Add runtime checks
    def _check():
        if sys.gettrace() is not None:
            sys.exit()
    _check()
    
    # Execute with timing variation
    time.sleep(random.uniform(0.1, 0.5))
    exec(code, globals())

# Execute with key
_load({key}, {final})
'''
        return loader
        
    def obfuscate_code(self, code: str, 
                       techniques: Optional[List[str]] = None) -> str:
        """Apply multiple obfuscation techniques"""
        if techniques is None:
            techniques = [
                ObfuscationType.RENAME,
                ObfuscationType.STRING,
                ObfuscationType.FLOW,
                ObfuscationType.JUNK,
                ObfuscationType.TIMING,
                ObfuscationType.ENCODE
            ]
            
        try:
            # Parse code
            tree = ast.parse(code)
            
            # Apply AST transformations
            if ObfuscationType.RENAME in techniques:
                self._rename_variables(tree)
            if ObfuscationType.STRING in techniques:
                self._obfuscate_strings(tree)
            if ObfuscationType.FLOW in techniques:
                self._add_control_flow(tree)
                
            # Convert back to source
            obfuscated = astor.to_source(tree)
            
            # Apply string-level transformations
            if ObfuscationType.JUNK in techniques:
                obfuscated = self._add_junk_code(obfuscated)
            if ObfuscationType.TIMING in techniques:
                obfuscated = self._add_timing_evasion(obfuscated)
            if ObfuscationType.ENCODE in techniques:
                obfuscated = self._encode_code(obfuscated)
                
            return obfuscated
            
        except Exception as e:
            self.logger.error(f"Obfuscation failed: {str(e)}")
            return code  # Return original code if obfuscation fails
            
    def obfuscate_file(self, input_file: str, output_file: str,
                       techniques: Optional[List[str]] = None) -> bool:
        """Obfuscate a Python source file"""
        try:
            with open(input_file, 'r') as f:
                code = f.read()
                
            obfuscated = self.obfuscate_code(code, techniques)
            
            with open(output_file, 'w') as f:
                f.write(obfuscated)
                
            return True
        except Exception as e:
            self.logger.error(f"File obfuscation failed: {str(e)}")
            return False
