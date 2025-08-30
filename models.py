"""
Core data models for factory simulation
Contains Job, Machine, and Factory classes
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from collections import deque
import math
import time


@dataclass
class Job:
    """งานที่ต้องผลิต"""
    id: int
    batch_size: int
    arrival_time: float
    required_machines: List[str]
    current_step: int = 0
    start_time: Optional[float] = None
    completion_time: Optional[float] = None
    priority: int = 1  # 1=Normal, 2=High, 3=Critical


class Machine:
    """เครื่องจักรในโรงงาน - Optimized Version"""
    
    def __init__(self, name: str, machine_type: str, base_time: float, setup_time: float, x: int = 0, y: int = 0):
        self.name = name
        self.machine_type = machine_type
        self.base_time = base_time
        self.setup_time = setup_time
        self.x = x
        self.y = y
        self.width = 120
        self.height = 80
        
        # Working state
        self.queue = deque(maxlen=100)  # Limit queue size for performance
        self.current_job = None
        self.is_working = False
        self.work_start_time = 0
        self.work_end_time = 0
        self.maintenance_time = 0
        
        # Statistics - optimized storage
        self.total_working_time = 0
        self.total_output = 0
        self.last_update_time = 0
        
        # Performance metrics cache
        self._cached_utilization = 0
        self._cached_throughput = 0
        self._cache_time = 0
        self._cache_duration = 0.5  # Cache for 0.5 seconds
        
        # Visual effects
        self.animation_phase = 0
        self.status_color = "#021120"
        
    def calculate_cycle_time(self, batch_size: int) -> float:
        """คำนวน Cycle Time แบบปรับปรุง"""
        if batch_size <= 0:
            return self.base_time + self.setup_time
        return self.base_time + (self.setup_time / batch_size)
    
    def add_job(self, job: Job) -> bool:
        """เพิ่มงานเข้าคิว - Priority based"""
        if len(self.queue) >= self.queue.maxlen:
            return False  # Queue full
        
        # Insert based on priority
        inserted = False
        for i, existing_job in enumerate(self.queue):
            if job.priority > existing_job.priority:
                # Convert deque to list, insert, convert back
                queue_list = list(self.queue)
                queue_list.insert(i, job)
                self.queue = deque(queue_list, maxlen=self.queue.maxlen)
                inserted = True
                break
        
        if not inserted:
            self.queue.append(job)
        
        return True
    
    def start_processing(self, current_time: float):
        """เริ่มประมวลผลงาน - Optimized"""
        if not self.is_working and len(self.queue) > 0:
            self.current_job = self.queue.popleft()
            self.is_working = True
            self.work_start_time = current_time
            
            cycle_time = self.calculate_cycle_time(self.current_job.batch_size)
            self.work_end_time = current_time + cycle_time
            
            if self.current_job.start_time is None:
                self.current_job.start_time = current_time
    
    def update(self, current_time: float) -> Optional[Job]:
        """อัปเดตสถานะ - High Performance"""
        completed_job = None
        
        # Update animation
        self.animation_phase = (self.animation_phase + 0.1) % (2 * math.pi)
        
        # Check job completion
        if self.is_working and current_time >= self.work_end_time:
            completed_job = self.current_job
            completed_job.completion_time = current_time
            
            # Update statistics
            work_duration = self.work_end_time - self.work_start_time
            self.total_working_time += work_duration
            self.total_output += completed_job.batch_size
            
            # Reset state
            self.current_job = None
            self.is_working = False
            
            # Start next job
            self.start_processing(current_time)
        
        # Update visual status
        self._update_visual_status(current_time)
        
        return completed_job
    
    def _update_visual_status(self, current_time: float):
        """อัปเดตสถานะภาพ"""
        if self.is_working:
            # Animate working state
            intensity = 0.5 + 0.5 * math.sin(self.animation_phase * 2)
            if self.current_job.priority >= 3:
                self.status_color = f"#ff{int(100 + 100 * intensity):02x}{int(100 + 100 * intensity):02x}"  # Red animation
            elif self.current_job.priority >= 2:
                self.status_color = f"#{int(255):02x}{int(200 + 55 * intensity):02x}{int(100):02x}"  # Orange animation
            else:
                self.status_color = f"{int(100 + 100 * intensity):02x}ff{int(100 + 100 * intensity):02x}"  # Green animation
        else:
            queue_ratio = min(len(self.queue) / 10, 1.0)  # Normalize to 0-1
            if queue_ratio > 0.7:
                self.status_color = "#fff3cd"  # Warning yellow
            elif queue_ratio > 0.3:
                self.status_color = "#d1ecf1"  # Info blue
            else:
                self.status_color = "#d4edda"  # Success green
    
    def get_utilization(self, total_time: float) -> float:
        """คำนวน Utilization แบบ Cached"""
        current_time = time.time()
        
        if current_time - self._cache_time < self._cache_duration:
            return self._cached_utilization
        
        if total_time <= 0:
            self._cached_utilization = 0
        else:
            self._cached_utilization = min((self.total_working_time / total_time) * 100, 100)
        
        self._cache_time = current_time
        return self._cached_utilization
    
    def get_throughput(self, total_time: float) -> float:
        """คำนวน Throughput แบบ Cached"""
        current_time = time.time()
        
        if current_time - self._cache_time < self._cache_duration:
            return self._cached_throughput
        
        if total_time <= 0:
            self._cached_throughput = 0
        else:
            self._cached_throughput = self.total_output / total_time
        
        return self._cached_throughput
    
    def get_queue_length(self) -> int:
        """ได้จำนวนงานในคิว"""
        return len(self.queue)
    
    def get_bounds(self) -> tuple:
        """ได้ bounds ของเครื่องจักร"""
        return (self.x, self.y, self.x + self.width, self.y + self.height)
    
    def clear_queue(self):
        """ล้างคิวงาน"""
        self.queue.clear()
    
    def reset_statistics(self):
        """รีเซ็ตสถิติ"""
        self.total_working_time = 0
        self.total_output = 0
        self._cached_utilization = 0
        self._cached_throughput = 0


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
        
    def add_machine(self, machine: Machine):
        """เพิ่มเครื่องจักร"""
        self.machines[machine.name] = machine
        self._machine_lookup[machine.name] = machine
        self._invalidate_cache()
    
    def remove_machine(self, machine_name: str):
        """ลบเครื่องจักร"""
        if machine_name in self.machines:
            del self.machines[machine_name]
            if machine_name in self._machine_lookup:
                del self._machine_lookup[machine_name]
            self._invalidate_cache()
    
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
            if machine_name in self._machine_lookup:
                return self._machine_lookup[machine_name].add_job(job)
        return False
    
    def get_total_wip(self) -> int:
        """คำนวน WIP รวม - Cached"""
        current_time = time.time()
        
        if current_time - self._last_wip_update < 0.1:  # Cache for 100ms
            return self._wip_cache
        
        total_wip = 0
        for machine in self.machines.values():
            total_wip += machine.get_queue_length()
            if machine.is_working:
                total_wip += 1
        
        self._wip_cache = total_wip
        self._last_wip_update = current_time
        return total_wip
    
    def get_average_utilization(self, total_time: float) -> float:
        """คำนวน Utilization เฉลี่ย"""
        if not self.machines:
            return 0
        return sum(machine.get_utilization(total_time) for machine in self.machines.values()) / len(self.machines)
    
    def get_total_throughput(self, total_time: float) -> float:
        """คำนวน Throughput รวม"""
        return sum(machine.get_throughput(total_time) for machine in self.machines.values())
    
    def reset(self):
        """รีเซ็ตโรงงาน"""
        for machine in self.machines.values():
            machine.clear_queue()
            machine.current_job = None
            machine.is_working = False
            machine.reset_statistics()
        
        self.jobs.clear()
        self.completed_jobs.clear()
        self.job_counter = 0
        self._invalidate_cache()
    
    def get_machine_by_name(self, name: str) -> Optional[Machine]:
        """ค้นหาเครื่องจักรด้วยชื่อ"""
        return self._machine_lookup.get(name)
    
    def get_machine_types(self) -> List[str]:
        """ได้รายการประเภทเครื่องจักรทั้งหมด"""
        return list(set(machine.machine_type for machine in self.machines.values()))
    
    def get_machines_by_type(self, machine_type: str) -> List[Machine]:
        """ได้เครื่องจักรตามประเภท"""
        return [machine for machine in self.machines.values() if machine.machine_type == machine_type]
    
    def validate_job_sequence(self, required_machines: List[str]) -> bool:
        """ตรวจสอบว่า sequence ของเครื่องจักรใช้ได้"""
        for machine_name in required_machines:
            if machine_name not in self.machines:
                return False
        return True
    
    def get_bottleneck_machine(self) -> Optional[Machine]:
        """หาเครื่องจักรที่เป็น bottleneck"""
        bottleneck = None
        max_queue = 0
        
        for machine in self.machines.values():
            queue_len = machine.get_queue_length()
            if queue_len > max_queue:
                max_queue = queue_len
                bottleneck = machine
        
        return bottleneck if max_queue > 0 else None
