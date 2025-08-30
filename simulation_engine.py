"""
Simulation engine for factory operations
Handles timing, events, and simulation state management
"""

import time
import threading
from collections import deque
from typing import Optional, Callable, List
from models import Factory, Job


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
        
        # Event callbacks
        self.on_job_completed_callback: Optional[Callable] = None
        self.on_bottleneck_detected_callback: Optional[Callable] = None
        
    def start(self):
        """เริ่มการจำลอง"""
        self.is_running = True
        self.is_paused = False
        self.start_real_time = time.time()
        self.current_time = 0
        self.step_count = 0
    
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
    
    def reset(self):
        """รีเซ็ตการจำลอง"""
        self.stop()
        self.current_time = 0
        self.step_count = 0
        self.time_history.clear()
        self.throughput_history.clear()
        self.utilization_history.clear()
        self.wip_history.clear()
        self.factory.reset()
    
    def set_speed(self, factor: float):
        """ตั้งค่าความเร็ว"""
        self.speed_factor = max(0.1, min(10.0, factor))
    
    def step(self, dt: float):
        """ก้าวการจำลอง - Optimized"""
        if not self.is_running or self.is_paused:
            return
        
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
            job.current_step += 1
            if job.current_step < len(job.required_machines):
                self.factory.route_job(job)
            else:
                self.factory.completed_jobs.append(job)
                # Trigger callback if set
                if self.on_job_completed_callback:
                    self.on_job_completed_callback(job)
        
        # Start new processing
        for machine in self.factory.machines.values():
            machine.start_processing(self.current_time)
        
        # Record statistics less frequently
        if self.current_time - self.last_record_time >= 0.5:  # Every 0.5 seconds
            self.record_statistics()
            self.last_record_time = self.current_time
            
            # Check for bottlenecks
            self._check_bottlenecks()
    
    def record_statistics(self):
        """บันทึกสถิติ - Optimized"""
        self.time_history.append(self.current_time)
        self.throughput_history.append(self.factory.get_total_throughput(self.current_time))
        self.utilization_history.append(self.factory.get_average_utilization(self.current_time))
        self.wip_history.append(self.factory.get_total_wip())
    
    def _check_bottlenecks(self):
        """ตรวจสอบ bottleneck และเรียก callback"""
        bottleneck = self.factory.get_bottleneck_machine()
        if bottleneck and bottleneck.get_queue_length() > 10:
            if self.on_bottleneck_detected_callback:
                self.on_bottleneck_detected_callback(bottleneck)
    
    def get_performance_summary(self) -> dict:
        """ได้สรุปประสิทธิภาพ"""
        if self.current_time <= 0:
            return {
                "total_throughput": 0,
                "average_utilization": 0,
                "total_wip": 0,
                "completed_jobs": 0,
                "active_jobs": 0,
                "bottleneck": None
            }
        
        return {
            "total_throughput": self.factory.get_total_throughput(self.current_time),
            "average_utilization": self.factory.get_average_utilization(self.current_time),
            "total_wip": self.factory.get_total_wip(),
            "completed_jobs": len(self.factory.completed_jobs),
            "active_jobs": len(self.factory.jobs),
            "bottleneck": self.factory.get_bottleneck_machine()
        }
    
    def add_sample_jobs(self):
        """เพิ่มงานตัวอย่าง"""
        sample_jobs = [
            (15, ["CNC-01", "Lathe-01", "Assembly-01"], 1),
            (25, ["CNC-02", "Drill-01", "Inspection-01"], 1),
            (10, ["CNC-01", "Drill-01", "Assembly-01"], 2),
            (30, ["Lathe-01", "Assembly-01", "Inspection-01"], 1),
            (5, ["CNC-02", "Lathe-01", "Drill-01", "Assembly-01"], 3),
        ]
        
        for batch_size, sequence, priority in sample_jobs:
            # Only create job if all machines exist
            if self.factory.validate_job_sequence(sequence):
                job = self.factory.create_job(batch_size, sequence, priority)
                self.factory.route_job(job)


class SimulationThread:
    """Dedicated simulation thread with proper lifecycle management"""
    
    def __init__(self, sim_manager: SimulationManager):
        self.sim_manager = sim_manager
        self.thread = None
        self.running = False
        self.target_fps = 30
        self.frame_time = 1.0 / self.target_fps
        
        # Performance monitoring
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.current_fps = 0
        
        # Callbacks
        self.on_fps_update_callback: Optional[Callable] = None
        
    def start(self):
        """เริ่ม simulation thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._simulation_loop, daemon=True)
            self.thread.start()
    
    def stop(self):
        """หยุด simulation thread"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
    
    def _simulation_loop(self):
        """Main simulation loop - Optimized"""
        last_time = time.time()
        
        while self.running:
            loop_start = time.time()
            
            # Calculate delta time
            current_real_time = time.time()
            dt = min(current_real_time - last_time, 0.1)  # Cap at 100ms
            last_time = current_real_time
            
            # Update simulation
            self.sim_manager.step(dt)
            
            # Update FPS counter
            self._update_fps_counter(current_real_time)
            
            # Frame rate limiting
            loop_duration = time.time() - loop_start
            sleep_time = max(0, self.frame_time - loop_duration)
            time.sleep(sleep_time)
    
    def _update_fps_counter(self, current_time: float):
        """อัปเดต FPS counter"""
        self.fps_counter += 1
        
        if current_time - self.last_fps_time >= 1.0:
            self.current_fps = self.fps_counter / (current_time - self.last_fps_time)
            self.fps_counter = 0
            self.last_fps_time = current_time
            
            # Trigger callback if set
            if self.on_fps_update_callback:
                self.on_fps_update_callback(self.current_fps)
    
    def get_fps(self) -> float:
        """ได้ค่า FPS ปัจจุบัน"""
        return self.current_fps


class PerformanceAnalyzer:
    """วิเคราะห์ประสิทธิภาพและสร้างคำแนะนำ"""
    
    def __init__(self, factory: Factory, sim_manager: SimulationManager):
        self.factory = factory
        self.sim_manager = sim_manager
    
    def analyze_bottlenecks(self) -> dict:
        """วิเคราะห์ bottleneck"""
        bottlenecks = []
        
        for machine in self.factory.machines.values():
            queue_len = machine.get_queue_length()
            util = machine.get_utilization(self.sim_manager.current_time)
            
            severity = 0
            if queue_len > 15:
                severity += 3
            elif queue_len > 10:
                severity += 2
            elif queue_len > 5:
                severity += 1
            
            if util > 95:
                severity += 3
            elif util > 85:
                severity += 2
            elif util > 75:
                severity += 1
            
            if severity > 0:
                bottlenecks.append({
                    "machine": machine,
                    "severity": severity,
                    "queue_length": queue_len,
                    "utilization": util
                })
        
        # Sort by severity
        bottlenecks.sort(key=lambda x: x["severity"], reverse=True)
        
        return {
            "bottlenecks": bottlenecks,
            "most_critical": bottlenecks[0] if bottlenecks else None
        }
    
    def generate_suggestions(self) -> List[str]:
        """สร้างคำแนะนำการปรับปรุง"""
        suggestions = []
        
        if not self.factory.machines:
            return ["Add machines to start production"]
        
        # Analyze each machine
        for machine in self.factory.machines.values():
            util = machine.get_utilization(self.sim_manager.current_time)
            queue_len = machine.get_queue_length()
            
            if util > 95:
                suggestions.append(f"CRITICAL: {machine.name} overloaded ({util:.1f}%) - Add parallel machine urgently")
            elif util > 85:
                suggestions.append(f"WARNING: {machine.name} high utilization ({util:.1f}%) - Consider load balancing")
            elif util < 15:
                suggestions.append(f"INFO: {machine.name} underutilized ({util:.1f}%) - Check job routing")
            
            if queue_len > 15:
                suggestions.append(f"BOTTLENECK: {machine.name} has large queue ({queue_len} jobs)")
        
        # System-wide analysis
        total_wip = self.factory.get_total_wip()
        avg_util = self.factory.get_average_utilization(self.sim_manager.current_time)
        
        if total_wip > len(self.factory.machines) * 5:
            suggestions.append(f"HIGH WIP: Current WIP ({total_wip}) - Consider reducing batch sizes")
        
        if avg_util < 30:
            suggestions.append(f"LOW UTILIZATION: Average {avg_util:.1f}% - Increase job arrival rate")
        elif avg_util > 85:
            suggestions.append(f"HIGH UTILIZATION: Average {avg_util:.1f}% - System near capacity")
        
        if not suggestions:
            suggestions.append("OPTIMAL: System appears well-balanced")
        
        return suggestions
    
    def calculate_oee(self, machine) -> dict:
        """คำนวน OEE (Overall Equipment Effectiveness)"""
        # Availability = Utilization
        availability = machine.get_utilization(self.sim_manager.current_time) / 100
        
        # Performance = Ideal time / Actual time
        ideal_time = machine.base_time
        actual_time = machine.calculate_cycle_time(15)  # Assume standard batch size
        performance = ideal_time / actual_time if actual_time > 0 else 0
        
        # Quality (assumed 95% for simulation)
        quality = 0.95
        
        oee = availability * performance * quality
        
        # Rating
        if oee >= 0.85:
            rating = "Excellent"
        elif oee >= 0.65:
            rating = "Good"
        elif oee >= 0.40:
            rating = "Fair"
        else:
            rating = "Poor"
        
        return {
            "availability": availability * 100,
            "performance": performance * 100,
            "quality": quality * 100,
            "oee": oee * 100,
            "rating": rating
        }
    
    def get_machine_efficiency_ranking(self) -> List[tuple]:
        """ได้การจัดอันดับประสิทธิภาพเครื่องจักร"""
        rankings = []
        
        for machine in self.factory.machines.values():
            oee_data = self.calculate_oee(machine)
            efficiency_score = oee_data["oee"]
            
            rankings.append((machine, efficiency_score, oee_data))
        
        # Sort by efficiency score
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings
    
    def detect_inefficiencies(self) -> dict:
        """ตรวจหาจุดไม่มีประสิทธิภาพ"""
        inefficiencies = {
            "idle_machines": [],
            "overloaded_machines": [],
            "imbalanced_flow": [],
            "setup_time_issues": []
        }
        
        for machine in self.factory.machines.values():
            util = machine.get_utilization(self.sim_manager.current_time)
            queue_len = machine.get_queue_length()
            
            if util < 20:
                inefficiencies["idle_machines"].append(machine)
            elif util > 90:
                inefficiencies["overloaded_machines"].append(machine)
            
            if queue_len > 10:
                inefficiencies["imbalanced_flow"].append(machine)
            
            # Check setup time efficiency
            cycle_time = machine.calculate_cycle_time(1)  # Single part
            setup_ratio = machine.setup_time / cycle_time
            if setup_ratio > 0.5:  # Setup time > 50% of cycle time
                inefficiencies["setup_time_issues"].append(machine)
        
        return inefficiencies
