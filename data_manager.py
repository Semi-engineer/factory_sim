"""
Data management for factory simulation
Handles export, import, and data persistence
"""

import csv
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from models import Factory, Machine
from simulation_engine import SimulationManager


class DataExporter:
    """Handles data export in various formats"""
    
    def __init__(self, factory: Factory, sim_manager: SimulationManager):
        self.factory = factory
        self.sim_manager = sim_manager
    
    def export_machine_data(self, filename: str = None) -> str:
        """Export machine data to CSV"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"factory_machines_{timestamp}.csv"
        
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Machine_Name", "Type", "Base_Time_min", "Setup_Time_min",
                "Position_X", "Position_Y", "Queue_Length", "Utilization_%",
                "Throughput_parts_per_min", "Total_Output", "Working_Time_min"
            ])
            
            for machine in self.factory.machines.values():
                writer.writerow([
                    machine.name, machine.machine_type, machine.base_time,
                    machine.setup_time, machine.x, machine.y,
                    machine.get_queue_length(),
                    f"{machine.get_utilization(self.sim_manager.current_time):.2f}",
                    f"{machine.get_throughput(self.sim_manager.current_time):.2f}",
                    machine.total_output, f"{machine.total_working_time:.2f}"
                ])
        
        return filename
    
    def export_timeseries_data(self, filename: str = None) -> str:
        """Export time series data to CSV"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"factory_timeseries_{timestamp}.csv"
        
        if not self.sim_manager.time_history:
            raise ValueError("No time series data available")
        
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Time_min", "Total_Throughput", "Avg_Utilization_%", "Total_WIP"])
            
            for i in range(len(self.sim_manager.time_history)):
                writer.writerow([
                    f"{self.sim_manager.time_history[i]:.2f}",
                    f"{self.sim_manager.throughput_history[i]:.2f}",
                    f"{self.sim_manager.utilization_history[i]:.2f}",
                    self.sim_manager.wip_history[i]
                ])
        
        return filename
    
    def export_layout_config(self, filename: str = None) -> str:
        """Export factory layout configuration to JSON"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"factory_layout_{timestamp}.json"
        
        layout_data = {
            "version": "2.0",
            "export_time": datetime.now().isoformat(),
            "simulation_params": {
                "current_time": self.sim_manager.current_time,
                "speed_factor": self.sim_manager.speed_factor,
                "is_running": self.sim_manager.is_running
            },
            "machines": []
        }
        
        for machine in self.factory.machines.values():
            layout_data["machines"].append({
                "name": machine.name,
                "type": machine.machine_type,
                "base_time": machine.base_time,
                "setup_time": machine.setup_time,
                "position": {"x": machine.x, "y": machine.y},
                "dimensions": {"width": machine.width, "height": machine.height}
            })
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(layout_data, f, indent=2)
        
        return filename
    
    def export_all_data(self) -> Dict[str, str]:
        """Export all data types"""
        files = {}
        
        try:
            files["machines"] = self.export_machine_data()
            files["layout"] = self.export_layout_config()
            
            if self.sim_manager.time_history:
                files["timeseries"] = self.export_timeseries_data()
            
        except Exception as e:
            raise Exception(f"Export failed: {str(e)}")
        
        return files


class DataImporter:
    """Handles data import from various formats"""
    
    def __init__(self, factory: Factory):
        self.factory = factory
    
    def import_layout_from_json(self, filename: str) -> bool:
        """Import factory layout from JSON file"""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Validate data structure
            if not self._validate_json_layout(data):
                raise ValueError("Invalid JSON layout format")
            
            # Clear existing machines
            self.factory.machines.clear()
            
            # Load machines
            for machine_data in data.get("machines", []):
                machine = Machine(
                    name=machine_data["name"],
                    machine_type=machine_data["type"],
                    base_time=machine_data["base_time"],
                    setup_time=machine_data["setup_time"],
                    x=machine_data.get("position", {}).get("x", machine_data.get("x", 0)),
                    y=machine_data.get("position", {}).get("y", machine_data.get("y", 0))
                )
                self.factory.add_machine(machine)
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to import JSON layout: {str(e)}")
    
    def import_machines_from_csv(self, filename: str) -> bool:
        """Import machines from CSV file"""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                # Clear existing machines
                self.factory.machines.clear()
                
                for row in reader:
                    machine = Machine(
                        name=row["Machine_Name"],
                        machine_type=row["Type"],
                        base_time=float(row["Base_Time_min"]),
                        setup_time=float(row["Setup_Time_min"]),
                        x=int(float(row["Position_X"])),
                        y=int(float(row["Position_Y"]))
                    )
                    self.factory.add_machine(machine)
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to import CSV machines: {str(e)}")
    
    def _validate_json_layout(self, data: dict) -> bool:
        """Validate JSON layout structure"""
        required_fields = ["machines"]
        for field in required_fields:
            if field not in data:
                return False
        
        # Validate machines
        for machine_data in data["machines"]:
            required_machine_fields = ["name", "type", "base_time", "setup_time"]
            for field in required_machine_fields:
                if field not in machine_data:
                    return False
        
        return True


class ConfigurationManager:
    """Manages simulation configuration and presets"""
    
    def __init__(self):
        self.presets = {}
        self.current_config = {}
    
    def create_preset(self, name: str, factory: Factory, sim_manager: SimulationManager):
        """Create a configuration preset"""
        preset_data = {
            "name": name,
            "created": datetime.now().isoformat(),
            "machines": [],
            "simulation_params": {
                "speed_factor": sim_manager.speed_factor,
                "target_fps": 30
            }
        }
        
        for machine in factory.machines.values():
            preset_data["machines"].append({
                "name": machine.name,
                "type": machine.machine_type,
                "base_time": machine.base_time,
                "setup_time": machine.setup_time,
                "position": {"x": machine.x, "y": machine.y}
            })
        
        self.presets[name] = preset_data
        return preset_data
    
    def load_preset(self, name: str, factory: Factory) -> bool:
        """Load a configuration preset"""
        if name not in self.presets:
            return False
        
        preset = self.presets[name]
        
        # Clear current factory
        factory.machines.clear()
        
        # Load machines from preset
        for machine_data in preset["machines"]:
            machine = Machine(
                name=machine_data["name"],
                machine_type=machine_data["type"],
                base_time=machine_data["base_time"],
                setup_time=machine_data["setup_time"],
                x=machine_data["position"]["x"],
                y=machine_data["position"]["y"]
            )
            factory.add_machine(machine)
        
        return True
    
    def get_preset_names(self) -> List[str]:
        """Get list of available preset names"""
        return list(self.presets.keys())
    
    def delete_preset(self, name: str) -> bool:
        """Delete a preset"""
        if name in self.presets:
            del self.presets[name]
            return True
        return False
    
    def save_presets_to_file(self, filename: str):
        """Save all presets to file"""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.presets, f, indent=2)
    
    def load_presets_from_file(self, filename: str):
        """Load presets from file"""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                self.presets = json.load(f)
        except Exception as e:
            raise Exception(f"Failed to load presets: {str(e)}")


class StatisticsCollector:
    """Collects and manages simulation statistics"""
    
    def __init__(self, factory: Factory, sim_manager: SimulationManager):
        self.factory = factory
        self.sim_manager = sim_manager
        self.collection_history = []
    
    def collect_current_stats(self) -> Dict[str, Any]:
        """Collect current simulation statistics"""
        current_time = self.sim_manager.current_time
        
        stats = {
            "timestamp": datetime.now().isoformat(),
            "simulation_time": current_time,
            "total_machines": len(self.factory.machines),
            "active_jobs": len(self.factory.jobs),
            "completed_jobs": len(self.factory.completed_jobs),
            "total_wip": self.factory.get_total_wip(),
            "total_throughput": self.factory.get_total_throughput(current_time),
            "average_utilization": self.factory.get_average_utilization(current_time),
            "machine_stats": {}
        }
        
        # Individual machine statistics
        for name, machine in self.factory.machines.items():
            stats["machine_stats"][name] = {
                "type": machine.machine_type,
                "queue_length": machine.get_queue_length(),
                "utilization": machine.get_utilization(current_time),
                "throughput": machine.get_throughput(current_time),
                "total_output": machine.total_output,
                "working_time": machine.total_working_time,
                "is_working": machine.is_working
            }
        
        self.collection_history.append(stats)
        return stats
    
    def get_performance_trends(self, window_size: int = 10) -> Dict[str, List]:
        """Get performance trends over time"""
        if len(self.collection_history) < window_size:
            return {"error": "Not enough data for trend analysis"}
        
        recent_stats = self.collection_history[-window_size:]
        
        trends = {
            "throughput": [stat["total_throughput"] for stat in recent_stats],
            "utilization": [stat["average_utilization"] for stat in recent_stats],
            "wip": [stat["total_wip"] for stat in recent_stats],
            "timestamps": [stat["simulation_time"] for stat in recent_stats]
        }
        
        return trends
    
    def calculate_summary_statistics(self) -> Dict[str, Any]:
        """Calculate summary statistics over the entire simulation"""
        if not self.collection_history:
            return {}
        
        throughputs = [stat["total_throughput"] for stat in self.collection_history]
        utilizations = [stat["average_utilization"] for stat in self.collection_history]
        wips = [stat["total_wip"] for stat in self.collection_history]
        
        return {
            "total_runtime": self.sim_manager.current_time,
            "total_jobs_completed": len(self.factory.completed_jobs),
            "avg_throughput": sum(throughputs) / len(throughputs) if throughputs else 0,
            "max_throughput": max(throughputs) if throughputs else 0,
            "min_throughput": min(throughputs) if throughputs else 0,
            "avg_utilization": sum(utilizations) / len(utilizations) if utilizations else 0,
            "max_wip": max(wips) if wips else 0,
            "avg_wip": sum(wips) / len(wips) if wips else 0
        }
    
    def export_statistics_report(self, filename: str = None) -> str:
        """Export comprehensive statistics report"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"factory_statistics_report_{timestamp}.json"
        
        report = {
            "report_info": {
                "generated": datetime.now().isoformat(),
                "simulation_version": "2.0",
                "total_data_points": len(self.collection_history)
            },
            "summary": self.calculate_summary_statistics(),
            "current_state": self.collect_current_stats(),
            "trends": self.get_performance_trends(),
            "detailed_history": self.collection_history[-50:]  # Last 50 data points
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        
        return filename


class DefaultFactoryTemplates:
    """Pre-defined factory templates for quick setup"""
    
    @staticmethod
    def create_simple_line() -> List[Machine]:
        """Simple production line template"""
        return [
            Machine("Input", "Input", 0.5, 2, 50, 200),
            Machine("Process-1", "CNC", 2.0, 10, 200, 200),
            Machine("Process-2", "Assembly", 3.0, 15, 350, 200),
            Machine("Output", "Inspection", 1.0, 5, 500, 200)
        ]
    
    @staticmethod
    def create_parallel_processing() -> List[Machine]:
        """Parallel processing template"""
        return [
            Machine("CNC-01", "CNC", 2.5, 10, 100, 150),
            Machine("CNC-02", "CNC", 2.8, 12, 100, 300),
            Machine("CNC-03", "CNC", 2.3, 9, 100, 450),
            Machine("Assembly-01", "Assembly", 4.0, 20, 350, 225),
            Machine("Assembly-02", "Assembly", 4.2, 22, 350, 375),
            Machine("Inspection", "Inspection", 1.5, 8, 600, 300)
        ]
    
    @staticmethod
    def create_complex_flow() -> List[Machine]:
        """Complex multi-path flow template"""
        return [
            Machine("Raw-Material", "Input", 0.3, 1, 50, 300),
            Machine("CNC-01", "CNC", 2.5, 10, 200, 150),
            Machine("CNC-02", "CNC", 2.8, 12, 200, 300),
            Machine("CNC-03", "CNC", 2.3, 9, 200, 450),
            Machine("Lathe-01", "Lathe", 3.2, 15, 400, 200),
            Machine("Lathe-02", "Lathe", 3.0, 13, 400, 400),
            Machine("Drill-01", "Drill", 1.8, 8, 600, 150),
            Machine("Drill-02", "Drill", 1.9, 9, 600, 350),
            Machine("Assembly-Main", "Assembly", 5.0, 30, 800, 225),
            Machine("QC-Check", "Inspection", 1.2, 5, 1000, 225),
            Machine("Packaging", "Packaging", 2.0, 10, 1150, 225)
        ]
    
    @staticmethod
    def get_template_names() -> List[str]:
        """Get available template names"""
        return ["Simple Line", "Parallel Processing", "Complex Flow"]
    
    @staticmethod
    def create_template_by_name(name: str) -> List[Machine]:
        """Create template by name"""
        templates = {
            "Simple Line": DefaultFactoryTemplates.create_simple_line(),
            "Parallel Processing": DefaultFactoryTemplates.create_parallel_processing(),
            "Complex Flow": DefaultFactoryTemplates.create_complex_flow()
        }
        
        return templates.get(name, DefaultFactoryTemplates.create_simple_line())
    
    @staticmethod
    def get_sample_job_sequences(template_name: str) -> List[tuple]:
        """Get appropriate job sequences for each template"""
        sequences = {
            "Simple Line": [
                (20, ["Input", "Process-1", "Process-2", "Output"], 1),
                (15, ["Input", "Process-1", "Process-2", "Output"], 2),
                (25, ["Input", "Process-1", "Process-2", "Output"], 1)
            ],
            "Parallel Processing": [
                (20, ["CNC-01", "Assembly-01", "Inspection"], 1),
                (15, ["CNC-02", "Assembly-02", "Inspection"], 2),
                (25, ["CNC-03", "Assembly-01", "Inspection"], 1),
                (10, ["CNC-01", "Assembly-02", "Inspection"], 3)
            ],
            "Complex Flow": [
                (30, ["Raw-Material", "CNC-01", "Lathe-01", "Assembly-Main", "QC-Check", "Packaging"], 1),
                (20, ["Raw-Material", "CNC-02", "Drill-01", "Assembly-Main", "QC-Check", "Packaging"], 2),
                (15, ["Raw-Material", "CNC-03", "Lathe-02", "Assembly-Main", "QC-Check", "Packaging"], 1),
                (25, ["Raw-Material", "CNC-01", "Drill-02", "Assembly-Main", "QC-Check", "Packaging"], 1)
            ]
        }
        
        return sequences.get(template_name, sequences["Simple Line"])


class DataValidator:
    """Validates data integrity and consistency"""
    
    @staticmethod
    def validate_machine_data(machine_data: dict) -> tuple[bool, str]:
        """Validate machine data structure"""
        required_fields = ["name", "type", "base_time", "setup_time"]
        
        for field in required_fields:
            if field not in machine_data:
                return False, f"Missing required field: {field}"
        
        # Validate data types and ranges
        try:
            base_time = float(machine_data["base_time"])
            setup_time = float(machine_data["setup_time"])
            
            if base_time <= 0:
                return False, "Base time must be positive"
            if setup_time < 0:
                return False, "Setup time cannot be negative"
            
        except ValueError:
            return False, "Invalid numeric values"
        
        return True, "Valid"
    
    @staticmethod
    def validate_job_data(job_data: dict, available_machines: List[str]) -> tuple[bool, str]:
        """Validate job data structure"""
        required_fields = ["batch_size", "required_machines"]
        
        for field in required_fields:
            if field not in job_data:
                return False, f"Missing required field: {field}"
        
        try:
            batch_size = int(job_data["batch_size"])
            if batch_size <= 0:
                return False, "Batch size must be positive"
            
            required_machines = job_data["required_machines"]
            if not isinstance(required_machines, list) or len(required_machines) == 0:
                return False, "Required machines must be a non-empty list"
            
            # Check if all required machines exist
            for machine_name in required_machines:
                if machine_name not in available_machines:
                    return False, f"Machine '{machine_name}' not found"
            
        except (ValueError, TypeError):
            return False, "Invalid data types"
        
        return True, "Valid"
    
    @staticmethod
    def validate_factory_layout(layout_data: dict) -> tuple[bool, str]:
        """Validate complete factory layout"""
        if "machines" not in layout_data:
            return False, "No machines defined in layout"
        
        machine_names = set()
        
        for machine_data in layout_data["machines"]:
            # Check for duplicate names
            name = machine_data.get("name", "")
            if name in machine_names:
                return False, f"Duplicate machine name: {name}"
            machine_names.add(name)
            
            # Validate individual machine
            is_valid, message = DataValidator.validate_machine_data(machine_data)
            if not is_valid:
                return False, f"Machine '{name}': {message}"
        
        return True, "Valid layout"