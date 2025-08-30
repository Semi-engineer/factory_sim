"""
Factory model for managing machines and jobs
"""
import time
from typing import Dict, List, Optional
from models.job import Job
from models.machine import Machine
from models.production_line import ProductionLine


class Factory:
    """โรงงาน - Enhanced with Production Lines"""
    
    def __init__(self):
        self.machines: Dict[str, Machine] = {}
        self.production_lines: Dict[str, ProductionLine] = {}
        self.jobs: List[Job] = []
        self.completed_jobs: List[Job] = []
        self.job_counter = 0
        
        # Performance optimization
        self._machine_lookup = {}  # Fast machine lookup
        self._wip_cache = 0
        self._last_wip_update = 0
        
    def add_machine(self, machine: Machine) -> bool:
        """เพิ่มเครื่องจักร"""
        if machine.name in self.machines:
            return False
            
        self.machines[machine.name] = machine
        self._machine_lookup[machine.name] = machine
        self._invalidate_cache()
        return True
    
    def add_production_line(self, production_line: ProductionLine) -> bool:
        """เพิ่มสายการผลิต"""
        if production_line.line_id in self.production_lines:
            return False
        
        self.production_lines[production_line.line_id] = production_line
        
        # เพิ่มเครื่องจักรในสายการผลิตเข้าโรงงาน
        for machine in production_line.machines:
            if machine.name not in self.machines:
                self.add_machine(machine)
        
        self._invalidate_cache()
        return True
    
    def remove_production_line(self, line_id: str) -> bool:
        """ลบสายการผลิต"""
        if line_id in self.production_lines:
            production_line = self.production_lines[line_id]
            
            # ลบเครื่องจักรออกจากโรงงาน (ถ้าไม่อยู่ในสายอื่น)
            for machine in production_line.machines:
                # ตรวจสอบว่าเครื่องจักรอยู่ในสายอื่นหรือไม่
                in_other_line = any(
                    machine in line.machines 
                    for line_id_check, line in self.production_lines.items() 
                    if line_id_check != line_id
                )
                
                if not in_other_line:
                    self.remove_machine(machine.name)
            
            del self.production_lines[line_id]
            self._invalidate_cache()
            return True
        return False
    
    def get_production_line(self, line_id: str) -> Optional[ProductionLine]:
        """ได้สายการผลิตตาม ID"""
        return self.production_lines.get(line_id)
    
    def remove_machine(self, machine_name: str) -> bool:
        """ลบเครื่องจักร"""
        if machine_name in self.machines:
            del self.machines[machine_name]
            del self._machine_lookup[machine_name]
            self._invalidate_cache()
            return True
        return False
    
    def get_machine(self, machine_name: str) -> Optional[Machine]:
        """ได้เครื่องจักรตามชื่อ"""
        return self.machines.get(machine_name)
    
    def _invalidate_cache(self):
        """ล้าง cache เมื่อมีการเปลี่ยนแปลง"""
        self._last_wip_update = 0
    
    def create_job(self, batch_size: int, required_machines: List[str], priority: int = 1) -> Job:
        """สร้างงานใหม่"""
        self.job_counter += 1
        job = Job(
            id=self.job_counter,
            batch_size=batch_size,
            arrival_time=time.time(),
            required_machines=required_machines.copy(),
            priority=priority
        )
        self.jobs.append(job)
        return job
    
    def route_job(self, job: Job) -> bool:
        """จัดเส้นทางงาน - Enhanced with Production Line support"""
        if job.current_step < len(job.required_machines):
            machine_name = job.required_machines[job.current_step]
            machine = self.get_machine(machine_name)
            
            if machine:
                # ตรวจสอบว่าเครื่องจักรอยู่ในสายการผลิตหรือไม่
                if hasattr(machine, 'production_line') and machine.production_line:
                    production_line = self.get_production_line(machine.production_line)
                    if production_line:
                        return production_line.simulate_flow(job, time.time())
                
                # ถ้าไม่อยู่ในสายการผลิต ใช้วิธีเดิม
                if machine.add_job(job):
                    return True
        return False
    
    def route_job_through_line(self, job: Job, line_id: str) -> bool:
        """จัดเส้นทางงานผ่านสายการผลิตเฉพาะ"""
        production_line = self.get_production_line(line_id)
        if production_line:
            return production_line.simulate_flow(job, time.time())
        return False
    
    def process_completed_job(self, job: Job):
        """ประมวลผลงานที่เสร็จสิ้น"""
        if job.advance_step():
            # ยังมีขั้นตอนเหลือ - route ไปขั้นตอนถัดไป
            if not self.route_job(job):
                # ไม่สามารถ route ได้ - ใส่กลับไปใน jobs list
                self.jobs.append(job)
        else:
            # งานเสร็จสิ้นแล้ว
            self.completed_jobs.append(job)
            if job in self.jobs:
                self.jobs.remove(job)
    
    def get_total_wip(self) -> int:
        """คำนวณ WIP รวม - Cached"""
        current_time = time.time()
        
        if current_time - self._last_wip_update < 0.1:
            return self._wip_cache
        
        total_wip = 0
        for machine in self.machines.values():
            total_wip += machine.get_queue_length()
            if machine.is_working:
                total_wip += 1
        
        # Add jobs waiting to be routed
        total_wip += len(self.jobs)
        
        self._wip_cache = total_wip
        self._last_wip_update = current_time
        return total_wip
    
    def get_average_utilization(self, total_time: float) -> float:
        """คำนวณ Utilization เฉลี่ย"""
        if not self.machines:
            return 0.0
        return sum(machine.get_utilization(total_time) for machine in self.machines.values()) / len(self.machines)
    
    def get_total_throughput(self, total_time: float) -> float:
        """คำนวณ Throughput รวม"""
        return sum(machine.get_throughput(total_time) for machine in self.machines.values())
    
    def get_machine_by_position(self, x: int, y: int) -> Optional[Machine]:
        """หาเครื่องจักรตามตำแหน่ง"""
        for machine in self.machines.values():
            if machine.is_position_inside(x, y):
                return machine
        return None
    
    def get_bottleneck_machines(self) -> List[Machine]:
        """หาเครื่องจักรที่เป็น bottleneck"""
        if not self.machines:
            return []
        
        # Find machines with highest queue length
        max_queue = max(machine.get_queue_length() for machine in self.machines.values())
        if max_queue == 0:
            return []
        
        return [machine for machine in self.machines.values() 
                if machine.get_queue_length() == max_queue]
    
    def get_idle_machines(self) -> List[Machine]:
        """หาเครื่องจักรที่ว่าง"""
        return [machine for machine in self.machines.values() 
                if not machine.is_working and machine.get_queue_length() == 0]
    
    def get_factory_summary(self) -> dict:
        """ได้สรุปสถานะโรงงาน - Enhanced with Production Lines"""
        return {
            "total_machines": len(self.machines),
            "total_production_lines": len(self.production_lines),
            "total_jobs": len(self.jobs),
            "completed_jobs": len(self.completed_jobs),
            "total_wip": self.get_total_wip(),
            "machine_types": list(set(machine.machine_type for machine in self.machines.values())),
            "bottlenecks": [machine.name for machine in self.get_bottleneck_machines()],
            "idle_machines": [machine.name for machine in self.get_idle_machines()],
            "production_lines_summary": {
                line_id: line.get_line_summary() 
                for line_id, line in self.production_lines.items()
            }
        }
    
    def analyze_production_lines(self) -> dict:
        """วิเคราะห์ประสิทธิภาพสายการผลิต"""
        analysis = {
            "total_lines": len(self.production_lines),
            "line_efficiencies": {},
            "bottleneck_analysis": {},
            "balance_suggestions": {}
        }
        
        for line_id, line in self.production_lines.items():
            analysis["line_efficiencies"][line_id] = line.calculate_line_efficiency()
            analysis["bottleneck_analysis"][line_id] = [m.name for m in line.analyze_bottleneck()]
            analysis["balance_suggestions"][line_id] = line.balance_line()
        
        return analysis
    
    def get_production_line_throughput(self, time_period: float) -> dict:
        """ได้ throughput ของแต่ละสายการผลิต"""
        throughputs = {}
        for line_id, line in self.production_lines.items():
            throughputs[line_id] = line.calculate_throughput(time_period)
        return throughputs
    
    def create_sample_production_line(self, line_id: str = "LINE-01") -> ProductionLine:
        """สร้างสายการผลิตตัวอย่าง"""
        from models.machine import Machine
        
        line = ProductionLine("Assembly Line 01", line_id)
        
        # สร้างเครื่องจักรสำหรับสายการผลิต
        machines = [
            Machine("PREP-01", "Preparation", 1.5, 5, config=getattr(self, 'config', None)),
            Machine("CUT-01", "Cutting", 2.0, 8, config=getattr(self, 'config', None)),
            Machine("DRILL-01", "Drilling", 1.8, 6, config=getattr(self, 'config', None)),
            Machine("ASM-01", "Assembly", 3.0, 15, config=getattr(self, 'config', None)),
            Machine("TEST-01", "Testing", 1.2, 3, config=getattr(self, 'config', None)),
            Machine("PACK-01", "Packaging", 0.8, 2, config=getattr(self, 'config', None))
        ]
        
        for machine in machines:
            line.add_machine(machine)
        
        # ตั้งค่า layout แบบ horizontal
        line.set_layout("horizontal", 50, 200, 180)
        
        # สร้าง production route
        machine_names = [m.name for m in machines]
        cycle_times = [m.base_time for m in machines]
        setup_times = [m.setup_time for m in machines]
        
        line.create_production_route(
            "Standard Product",
            machine_names,
            cycle_times,
            setup_times
        )
        
        # เพิ่มสายการผลิตเข้าโรงงาน
        self.add_production_line(line)
        
        return line
    
    def clear_all_jobs(self):
        """ล้างงานทั้งหมด"""
        self.jobs.clear()
        self.completed_jobs.clear()
        for machine in self.machines.values():
            machine.clear_queue()
            machine.current_job = None
            machine.is_working = False
    
    def reset_statistics(self):
        """รีเซ็ตสถิติ"""
        for machine in self.machines.values():
            machine.total_working_time = 0
            machine.total_output = 0
            machine.last_update_time = 0
        self._invalidate_cache()
    
    def __str__(self) -> str:
        return f"Factory: {len(self.machines)} machines, {len(self.jobs)} active jobs, {len(self.completed_jobs)} completed"
