"""
Machine model for factory simulation
"""
import math
import time
import random
from collections import deque
from typing import Optional, List
from models.job import Job


class Machine:
    """เครื่องจักรในโรงงาน - Enhanced with configuration support"""
    
    def __init__(self, name: str, machine_type: str, base_time: float, setup_time: float, 
                 x: int = 0, y: int = 0, config=None):
        self.name = name
        self.machine_type = machine_type
        self.base_time = base_time
        self.setup_time = setup_time
        self.x = x
        self.y = y
        self.width = 120
        self.height = 80
        self.config = config  # SimulationConfig object
        
        # Working state
        self.queue = deque(maxlen=100)
        self.current_job = None
        self.is_working = False
        self.is_down = False  # Machine breakdown state
        self.work_start_time = 0
        self.work_end_time = 0
        self.maintenance_time = 0
        self.downtime_start = 0
        self.downtime_end = 0
        
        # Statistics - enhanced
        self.total_working_time = 0
        self.total_output = 0
        self.total_defects = 0
        self.total_rework = 0
        self.total_downtime = 0
        self.last_update_time = 0
        
        # Cost tracking
        self.total_operating_cost = 0
        self.total_material_cost = 0
        self.total_defect_cost = 0
        
        # Performance metrics cache
        self._cached_utilization = 0
        self._cached_throughput = 0
        self._cached_oee = 0
        self._cache_time = 0
        self._cache_duration = 0.5
        
        # Visual effects
        self.animation_phase = 0
        self.status_color = "#f8f9fa"
        
        # Quality tracking
        self.quality_score = 100.0
        self.buffer_count = 0
        
    def calculate_cycle_time(self, batch_size: int) -> float:
        """คำนวณ Cycle Time แบบปรับปรุง"""
        if batch_size <= 0:
            return self.base_time
        return self.base_time + (self.setup_time / batch_size)
    
    def add_job(self, job: Job) -> bool:
        """เพิ่มงานเข้าคิว - Priority based with buffer capacity check"""
        # Check buffer capacity
        if self.config and len(self.queue) >= self.config.buffer_capacity:
            return False
        elif len(self.queue) >= self.queue.maxlen:
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
        
        self.buffer_count = len(self.queue)
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
        """อัปเดตสถานะ - Enhanced with quality and downtime"""
        completed_job = None
        
        # Update animation
        self.animation_phase = (self.animation_phase + 0.1) % (2 * math.pi)
        
        # Check for random downtime
        if not self.is_down and self.config and random.random() < self.config.downtime_rate / 3600:
            self._trigger_downtime(current_time)
        
        # Check downtime completion
        if self.is_down and current_time >= self.downtime_end:
            self._end_downtime(current_time)
        
        # Check job completion
        if self.is_working and not self.is_down and current_time >= self.work_end_time:
            completed_job = self._complete_job(current_time)
        
        # Update visual status
        self._update_visual_status(current_time)
        
        return completed_job
    
    def _trigger_downtime(self, current_time: float):
        """เริ่มการหยุดทำงาน"""
        self.is_down = True
        self.downtime_start = current_time
        # Random downtime duration between 5-30 minutes
        downtime_duration = random.uniform(5, 30) / 60  # Convert to hours
        self.downtime_end = current_time + downtime_duration
        
        if self.is_working:
            self.is_working = False
    
    def _end_downtime(self, current_time: float):
        """สิ้นสุดการหยุดทำงาน"""
        downtime_duration = current_time - self.downtime_start
        self.total_downtime += downtime_duration
        self.is_down = False
        self.downtime_start = 0
        self.downtime_end = 0
    
    def _complete_job(self, current_time: float) -> Job:
        """เสร็จสิ้นงาน - Enhanced with quality checks"""
        completed_job = self.current_job
        completed_job.completion_time = current_time
        
        # Quality check
        is_defective = False
        needs_rework = False
        
        if self.config:
            # Check for defects
            if random.random() < self.config.defect_rate:
                is_defective = True
                self.total_defects += completed_job.batch_size
                self.total_defect_cost += completed_job.batch_size * self.config.defect_cost
            
            # Check for rework (only if not defective)
            elif random.random() < self.config.rework_rate:
                needs_rework = True
                self.total_rework += completed_job.batch_size
                # Add rework time
                rework_time = self.calculate_cycle_time(completed_job.batch_size) * 0.5
                completed_job.completion_time += rework_time
            
            # Add material cost
            self.total_material_cost += completed_job.batch_size * self.config.material_cost
        
        # Mark job quality
        completed_job.is_defective = is_defective
        completed_job.needs_rework = needs_rework
        
        # Update statistics
        work_duration = self.work_end_time - self.work_start_time
        self.total_working_time += work_duration
        if not is_defective:
            self.total_output += completed_job.batch_size
        
        # Calculate operating cost
        if self.config:
            hourly_costs = self.config.get_hourly_costs()
            self.total_operating_cost += work_duration * hourly_costs["total_cost_per_hour"]
        
        # Update quality score
        self._update_quality_score()
        
        # Reset working state
        self.current_job = None
        self.is_working = False
        self.last_update_time = current_time
        
        return completed_job
    
    def _update_visual_status(self, current_time: float):
        """อัปเดตสถานะภาพ"""
        if self.is_down:
            self.status_color = "#dc3545"  # Red for breakdown
        elif self.is_working:
            self.status_color = "#28a745"  # Green for working
        else:
            if len(self.queue) > 0:
                self.status_color = "#ffc107"  # Yellow for waiting
            else:
                self.status_color = "#6c757d"  # Gray for idle
    
    def _update_quality_score(self):
        """อัปเดตคะแนนคุณภาพ"""
        if self.total_output + self.total_defects > 0:
            good_parts = self.total_output
            total_parts = self.total_output + self.total_defects
            self.quality_score = (good_parts / total_parts) * 100
        else:
            self.quality_score = 100.0
    
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
        """ได้สรุปสถานะเครื่องจักร - Enhanced"""
        availability = self._calculate_availability()
        performance = self._calculate_performance()
        quality = self.quality_score
        oee = self._calculate_oee(availability, performance, quality)
        
        return {
            "name": self.name,
            "type": self.machine_type,
            "working": self.is_working,
            "down": self.is_down,
            "queue_length": self.get_queue_length(),
            "buffer_utilization": (self.buffer_count / self.config.buffer_capacity * 100) if self.config else 0,
            "current_job": str(self.current_job) if self.current_job else None,
            "total_output": self.total_output,
            "total_defects": self.total_defects,
            "total_rework": self.total_rework,
            "quality_score": self.quality_score,
            "availability": availability,
            "performance": performance,
            "oee": oee,
            "total_cost": self.total_operating_cost + self.total_material_cost + self.total_defect_cost,
            "position": (self.x, self.y)
        }
    
    def _calculate_availability(self) -> float:
        """คำนวณ Availability"""
        total_time = self.total_working_time + self.total_downtime
        if total_time > 0:
            return ((total_time - self.total_downtime) / total_time) * 100
        return 100.0
    
    def _calculate_performance(self) -> float:
        """คำนวณ Performance"""
        if self.config and self.total_working_time > 0:
            actual_throughput = self.total_output / self.total_working_time
            target_throughput = self.config.throughput_target
            return min((actual_throughput / target_throughput) * 100, 100.0)
        return 100.0
    
    def _calculate_oee(self, availability: float, performance: float, quality: float) -> float:
        """คำนวณ OEE (Overall Equipment Effectiveness)"""
        return (availability / 100) * (performance / 100) * (quality / 100) * 100
    
    def get_cost_breakdown(self) -> dict:
        """ได้รายละเอียดต้นทุน"""
        return {
            "operating_cost": self.total_operating_cost,
            "material_cost": self.total_material_cost,
            "defect_cost": self.total_defect_cost,
            "total_cost": self.total_operating_cost + self.total_material_cost + self.total_defect_cost
        }
    
    def reset_statistics(self):
        """รีเซ็ตสถิติ - Enhanced"""
        self.total_working_time = 0
        self.total_output = 0
        self.total_defects = 0
        self.total_rework = 0
        self.total_downtime = 0
        self.total_operating_cost = 0
        self.total_material_cost = 0
        self.total_defect_cost = 0
        self.last_update_time = 0
        self.quality_score = 100.0
        self.buffer_count = 0
    
    def __str__(self) -> str:
        return f"{self.name} ({self.machine_type}) - Queue: {self.get_queue_length()}"
