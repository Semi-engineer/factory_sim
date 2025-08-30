"""
Configuration management for factory simulation
"""
from dataclasses import dataclass
from typing import Dict, Any
import json


@dataclass
class SimulationConfig:
    """Configuration parameters for factory simulation"""
    
    # Global Parameters
    sim_hours: float = 8.0
    target_prod: int = 1000
    quality_target: float = 95.0  # percentage
    
    # Material & Cost
    material_cost: float = 5.0  # cost per piece
    setup_cost: float = 100.0  # setup cost
    inventory_cost: float = 0.02  # percentage
    defect_cost: float = 10.0  # cost per defective piece
    
    # Labor
    labor_rate: float = 25.0  # per hour
    operators_per_machine: int = 1
    overhead_rate: float = 15.0  # per hour
    
    # Machine
    machine_cost: float = 50.0  # per hour
    maintenance_rate: float = 0.05  # downtime rate
    energy_cost: float = 0.12  # per kWh
    utilization_target: float = 85.0  # percentage
    
    # Quality
    defect_rate: float = 0.02  # 2% defect rate
    rework_rate: float = 0.05  # 5% rework rate
    downtime_rate: float = 0.03  # 3% downtime rate
    
    # Buffer & Flow
    buffer_capacity: int = 50  # pieces
    transport_speed: float = 1.0  # pieces per minute
    batch_size: int = 10  # pieces per batch
    
    # Performance Targets
    oee_target: float = 80.0  # Overall Equipment Effectiveness target
    throughput_target: float = 100.0  # pieces per hour
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            field.name: getattr(self, field.name) 
            for field in self.__dataclass_fields__.values()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationConfig':
        """Create config from dictionary"""
        valid_fields = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)
    
    def save_to_file(self, filename: str):
        """Save configuration to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filename: str) -> 'SimulationConfig':
        """Load configuration from JSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def validate(self) -> list:
        """Validate configuration parameters and return list of issues"""
        issues = []
        
        if self.sim_hours <= 0:
            issues.append("Simulation hours must be positive")
        
        if self.target_prod <= 0:
            issues.append("Target production must be positive")
        
        if not 0 <= self.quality_target <= 100:
            issues.append("Quality target must be between 0 and 100")
        
        if self.material_cost < 0:
            issues.append("Material cost cannot be negative")
        
        if self.labor_rate < 0:
            issues.append("Labor rate cannot be negative")
        
        if self.operators_per_machine < 0:
            issues.append("Operators per machine cannot be negative")
        
        if not 0 <= self.defect_rate <= 1:
            issues.append("Defect rate must be between 0 and 1")
        
        if not 0 <= self.rework_rate <= 1:
            issues.append("Rework rate must be between 0 and 1")
        
        if not 0 <= self.downtime_rate <= 1:
            issues.append("Downtime rate must be between 0 and 1")
        
        if self.buffer_capacity <= 0:
            issues.append("Buffer capacity must be positive")
        
        if self.transport_speed <= 0:
            issues.append("Transport speed must be positive")
        
        if self.batch_size <= 0:
            issues.append("Batch size must be positive")
        
        return issues
    
    def get_hourly_costs(self) -> Dict[str, float]:
        """Calculate hourly costs based on configuration"""
        return {
            "labor_cost_per_hour": self.labor_rate * self.operators_per_machine,
            "machine_cost_per_hour": self.machine_cost,
            "overhead_cost_per_hour": self.overhead_rate,
            "total_cost_per_hour": (
                self.labor_rate * self.operators_per_machine + 
                self.machine_cost + 
                self.overhead_rate
            )
        }
    
    def get_quality_metrics(self) -> Dict[str, float]:
        """Get quality-related metrics"""
        good_rate = 1 - self.defect_rate
        effective_rate = good_rate * (1 - self.rework_rate)
        
        return {
            "good_rate": good_rate * 100,
            "effective_rate": effective_rate * 100,
            "expected_defects_per_hour": self.throughput_target * self.defect_rate,
            "expected_rework_per_hour": self.throughput_target * self.rework_rate
        }
    
    def calculate_oee(self, availability: float, performance: float, quality: float) -> float:
        """Calculate Overall Equipment Effectiveness"""
        return (availability / 100) * (performance / 100) * (quality / 100) * 100
    
    def __str__(self) -> str:
        return f"SimulationConfig(hours={self.sim_hours}, target={self.target_prod}, quality={self.quality_target}%)"


# Default configurations for different scenarios
class ConfigPresets:
    """Predefined configuration presets for different scenarios"""
    
    @staticmethod
    def high_volume_production() -> SimulationConfig:
        """Configuration for high-volume production"""
        return SimulationConfig(
            sim_hours=24.0,
            target_prod=5000,
            quality_target=98.0,
            batch_size=50,
            buffer_capacity=100,
            utilization_target=90.0,
            defect_rate=0.01,
            throughput_target=200.0
        )
    
    @staticmethod
    def precision_manufacturing() -> SimulationConfig:
        """Configuration for precision manufacturing"""
        return SimulationConfig(
            sim_hours=8.0,
            target_prod=200,
            quality_target=99.5,
            material_cost=25.0,
            defect_cost=100.0,
            defect_rate=0.005,
            rework_rate=0.02,
            batch_size=5,
            throughput_target=25.0
        )
    
    @staticmethod
    def cost_optimized() -> SimulationConfig:
        """Configuration optimized for cost efficiency"""
        return SimulationConfig(
            sim_hours=8.0,
            target_prod=800,
            material_cost=2.0,
            labor_rate=18.0,
            machine_cost=30.0,
            overhead_rate=10.0,
            utilization_target=95.0,
            batch_size=25,
            buffer_capacity=30
        )
    
    @staticmethod
    def flexible_manufacturing() -> SimulationConfig:
        """Configuration for flexible manufacturing"""
        return SimulationConfig(
            sim_hours=8.0,
            target_prod=500,
            batch_size=1,  # Single piece flow
            buffer_capacity=10,
            transport_speed=2.0,
            rework_rate=0.08,
            utilization_target=75.0,
            throughput_target=60.0
        )
