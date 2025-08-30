"""
Factory Simulation Package
"""

# Version info
__version__ = "2.0.0"
__author__ = "Factory Simulation Team"
__description__ = "Modern Factory Real-Time Simulation with GUI"

# Import main classes for easy access
from models.job import Job
from models.machine import Machine
from models.factory import Factory
from simulation.simulation_manager import SimulationManager

__all__ = [
    "Job",
    "Machine", 
    "Factory",
    "SimulationManager"
]
