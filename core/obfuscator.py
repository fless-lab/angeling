import random
import string
import base64
import zlib
import ast
import astor

class CodeObfuscator:
    def __init__(self):
        self.var_mapping = {}
        
    def _generate_random_name(self, length=10):
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
        
    def _rename_variables(self, node):
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Store):
                if node.id not in self.var_mapping:
                    self.var_mapping[node.id] = self._generate_random_name()
            if node.id in self.var_mapping:
                node.id = self.var_mapping[node.id]
        for child in ast.iter_child_nodes(node):
            self._rename_variables(child)
            
    def obfuscate_code(self, code):
        # Parse the code into an AST
        tree = ast.parse(code)
        
        # Rename variables
        self._rename_variables(tree)
        
        # Convert back to source code
        obfuscated = astor.to_source(tree)
        
        # Compress and encode
        compressed = zlib.compress(obfuscated.encode())
        encoded = base64.b85encode(compressed)
        
        # Create self-extracting code
        loader = f'''
import base64
import zlib
exec(zlib.decompress(base64.b85decode({encoded})))
'''
        return loader
        
    def add_junk_code(self, code):
        """Add meaningless code to confuse analysis"""
        junk_functions = [
            'def _' + self._generate_random_name() + '():\n    return ' + str(random.randint(1, 1000)),
            'def _' + self._generate_random_name() + '():\n    x = ' + str(random.random()) + '\n    return x * 2',
        ]
        
        lines = code.split('\n')
        for _ in range(random.randint(3, 7)):
            pos = random.randint(0, len(lines))
            junk = random.choice(junk_functions)
            lines.insert(pos, junk)
            
        return '\n'.join(lines)
        
    def add_timing_evasion(self, code):
        """Add timing-based sandbox evasion"""
        evasion_code = '''
import time
import random
time.sleep(random.uniform(1, 3))  # Random sleep to evade timing analysis
'''
        return evasion_code + code
