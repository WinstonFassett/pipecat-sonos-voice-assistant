import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class MCPServer:
    command: str
    args: List[str]
    env: Dict[str, str]
    description: str = ""
    
class MCPRegistry:
    """A local MCP Registry that reads from a local JSON file"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the registry with a local configuration file"""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "mcp_registry_config.json")
        
        self.config_path = config_path
        self._load_config()
    
    def _load_config(self):
        """Load the configuration from the JSON file"""
        try:
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {"mcpServers": {}}
            # Create the file with empty config
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2)
    
    def get_servers(self) -> List[MCPServer]:
        """Get a list of all available servers"""
        servers = []
        for name, server_config in self.config.get("mcpServers", {}).items():
            servers.append(
                MCPServer(
                    command=server_config.get("command", ""),
                    args=server_config.get("args", []),
                    env=server_config.get("env", {}),
                    description=server_config.get("description", "")
                )
            )
        return servers