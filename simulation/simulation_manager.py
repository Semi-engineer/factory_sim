"""
Simulation manager for controlling simulation state and statistics
"""
import time
from collections import deque
from typing import Optional
from models.factory import Factory


class SimulationManager:
    """จัดการการจำลอง - High Performance"""
    
    def __init__(self, factory: Factory):
        self.factory = factory
        self.current_time = 0
        self.speed_factor = 1.0
        self.is_running = False
        self.is_paused = False
        self.start_real_time = 0
        
        # Optimized history storage
        self.max_history = 200
        self.time_history = deque(maxlen=self.max_history)
        self.throughput_history = deque(maxlen=self.max_history)
        self.utilization_history = deque(maxlen=self.max_history)
        self.wip_history = deque(maxlen=self.max_history)
        
        # Performance tracking
        self.step_count = 0
        self.last_record_time = 0
        
    def start(self):
        """เริ่มการจำลอง"""
        self.is_running = True
        self.is_paused = False
        self.start_real_time = time.time()
        self.current_time = 0
        self.step_count = 0
        self.clear_history()
    
    def pause(self):
        """หยุดชั่วคราว"""
        self.is_paused = True
    
    def resume(self):
        """เริ่มต่อ"""
        self.is_paused = False
    
    def stop(self):
        """หยุดการจำลอง"""
        self.is_running = False
        self.is_paused = False
    
    def set_speed(self, factor: float):
        """ตั้งค่าความเร็วการจำลอง"""
        self.speed_factor = max(0.1, min(10.0, factor))
    
    def step(self, dt: float) -> bool:
        """ก้าวการจำลอง - Optimized"""
        if not self.is_running or self.is_paused:
            return False
        
        self.current_time += dt * self.speed_factor
        self.step_count += 1
        
        # Batch update machines for better performance
        completed_jobs = []
        
        for machine in self.factory.machines.values():
            completed_job = machine.update(self.current_time)
            if completed_job:
                completed_jobs.append(completed_job)
        
        # Process completed jobs
        for job in completed_jobs:
            self.factory.process_completed_job(job)
        
        # Start new processing
        for machine in self.factory.machines.values():
            machine.start_processing(self.current_time)
        
        # Try to route pending jobs
        jobs_to_remove = []
        for job in self.factory.jobs[:]:  # Copy list to avoid modification during iteration
            if self.factory.route_job(job):
                jobs_to_remove.append(job)
        
        for job in jobs_to_remove:
            self.factory.jobs.remove(job)
        
        # Record statistics less frequently
        if self.current_time - self.last_record_time >= 0.5:
            self.record_statistics()
            self.last_record_time = self.current_time
        
        return True
    
    def record_statistics(self):
        """บันทึกสถิติ - Optimized"""
        self.time_history.append(self.current_time)
        self.throughput_history.append(self.factory.get_total_throughput(self.current_time))
        self.utilization_history.append(self.factory.get_average_utilization(self.current_time))
        self.wip_history.append(self.factory.get_total_wip())
    
    def clear_history(self):
        """ล้างประวัติสถิติ"""
        self.time_history.clear()
        self.throughput_history.clear()
        self.utilization_history.clear()
        self.wip_history.clear()
    
    def get_simulation_summary(self) -> dict:
        """ได้สรุปการจำลอง"""
        real_elapsed = time.time() - self.start_real_time if self.start_real_time > 0 else 0
        
        return {
            "simulation_time": self.current_time,
            "real_time_elapsed": real_elapsed,
            "speed_factor": self.speed_factor,
            "step_count": self.step_count,
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "data_points": len(self.time_history)
        }
    
    def get_latest_metrics(self) -> dict:
        """ได้ metrics ล่าสุด"""
        if not self.time_history:
            return {
                "throughput": 0.0,
                "utilization": 0.0,
                "wip": 0,
                "time": 0.0
            }
        
        return {
            "throughput": self.throughput_history[-1] if self.throughput_history else 0.0,
            "utilization": self.utilization_history[-1] if self.utilization_history else 0.0,
            "wip": self.wip_history[-1] if self.wip_history else 0,
            "time": self.current_time
        }
    
    def reset(self):
        """รีเซ็ตการจำลอง"""
        self.stop()
        self.current_time = 0
        self.step_count = 0
        self.start_real_time = 0
        self.clear_history()
        self.factory.clear_all_jobs()
        self.factory.reset_statistics()
    
    def __str__(self) -> str:
        status = "Running" if self.is_running else "Paused" if self.is_paused else "Stopped"
        return f"Simulation: {status}, Time: {self.current_time:.1f}, Speed: {self.speed_factor}x"
