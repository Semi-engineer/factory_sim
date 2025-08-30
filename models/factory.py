"""
Factory model for managing machines and jobs
"""
import time
from typing import Dict, List, Optional
from models.job import Job
from models.machine import Machine


class Factory:
    """โรงงาน - Optimized with better data structures"""
    
    def __init__(self):
        self.machines: Dict[str, Machine] = {}
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
        """จัดเส้นทางงาน - Optimized"""
        if job.current_step < len(job.required_machines):
            machine_name = job.required_machines[job.current_step]
            machine = self.get_machine(machine_name)
            
            if machine and machine.add_job(job):
                return True
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
        """ได้สรุปสถานะโรงงาน"""
        return {
            "total_machines": len(self.machines),
            "total_jobs": len(self.jobs),
            "completed_jobs": len(self.completed_jobs),
            "total_wip": self.get_total_wip(),
            "machine_types": list(set(machine.machine_type for machine in self.machines.values())),
            "bottlenecks": [machine.name for machine in self.get_bottleneck_machines()],
            "idle_machines": [machine.name for machine in self.get_idle_machines()]
        }
    
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
