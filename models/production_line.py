"""
Production Line model for factory simulation
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from models.machine import Machine
from models.job import Job


@dataclass
class ProductionStep:
    """ขั้นตอนการผลิตในสายการผลิต"""
    machine: Machine
    step_number: int
    cycle_time: float
    setup_time: float = 0.0
    quality_check: bool = False
    is_bottleneck: bool = False


@dataclass
class ProductionRoute:
    """เส้นทางการผลิตสำหรับผลิตภัณฑ์"""
    product_name: str
    steps: List[ProductionStep] = field(default_factory=list)
    total_cycle_time: float = 0.0
    
    def calculate_total_cycle_time(self):
        """คำนวณเวลาการผลิตรวม"""
        self.total_cycle_time = sum(step.cycle_time for step in self.steps)
    
    def get_bottleneck_step(self) -> Optional[ProductionStep]:
        """หาขั้นตอนที่เป็น bottleneck"""
        if not self.steps:
            return None
        return max(self.steps, key=lambda x: x.cycle_time)


class ProductionLine:
    """สายการผลิต (Production Line)"""
    
    def __init__(self, name: str, line_id: str):
        self.name = name
        self.line_id = line_id
        self.machines: List[Machine] = []
        self.routes: Dict[str, ProductionRoute] = {}
        self.current_jobs: List[Job] = []
        
        # Line statistics
        self.total_throughput = 0
        self.total_cycle_time = 0
        self.line_efficiency = 0.0
        self.takt_time = 0.0  # เวลาที่ต้องการในการผลิต 1 ชิ้น
        
        # Visual properties
        self.start_x = 0
        self.start_y = 0
        self.direction = "horizontal"  # horizontal, vertical, L-shape, U-shape
        self.spacing = 200  # ระยะห่างระหว่างเครื่องจักร
        
        # Production flow
        self.wip_between_stations = []  # WIP ระหว่างสถานี
        self.conveyor_speed = 1.0  # ความเร็วสายพาน (ชิ้น/นาที)
    
    def add_machine(self, machine: Machine, position: int = -1):
        """เพิ่มเครื่องจักรเข้าสายการผลิต"""
        if position == -1:
            self.machines.append(machine)
        else:
            self.machines.insert(position, machine)
        
        self._update_machine_positions()
        machine.production_line = self.line_id
    
    def remove_machine(self, machine: Machine):
        """ลบเครื่องจักรออกจากสายการผลิต"""
        if machine in self.machines:
            self.machines.remove(machine)
            machine.production_line = None
            self._update_machine_positions()
    
    def _update_machine_positions(self):
        """อัปเดตตำแหน่งเครื่องจักรตามรูปแบบสายการผลิต"""
        if not self.machines:
            return
        
        for i, machine in enumerate(self.machines):
            if self.direction == "horizontal":
                machine.x = self.start_x + (i * self.spacing)
                machine.y = self.start_y
            elif self.direction == "vertical":
                machine.x = self.start_x
                machine.y = self.start_y + (i * self.spacing)
            elif self.direction == "L-shape":
                if i < len(self.machines) // 2:
                    machine.x = self.start_x + (i * self.spacing)
                    machine.y = self.start_y
                else:
                    machine.x = self.start_x + ((len(self.machines) // 2 - 1) * self.spacing)
                    machine.y = self.start_y + ((i - len(self.machines) // 2 + 1) * self.spacing)
            elif self.direction == "U-shape":
                machines_per_side = len(self.machines) // 2
                if i < machines_per_side:
                    # ด้านซ้าย
                    machine.x = self.start_x
                    machine.y = self.start_y + (i * self.spacing)
                else:
                    # ด้านขวา
                    machine.x = self.start_x + self.spacing * 2
                    machine.y = self.start_y + ((len(self.machines) - i - 1) * self.spacing)
    
    def create_production_route(self, product_name: str, machine_sequence: List[str], 
                              cycle_times: List[float], setup_times: List[float] = None) -> ProductionRoute:
        """สร้างเส้นทางการผลิต"""
        if setup_times is None:
            setup_times = [0.0] * len(machine_sequence)
        
        route = ProductionRoute(product_name)
        
        for i, (machine_name, cycle_time, setup_time) in enumerate(zip(machine_sequence, cycle_times, setup_times)):
            # หาเครื่องจักรในสายการผลิต
            machine = next((m for m in self.machines if m.name == machine_name), None)
            if machine:
                step = ProductionStep(
                    machine=machine,
                    step_number=i + 1,
                    cycle_time=cycle_time,
                    setup_time=setup_time,
                    quality_check=(i == len(machine_sequence) - 1)  # Quality check ที่ขั้นตอนสุดท้าย
                )
                route.steps.append(step)
        
        route.calculate_total_cycle_time()
        self.routes[product_name] = route
        return route
    
    def calculate_takt_time(self, demand_per_hour: float) -> float:
        """คำนวณ Takt Time"""
        if demand_per_hour > 0:
            self.takt_time = 60 / demand_per_hour  # นาทีต่อชิ้น
        else:
            self.takt_time = 0
        return self.takt_time
    
    def analyze_bottleneck(self) -> List[Machine]:
        """วิเคราะห์ bottleneck ในสายการผลิต"""
        bottlenecks = []
        
        if not self.machines:
            return bottlenecks
        
        # หาเครื่องจักรที่มี cycle time สูงสุด
        max_cycle_time = 0
        for route in self.routes.values():
            for step in route.steps:
                if step.cycle_time > max_cycle_time:
                    max_cycle_time = step.cycle_time
        
        # หาเครื่องจักรที่มีคิวยาวที่สุด
        max_queue_length = max(machine.get_queue_length() for machine in self.machines)
        
        for machine in self.machines:
            # ถือว่าเป็น bottleneck ถ้า cycle time สูงหรือคิวยาว
            if (machine.base_time >= max_cycle_time * 0.9 or 
                machine.get_queue_length() >= max_queue_length * 0.8):
                bottlenecks.append(machine)
        
        return bottlenecks
    
    def calculate_line_efficiency(self) -> float:
        """คำนวณประสิทธิภาพของสายการผลิต"""
        if not self.machines:
            return 0.0
        
        # Average utilization of all machines
        total_utilization = sum(machine.get_utilization(100) for machine in self.machines)
        avg_utilization = total_utilization / len(self.machines)
        
        # Factor in bottleneck impact
        bottlenecks = self.analyze_bottleneck()
        bottleneck_penalty = len(bottlenecks) * 5  # 5% penalty per bottleneck
        
        self.line_efficiency = max(0, avg_utilization - bottleneck_penalty)
        return self.line_efficiency
    
    def calculate_throughput(self, time_period: float) -> float:
        """คำนวณ throughput ของสายการผลิต"""
        if not self.machines:
            return 0.0
        
        # Throughput จำกัดโดยเครื่องจักรที่ช้าที่สุด (bottleneck)
        min_throughput = float('inf')
        
        for machine in self.machines:
            machine_throughput = machine.get_throughput(time_period)
            if machine_throughput < min_throughput:
                min_throughput = machine_throughput
        
        self.total_throughput = min_throughput if min_throughput != float('inf') else 0
        return self.total_throughput
    
    def balance_line(self) -> List[str]:
        """สมดุลสายการผลิต (Line Balancing)"""
        suggestions = []
        
        if not self.machines:
            return suggestions
        
        # หา cycle time เฉลี่ย
        cycle_times = [machine.base_time for machine in self.machines]
        avg_cycle_time = sum(cycle_times) / len(cycle_times)
        
        for machine in self.machines:
            deviation = abs(machine.base_time - avg_cycle_time) / avg_cycle_time * 100
            
            if deviation > 20:  # เกิน 20% จากค่าเฉลี่ย
                if machine.base_time > avg_cycle_time:
                    suggestions.append(f"Consider splitting {machine.name} operation or adding parallel machine")
                else:
                    suggestions.append(f"Consider combining {machine.name} with adjacent operation")
        
        # ตรวจสอบ takt time
        if self.takt_time > 0:
            for machine in self.machines:
                if machine.base_time > self.takt_time:
                    suggestions.append(f"{machine.name} cycle time exceeds takt time - urgent optimization needed")
        
        return suggestions
    
    def simulate_flow(self, job: Job, current_time: float) -> bool:
        """จำลองการไฟล์ของงานผ่านสายการผลิต"""
        if not self.machines or job.current_step >= len(self.machines):
            return False
        
        current_machine = self.machines[job.current_step]
        
        # ตรวจสอบว่าเครื่องจักรว่างหรือไม่
        if not current_machine.is_working and len(current_machine.queue) == 0:
            # เริ่มงานทันที
            current_machine.add_job(job)
            current_machine.start_processing(current_time)
            return True
        else:
            # เพิ่มเข้าคิว
            return current_machine.add_job(job)
    
    def get_line_summary(self) -> dict:
        """สรุปข้อมูลสายการผลิต"""
        return {
            "line_id": self.line_id,
            "name": self.name,
            "machine_count": len(self.machines),
            "routes_count": len(self.routes),
            "efficiency": self.line_efficiency,
            "throughput": self.total_throughput,
            "takt_time": self.takt_time,
            "bottlenecks": [m.name for m in self.analyze_bottleneck()],
            "direction": self.direction,
            "total_wip": sum(machine.get_queue_length() for machine in self.machines)
        }
    
    def get_machine_positions(self) -> List[Tuple[str, int, int]]:
        """ได้ตำแหน่งเครื่องจักรทั้งหมด"""
        return [(machine.name, machine.x, machine.y) for machine in self.machines]
    
    def set_layout(self, direction: str, start_x: int, start_y: int, spacing: int = 200):
        """ตั้งค่า layout ของสายการผลิต"""
        self.direction = direction
        self.start_x = start_x
        self.start_y = start_y
        self.spacing = spacing
        self._update_machine_positions()
    
    def export_layout(self) -> dict:
        """ส่งออกข้อมูล layout"""
        return {
            "line_id": self.line_id,
            "name": self.name,
            "direction": self.direction,
            "start_x": self.start_x,
            "start_y": self.start_y,
            "spacing": self.spacing,
            "machines": [
                {
                    "name": machine.name,
                    "type": machine.machine_type,
                    "x": machine.x,
                    "y": machine.y,
                    "base_time": machine.base_time,
                    "setup_time": machine.setup_time
                }
                for machine in self.machines
            ],
            "routes": {
                name: {
                    "product_name": route.product_name,
                    "total_cycle_time": route.total_cycle_time,
                    "steps": [
                        {
                            "machine_name": step.machine.name,
                            "step_number": step.step_number,
                            "cycle_time": step.cycle_time,
                            "setup_time": step.setup_time,
                            "quality_check": step.quality_check
                        }
                        for step in route.steps
                    ]
                }
                for name, route in self.routes.items()
            }
        }
    
    def __str__(self) -> str:
        return f"ProductionLine {self.line_id}: {self.name} ({len(self.machines)} machines)"
