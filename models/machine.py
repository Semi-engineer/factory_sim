"""
Machine model for factory simulation
"""
import math
import time
from collections import deque
from typing import Optional, List
from models.job import Job


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
        self.status_color = "#f8f9fa"
        
    def calculate_cycle_time(self, batch_size: int) -> float:
        """คำนวณ Cycle Time แบบปรับปรุง"""
        if batch_size <= 0:
            return self.base_time
        return self.base_time + (self.setup_time / batch_size)
    
    def add_job(self, job: Job) -> bool:
        """เพิ่มงานเข้าคิว - Priority based"""
        if len(self.queue) >= self.queue.maxlen:
            return False
        
        # Insert based on priority
        inserted = False
        for i, existing_job in enumerate(self.queue):
            if job.priority > existing_job.priority:
                self.queue.insert(i, job)
                inserted = True
                break
        
        if not inserted:
            self.queue.append(job)
        
        return True
    
    def start_processing(self, current_time: float) -> bool:
        """เริ่มประมวลผลงาน - Optimized"""
        if not self.is_working and len(self.queue) > 0:
            self.current_job = self.queue.popleft()
            self.current_job.start_time = current_time
            
            cycle_time = self.calculate_cycle_time(self.current_job.batch_size)
            self.work_start_time = current_time
            self.work_end_time = current_time + cycle_time
            self.is_working = True
            return True
        return False
    
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
            
            # Reset working state
            self.current_job = None
            self.is_working = False
            self.last_update_time = current_time
        
        # Update visual status
        self._update_visual_status(current_time)
        
        return completed_job
    
    def _update_visual_status(self, current_time: float):
        """อัปเดตสถานะภาพ"""
        if self.is_working:
            # Working state - green
            self.status_color = "#28a745"
        else:
            if len(self.queue) > 0:
                self.status_color = "#ffc107"  # Yellow for waiting
            else:
                self.status_color = "#6c757d"  # Gray for idle
    
    def get_utilization(self, total_time: float) -> float:
        """คำนวณ Utilization แบบ Cached"""
        current_time = time.time()
        
        if current_time - self._cache_time < self._cache_duration:
            return self._cached_utilization
        
        if total_time <= 0:
            self._cached_utilization = 0
        else:
            self._cached_utilization = (self.total_working_time / total_time) * 100
        
        self._cache_time = current_time
        return self._cached_utilization
    
    def get_throughput(self, total_time: float) -> float:
        """คำนวณ Throughput แบบ Cached"""
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
    
    def is_position_inside(self, x: int, y: int) -> bool:
        """ตรวจสอบว่าตำแหน่งอยู่ในเครื่องจักรหรือไม่"""
        x1, y1, x2, y2 = self.get_bounds()
        return x1 <= x <= x2 and y1 <= y <= y2
    
    def clear_queue(self):
        """ล้างคิวงาน"""
        self.queue.clear()
    
    def get_status_summary(self) -> dict:
        """ได้สรุปสถานะเครื่องจักร"""
        return {
            "name": self.name,
            "type": self.machine_type,
            "working": self.is_working,
            "queue_length": self.get_queue_length(),
            "current_job": str(self.current_job) if self.current_job else None,
            "total_output": self.total_output,
            "position": (self.x, self.y)
        }
    
    def __str__(self) -> str:
        return f"{self.name} ({self.machine_type}) - Queue: {self.get_queue_length()}"
