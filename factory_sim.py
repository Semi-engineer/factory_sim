import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import time
import math
import csv
from datetime import datetime
from collections import deque
from dataclasses import dataclass
from typing import List, Dict, Optional
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import json

# Configure matplotlib for better performance
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'
matplotlib.use('TkAgg')

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
        """คำนวณ Cycle Time แบบปรับปรุง"""
        if batch_size <= 0:
            return self.base_time + self.setup_time
        return self.base_time + (self.setup_time / batch_size)
    
    def add_job(self, job: Job):
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
        """คำนวณ Utilization แบบ Cached"""
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
        """คำนวณ WIP รวม - Cached"""
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
        """คำนวณ Utilization เฉลี่ย"""
        if not self.machines:
            return 0
        return sum(machine.get_utilization(total_time) for machine in self.machines.values()) / len(self.machines)
    
    def get_total_throughput(self, total_time: float) -> float:
        """คำนวณ Throughput รวม"""
        return sum(machine.get_throughput(total_time) for machine in self.machines.values())

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
    
    def pause(self):
        self.is_paused = True
    
    def resume(self):
        self.is_paused = False
    
    def stop(self):
        self.is_running = False
        self.is_paused = False
    
    def set_speed(self, factor: float):
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
        
        # Start new processing
        for machine in self.factory.machines.values():
            machine.start_processing(self.current_time)
        
        # Record statistics less frequently
        if self.current_time - self.last_record_time >= 0.5:  # Every 0.5 seconds
            self.record_statistics()
            self.last_record_time = self.current_time
    
    def record_statistics(self):
        """บันทึกสถิติ - Optimized"""
        self.time_history.append(self.current_time)
        self.throughput_history.append(self.factory.get_total_throughput(self.current_time))
        self.utilization_history.append(self.factory.get_average_utilization(self.current_time))
        self.wip_history.append(self.factory.get_total_wip())

class ModernFactoryCanvas:
    """Modern Factory Canvas with better rendering"""
    
    def __init__(self, parent, factory: Factory, sim_manager: SimulationManager):
        self.factory = factory
        self.sim_manager = sim_manager
        
        # Create modern canvas with ttkbootstrap
        self.canvas_frame = ttk.Frame(parent)
        self.canvas = tk.Canvas(
            self.canvas_frame, 
            bg="#f8f9fa", 
            highlightthickness=0,
            relief='flat'
        )
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack elements
        self.canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # Canvas properties
        self.canvas_objects = {}
        self.selected_machine = None
        self.dragging_machine = None
        self.last_click_pos = (0, 0)
        
        # Bind events
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<MouseWheel>", self.on_scroll)
        
        # Grid settings
        self.grid_size = 20
        self.show_grid = True
        
    def pack(self, **kwargs):
        self.canvas_frame.pack(**kwargs)
    
    def draw_grid(self):
        """วาดเส้น Grid"""
        if not self.show_grid:
            return
            
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Vertical lines
        for x in range(0, canvas_width, self.grid_size):
            self.canvas.create_line(x, 0, x, canvas_height, fill="#e9ecef", width=1, tags="grid")
        
        # Horizontal lines
        for y in range(0, canvas_height, self.grid_size):
            self.canvas.create_line(0, y, canvas_width, y, fill="#e9ecef", width=1, tags="grid")
    
    def draw_machine(self, machine: Machine):
        """วาดเครื่องจักร - Modern style"""
        x1, y1, x2, y2 = machine.get_bounds()
        
        # Main body with gradient effect
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=machine.status_color,
            outline="#495057",
            width=2,
            tags=f"machine_{machine.name}"
        )
        
        # Machine type indicator
        type_colors = {
            "CNC": "#007bff", "Lathe": "#28a745", "Drill": "#ffc107",
            "Assembly": "#dc3545", "Inspection": "#6f42c1", "Packaging": "#fd7e14"
        }
        
        color = type_colors.get(machine.machine_type, "#6c757d")
        self.canvas.create_rectangle(
            x1, y1, x1 + 10, y2,
            fill=color, outline="",
            tags=f"machine_{machine.name}"
        )
        
        # Machine name
        self.canvas.create_text(
            x1 + 60, y1 + 15,
            text=machine.name,
            font=("Segoe UI", 10, "bold"),
            fill="#212529",
            tags=f"machine_{machine.name}"
        )
        
        # Status information
        queue_len = machine.get_queue_length()
        util = machine.get_utilization(self.sim_manager.current_time)
        
        self.canvas.create_text(
            x1 + 60, y1 + 35,
            text=f"Queue: {queue_len}",
            font=("Segoe UI", 9),
            fill="#495057",
            tags=f"machine_{machine.name}"
        )
        
        self.canvas.create_text(
            x1 + 60, y1 + 50,
            text=f"Util: {util:.1f}%",
            font=("Segoe UI", 9),
            fill="#495057",
            tags=f"machine_{machine.name}"
        )
        
        # Working indicator
        if machine.is_working:
            # Animated working indicator
            pulse = 0.7 + 0.3 * math.sin(machine.animation_phase * 4)
            self.canvas.create_oval(
                x2 - 20, y1 + 10, x2 - 10, y1 + 20,
                fill=f"#ff{int(100 + 155 * pulse):02x}00",
                outline="#dc3545",
                width=2,
                tags=f"machine_{machine.name}"
            )
        
        # Queue visualization
        if queue_len > 0:
            queue_width = min(queue_len * 3, 30)
            self.canvas.create_rectangle(
                x1 + 15, y2 - 8, x1 + 15 + queue_width, y2 - 3,
                fill="#ffc107", outline="#e0a800",
                tags=f"machine_{machine.name}"
            )
    
    def update_display(self):
        """อัปเดตการแสดงผล - Optimized"""
        # Clear only machine objects, keep grid
        self.canvas.delete("machine")
        
        # Redraw grid if needed
        if self.show_grid:
            self.canvas.delete("grid")
            self.draw_grid()
        
        # Draw machines
        for machine in self.factory.machines.values():
            self.draw_machine(machine)
        
        # Draw connections/flow lines
        self.draw_flow_lines()
    
    def draw_flow_lines(self):
        """วาดเส้นเชื่อมระหว่างเครื่องจักร"""
        # Simple flow visualization for active jobs
        for job in self.factory.jobs:
            if job.current_step < len(job.required_machines) - 1:
                current_machine_name = job.required_machines[job.current_step]
                next_machine_name = job.required_machines[job.current_step + 1]
                
                if (current_machine_name in self.factory.machines and 
                    next_machine_name in self.factory.machines):
                    
                    m1 = self.factory.machines[current_machine_name]
                    m2 = self.factory.machines[next_machine_name]
                    
                    # Draw arrow
                    x1, y1 = m1.x + m1.width, m1.y + m1.height // 2
                    x2, y2 = m2.x, m2.y + m2.height // 2
                    
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill="#6c757d", width=2, dash=(5, 5),
                        arrow=tk.LAST, arrowshape=(10, 12, 3),
                        tags="flow"
                    )
    
    def on_click(self, event):
        """จัดการการคลิก"""
        self.last_click_pos = (event.x, event.y)
        clicked_machine = self.get_machine_at_position(event.x, event.y)
        
        if clicked_machine:
            self.selected_machine = clicked_machine
            self.dragging_machine = clicked_machine
    
    def on_drag(self, event):
        """จัดการการลาก - Snap to grid"""
        if self.dragging_machine:
            # Snap to grid
            new_x = ((event.x // self.grid_size) * self.grid_size)
            new_y = ((event.y // self.grid_size) * self.grid_size)
            
            # Boundary checking
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            new_x = max(0, min(canvas_width - self.dragging_machine.width, new_x))
            new_y = max(0, min(canvas_height - self.dragging_machine.height, new_y))
            
            self.dragging_machine.x = new_x
            self.dragging_machine.y = new_y
    
    def on_release(self, event):
        """ปล่อยการลาก"""
        self.dragging_machine = None
    
    def on_double_click(self, event):
        """Double click เพื่อกำหนดค่า"""
        machine = self.get_machine_at_position(event.x, event.y)
        if machine:
            # Trigger machine configuration
            if hasattr(self, 'config_callback'):
                self.config_callback(machine)
    
    def on_scroll(self, event):
        """Zoom in/out"""
        pass  # Could implement zoom functionality
    
    def get_machine_at_position(self, x: int, y: int) -> Optional[Machine]:
        """หาเครื่องจักรที่ตำแหน่งที่คลิก"""
        for machine in self.factory.machines.values():
            x1, y1, x2, y2 = machine.get_bounds()
            if x1 <= x <= x2 and y1 <= y <= y2:
                return machine
        return None

class ModernChartsPanel:
    """Modern Charts Panel with better performance"""
    
    def __init__(self, parent, sim_manager: SimulationManager):
        self.sim_manager = sim_manager
        self.parent = parent
        
        # Create figure with modern style
        plt.style.use('seaborn-v0_8-whitegrid')
        self.fig = Figure(figsize=(8, 10), facecolor='white', tight_layout=True)
        
        # Create subplots
        self.ax1 = self.fig.add_subplot(221)  # Throughput
        self.ax2 = self.fig.add_subplot(222)  # Utilization
        self.ax3 = self.fig.add_subplot(223)  # WIP
        self.ax4 = self.fig.add_subplot(224)  # Machine comparison
        
        # Style the plots
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.grid(True, alpha=0.3)
            ax.set_facecolor('#f8f9fa')
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().configure(bg='white')
        
        # Performance optimization
        self.last_update_time = 0
        self.update_interval = 1.0  # Update every 1 second
        
        # Chart data cache
        self._cached_plots = {}
        
    def pack(self, **kwargs):
        self.canvas.get_tk_widget().pack(**kwargs)
    
    def update_charts(self, force_update=False):
        """อัปเดตกราฟ - Optimized"""
        current_time = time.time()
        
        if not force_update and current_time - self.last_update_time < self.update_interval:
            return
        
        if len(self.sim_manager.time_history) < 2:
            return
        
        # Convert deques to numpy arrays for better performance
        times = np.array(self.sim_manager.time_history)
        throughputs = np.array(self.sim_manager.throughput_history)
        utilizations = np.array(self.sim_manager.utilization_history)
        wips = np.array(self.sim_manager.wip_history)
        
        # Clear and redraw with modern styling
        self.ax1.clear()
        self.ax2.clear() 
        self.ax3.clear()
        self.ax4.clear()
        
        # Throughput chart
        self.ax1.plot(times, throughputs, color='#007bff', linewidth=2, alpha=0.8)
        self.ax1.fill_between(times, throughputs, alpha=0.2, color='#007bff')
        self.ax1.set_title('Throughput Over Time', fontweight='bold', pad=15)
        self.ax1.set_ylabel('Parts/min')
        self.ax1.grid(True, alpha=0.3)
        
        # Utilization chart
        self.ax2.plot(times, utilizations, color='#28a745', linewidth=2, alpha=0.8)
        self.ax2.fill_between(times, utilizations, alpha=0.2, color='#28a745')
        self.ax2.set_title('Average Utilization', fontweight='bold', pad=15)
        self.ax2.set_ylabel('Utilization (%)')
        self.ax2.set_ylim(0, 100)
        self.ax2.grid(True, alpha=0.3)
        
        # WIP chart
        self.ax3.plot(times, wips, color='#dc3545', linewidth=2, alpha=0.8)
        self.ax3.fill_between(times, wips, alpha=0.2, color='#dc3545')
        self.ax3.set_title('Work In Process', fontweight='bold', pad=15)
        self.ax3.set_ylabel('WIP Count')
        self.ax3.set_xlabel('Time (min)')
        self.ax3.grid(True, alpha=0.3)
        
        # Machine utilization comparison
        if self.sim_manager.factory.machines:
            machine_names = list(self.sim_manager.factory.machines.keys())
            utilizations = [m.get_utilization(self.sim_manager.current_time) 
                          for m in self.sim_manager.factory.machines.values()]
            
            # Color bars based on utilization level
            colors = []
            for util in utilizations:
                if util > 80:
                    colors.append('#dc3545')  # Red
                elif util > 60:
                    colors.append('#ffc107')  # Yellow
                elif util > 40:
                    colors.append('#28a745')  # Green
                else:
                    colors.append('#6c757d')  # Gray
            
            bars = self.ax4.bar(range(len(machine_names)), utilizations, color=colors, alpha=0.8)
            self.ax4.set_title('Machine Utilization', fontweight='bold', pad=15)
            self.ax4.set_ylabel('Utilization (%)')
            self.ax4.set_xticks(range(len(machine_names)))
            self.ax4.set_xticklabels(machine_names, rotation=45, ha='right')
            self.ax4.set_ylim(0, 100)
            self.ax4.grid(True, alpha=0.3)
            
            # Add value labels on bars
            for bar, util in zip(bars, utilizations):
                height = bar.get_height()
                self.ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                             f'{util:.1f}%', ha='center', va='bottom', fontsize=8)
        
        # Redraw canvas
        self.canvas.draw_idle()  # Use idle draw for better performance
        self.last_update_time = current_time
    
    def on_click(self, event):
        """จัดการการคลิก"""
        self.last_click_pos = (event.x, event.y)
        machine = self.get_machine_at_position(event.x, event.y)
        
        if machine:
            self.selected_machine = machine
            self.dragging_machine = machine
            # Highlight selected machine
            self.highlight_machine(machine)
    
    def on_drag(self, event):
        """จัดการการลาก"""
        if self.dragging_machine:
            # Snap to grid
            new_x = ((event.x // self.grid_size) * self.grid_size)
            new_y = ((event.y // self.grid_size) * self.grid_size)
            
            # Boundary checking
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            new_x = max(0, min(canvas_width - self.dragging_machine.width, new_x))
            new_y = max(0, min(canvas_height - self.dragging_machine.height, new_y))
            
            self.dragging_machine.x = new_x
            self.dragging_machine.y = new_y
    
    def on_release(self, event):
        """ปล่อยการลาก"""
        self.dragging_machine = None
    
    def on_double_click(self, event):
        """Double click configuration"""
        machine = self.get_machine_at_position(event.x, event.y)
        if machine and hasattr(self, 'config_callback'):
            self.config_callback(machine)
    
    def on_scroll(self, event):
        """Mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def get_machine_at_position(self, x: int, y: int) -> Optional[Machine]:
        """หาเครื่องจักรที่ตำแหน่งคลิก"""
        for machine in self.factory.machines.values():
            x1, y1, x2, y2 = machine.get_bounds()
            if x1 <= x <= x2 and y1 <= y <= y2:
                return machine
        return None
    
    def highlight_machine(self, machine: Machine):
        """เน้นเครื่องจักรที่เลือก"""
        # Add selection highlight
        x1, y1, x2, y2 = machine.get_bounds()
        self.canvas.create_rectangle(
            x1 - 3, y1 - 3, x2 + 3, y2 + 3,
            outline="#007bff", width=3, fill="",
            tags="selection"
        )

class ModernChartsPanel:
    """Modern Charts Panel with better performance"""
    
    def __init__(self, parent, sim_manager: SimulationManager):
        self.sim_manager = sim_manager
        self.parent = parent
        
        # Create figure with modern style
        plt.style.use('seaborn-v0_8-whitegrid')
        self.fig = Figure(figsize=(8, 10), facecolor='white', tight_layout=True)
        
        # Create subplots
        self.ax1 = self.fig.add_subplot(221)  # Throughput
        self.ax2 = self.fig.add_subplot(222)  # Utilization
        self.ax3 = self.fig.add_subplot(223)  # WIP
        self.ax4 = self.fig.add_subplot(224)  # Machine comparison
        
        # Style the plots
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.grid(True, alpha=0.3)
            ax.set_facecolor('#f8f9fa')
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().configure(bg='white')
        
        # Performance optimization
        self.last_update_time = 0
        self.update_interval = 1.0  # Update every 1 second
        
        # Chart data cache
        self._cached_plots = {}
        
    def pack(self, **kwargs):
        self.canvas.get_tk_widget().pack(**kwargs)
    
    def update_charts(self, force_update=False):
        """อัปเดตกราฟ - Optimized"""
        current_time = time.time()
        
        if not force_update and current_time - self.last_update_time < self.update_interval:
            return
        
        if len(self.sim_manager.time_history) < 2:
            return
        
        # Convert deques to numpy arrays for better performance
        times = np.array(self.sim_manager.time_history)
        throughputs = np.array(self.sim_manager.throughput_history)
        utilizations = np.array(self.sim_manager.utilization_history)
        wips = np.array(self.sim_manager.wip_history)
        
        # Clear and redraw with modern styling
        self.ax1.clear()
        self.ax2.clear() 
        self.ax3.clear()
        self.ax4.clear()
        
        # Throughput chart
        self.ax1.plot(times, throughputs, color='#007bff', linewidth=2, alpha=0.8)
        self.ax1.fill_between(times, throughputs, alpha=0.2, color='#007bff')
        self.ax1.set_title('Throughput Over Time', fontweight='bold', pad=15)
        self.ax1.set_ylabel('Parts/min')
        self.ax1.grid(True, alpha=0.3)
        
        # Utilization chart
        self.ax2.plot(times, utilizations, color='#28a745', linewidth=2, alpha=0.8)
        self.ax2.fill_between(times, utilizations, alpha=0.2, color='#28a745')
        self.ax2.set_title('Average Utilization', fontweight='bold', pad=15)
        self.ax2.set_ylabel('Utilization (%)')
        self.ax2.set_ylim(0, 100)
        self.ax2.grid(True, alpha=0.3)
        
        # WIP chart
        self.ax3.plot(times, wips, color='#dc3545', linewidth=2, alpha=0.8)
        self.ax3.fill_between(times, wips, alpha=0.2, color='#dc3545')
        self.ax3.set_title('Work In Process', fontweight='bold', pad=15)
        self.ax3.set_ylabel('WIP Count')
        self.ax3.set_xlabel('Time (min)')
        self.ax3.grid(True, alpha=0.3)
        
        # Machine utilization comparison
        if self.sim_manager.factory.machines:
            machine_names = list(self.sim_manager.factory.machines.keys())
            utilizations = [m.get_utilization(self.sim_manager.current_time) 
                          for m in self.sim_manager.factory.machines.values()]
            
            # Color bars based on utilization level
            colors = []
            for util in utilizations:
                if util > 80:
                    colors.append('#dc3545')  # Red
                elif util > 60:
                    colors.append('#ffc107')  # Yellow
                elif util > 40:
                    colors.append('#28a745')  # Green
                else:
                    colors.append('#6c757d')  # Gray
            
            bars = self.ax4.bar(range(len(machine_names)), utilizations, color=colors, alpha=0.8)
            self.ax4.set_title('Machine Utilization', fontweight='bold', pad=15)
            self.ax4.set_ylabel('Utilization (%)')
            self.ax4.set_xticks(range(len(machine_names)))
            self.ax4.set_xticklabels(machine_names, rotation=45, ha='right')
            self.ax4.set_ylim(0, 100)
            self.ax4.grid(True, alpha=0.3)
            
            # Add value labels on bars
            for bar, util in zip(bars, utilizations):
                height = bar.get_height()
                self.ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                             f'{util:.1f}%', ha='center', va='bottom', fontsize=8)
        
        # Redraw canvas
        self.canvas.draw_idle()  # Use idle draw for better performance
        self.last_update_time = current_time
    
    def on_click(self, event):
        """จัดการการคลิก"""
        self.last_click_pos = (event.x, event.y)
        machine = self.get_machine_at_position(event.x, event.y)
        
        if machine:
            self.selected_machine = machine
            self.dragging_machine = machine
            # Highlight selected machine
            self.highlight_machine(machine)
    
    def on_drag(self, event):
        """จัดการการลาก"""
        if self.dragging_machine:
            # Snap to grid
            new_x = ((event.x // self.grid_size) * self.grid_size)
            new_y = ((event.y // self.grid_size) * self.grid_size)
            
            # Boundary checking
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            new_x = max(0, min(canvas_width - self.dragging_machine.width, new_x))
            new_y = max(0, min(canvas_height - self.dragging_machine.height, new_y))
            
            self.dragging_machine.x = new_x
            self.dragging_machine.y = new_y
    
    def on_release(self, event):
        """ปล่อยการลาก"""
        self.dragging_machine = None
    
    def on_double_click(self, event):
        """Double click configuration"""
        machine = self.get_machine_at_position(event.x, event.y)
        if machine and hasattr(self, 'config_callback'):
            self.config_callback(machine)
    
    def on_scroll(self, event):
        """Mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def get_machine_at_position(self, x: int, y: int) -> Optional[Machine]:
        """หาเครื่องจักรที่ตำแหน่งที่คลิก"""
        for machine in self.factory.machines.values():
            x1, y1, x2, y2 = machine.get_bounds()
            if x1 <= x <= x2 and y1 <= y <= y2:
                return machine
        return None
    
    def highlight_machine(self, machine: Machine):
        """เน้นเครื่องจักรที่เลือก"""
        # Add selection highlight
        x1, y1, x2, y2 = machine.get_bounds()
        self.canvas.create_rectangle(
            x1 - 3, y1 - 3, x2 + 3, y2 + 3,
            outline="#007bff", width=3, fill="",
            tags="selection"
        )

class ModernChartsPanel:
    """Modern Charts Panel with better performance"""
    
    def __init__(self, parent, sim_manager: SimulationManager):
        self.sim_manager = sim_manager
        self.parent = parent
        
        # Create figure with modern style
        plt.style.use('seaborn-v0_8-whitegrid')
        self.fig = Figure(figsize=(8, 10), facecolor='white', tight_layout=True)
        
        # Create subplots
        self.ax1 = self.fig.add_subplot(221)  # Throughput
        self.ax2 = self.fig.add_subplot(222)  # Utilization
        self.ax3 = self.fig.add_subplot(223)  # WIP
        self.ax4 = self.fig.add_subplot(224)  # Machine comparison
        
        # Style the plots
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.grid(True, alpha=0.3)
            ax.set_facecolor('#f8f9fa')
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().configure(bg='white')
        
        # Performance optimization
        self.last_update_time = 0
        self.update_interval = 1.0  # Update every 1 second
        
        # Chart data cache
        self._cached_plots = {}
        
    def pack(self, **kwargs):
        self.canvas.get_tk_widget().pack(**kwargs)
    
    def update_charts(self, force_update=False):
        """อัปเดตกราฟ - Optimized"""
        current_time = time.time()
        
        if not force_update and current_time - self.last_update_time < self.update_interval:
            return
        
        if len(self.sim_manager.time_history) < 2:
            return
        
        # Convert deques to numpy arrays for better performance
        times = np.array(self.sim_manager.time_history)
        throughputs = np.array(self.sim_manager.throughput_history)
        utilizations = np.array(self.sim_manager.utilization_history)
        wips = np.array(self.sim_manager.wip_history)
        
        # Clear and redraw with modern styling
        self.ax1.clear()
        self.ax2.clear() 
        self.ax3.clear()
        self.ax4.clear()
        
        # Throughput chart
        self.ax1.plot(times, throughputs, color='#007bff', linewidth=2, alpha=0.8)
        self.ax1.fill_between(times, throughputs, alpha=0.2, color='#007bff')
        self.ax1.set_title('Throughput Over Time', fontweight='bold', pad=15)
        self.ax1.set_ylabel('Parts/min')
        self.ax1.grid(True, alpha=0.3)
        
        # Utilization chart
        self.ax2.plot(times, utilizations, color='#28a745', linewidth=2, alpha=0.8)
        self.ax2.fill_between(times, utilizations, alpha=0.2, color='#28a745')
        self.ax2.set_title('Average Utilization', fontweight='bold', pad=15)
        self.ax2.set_ylabel('Utilization (%)')
        self.ax2.set_ylim(0, 100)
        self.ax2.grid(True, alpha=0.3)
        
        # WIP chart
        self.ax3.plot(times, wips, color='#dc3545', linewidth=2, alpha=0.8)
        self.ax3.fill_between(times, wips, alpha=0.2, color='#dc3545')
        self.ax3.set_title('Work In Process', fontweight='bold', pad=15)
        self.ax3.set_ylabel('WIP Count')
        self.ax3.set_xlabel('Time (min)')
        self.ax3.grid(True, alpha=0.3)
        
        # Machine utilization comparison
        if self.sim_manager.factory.machines:
            machine_names = list(self.sim_manager.factory.machines.keys())
            utilizations = [m.get_utilization(self.sim_manager.current_time) 
                          for m in self.sim_manager.factory.machines.values()]
            
            # Color bars based on utilization level
            colors = []
            for util in utilizations:
                if util > 80:
                    colors.append('#dc3545')  # Red
                elif util > 60:
                    colors.append('#ffc107')  # Yellow
                elif util > 40:
                    colors.append('#28a745')  # Green
                else:
                    colors.append('#6c757d')  # Gray
            
            bars = self.ax4.bar(range(len(machine_names)), utilizations, color=colors, alpha=0.8)
            self.ax4.set_title('Machine Utilization', fontweight='bold', pad=15)
            self.ax4.set_ylabel('Utilization (%)')
            self.ax4.set_xticks(range(len(machine_names)))
            self.ax4.set_xticklabels(machine_names, rotation=45, ha='right')
            self.ax4.set_ylim(0, 100)
            self.ax4.grid(True, alpha=0.3)
            
            # Add value labels on bars
            for bar, util in zip(bars, utilizations):
                height = bar.get_height()
                self.ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                             f'{util:.1f}%', ha='center', va='bottom', fontsize=8)
        
        # Redraw canvas
        self.canvas.draw_idle()  # Use idle draw for better performance
        self.last_update_time = current_time
    
    def on_click(self, event):
        """จัดการการคลิก"""
        self.last_click_pos = (event.x, event.y)
        machine = self.get_machine_at_position(event.x, event.y)
        
        if machine:
            self.selected_machine = machine
            self.dragging_machine = machine
            # Highlight selected machine
            self.highlight_machine(machine)
    
    def on_drag(self, event):
        """จัดการการลาก"""
        if self.dragging_machine:
            # Snap to grid
            new_x = ((event.x // self.grid_size) * self.grid_size)
            new_y = ((event.y // self.grid_size) * self.grid_size)
            
            # Boundary checking
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            new_x = max(0, min(canvas_width - self.dragging_machine.width, new_x))
            new_y = max(0, min(canvas_height - self.dragging_machine.height, new_y))
            
            self.dragging_machine.x = new_x
            self.dragging_machine.y = new_y
    
    def on_release(self, event):
        """ปล่อยการลาก"""
        self.dragging_machine = None
    
    def on_double_click(self, event):
        """Double click configuration"""
        machine = self.get_machine_at_position(event.x, event.y)
        if machine and hasattr(self, 'config_callback'):
            self.config_callback(machine)
    
    def on_scroll(self, event):
        """Mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def get_machine_at_position(self, x: int, y: int) -> Optional[Machine]:
        """หาเครื่องจักรที่ตำแหน่งที่คลิก"""
        for machine in self.factory.machines.values():
            x1, y1, x2, y2 = machine.get_bounds()
            if x1 <= x <= x2 and y1 <= y <= y2:
                return machine
        return None
    
    def highlight_machine(self, machine: Machine):
        """เน้นเครื่องจักรที่เลือก"""
        # Add selection highlight
        x1, y1, x2, y2 = machine.get_bounds()
        self.canvas.create_rectangle(
            x1 - 3, y1 - 3, x2 + 3, y2 + 3,
            outline="#007bff", width=3, fill="",
            tags="selection"
        )

class ModernFactorySimulationGUI:
    """Modern GUI using ttkbootstrap"""
    
    def __init__(self):
        # Create main window with modern theme
        self.root = ttk.Window(themename="superhero")  # Modern theme
        self.root.title("🏭 Factory RTS Simulation - Modern Edition")
        self.root.geometry("1600x1000")
        self.root.minsize(1200, 800)
        
        # Initialize core components
        self.factory = Factory()
        self.sim_manager = SimulationManager(self.factory)
        
        # GUI state
        self.selected_machine = None
        self.update_timer = None
        self.step_count = 0  # <-- Add this line
        
        # Setup
        self.setup_default_machines()
        self.setup_modern_gui()
        self.setup_simulation_thread()
        
    def setup_default_machines(self):
        """สร้างเครื่องจักรตัวอย่าง"""
        machines = [
            Machine("CNC-01", "CNC", 2.5, 10, 100, 150),
            Machine("CNC-02", "CNC", 2.8, 12, 100, 300),
            Machine("Lathe-01", "Lathe", 3.2, 15, 350, 150),
            Machine("Drill-01", "Drill", 1.8, 8, 600, 150),
            Machine("Assembly-01", "Assembly", 4.5, 25, 850, 150),
            Machine("Inspection-01", "Inspection", 1.2, 5, 850, 300),
        ]
        
        for machine in machines:
            self.factory.add_machine(machine)
    
    def setup_modern_gui(self):
        """สร้าง Modern GUI Layout"""
        # Main container with modern styling
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Top control panel with modern buttons
        self.setup_control_panel(main_container)
        
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(main_container, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=True, pady=(10, 0))
        
        # Factory Layout Tab
        self.factory_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.factory_tab, text="🏭 Factory Layout")
        
        # Analytics Tab
        self.analytics_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.analytics_tab, text="📊 Analytics")
        
        # Machine Details Tab
        self.details_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.details_tab, text="⚙️ Machine Details")
        
        # Setup tab contents
        self.setup_factory_tab()
        self.setup_analytics_tab()
        self.setup_details_tab()
        
        # Status bar
        self.setup_status_bar(main_container)
    
    def setup_control_panel(self, parent):
        """Modern Control Panel"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=X, pady=(0, 10))
        
        # Left controls
        left_controls = ttk.Frame(control_frame)
        left_controls.pack(side=LEFT, fill=X, expand=True)
        
        # Simulation controls with modern buttons
        sim_controls = ttk.LabelFrame(left_controls, text="🎮 Simulation Controls", padding=10)
        sim_controls.pack(side=LEFT, padx=(0, 10))
        
        self.start_btn = ttk.Button(sim_controls, text="▶ Start", bootstyle="success", command=self.start_simulation)
        self.start_btn.pack(side=LEFT, padx=2)
        
        self.pause_btn = ttk.Button(sim_controls, text="⏸ Pause", bootstyle="warning", command=self.pause_simulation)
        self.pause_btn.pack(side=LEFT, padx=2)
        
        self.resume_btn = ttk.Button(sim_controls, text="⏵ Resume", bootstyle="info", command=self.resume_simulation)
        self.resume_btn.pack(side=LEFT, padx=2)
        
        self.stop_btn = ttk.Button(sim_controls, text="⏹ Stop", bootstyle="danger", command=self.stop_simulation)
        self.stop_btn.pack(side=LEFT, padx=2)
        
        # Speed control with modern styling
        speed_frame = ttk.LabelFrame(left_controls, text="⚡ Speed Control", padding=10)
        speed_frame.pack(side=LEFT, padx=(0, 10))
        
        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_scale = ttk.Scale(
            speed_frame, from_=0.1, to=5.0, orient=HORIZONTAL,
            variable=self.speed_var, command=self.on_speed_change,
            bootstyle="info", length=150
        )
        self.speed_scale.pack(side=LEFT, padx=5)
        
        self.speed_label = ttk.Label(speed_frame, text="1.0x", font=("Segoe UI", 10, "bold"))
        self.speed_label.pack(side=LEFT, padx=5)
        
        # Factory controls
        factory_controls = ttk.LabelFrame(left_controls, text="🏗️ Factory Management", padding=10)
        factory_controls.pack(side=LEFT)
        
        ttk.Button(factory_controls, text="➕ Add Job", bootstyle="primary-outline", 
                  command=self.add_job_dialog).pack(side=LEFT, padx=2)
        ttk.Button(factory_controls, text="🔧 Add Machine", bootstyle="secondary-outline", 
                  command=self.add_machine_dialog).pack(side=LEFT, padx=2)
        ttk.Button(factory_controls, text="💾 Export", bootstyle="success-outline", 
                  command=self.export_data).pack(side=LEFT, padx=2)
    
    def setup_factory_tab(self):
        """Factory Layout Tab"""
        # Split into canvas and mini-dashboard
        paned = ttk.PanedWindow(self.factory_tab, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # Factory canvas
        canvas_frame = ttk.LabelFrame(paned, text="🏭 Factory Floor", padding=5)
        self.factory_canvas = ModernFactoryCanvas(canvas_frame, self.factory, self.sim_manager)
        self.factory_canvas.config_callback = self.configure_machine
        self.factory_canvas.pack(fill=BOTH, expand=True)
        paned.add(canvas_frame, weight=3)
        
        # Live dashboard
        dashboard_frame = ttk.LabelFrame(paned, text="📈 Live Dashboard", padding=10)
        self.setup_live_dashboard(dashboard_frame)
        paned.add(dashboard_frame, weight=1)
    
    def setup_live_dashboard(self, parent):
        """Live performance dashboard"""
        # Key metrics with modern cards
        metrics_frame = ttk.Frame(parent)
        metrics_frame.pack(fill=X, pady=(0, 10))
        
        # Time card
        time_card = ttk.LabelFrame(metrics_frame, text="⏱️ Simulation Time", padding=10)
        time_card.pack(fill=X, pady=2)
        self.time_label = ttk.Label(time_card, text="0.0 min", font=("Segoe UI", 14, "bold"), 
                                   bootstyle="primary")
        self.time_label.pack()
        
        # Throughput card
        throughput_card = ttk.LabelFrame(metrics_frame, text="🚀 Total Throughput", padding=10)
        throughput_card.pack(fill=X, pady=2)
        self.throughput_label = ttk.Label(throughput_card, text="0.0 parts/min", 
                                         font=("Segoe UI", 12, "bold"), bootstyle="success")
        self.throughput_label.pack()
        
        # Utilization card
        util_card = ttk.LabelFrame(metrics_frame, text="📊 Avg Utilization", padding=10)
        util_card.pack(fill=X, pady=2)
        self.utilization_label = ttk.Label(util_card, text="0.0%", 
                                          font=("Segoe UI", 12, "bold"), bootstyle="info")
        self.utilization_label.pack()
        
        # WIP card
        wip_card = ttk.LabelFrame(metrics_frame, text="📦 Total WIP", padding=10)
        wip_card.pack(fill=X, pady=2)
        self.wip_label = ttk.Label(wip_card, text="0", font=("Segoe UI", 12, "bold"), 
                                  bootstyle="warning")
        self.wip_label.pack()
        
        # Quick actions
        actions_frame = ttk.LabelFrame(parent, text="⚡ Quick Actions", padding=10)
        actions_frame.pack(fill=X, pady=(10, 0))
        
        ttk.Button(actions_frame, text="🔍 Find Bottleneck", bootstyle="outline-danger",
                  command=self.find_bottleneck).pack(fill=X, pady=2)
        ttk.Button(actions_frame, text="💡 Suggestions", bootstyle="outline-warning",
                  command=self.show_suggestions).pack(fill=X, pady=2)
        ttk.Button(actions_frame, text="🏆 OEE Analysis", bootstyle="outline-info",
                  command=self.show_oee_dialog).pack(fill=X, pady=2)
    
    def setup_analytics_tab(self):
        """Analytics Tab with modern charts"""
        self.charts_panel = ModernChartsPanel(self.analytics_tab, self.sim_manager)
        self.charts_panel.pack(fill=BOTH, expand=True, padx=5, pady=5)
    
    def setup_details_tab(self):
        """Machine Details Tab"""
        # Search and filter
        search_frame = ttk.Frame(self.details_tab)
        search_frame.pack(fill=X, padx=10, pady=10)
        
        ttk.Label(search_frame, text="🔍 Search:").pack(side=LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=LEFT, padx=(0, 10))
        search_entry.bind('<KeyRelease>', self.filter_machines)
        
        # Filter by type
        ttk.Label(search_frame, text="Filter Type:").pack(side=LEFT, padx=(10, 5))
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(search_frame, textvariable=self.filter_var, width=15,
                                   values=["All", "CNC", "Lathe", "Drill", "Assembly", "Inspection", "Packaging"])
        filter_combo.pack(side=LEFT)
        filter_combo.bind('<<ComboboxSelected>>', self.filter_machines)
        
        # Modern table with sorting
        table_frame = ttk.Frame(self.details_tab)
        table_frame.pack(fill=BOTH, expand=True, padx=10, pady=(0, 10))
        
        columns = ("Name", "Type", "Queue", "Utilization", "Throughput", "Cycle Time", "Status")
        self.machine_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # Configure columns with sorting
        column_widths = {"Name": 120, "Type": 100, "Queue": 80, "Utilization": 100, 
                        "Throughput": 120, "Cycle Time": 100, "Status": 100}
        
        for col in columns:
            self.machine_tree.heading(col, text=col, command=lambda c=col: self.sort_column(c))
            self.machine_tree.column(col, width=column_widths.get(col, 100))
        
        # Scrollbar for table
        scrollbar = ttk.Scrollbar(table_frame, orient=VERTICAL, command=self.machine_tree.yview)
        self.machine_tree.configure(yscrollcommand=scrollbar.set)
        
        self.machine_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Bind selection
        self.machine_tree.bind("<<TreeviewSelect>>", self.on_machine_table_select)
        self.machine_tree.bind("<Double-1>", self.on_machine_table_double_click)
        
        # Sort state
        self.sort_column_name = None
        self.sort_reverse = False
    
    def setup_status_bar(self, parent):
        """Modern status bar"""
        self.status_frame = ttk.Frame(parent)
        self.status_frame.pack(fill=X, pady=(10, 0))
        
        # Status indicators
        ttk.Label(self.status_frame, text="Status:", font=("Segoe UI", 9)).pack(side=LEFT)
        
        self.status_indicator = ttk.Label(self.status_frame, text="● Stopped", 
                                         foreground="#dc3545", font=("Segoe UI", 9, "bold"))
        self.status_indicator.pack(side=LEFT, padx=(5, 20))
        
        ttk.Label(self.status_frame, text="Performance:", font=("Segoe UI", 9)).pack(side=LEFT)
        self.perf_label = ttk.Label(self.status_frame, text="-- FPS", font=("Segoe UI", 9))
        self.perf_label.pack(side=LEFT, padx=5)
    
    def setup_simulation_thread(self):
        """Setup optimized simulation thread"""
        self.simulation_thread = None
        self.thread_running = False
        self.fps_counter = 0
        self.last_fps_time = time.time()
    
    def simulation_loop(self):
        """Optimized simulation loop"""
        last_time = time.time()
        target_fps = 30  # Target 30 FPS
        frame_time = 1.0 / target_fps
        
        while self.thread_running:
            loop_start = time.time()
            
            # Calculate delta time
            current_real_time = time.time()
            dt = min(current_real_time - last_time, 0.1)  # Cap at 100ms
            last_time = current_real_time
            
            # Update simulation
            self.sim_manager.step(dt)
            
            # Update FPS counter
            self.fps_counter += 1
            if current_real_time - self.last_fps_time >= 1.0:
                fps = self.fps_counter / (current_real_time - self.last_fps_time)
                self.root.after_idle(lambda: self.perf_label.config(text=f"{fps:.1f} FPS"))
                self.fps_counter = 0
                self.last_fps_time = current_real_time
            
            # Schedule GUI update (less frequent)
            if self.step_count % 10 == 0:  # Update GUI every 10 steps
                self.root.after_idle(self.update_gui)
            
            # Frame rate limiting
            loop_duration = time.time() - loop_start
            sleep_time = max(0, frame_time - loop_duration)
            time.sleep(sleep_time)
            
            self.step_count = getattr(self, 'step_count', 0) + 1
    
    def start_simulation(self):
        """เริ่มการจำลอง"""
        if not self.thread_running:
            self.sim_manager.start()
            self.thread_running = True
            self.simulation_thread = threading.Thread(target=self.simulation_loop, daemon=True)
            self.simulation_thread.start()
            
            # Update UI
            self.start_btn.config(state="disabled")
            self.pause_btn.config(state="normal")
            self.stop_btn.config(state="normal")
            self.status_indicator.config(text="● Running", foreground="#28a745")
            self.update_gui()  # <-- Add this line
    
    def pause_simulation(self):
        """หยุดชั่วคราว"""
        self.sim_manager.pause()
        self.status_indicator.config(text="● Paused", foreground="#ffc107")
        self.pause_btn.config(state="disabled")
        self.resume_btn.config(state="normal")
    
    def resume_simulation(self):
        """เริ่มต่อ"""
        self.sim_manager.resume()
        self.status_indicator.config(text="● Running", foreground="#28a745")
        self.pause_btn.config(state="normal")
        self.resume_btn.config(state="disabled")
    
    def stop_simulation(self):
        """หยุดการจำลอง"""
        self.thread_running = False
        self.sim_manager.stop()
        
        # Update UI
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        self.resume_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")
        self.status_indicator.config(text="● Stopped", foreground="#dc3545")
    
    def on_speed_change(self, value):
        """เปลี่ยนความเร็ว"""
        speed = float(value)
        self.sim_manager.set_speed(speed)
        self.speed_label.config(text=f"{speed:.1f}x")
    
    def setup_factory_tab(self):
        """Setup Factory Layout Tab"""
        # Create paned window
        paned = ttk.PanedWindow(self.factory_tab, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # Canvas frame
        canvas_container = ttk.LabelFrame(paned, text="🏭 Factory Floor", padding=5)
        
        # Canvas with modern styling
        self.canvas = tk.Canvas(
            canvas_container,
            bg="#f8f9fa",
            highlightthickness=0,
            relief='flat',
            scrollregion=(0, 0, 1200, 800)
        )
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(canvas_container, orient="vertical", command=self.canvas.yview)
        h_scroll = ttk.Scrollbar(canvas_container, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Pack canvas elements
        self.canvas.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        
        paned.add(canvas_container, weight=3)
        
        # Canvas bindings
        self.setup_canvas_bindings()
        
        # Side panel for quick stats
        side_panel = ttk.LabelFrame(paned, text="📊 Quick Stats", padding=10)
        self.setup_quick_stats(side_panel)
        paned.add(side_panel, weight=1)
    
    def setup_canvas_bindings(self):
        """Setup canvas event bindings"""
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Double-Button-1>", self.on_canvas_double_click)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)
        self.canvas.bind("<MouseWheel>", self.on_canvas_scroll)
        
        # Canvas state
        self.canvas_objects = {}
        self.dragging_machine = None
        self.drag_start_pos = (0, 0)
        self.grid_size = 20
    
    def setup_quick_stats(self, parent):
        """Quick statistics panel"""
        # Machine count
        count_frame = ttk.Frame(parent)
        count_frame.pack(fill=X, pady=5)
        ttk.Label(count_frame, text="🔧 Machines:", font=("Segoe UI", 10)).pack(side=LEFT)
        self.machine_count_label = ttk.Label(count_frame, text="0", font=("Segoe UI", 10, "bold"))
        self.machine_count_label.pack(side=RIGHT)
        
        # Active jobs
        jobs_frame = ttk.Frame(parent)
        jobs_frame.pack(fill=X, pady=5)
        ttk.Label(jobs_frame, text="📋 Active Jobs:", font=("Segoe UI", 10)).pack(side=LEFT)
        self.jobs_count_label = ttk.Label(jobs_frame, text="0", font=("Segoe UI", 10, "bold"))
        self.jobs_count_label.pack(side=RIGHT)
        
        # Completed jobs
        completed_frame = ttk.Frame(parent)
        completed_frame.pack(fill=X, pady=5)
        ttk.Label(completed_frame, text="✅ Completed:", font=("Segoe UI", 10)).pack(side=LEFT)
        self.completed_label = ttk.Label(completed_frame, text="0", font=("Segoe UI", 10, "bold"))
        self.completed_label.pack(side=RIGHT)
        
        ttk.Separator(parent, orient=HORIZONTAL).pack(fill=X, pady=10)
        
        # Bottleneck indicator
        bottleneck_frame = ttk.LabelFrame(parent, text="🚨 Bottleneck Alert", padding=5)
        bottleneck_frame.pack(fill=X, pady=5)
        self.bottleneck_label = ttk.Label(bottleneck_frame, text="None detected", 
                                         font=("Segoe UI", 9), bootstyle="success")
        self.bottleneck_label.pack()
    
    def update_gui(self):
        """Optimized GUI update"""
        # Guard: Only update if dashboard widgets exist
        if not hasattr(self, "time_label"):
            return
        try:
            # Update dashboard
            self.time_label.config(text=f"{self.sim_manager.current_time:.1f} min")
            self.throughput_label.config(text=f"{self.factory.get_total_throughput(self.sim_manager.current_time):.2f} parts/min")
            self.utilization_label.config(text=f"{self.factory.get_average_utilization(self.sim_manager.current_time):.1f}%")
            self.wip_label.config(text=str(self.factory.get_total_wip()))
            
            # Update quick stats
            self.machine_count_label.config(text=str(len(self.factory.machines)))
            self.jobs_count_label.config(text=str(len(self.factory.jobs)))
            self.completed_label.config(text=str(len(self.factory.completed_jobs)))
            
            # Update canvas
            self.update_factory_canvas()
            
            # Update machine table (less frequently)
            if hasattr(self, 'last_table_update'):
                if time.time() - self.last_table_update > 1.0:  # Every 1 second
                    self.update_machine_table()
                    self.last_table_update = time.time()
            else:
                self.last_table_update = time.time()
            
            # Update charts (less frequently)
            if hasattr(self, 'last_chart_update'):
                if time.time() - self.last_chart_update > 2.0:  # Every 2 seconds
                    self.charts_panel.update_charts()
                    self.last_chart_update = time.time()
            else:
                self.last_chart_update = time.time()
            
            # Check for bottlenecks
            self.check_bottleneck()
            
        except Exception as e:
            print(f"GUI update error: {e}")
    
    def update_factory_canvas(self):
        """อัปเดต Factory Canvas - Optimized"""
        # Clear previous machine drawings
        self.canvas.delete("machine")
        self.canvas.delete("connection")
        
        # Draw grid
        self.draw_grid()
        
        # Draw machines with modern styling
        for machine in self.factory.machines.values():
            self.draw_modern_machine(machine)
        
        # Draw job flow connections
        self.draw_job_flows()
    
    def draw_grid(self):
        """วาดเส้น Grid แบบ subtle"""
        self.canvas.delete("grid")
        
        canvas_width = 1200
        canvas_height = 800
        
        for x in range(0, canvas_width, self.grid_size):
            self.canvas.create_line(x, 0, x, canvas_height, fill="#e9ecef", width=1, tags="grid")
        
        for y in range(0, canvas_height, self.grid_size):
            self.canvas.create_line(0, y, canvas_width, y, fill="#e9ecef", width=1, tags="grid")
    
    def draw_modern_machine(self, machine: Machine):
        """วาดเครื่องจักรแบบ Modern"""
        x1, y1, x2, y2 = machine.get_bounds()
        
        # Shadow effect
        self.canvas.create_rectangle(
            x1 + 3, y1 + 3, x2 + 3, y2 + 3,
            fill="#00000020", outline="", tags="machine"
        )
        
        # Main body
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=machine.status_color,
            outline="#495057", width=2,
            tags="machine"
        )
        
        # Type indicator stripe
        type_colors = {
            "CNC": "#007bff", "Lathe": "#28a745", "Drill": "#ffc107",
            "Assembly": "#dc3545", "Inspection": "#6f42c1", "Packaging": "#fd7e14"
        }
        
        color = type_colors.get(machine.machine_type, "#6c757d")
        self.canvas.create_rectangle(
            x1, y1, x1 + 8, y2,
            fill=color, outline="", tags="machine"
        )
        
        # Machine info with modern typography
        self.canvas.create_text(
            x1 + 60, y1 + 18,
            text=machine.name,
            font=("Segoe UI", 10, "bold"),
            fill="#212529", tags="machine"
        )
        
        # Status info
        queue_len = machine.get_queue_length()
        util = machine.get_utilization(self.sim_manager.current_time)
        
        self.canvas.create_text(
            x1 + 60, y1 + 35,
            text=f"Queue: {queue_len}",
            font=("Segoe UI", 9),
            fill="#495057", tags="machine"
        )
        
        self.canvas.create_text(
            x1 + 60, y1 + 50,
            text=f"Util: {util:.1f}%",
            font=("Segoe UI", 9),
            fill="#495057", tags="machine"
        )
        
        # Working indicator with animation
        if machine.is_working:
            pulse = 0.6 + 0.4 * math.sin(machine.animation_phase * 3)
            self.canvas.create_oval(
                x2 - 25, y1 + 8, x2 - 8, y1 + 25,
                fill=f"#ff{int(80 + 175 * pulse):02x}00",
                outline="#dc3545", width=2,
                tags="machine"
            )
            
            # Progress bar for current job
            if machine.current_job:
                progress = ((self.sim_manager.current_time - machine.work_start_time) / 
                           (machine.work_end_time - machine.work_start_time))
                progress = max(0, min(1, progress))
                
                bar_width = 80
                bar_x = x1 + 20
                bar_y = y2 - 12
                
                # Background
                self.canvas.create_rectangle(
                    bar_x, bar_y, bar_x + bar_width, bar_y + 6,
                    fill="#e9ecef", outline="#dee2e6", tags="machine"
                )
                
                # Progress
                if progress > 0:
                    self.canvas.create_rectangle(
                        bar_x, bar_y, bar_x + (bar_width * progress), bar_y + 6,
                        fill="#28a745", outline="", tags="machine"
                    )
        
        # Queue visualization
        if queue_len > 0:
            queue_indicator_width = min(queue_len * 4, 40)
            self.canvas.create_rectangle(
                x1 + 15, y1 + 65, x1 + 15 + queue_indicator_width, y1 + 70,
                fill="#ffc107", outline="#e0a800", tags="machine"
            )
            
            # Queue count badge
            if queue_len > 5:
                self.canvas.create_oval(
                    x1 + 90, y1 + 60, x1 + 105, y1 + 75,
                    fill="#dc3545", outline="white", width=2, tags="machine"
                )
                self.canvas.create_text(
                    x1 + 97, y1 + 67,
                    text=str(queue_len), fill="white",
                    font=("Segoe UI", 8, "bold"), tags="machine"
                )
    
    def draw_job_flows(self):
        """วาดเส้นแสดงการไฟล์งาน"""
        # Draw active job flows
        for job in self.factory.jobs:
            if job.current_step < len(job.required_machines) - 1:
                current_machine_name = job.required_machines[job.current_step]
                next_machine_name = job.required_machines[job.current_step + 1]
                
                if (current_machine_name in self.factory.machines and 
                    next_machine_name in self.factory.machines):
                    
                    m1 = self.factory.machines[current_machine_name]
                    m2 = self.factory.machines[next_machine_name]
                    
                    # Calculate connection points
                    x1 = m1.x + m1.width
                    y1 = m1.y + m1.height // 2
                    x2 = m2.x
                    y2 = m2.y + m2.height // 2
                    
                    # Priority-based line styling
                    if job.priority >= 3:
                        color, width = "#dc3545", 3
                    elif job.priority >= 2:
                        color, width = "#ffc107", 2
                    else:
                        color, width = "#28a745", 1
                    
                    # Draw curved connection
                    mid_x = (x1 + x2) / 2
                    self.canvas.create_line(
                        x1, y1, mid_x, y1, mid_x, y2, x2, y2,
                        fill=color, width=width, smooth=True,
                        arrow=tk.LAST, arrowshape=(8, 10, 3),
                        tags="connection"
                    )
    
    def on_canvas_click(self, event):
        """จัดการการคลิกบน Canvas"""
        machine = self.get_machine_at_position(event.x, event.y)
        
        if machine:
            self.selected_machine = machine
            self.dragging_machine = machine
            self.drag_start_pos = (event.x, event.y)
            self.highlight_selected_machine(machine)
    
    def on_canvas_drag(self, event):
        """จัดการการลาก"""
        if self.dragging_machine:
            # Snap to grid
            new_x = ((event.x // self.grid_size) * self.grid_size)
            new_y = ((event.y // self.grid_size) * self.grid_size)
            
            # Boundary checking
            new_x = max(0, min(1080, new_x))  # 1200 - 120 (machine width)
            new_y = max(0, min(720, new_y))   # 800 - 80 (machine height)
            
            self.dragging_machine.x = new_x
            self.dragging_machine.y = new_y
    
    def on_canvas_release(self, event):
        """ปล่อยการลาก"""
        self.dragging_machine = None
    
    def on_canvas_double_click(self, event):
        """Double click เพื่อกำหนดค่า"""
        machine = self.get_machine_at_position(event.x, event.y)
        if machine:
            self.configure_machine(machine)
    
    def on_canvas_right_click(self, event):
        """Right click context menu"""
        machine = self.get_machine_at_position(event.x, event.y)
        if machine:
            self.show_machine_context_menu(event, machine)
    
    def on_canvas_scroll(self, event):
        """Mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def get_machine_at_position(self, x: int, y: int) -> Optional[Machine]:
        """หาเครื่องจักรที่ตำแหน่งคลิก"""
        for machine in self.factory.machines.values():
            x1, y1, x2, y2 = machine.get_bounds()
            if x1 <= x <= x2 and y1 <= y <= y2:
                return machine
        return None
    
    def highlight_selected_machine(self, machine: Machine):
        """เน้นเครื่องจักรที่เลือก"""
        self.canvas.delete("selection")
        x1, y1, x2, y2 = machine.get_bounds()
        
        # Glow effect
        for i in range(3):
            self.canvas.create_rectangle(
                x1 - i - 1, y1 - i - 1, x2 + i + 1, y2 + i + 1,
                outline="#007bff", width=1, fill="",
                tags="selection"
            )
    
    def add_job_dialog(self):
        """Modern Add Job Dialog"""
        dialog = ttk.Toplevel(self.root)
        dialog.title("➕ Add New Job")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Modern styling
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Job details section
        details_frame = ttk.LabelFrame(main_frame, text="📋 Job Details", padding=15)
        details_frame.pack(fill=X, pady=(0, 15))
        
        # Batch size
        ttk.Label(details_frame, text="Batch Size:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky=W, pady=5)
        batch_size_var = tk.IntVar(value=20)
        batch_entry = ttk.Entry(details_frame, textvariable=batch_size_var, width=15)
        batch_entry.grid(row=0, column=1, sticky=W, padx=(10, 0), pady=5)
        
        # Priority
        ttk.Label(details_frame, text="Priority:", font=("Segoe UI", 10)).grid(row=1, column=0, sticky=W, pady=5)
        priority_var = tk.StringVar(value="Normal")
        priority_combo = ttk.Combobox(details_frame, textvariable=priority_var, width=12,
                                     values=["Normal", "High", "Critical"], state="readonly")
        priority_combo.grid(row=1, column=1, sticky=W, padx=(10, 0), pady=5)
        
        # Machine sequence section
        sequence_frame = ttk.LabelFrame(main_frame, text="🔧 Machine Sequence", padding=15)
        sequence_frame.pack(fill=BOTH, expand=True, pady=(0, 15))
        
        # Available machines
        ttk.Label(sequence_frame, text="Available Machines:", font=("Segoe UI", 10)).pack(anchor=W)
        
        available_frame = ttk.Frame(sequence_frame)
        available_frame.pack(fill=X, pady=5)
        
        self.available_listbox = tk.Listbox(available_frame, height=6, selectmode=tk.SINGLE)
        self.available_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Add all machines
        for machine_name in sorted(self.factory.machines.keys()):
            self.available_listbox.insert(tk.END, machine_name)
        
        # Control buttons
        control_frame = ttk.Frame(available_frame)
        control_frame.pack(side=RIGHT, padx=(10, 0))
        
        ttk.Button(control_frame, text="➡️ Add", command=lambda: self.move_machine_to_sequence()).pack(pady=2)
        ttk.Button(control_frame, text="⬆️ Up", command=lambda: self.move_sequence_up()).pack(pady=2)
        ttk.Button(control_frame, text="⬇️ Down", command=lambda: self.move_sequence_down()).pack(pady=2)
        ttk.Button(control_frame, text="❌ Remove", command=lambda: self.remove_from_sequence()).pack(pady=2)
        
        # Selected sequence
        ttk.Label(sequence_frame, text="Job Sequence:", font=("Segoe UI", 10)).pack(anchor=W, pady=(10, 0))
        self.sequence_listbox = tk.Listbox(sequence_frame, height=6)
        self.sequence_listbox.pack(fill=X, pady=5)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X)
        
        ttk.Button(button_frame, text="✅ Create Job", bootstyle="success", 
                  command=lambda: self.create_job_from_dialog(batch_size_var, priority_var, dialog)).pack(side=RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="❌ Cancel", bootstyle="secondary", 
                  command=dialog.destroy).pack(side=RIGHT)
    
    def move_machine_to_sequence(self):
        """ย้ายเครื่องจักรไปยัง sequence"""
        selection = self.available_listbox.curselection()
        if selection:
            machine_name = self.available_listbox.get(selection[0])
            self.sequence_listbox.insert(tk.END, machine_name)
    
    def move_sequence_up(self):
        """ย้าย sequence ขึ้น"""
        selection = self.sequence_listbox.curselection()
        if selection and selection[0] > 0:
            idx = selection[0]
            item = self.sequence_listbox.get(idx)
            self.sequence_listbox.delete(idx)
            self.sequence_listbox.insert(idx - 1, item)
            self.sequence_listbox.selection_set(idx - 1)
    
    def move_sequence_down(self):
        """ย้าย sequence ลง"""
        selection = self.sequence_listbox.curselection()
        if selection and selection[0] < self.sequence_listbox.size() - 1:
            idx = selection[0]
            item = self.sequence_listbox.get(idx)
            self.sequence_listbox.delete(idx)
            self.sequence_listbox.insert(idx + 1, item)
            self.sequence_listbox.selection_set(idx + 1)
    
    def remove_from_sequence(self):
        """ลบจาก sequence"""
        selection = self.sequence_listbox.curselection()
        if selection:
            self.sequence_listbox.delete(selection[0])
    
    def create_job_from_dialog(self, batch_size_var, priority_var, dialog):
        """สร้างงานจาก Dialog"""
        try:
            batch_size = batch_size_var.get()
            priority_text = priority_var.get()
            
            # Convert priority text to number
            priority_map = {"Normal": 1, "High": 2, "Critical": 3}
            priority = priority_map.get(priority_text, 1)
            
            # Get machine sequence
            sequence = []
            for i in range(self.sequence_listbox.size()):
                sequence.append(self.sequence_listbox.get(i))
            
            if batch_size <= 0:
                messagebox.showerror("Error", "Batch size must be positive")
                return
            
            if not sequence:
                messagebox.showerror("Error", "Please select at least one machine")
                return
            
            # Create and route job
            job = self.factory.create_job(batch_size, sequence, priority)
            success = self.factory.route_job(job)
            
            if success:
                dialog.destroy()
                messagebox.showinfo("Success", f"Job #{job.id} created successfully!")
            else:
                messagebox.showerror("Error", "Failed to route job")
                
        except Exception as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
    
    def add_machine_dialog(self):
        """Modern Add Machine Dialog"""
        dialog = ttk.Toplevel(self.root)
        dialog.title("🔧 Add New Machine")
        dialog.geometry("450x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Machine info
        info_frame = ttk.LabelFrame(main_frame, text="🏷️ Machine Information", padding=15)
        info_frame.pack(fill=X, pady=(0, 15))
        
        # Name
        ttk.Label(info_frame, text="Machine Name:").grid(row=0, column=0, sticky=W, pady=5)
        name_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=name_var, width=20).grid(row=0, column=1, sticky=W, padx=(10, 0), pady=5)
        
        # Type
        ttk.Label(info_frame, text="Machine Type:").grid(row=1, column=0, sticky=W, pady=5)
        type_var = tk.StringVar(value="CNC")
        type_combo = ttk.Combobox(info_frame, textvariable=type_var, width=17,
                                 values=["CNC", "Lathe", "Drill", "Assembly", "Inspection", "Packaging"])
        type_combo.grid(row=1, column=1, sticky=W, padx=(10, 0), pady=5)
        
        # Performance parameters
        perf_frame = ttk.LabelFrame(main_frame, text="⚙️ Performance Parameters", padding=15)
        perf_frame.pack(fill=X, pady=(0, 15))
        
        # Base time
        ttk.Label(perf_frame, text="Base Time (min/part):").grid(row=0, column=0, sticky=W, pady=5)
        base_time_var = tk.DoubleVar(value=2.0)
        ttk.Entry(perf_frame, textvariable=base_time_var, width=20).grid(row=0, column=1, sticky=W, padx=(10, 0), pady=5)
        
        # Setup time
        ttk.Label(perf_frame, text="Setup Time (min):").grid(row=1, column=0, sticky=W, pady=5)
        setup_time_var = tk.DoubleVar(value=10.0)
        ttk.Entry(perf_frame, textvariable=setup_time_var, width=20).grid(row=1, column=1, sticky=W, padx=(10, 0), pady=5)
        
        # Position
        pos_frame = ttk.LabelFrame(main_frame, text="📍 Position", padding=15)
        pos_frame.pack(fill=X, pady=(0, 15))
        
        ttk.Label(pos_frame, text="X Position:").grid(row=0, column=0, sticky=W, pady=5)
        x_var = tk.IntVar(value=200)
        ttk.Entry(pos_frame, textvariable=x_var, width=20).grid(row=0, column=1, sticky=W, padx=(10, 0), pady=5)
        
        ttk.Label(pos_frame, text="Y Position:").grid(row=1, column=0, sticky=W, pady=5)
        y_var = tk.IntVar(value=200)
        ttk.Entry(pos_frame, textvariable=y_var, width=20).grid(row=1, column=1, sticky=W, padx=(10, 0), pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(10, 0))
        
        ttk.Button(button_frame, text="✅ Add Machine", bootstyle="success",
                  command=lambda: self.create_machine_from_dialog(
                      name_var, type_var, base_time_var, setup_time_var, x_var, y_var, dialog
                  )).pack(side=RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="❌ Cancel", bootstyle="secondary",
                  command=dialog.destroy).pack(side=RIGHT)
    
    def create_machine_from_dialog(self, name_var, type_var, base_time_var, setup_time_var, x_var, y_var, dialog):
        """สร้างเครื่องจักรจาก Dialog"""
        try:
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Machine name is required")
                return
            
            if name in self.factory.machines:
                messagebox.showerror("Error", "Machine name already exists")
                return
            
            machine = Machine(
                name=name,
                machine_type=type_var.get(),
                base_time=base_time_var.get(),
                setup_time=setup_time_var.get(),
                x=x_var.get(),
                y=y_var.get()
            )
            
            self.factory.add_machine(machine)
            dialog.destroy()
            messagebox.showinfo("Success", f"Machine {name} added successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
    
    def configure_machine(self, machine: Machine):
        """กำหนดค่าเครื่องจักร"""
        dialog = ttk.Toplevel(self.root)
        dialog.title(f"⚙️ Configure {machine.name}")
        dialog.geometry("400x350")
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Parameters
        ttk.Label(main_frame, text="Base Time (min/part):").pack(anchor=W, pady=2)
        base_time_var = tk.DoubleVar(value=machine.base_time)
        ttk.Entry(main_frame, textvariable=base_time_var).pack(fill=X, pady=(0, 10))
        
        ttk.Label(main_frame, text="Setup Time (min):").pack(anchor=W, pady=2)
        setup_time_var = tk.DoubleVar(value=machine.setup_time)
        ttk.Entry(main_frame, textvariable=setup_time_var).pack(fill=X, pady=(0, 10))
        
        # Position
        pos_frame = ttk.Frame(main_frame)
        pos_frame.pack(fill=X, pady=10)
        
        ttk.Label(pos_frame, text="X:").pack(side=LEFT)
        x_var = tk.IntVar(value=machine.x)
        ttk.Entry(pos_frame, textvariable=x_var, width=10).pack(side=LEFT, padx=(5, 20))
        
        ttk.Label(pos_frame, text="Y:").pack(side=LEFT)
        y_var = tk.IntVar(value=machine.y)
        ttk.Entry(pos_frame, textvariable=y_var, width=10).pack(side=LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(20, 0))
        
        def apply_changes():
            try:
                machine.base_time = base_time_var.get()
                machine.setup_time = setup_time_var.get()
                machine.x = x_var.get()
                machine.y = y_var.get()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid input: {str(e)}")
        
        def delete_machine():
            if messagebox.askyesno("Confirm", f"Delete {machine.name}?"):
                self.factory.remove_machine(machine.name)
                dialog.destroy()
        
        ttk.Button(button_frame, text="✅ Apply", bootstyle="success", command=apply_changes).pack(side=RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="🗑️ Delete", bootstyle="danger", command=delete_machine).pack(side=RIGHT)
        ttk.Button(button_frame, text="❌ Cancel", bootstyle="secondary", command=dialog.destroy).pack(side=RIGHT, padx=(0, 5))
    
    def show_machine_context_menu(self, event, machine: Machine):
        """แสดง Context Menu"""
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="⚙️ Configure", command=lambda: self.configure_machine(machine))
        context_menu.add_command(label="🧹 Clear Queue", command=lambda: self.clear_machine_queue(machine))
        context_menu.add_command(label="📊 View Details", command=lambda: self.show_machine_details(machine))
        context_menu.add_separator()
        context_menu.add_command(label="🗑️ Delete", command=lambda: self.delete_machine(machine))
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def clear_machine_queue(self, machine: Machine):
        """ล้างคิวเครื่องจักร"""
        queue_size = machine.get_queue_length()
        machine.queue.clear()
        messagebox.showinfo("Queue Cleared", f"Cleared {queue_size} jobs from {machine.name}")
    
    def delete_machine(self, machine: Machine):
        """ลบเครื่องจักร"""
        if messagebox.askyesno("Confirm Delete", f"Delete {machine.name}?\nThis action cannot be undone."):
            self.factory.remove_machine(machine.name)
            if self.selected_machine == machine:
                self.selected_machine = None
    
    def show_machine_details(self, machine: Machine):
        """แสดงรายละเอียดเครื่องจักร"""
        dialog = ttk.Toplevel(self.root)
        dialog.title(f"📊 {machine.name} - Detailed Analysis")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Current metrics
        current_frame = ttk.LabelFrame(main_frame, text="📈 Current Metrics", padding=10)
        current_frame.pack(fill=X, pady=(0, 10))
        
        util = machine.get_utilization(self.sim_manager.current_time)
        throughput = machine.get_throughput(self.sim_manager.current_time)
        cycle_time = machine.calculate_cycle_time(20)  # Assume batch size 20
        
        metrics_text = f"""
Queue Length: {machine.get_queue_length()} jobs
Utilization: {util:.2f}%
Throughput: {throughput:.2f} parts/min
Cycle Time: {cycle_time:.2f} min (batch size 20)
Total Output: {machine.total_output} parts
Working Time: {machine.total_working_time:.1f} min
Status: {'🟢 Working' if machine.is_working else '🔴 Idle'}
        """
        
        ttk.Label(current_frame, text=metrics_text.strip(), justify=LEFT).pack(anchor=W)
        
        # Performance analysis
        analysis_frame = ttk.LabelFrame(main_frame, text="🎯 Performance Analysis", padding=10)
        analysis_frame.pack(fill=BOTH, expand=True)
        
        # Simple performance indicators
        if util > 90:
            status = "🔴 Overloaded - Consider load balancing"
        elif util > 70:
            status = "🟡 High utilization - Monitor closely"
        elif util > 30:
            status = "🟢 Good utilization"
        else:
            status = "🔵 Underutilized - Check job routing"
        
        ttk.Label(analysis_frame, text=f"Status: {status}", font=("Segoe UI", 10)).pack(anchor=W, pady=5)
        
        # Recommendations
        recommendations = []
        if machine.get_queue_length() > 10:
            recommendations.append("• Consider adding parallel machine")
        if util < 20:
            recommendations.append("• Check if machine is properly utilized")
        if cycle_time > 10:
            recommendations.append("• Review setup time optimization")
        
        if recommendations:
            ttk.Label(analysis_frame, text="💡 Recommendations:", font=("Segoe UI", 10, "bold")).pack(anchor=W, pady=(10, 5))
            rec_text = "\n".join(recommendations)
            ttk.Label(analysis_frame, text=rec_text, justify=LEFT).pack(anchor=W)
        
        ttk.Button(main_frame, text="Close", command=dialog.destroy).pack(pady=(20, 0))
    
    def update_machine_table(self):
        """อัปเดตตารางเครื่องจักร"""
        # Clear existing items
        for item in self.machine_tree.get_children():
            self.machine_tree.delete(item)
        
        # Apply filters
        search_text = self.search_var.get().lower()
        filter_type = self.filter_var.get()
        
        # Add filtered machines
        for machine in self.factory.machines.values():
            # Apply search filter
            if search_text and search_text not in machine.name.lower():
                continue
            
            # Apply type filter
            if filter_type != "All" and machine.machine_type != filter_type:
                continue
            
            # Calculate metrics
            util = machine.get_utilization(self.sim_manager.current_time)
            throughput = machine.get_throughput(self.sim_manager.current_time)
            cycle_time = machine.calculate_cycle_time(15)
            status = "🟢 Working" if machine.is_working else "⚪ Idle"
            
            # Color coding based on utilization
            if util > 90:
                tags = ("overload",)
            elif util > 70:
                tags = ("high",)
            elif util > 30:
                tags = ("normal",)
            else:
                tags = ("low",)
            
            self.machine_tree.insert("", tk.END, values=(
                machine.name,
                machine.machine_type,
                machine.get_queue_length(),
                f"{util:.1f}%",
                f"{throughput:.2f}",
                f"{cycle_time:.2f}",
                status
            ), tags=tags)
        
        # Configure row colors
        self.machine_tree.tag_configure("overload", background="#ffe6e6")
        self.machine_tree.tag_configure("high", background="#fff3cd")
        self.machine_tree.tag_configure("normal", background="#d4edda")
        self.machine_tree.tag_configure("low", background="#e2e3e5")
    
    def filter_machines(self, event=None):
        """กรองเครื่องจักรในตาราง"""
        self.update_machine_table()
    
    def sort_column(self, column):
        """เรียงลำดับคอลัมน์"""
        if self.sort_column_name == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column_name = column
            self.sort_reverse = False
        
        # Get all items
        items = []
        for item in self.machine_tree.get_children():
            values = self.machine_tree.item(item, 'values')
            items.append((values, item))
        
        # Sort items
        col_index = ["Name", "Type", "Queue", "Utilization", "Throughput", "Cycle Time", "Status"].index(column)
        
        def sort_key(item):
            value = item[0][col_index]
            # Convert numeric columns
            if column in ["Queue", "Utilization", "Throughput", "Cycle Time"]:
                try:
                    return float(value.replace('%', '').replace(' parts/min', '').replace(' min', ''))
                except:
                    return 0
            return value
        
        items.sort(key=sort_key, reverse=self.sort_reverse)
        
        # Rearrange items
        for index, (values, item) in enumerate(items):
            self.machine_tree.move(item, '', index)
    
    def on_machine_table_select(self, event):
        """เลือกเครื่องจักรจากตาราง"""
        selection = self.machine_tree.selection()
        if selection:
            item = self.machine_tree.item(selection[0])
            machine_name = item['values'][0]
            if machine_name in self.factory.machines:
                self.selected_machine = self.factory.machines[machine_name]
                self.highlight_selected_machine(self.selected_machine)
    
    def on_machine_table_double_click(self, event):
        """Double click บนตาราง"""
        if self.selected_machine:
            self.configure_machine(self.selected_machine)
    
    def find_bottleneck(self):
        """หา Bottleneck"""
        bottleneck = None
        max_queue = 0
        
        for machine in self.factory.machines.values():
            queue_len = machine.get_queue_length()
            if queue_len > max_queue:
                max_queue = queue_len
                bottleneck = machine
        
        if bottleneck and max_queue > 0:
            message = f"🚨 Bottleneck Detected!\n\n"
            message += f"Machine: {bottleneck.name}\n"
            message += f"Queue Length: {max_queue} jobs\n"
            message += f"Utilization: {bottleneck.get_utilization(self.sim_manager.current_time):.1f}%\n\n"
            message += "💡 Suggestions:\n"
            message += "• Add parallel machine\n"
            message += "• Reduce setup time\n"
            message += "• Increase batch sizes"
            
            messagebox.showwarning("Bottleneck Analysis", message)
            
            # Update bottleneck indicator
            self.bottleneck_label.config(text=f"{bottleneck.name} ({max_queue} jobs)", 
                                        bootstyle="danger")
        else:
            messagebox.showinfo("Bottleneck Analysis", "✅ No bottleneck detected")
            self.bottleneck_label.config(text="None detected", bootstyle="success")
    
    def show_suggestions(self):
        """แสดงคำแนะนำ"""
        dialog = ttk.Toplevel(self.root)
        dialog.title("💡 Optimization Suggestions")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Generate suggestions
        suggestions = self.generate_suggestions()
        
        # Display suggestions
        text_widget = tk.Text(main_frame, wrap=tk.WORD, font=("Segoe UI", 10), height=20)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Insert suggestions
        for i, suggestion in enumerate(suggestions, 1):
            text_widget.insert(tk.END, f"{i}. {suggestion}\n\n")
        
        text_widget.config(state=tk.DISABLED)
        
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
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
                suggestions.append(f"🔴 {machine.name}: Critically overloaded ({util:.1f}%) - Add parallel machine urgently")
            elif util > 85:
                suggestions.append(f"🟡 {machine.name}: High utilization ({util:.1f}%) - Consider load balancing")
            elif util < 15:
                suggestions.append(f"🔵 {machine.name}: Low utilization ({util:.1f}%) - Check job routing or remove if unnecessary")
            
            if queue_len > 15:
                suggestions.append(f"📋 {machine.name}: Large queue ({queue_len} jobs) - Potential bottleneck")
        
        # System-wide suggestions
        total_wip = self.factory.get_total_wip()
        avg_util = self.factory.get_average_utilization(self.sim_manager.current_time)
        
        if total_wip > len(self.factory.machines) * 5:
            suggestions.append(f"📦 High WIP level ({total_wip}) - Consider reducing batch sizes or improving flow")
        
        if avg_util < 30:
            suggestions.append(f"⚡ Low average utilization ({avg_util:.1f}%) - Increase job arrival rate")
        elif avg_util > 85:
            suggestions.append(f"🔥 High average utilization ({avg_util:.1f}%) - System near capacity")
        
        if not suggestions:
            suggestions.append("✅ System appears well-balanced - Continue monitoring")
        
        return suggestions
    
    def show_oee_dialog(self):
        """แสดง OEE Analysis"""
        dialog = ttk.Toplevel(self.root)
        dialog.title("🏆 OEE (Overall Equipment Effectiveness)")
        dialog.geometry("700x500")
        dialog.transient(self.root)
        
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # OEE Table
        columns = ("Machine", "Availability", "Performance", "Quality", "OEE", "Rating")
        oee_tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=12)
        
        for col in columns:
            oee_tree.heading(col, text=col)
            oee_tree.column(col, width=100)
        
        # Calculate OEE for each machine
        for machine in self.factory.machines.values():
            # Simplified OEE calculation
            availability = machine.get_utilization(self.sim_manager.current_time) / 100
            
            # Performance = Ideal time / Actual time
            ideal_time = machine.base_time
            actual_time = machine.calculate_cycle_time(15)
            performance = ideal_time / actual_time if actual_time > 0 else 0
            
            # Quality (assumed 95% for simulation)
            quality = 0.95
            
            oee = availability * performance * quality * 100
            
            # Rating
            if oee >= 85:
                rating = "🏆 Excellent"
                tags = ("excellent",)
            elif oee >= 65:
                rating = "👍 Good"
                tags = ("good",)
            elif oee >= 40:
                rating = "⚠️ Fair"
                tags = ("fair",)
            else:
                rating = "❌ Poor"
                tags = ("poor",)
            
            oee_tree.insert("", tk.END, values=(
                machine.name,
                f"{availability * 100:.1f}%",
                f"{performance * 100:.1f}%",
                f"{quality * 100:.1f}%",
                f"{oee:.1f}%",
                rating
            ), tags=tags)
        
        # Configure colors
        oee_tree.tag_configure("excellent", background="#d4edda")
        oee_tree.tag_configure("good", background="#cce5ff")
        oee_tree.tag_configure("fair", background="#fff3cd")
        oee_tree.tag_configure("poor", background="#ffe6e6")
        
        oee_tree.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        ttk.Button(main_frame, text="Close", command=dialog.destroy).pack()
    
    def check_bottleneck(self):
        """ตรวจสอบ Bottleneck อัตโนมัติ"""
        bottleneck = None
        max_queue = 0
        
        for machine in self.factory.machines.values():
            queue_len = machine.get_queue_length()
            if queue_len > max_queue:
                max_queue = queue_len
                bottleneck = machine
        
        if bottleneck and max_queue > 8:  # Threshold for bottleneck warning
            self.bottleneck_label.config(text=f"⚠️ {bottleneck.name} ({max_queue})", bootstyle="warning")
        elif bottleneck and max_queue > 15:
            self.bottleneck_label.config(text=f"🚨 {bottleneck.name} ({max_queue})", bootstyle="danger")
        else:
            self.bottleneck_label.config(text="✅ None detected", bootstyle="success")
    
    def create_sample_jobs(self):
        """สร้างงานตัวอย่าง"""
        sample_jobs = [
            (15, ["CNC-01", "Lathe-01", "Assembly-01"], 1),
            (25, ["CNC-02", "Drill-01", "Inspection-01"], 1),
            (10, ["CNC-01", "Drill-01", "Assembly-01"], 2),
            (30, ["Lathe-01", "Assembly-01", "Inspection-01"], 1),
            (5, ["CNC-02", "Lathe-01", "Drill-01", "Assembly-01"], 3),
        ]
        
        for batch_size, sequence, priority in sample_jobs:
            job = self.factory.create_job(batch_size, sequence, priority)
            self.factory.route_job(job)
    
    def export_data(self):
        """Export ข้อมูลแบบ Modern"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Export machine data
            machine_file = f"factory_machines_{timestamp}.csv"
            with open(machine_file, "w", newline="", encoding="utf-8") as f:
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
            
            # Export time series data
            if self.sim_manager.time_history:
                timeseries_file = f"factory_timeseries_{timestamp}.csv"
                with open(timeseries_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Time_min", "Total_Throughput", "Avg_Utilization_%", "Total_WIP"])
                    
                    for i in range(len(self.sim_manager.time_history)):
                        writer.writerow([
                            f"{self.sim_manager.time_history[i]:.2f}",
                            f"{self.sim_manager.throughput_history[i]:.2f}",
                            f"{self.sim_manager.utilization_history[i]:.2f}",
                            self.sim_manager.wip_history[i]
                        ])
            
            # Export layout configuration
            layout_file = f"factory_layout_{timestamp}.json"
            layout_data = {
                "machines": [],
                "simulation_params": {
                    "current_time": self.sim_manager.current_time,
                    "speed_factor": self.sim_manager.speed_factor
                }
            }
            
            for machine in self.factory.machines.values():
                layout_data["machines"].append({
                    "name": machine.name,
                    "type": machine.machine_type,
                    "base_time": machine.base_time,
                    "setup_time": machine.setup_time,
                    "x": machine.x,
                    "y": machine.y
                })
            
            with open(layout_file, "w", encoding="utf-8") as f:
                json.dump(layout_data, f, indent=2)
            
            messagebox.showinfo("✅ Export Success", 
                              f"Data exported successfully!\n\n"
                              f"📊 Machine Data: {machine_file}\n"
                              f"📈 Time Series: {timeseries_file}\n"
                              f"🏭 Layout: {layout_file}")
            
        except Exception as e:
            messagebox.showerror("❌ Export Error", f"Failed to export data:\n{str(e)}")
    
    def load_layout(self):
        """โหลด Layout จากไฟล์"""
        filename = filedialog.askopenfilename(
            title="Load Factory Layout",
            filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    self.load_json_layout(filename)
                elif filename.endswith('.csv'):
                    self.load_csv_layout(filename)
                
                messagebox.showinfo("✅ Load Success", "Layout loaded successfully!")
                
            except Exception as e:
                messagebox.showerror("❌ Load Error", f"Failed to load layout:\n{str(e)}")
    
    def load_json_layout(self, filename):
        """โหลด JSON Layout"""
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Clear existing machines
        self.factory.machines.clear()
        
        # Load machines
        for machine_data in data.get("machines", []):
            machine = Machine(
                name=machine_data["name"],
                machine_type=machine_data["type"],
                base_time=machine_data["base_time"],
                setup_time=machine_data["setup_time"],
                x=machine_data["x"],
                y=machine_data["y"]
            )
            self.factory.add_machine(machine)
    
    def load_csv_layout(self, filename):
        """โหลด CSV Layout"""
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
                    x=int(row["Position_X"]),
                    y=int(row["Position_Y"])
                )
                self.factory.add_machine(machine)
    
    def setup_menu_bar(self):
        """สร้าง Menu Bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="📁 File", menu=file_menu)
        file_menu.add_command(label="💾 Export Data", command=self.export_data)
        file_menu.add_command(label="📂 Load Layout", command=self.load_layout)
        file_menu.add_separator()
        file_menu.add_command(label="🚪 Exit", command=self.on_closing)
        
        # Simulation Menu
        sim_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="🎮 Simulation", menu=sim_menu)
        sim_menu.add_command(label="▶️ Start", command=self.start_simulation)
        sim_menu.add_command(label="⏸️ Pause", command=self.pause_simulation)
        sim_menu.add_command(label="⏹️ Stop", command=self.stop_simulation)
        sim_menu.add_separator()
        sim_menu.add_command(label="🔄 Reset", command=self.reset_simulation)
        
        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="🔧 Tools", menu=tools_menu)
        tools_menu.add_command(label="🔍 Find Bottleneck", command=self.find_bottleneck)
        tools_menu.add_command(label="💡 Suggestions", command=self.show_suggestions)
        tools_menu.add_command(label="🏆 OEE Analysis", command=self.show_oee_dialog)
        
        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="❓ Help", menu=help_menu)
        help_menu.add_command(label="📖 User Guide", command=self.show_help)
        help_menu.add_command(label="ℹ️ About", command=self.show_about)
    
    def reset_simulation(self):
        """รีเซ็ตการจำลอง"""
        if messagebox.askyesno("Reset Simulation", "Reset all simulation data?\nThis will clear all statistics and jobs."):
            self.stop_simulation()
            
            # Reset all machines
            for machine in self.factory.machines.values():
                machine.queue.clear()
                machine.current_job = None
                machine.is_working = False
                machine.total_working_time = 0
                machine.total_output = 0
            
            # Reset factory
            self.factory.jobs.clear()
            self.factory.completed_jobs.clear()
            self.factory.job_counter = 0
            
            # Reset simulation manager
            self.sim_manager.current_time = 0
            self.sim_manager.time_history.clear()
            self.sim_manager.throughput_history.clear()
            self.sim_manager.utilization_history.clear()
            self.sim_manager.wip_history.clear()
            
            # Create new sample jobs
            self.create_sample_jobs()
    
    def show_help(self):
        """แสดงคู่มือการใช้งาน"""
        dialog = ttk.Toplevel(self.root)
        dialog.title("📖 User Guide")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        help_text = """
🏭 Factory RTS Simulation - User Guide

🎮 SIMULATION CONTROLS:
• Start/Pause/Resume/Stop simulation
• Adjust speed (0.1x to 5.0x)
• Real-time performance monitoring

🔧 MACHINE MANAGEMENT:
• Drag machines to reposition
• Double-click to configure
• Right-click for context menu
• Add/remove machines dynamically

📋 JOB MANAGEMENT:
• Create jobs with custom batch sizes
• Set priority levels (Normal/High/Critical)
• Define multi-step production sequences
• Monitor job progress in real-time

📊 ANALYTICS:
• Real-time throughput monitoring
• Utilization tracking per machine
• WIP (Work In Process) analysis
• Bottleneck detection
• OEE (Overall Equipment Effectiveness)

🔍 KEY METRICS:
• Cycle Time = Base Time + (Setup Time / Batch Size)
• Utilization = (Working Time / Total Time) × 100%
• Throughput = Total Output / Simulation Time
• WIP = Sum of all queues + active jobs

💡 OPTIMIZATION TIPS:
• Balance machine utilization (60-80% ideal)
• Minimize WIP levels
• Identify and resolve bottlenecks
• Optimize batch sizes for setup time
• Monitor OEE for equipment effectiveness
        """
        
        text_widget = tk.Text(main_frame, wrap=tk.WORD, font=("Segoe UI", 10))
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        text_widget.insert(tk.END, help_text.strip())
        text_widget.config(state=tk.DISABLED)
        
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def show_about(self):
        """แสดงข้อมูลเกี่ยวกับโปรแกรม"""
        messagebox.showinfo("ℹ️ About Factory RTS Simulation",
                           "🏭 Factory RTS Simulation v2.0\n\n"
                           "A modern real-time factory simulation\n"
                           "with advanced analytics and optimization.\n\n"
                           "Features:\n"
                           "• Real-time discrete event simulation\n"
                           "• Modern UI with ttkbootstrap\n"
                           "• Advanced performance metrics\n"
                           "• Interactive factory layout\n"
                           "• Bottleneck detection\n"
                           "• OEE analysis\n\n"
                           "Built with Python, tkinter, and matplotlib")
    
    def run(self):
        """เริ่มรันโปรแกรม"""
        # Setup menu bar
        self.setup_menu_bar()
        
        # Initial GUI update
        self.update_gui()
        
        # Create sample jobs after GUI is ready
        self.create_sample_jobs()
        
        # Start update timer
        self.schedule_updates()
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start the main loop
        self.root.mainloop()
    
    def schedule_updates(self):
        """จัดการการอัปเดต GUI"""
        if self.thread_running or self.sim_manager.is_running:
            self.update_gui()
        
        # Schedule next update
        self.root.after(200, self.schedule_updates)  # Update every 200ms
    
    def on_closing(self):
        """จัดการการปิดโปรแกรม"""
        if messagebox.askyesno("Exit", "Exit Factory Simulation?"):
            self.stop_simulation()
            self.root.quit()
            self.root.destroy()

def main():
    """ฟังก์ชันหลัก"""
    try:
        print("🏭 Starting Factory RTS Simulation...")
        print("📦 Required packages: ttkbootstrap, matplotlib, numpy")
        print("💡 Install with: pip install ttkbootstrap matplotlib numpy")
        
        app = ModernFactorySimulationGUI()
        app.run()
        
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("📦 Please install: pip install ttkbootstrap matplotlib numpy")
    except Exception as e:
        print(f"❌ Error starting simulation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()