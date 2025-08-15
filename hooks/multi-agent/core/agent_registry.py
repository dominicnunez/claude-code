#!/usr/bin/env python3
"""
Agent registry for multi-agent orchestration system.
Manages agent discovery, validation, and health monitoring.
"""

import os
import json
import time
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass
class AgentInfo:
    """Information about an available agent."""
    name: str
    path: str
    description: str
    capabilities: List[str]
    model: Optional[str] = None
    tools: Optional[List[str]] = None
    language_affinity: Optional[str] = None
    last_validated: Optional[datetime] = None
    validation_status: str = "unknown"  # unknown, valid, invalid
    performance_metrics: Optional[Dict] = None


@dataclass
class AgentHealth:
    """Health metrics for an agent."""
    agent_name: str
    success_rate: float
    avg_response_time: float
    last_success: Optional[datetime]
    last_failure: Optional[datetime]
    total_invocations: int
    recent_failures: List[str]  # Recent error messages


class AgentRegistry:
    """Manages discovery and validation of available agents."""
    
    def __init__(self, agents_path: Optional[str] = None):
        """Initialize agent registry."""
        if agents_path is None:
            agents_path = Path.home() / ".claude" / "agents"
        
        self.agents_path = Path(agents_path)
        self.agents: Dict[str, AgentInfo] = {}
        self.health_metrics: Dict[str, AgentHealth] = {}
        self.last_scan: Optional[datetime] = None
        
        # Language patterns for automatic affinity detection
        self.language_patterns = {
            'go': ['golang', 'go lang', 'go programming', 'gopher'],
            'python': ['python', 'py', 'django', 'flask', 'fastapi'],
            'rust': ['rust', 'cargo', 'rustacean'],
            'javascript': ['javascript', 'js', 'node', 'npm', 'react', 'vue'],
            'typescript': ['typescript', 'ts', 'angular'],
            'java': ['java', 'spring', 'maven', 'gradle'],
            'csharp': ['c#', 'csharp', 'dotnet', '.net'],
            'cpp': ['c++', 'cpp', 'cmake'],
            'c': ['c programming', ' c lang']
        }
        
    def scan_agents(self, force: bool = False) -> None:
        """
        Scan agents directory for available agents.
        
        Args:
            force: Force rescan even if recently scanned
        """
        if not force and self.last_scan and datetime.now() - self.last_scan < timedelta(minutes=5):
            return  # Skip if recently scanned
            
        self.agents.clear()
        
        if not self.agents_path.exists():
            print(f"Warning: Agents directory not found: {self.agents_path}")
            return
            
        for agent_file in self.agents_path.glob("*.md"):
            try:
                agent_info = self._parse_agent_file(agent_file)
                if agent_info:
                    self.agents[agent_info.name] = agent_info
            except Exception as e:
                print(f"Warning: Failed to parse agent file {agent_file}: {e}")
                
        self.last_scan = datetime.now()
        
    def _parse_agent_file(self, agent_file: Path) -> Optional[AgentInfo]:
        """Parse an agent markdown file to extract agent information."""
        try:
            with open(agent_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return None
            
        # Extract agent name from filename
        agent_name = agent_file.stem
        
        # Parse YAML frontmatter if present
        frontmatter = {}
        description = ""
        
        if content.startswith('---'):
            try:
                # Split frontmatter and content
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                    content = parts[2].strip()
                    
            except yaml.YAMLError:
                pass
                
        # Extract description (first paragraph or from frontmatter)
        if 'description' in frontmatter:
            description = frontmatter['description']
        else:
            # Extract first paragraph as description
            lines = content.split('\n')
            desc_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    desc_lines.append(line)
                elif desc_lines:  # Stop at first blank line after content
                    break
            description = ' '.join(desc_lines)[:200]  # Limit length
            
        # Extract capabilities from description and content
        capabilities = self._extract_capabilities(description, content)
        
        # Detect language affinity
        language_affinity = self._detect_language_affinity(agent_name, description, content)
        
        # Extract model and tools from frontmatter
        model = frontmatter.get('model')
        tools = frontmatter.get('tools', [])
        if isinstance(tools, str):
            tools = [tools]
            
        return AgentInfo(
            name=agent_name,
            path=str(agent_file),
            description=description,
            capabilities=capabilities,
            model=model,
            tools=tools,
            language_affinity=language_affinity
        )
        
    def _extract_capabilities(self, description: str, content: str) -> List[str]:
        """Extract agent capabilities from description and content."""
        capabilities = []
        text = (description + " " + content).lower()
        
        # Architecture-related capabilities
        if any(word in text for word in ['architect', 'design', 'architecture', 'system design']):
            capabilities.append('architecture')
            
        # Implementation capabilities
        if any(word in text for word in ['implement', 'development', 'coding', 'programming']):
            capabilities.append('implementation')
            
        # Code review capabilities
        if any(word in text for word in ['review', 'analyze', 'audit', 'quality']):
            capabilities.append('code_review')
            
        # Microservices capabilities
        if any(word in text for word in ['microservice', 'distributed', 'api', 'service']):
            capabilities.append('microservices')
            
        # Testing capabilities
        if any(word in text for word in ['test', 'testing', 'unit test', 'integration']):
            capabilities.append('testing')
            
        # Documentation capabilities
        if any(word in text for word in ['document', 'documentation', 'readme', 'docs']):
            capabilities.append('documentation')
            
        return capabilities
        
    def _detect_language_affinity(self, agent_name: str, description: str, content: str) -> Optional[str]:
        """Detect programming language affinity from agent information."""
        text = (agent_name + " " + description + " " + content).lower()
        
        # Score each language based on pattern matches
        language_scores = {}
        for language, patterns in self.language_patterns.items():
            score = 0
            for pattern in patterns:
                count = text.count(pattern.lower())
                score += count
                
            if score > 0:
                language_scores[language] = score
                
        # Return language with highest score
        if language_scores:
            return max(language_scores.items(), key=lambda x: x[1])[0]
            
        return None
        
    def get_agents_by_capability(self, capability: str) -> List[AgentInfo]:
        """Get agents that have a specific capability."""
        return [agent for agent in self.agents.values() 
                if capability in agent.capabilities]
                
    def get_agents_by_language(self, language: str) -> List[AgentInfo]:
        """Get agents with affinity for a specific language."""
        return [agent for agent in self.agents.values() 
                if agent.language_affinity == language.lower()]
                
    def get_architect_agents(self, language: Optional[str] = None) -> List[AgentInfo]:
        """Get agents capable of architecture design for a language."""
        architects = self.get_agents_by_capability('architecture')
        
        if language:
            # Filter by language affinity
            lang_architects = [a for a in architects if a.language_affinity == language.lower()]
            if lang_architects:
                return lang_architects
                
        return architects
        
    def get_developer_agents(self, language: Optional[str] = None) -> List[AgentInfo]:
        """Get agents capable of implementation for a language."""
        developers = self.get_agents_by_capability('implementation')
        
        if language:
            # Filter by language affinity
            lang_developers = [d for d in developers if d.language_affinity == language.lower()]
            if lang_developers:
                return lang_developers
                
        return developers
        
    def validate_agent(self, agent_name: str) -> bool:
        """
        Validate that an agent is available and functional.
        
        Args:
            agent_name: Name of agent to validate
            
        Returns:
            True if agent is valid and available
        """
        if agent_name not in self.agents:
            return False
            
        agent = self.agents[agent_name]
        
        # Check if agent file still exists
        if not Path(agent.path).exists():
            agent.validation_status = "invalid"
            return False
            
        # For now, mark as valid if file exists
        # In future, could test with a simple prompt
        agent.validation_status = "valid"
        agent.last_validated = datetime.now()
        
        return True
        
    def record_agent_invocation(self, agent_name: str, success: bool, 
                              response_time: float, error_msg: Optional[str] = None) -> None:
        """Record metrics from an agent invocation."""
        if agent_name not in self.health_metrics:
            self.health_metrics[agent_name] = AgentHealth(
                agent_name=agent_name,
                success_rate=0.0,
                avg_response_time=0.0,
                last_success=None,
                last_failure=None,
                total_invocations=0,
                recent_failures=[]
            )
            
        health = self.health_metrics[agent_name]
        health.total_invocations += 1
        
        # Update response time (rolling average)
        if health.avg_response_time == 0:
            health.avg_response_time = response_time
        else:
            health.avg_response_time = (health.avg_response_time * 0.8 + response_time * 0.2)
            
        if success:
            health.last_success = datetime.now()
        else:
            health.last_failure = datetime.now()
            if error_msg:
                health.recent_failures.append(error_msg)
                # Keep only last 5 failures
                health.recent_failures = health.recent_failures[-5:]
                
        # Recalculate success rate (simple moving average over last 100 invocations)
        # This is simplified - in practice would track individual results
        current_successes = health.total_invocations * health.success_rate
        if success:
            current_successes += 1
        health.success_rate = current_successes / health.total_invocations
        
    def get_best_agents(self, capability: str, language: Optional[str] = None, 
                       count: int = 5) -> List[AgentInfo]:
        """
        Get best agents for a capability, optionally filtered by language.
        
        Args:
            capability: Required capability
            language: Optional language filter
            count: Maximum number of agents to return
            
        Returns:
            List of best agents sorted by health metrics
        """
        candidates = self.get_agents_by_capability(capability)
        
        if language:
            lang_candidates = [a for a in candidates if a.language_affinity == language.lower()]
            if lang_candidates:
                candidates = lang_candidates
                
        # Sort by health metrics (success rate, then response time)
        def agent_score(agent: AgentInfo) -> tuple:
            health = self.health_metrics.get(agent.name)
            if health:
                return (health.success_rate, -health.avg_response_time)
            else:
                return (1.0, 0.0)  # Unknown agents get default score
                
        candidates.sort(key=agent_score, reverse=True)
        return candidates[:count]
        
    def get_registry_stats(self) -> Dict:
        """Get statistics about the agent registry."""
        total_agents = len(self.agents)
        by_language = {}
        by_capability = {}
        
        for agent in self.agents.values():
            # Count by language
            if agent.language_affinity:
                by_language[agent.language_affinity] = by_language.get(agent.language_affinity, 0) + 1
                
            # Count by capability
            for cap in agent.capabilities:
                by_capability[cap] = by_capability.get(cap, 0) + 1
                
        return {
            'total_agents': total_agents,
            'by_language': by_language,
            'by_capability': by_capability,
            'last_scan': self.last_scan.isoformat() if self.last_scan else None
        }


def main():
    """Test agent registry functionality."""
    registry = AgentRegistry()
    
    print("Scanning agents...")
    registry.scan_agents()
    
    print(f"\nRegistry Stats:")
    stats = registry.get_registry_stats()
    print(f"  Total agents: {stats['total_agents']}")
    print(f"  By language: {stats['by_language']}")
    print(f"  By capability: {stats['by_capability']}")
    
    print(f"\nArchitect agents:")
    architects = registry.get_architect_agents()
    for agent in architects:
        print(f"  {agent.name}: {agent.language_affinity} - {agent.description[:50]}...")
        
    print(f"\nDeveloper agents:")
    developers = registry.get_developer_agents()
    for agent in developers:
        print(f"  {agent.name}: {agent.language_affinity} - {agent.description[:50]}...")


if __name__ == "__main__":
    main()