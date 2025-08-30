"""
Reusable GUI components for the factory simulation
Contains modern styled widgets and panels
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import math
import time
from typing import Optional, Callable, List, Dict, Any
from models import Machine, Factory, Job
from simulation_engine import SimulationManager


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
        
        # Callbacks
        self.config_callback: Optional[Callable] = None
        
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
            "Assembly": "#dc3545", "Inspection": "#6f42c1", "Packaging": "#fd7e14",
            "Input": "#17a2b8", "Output": "#6c757d"
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
        if machine and self.config_callback:
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
        
    def pack(self, **kwargs):
        self.canvas.get_tk_widget().pack(**kwargs)
    
    def update_charts(self, force_update=False):
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


class LiveDashboard:
    """Live performance dashboard with modern metrics cards"""
    
    def __init__(self, parent, factory: Factory, sim_manager: SimulationManager):
        self.factory = factory
        self.sim_manager = sim_manager
        
        # Main container
        self.frame = ttk.Frame(parent, padding=10)
        
        # Create metric cards
        self.create_metric_cards()
        
        # Quick actions section
        self.create_quick_actions()
        
        # Bottleneck alert
        self.create_bottleneck_alert()
        
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
    
    def create_metric_cards(self):
        """Create modern metric cards"""
        metrics_frame = ttk.Frame(self.frame)
        metrics_frame.pack(fill=X, pady=(0, 10))
        
        # Time card
        time_card = ttk.LabelFrame(metrics_frame, text="Simulation Time", padding=10)
        time_card.pack(fill=X, pady=2)
        self.time_label = ttk.Label(time_card, text="0.0 min", font=("Segoe UI", 14, "bold"), 
                                   bootstyle="primary")
        self.time_label.pack()
        
        # Throughput card
        throughput_card = ttk.LabelFrame(metrics_frame, text="Total Throughput", padding=10)
        throughput_card.pack(fill=X, pady=2)
        self.throughput_label = ttk.Label(throughput_card, text="0.0 parts/min", 
                                         font=("Segoe UI", 12, "bold"), bootstyle="success")
        self.throughput_label.pack()
        
        # Utilization card
        util_card = ttk.LabelFrame(metrics_frame, text="Avg Utilization", padding=10)
        util_card.pack(fill=X, pady=2)
        self.utilization_label = ttk.Label(util_card, text="0.0%", 
                                          font=("Segoe UI", 12, "bold"), bootstyle="info")
        self.utilization_label.pack()
        
        # WIP card
        wip_card = ttk.LabelFrame(metrics_frame, text="Total WIP", padding=10)
        wip_card.pack(fill=X, pady=2)
        self.wip_label = ttk.Label(wip_card, text="0", font=("Segoe UI", 12, "bold"), 
                                  bootstyle="warning")
        self.wip_label.pack()
    
    def create_quick_actions(self):
        """Create quick action buttons"""
        actions_frame = ttk.LabelFrame(self.frame, text="Quick Actions", padding=10)
        actions_frame.pack(fill=X, pady=(10, 0))
        
        self.bottleneck_callback: Optional[Callable] = None
        self.suggestions_callback: Optional[Callable] = None
        self.oee_callback: Optional[Callable] = None
        
        ttk.Button(actions_frame, text="Find Bottleneck", bootstyle="outline-danger",
                  command=self._on_bottleneck_click).pack(fill=X, pady=2)
        ttk.Button(actions_frame, text="Suggestions", bootstyle="outline-warning",
                  command=self._on_suggestions_click).pack(fill=X, pady=2)
        ttk.Button(actions_frame, text="OEE Analysis", bootstyle="outline-info",
                  command=self._on_oee_click).pack(fill=X, pady=2)
    
    def create_bottleneck_alert(self):
        """Create bottleneck alert section"""
        alert_frame = ttk.LabelFrame(self.frame, text="Bottleneck Alert", padding=5)
        alert_frame.pack(fill=X, pady=(10, 0))
        self.bottleneck_label = ttk.Label(alert_frame, text="None detected", 
                                         font=("Segoe UI", 9), bootstyle="success")
        self.bottleneck_label.pack()
    
    def update_metrics(self):
        """Update all dashboard metrics"""
        # Update time
        self.time_label.config(text=f"{self.sim_manager.current_time:.1f} min")
        
        # Update throughput
        throughput = self.factory.get_total_throughput(self.sim_manager.current_time)
        self.throughput_label.config(text=f"{throughput:.2f} parts/min")
        
        # Update utilization
        utilization = self.factory.get_average_utilization(self.sim_manager.current_time)
        self.utilization_label.config(text=f"{utilization:.1f}%")
        
        # Update WIP
        wip = self.factory.get_total_wip()
        self.wip_label.config(text=str(wip))
        
        # Check bottleneck
        self.check_bottleneck()
    
    def check_bottleneck(self):
        """Check and update bottleneck indicator"""
        bottleneck = self.factory.get_bottleneck_machine()
        
        if bottleneck:
            queue_len = bottleneck.get_queue_length()
            if queue_len > 15:
                self.bottleneck_label.config(text=f"CRITICAL: {bottleneck.name} ({queue_len})", 
                                           bootstyle="danger")
            elif queue_len > 8:
                self.bottleneck_label.config(text=f"WARNING: {bottleneck.name} ({queue_len})", 
                                           bootstyle="warning")
            else:
                self.bottleneck_label.config(text="None detected", bootstyle="success")
        else:
            self.bottleneck_label.config(text="None detected", bootstyle="success")
    
    def _on_bottleneck_click(self):
        if self.bottleneck_callback:
            self.bottleneck_callback()
    
    def _on_suggestions_click(self):
        if self.suggestions_callback:
            self.suggestions_callback()
    
    def _on_oee_click(self):
        if self.oee_callback:
            self.oee_callback()


class MachineTable:
    """Modern machine data table with sorting and filtering"""
    
    def __init__(self, parent, factory: Factory, sim_manager: SimulationManager):
        self.factory = factory
        self.sim_manager = sim_manager
        
        # Main container
        self.frame = ttk.Frame(parent)
        
        # Search and filter controls
        self.create_filter_controls()
        
        # Create table
        self.create_table()
        
        # Table state
        self.sort_column_name = None
        self.sort_reverse = False
        
        # Callbacks
        self.on_machine_select_callback: Optional[Callable] = None
        self.on_machine_configure_callback: Optional[Callable] = None
    
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
    
    def create_filter_controls(self):
        """Create search and filter controls"""
        filter_frame = ttk.Frame(self.frame)
        filter_frame.pack(fill=X, padx=10, pady=10)
        
        # Search
        ttk.Label(filter_frame, text="Search:").pack(side=LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=LEFT, padx=(0, 10))
        search_entry.bind('<KeyRelease>', self.filter_machines)
        
        # Filter by type
        ttk.Label(filter_frame, text="Filter Type:").pack(side=LEFT, padx=(10, 5))
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var, width=15,
                                   values=["All", "CNC", "Lathe", "Drill", "Assembly", "Inspection", "Packaging"])
        filter_combo.pack(side=LEFT)
        filter_combo.bind('<<ComboboxSelected>>', self.filter_machines)
    
    def create_table(self):
        """Create the machine data table"""
        table_frame = ttk.Frame(self.frame)
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
        
        # Bind events
        self.machine_tree.bind("<<TreeviewSelect>>", self.on_machine_select)
        self.machine_tree.bind("<Double-1>", self.on_machine_double_click)
    
    def update_table(self):
        """Update machine table data"""
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
            status = "Working" if machine.is_working else "Idle"
            
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
        """Filter machines in table"""
        self.update_table()
    
    def sort_column(self, column):
        """Sort table by column"""
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
    
    def on_machine_select(self, event):
        """Handle machine selection"""
        selection = self.machine_tree.selection()
        if selection and self.on_machine_select_callback:
            item = self.machine_tree.item(selection[0])
            machine_name = item['values'][0]
            if machine_name in self.factory.machines:
                machine = self.factory.machines[machine_name]
                self.on_machine_select_callback(machine)
    
    def on_machine_double_click(self, event):
        """Handle double click on machine"""
        if self.on_machine_configure_callback:
            selection = self.machine_tree.selection()
            if selection:
                item = self.machine_tree.item(selection[0])
                machine_name = item['values'][0]
                if machine_name in self.factory.machines:
                    machine = self.factory.machines[machine_name]
                    self.on_machine_configure_callback(machine)


class ControlPanel:
    """Modern control panel for simulation controls"""
    
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        
        # Create control sections
        self.create_simulation_controls()
        self.create_speed_control()
        self.create_factory_controls()
        
        # Callbacks
        self.start_callback: Optional[Callable] = None
        self.pause_callback: Optional[Callable] = None
        self.resume_callback: Optional[Callable] = None
        self.stop_callback: Optional[Callable] = None
        self.speed_callback: Optional[Callable] = None
        self.add_job_callback: Optional[Callable] = None
        self.add_machine_callback: Optional[Callable] = None
        self.export_callback: Optional[Callable] = None
    
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
    
    def create_simulation_controls(self):
        """Create simulation control buttons"""
        sim_controls = ttk.LabelFrame(self.frame, text="Simulation Controls", padding=10)
        sim_controls.pack(side=LEFT, padx=(0, 10))
        
        self.start_btn = ttk.Button(sim_controls, text="Start", bootstyle="success", 
                                   command=self._on_start)
        self.start_btn.pack(side=LEFT, padx=2)
        
        self.pause_btn = ttk.Button(sim_controls, text="Pause", bootstyle="warning", 
                                   command=self._on_pause)
        self.pause_btn.pack(side=LEFT, padx=2)
        
        self.resume_btn = ttk.Button(sim_controls, text="Resume", bootstyle="info", 
                                    command=self._on_resume)
        self.resume_btn.pack(side=LEFT, padx=2)
        
        self.stop_btn = ttk.Button(sim_controls, text="Stop", bootstyle="danger", 
                                  command=self._on_stop)
        self.stop_btn.pack(side=LEFT, padx=2)
    
    def create_speed_control(self):
        """Create speed control"""
        speed_frame = ttk.LabelFrame(self.frame, text="Speed Control", padding=10)
        speed_frame.pack(side=LEFT, padx=(0, 10))
        
        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_scale = ttk.Scale(
            speed_frame, from_=0.1, to=5.0, orient=HORIZONTAL,
            variable=self.speed_var, command=self._on_speed_change,
            bootstyle="info", length=150
        )
        self.speed_scale.pack(side=LEFT, padx=5)
        
        self.speed_label = ttk.Label(speed_frame, text="1.0x", font=("Segoe UI", 10, "bold"))
        self.speed_label.pack(side=LEFT, padx=5)
    
    def create_factory_controls(self):
        """Create factory management controls"""
        factory_controls = ttk.LabelFrame(self.frame, text="Factory Management", padding=10)
        factory_controls.pack(side=LEFT)
        
        ttk.Button(factory_controls, text="Add Job", bootstyle="primary-outline", 
                  command=self._on_add_job).pack(side=LEFT, padx=2)
        ttk.Button(factory_controls, text="Add Machine", bootstyle="secondary-outline", 
                  command=self._on_add_machine).pack(side=LEFT, padx=2)
        ttk.Button(factory_controls, text="Export", bootstyle="success-outline", 
                  command=self._on_export).pack(side=LEFT, padx=2)
    
    def set_simulation_state(self, is_running: bool, is_paused: bool):
        """Update button states based on simulation state"""
        if is_running and not is_paused:
            self.start_btn.config(state="disabled")
            self.pause_btn.config(state="normal")
            self.resume_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
        elif is_running and is_paused:
            self.start_btn.config(state="disabled")
            self.pause_btn.config(state="disabled")
            self.resume_btn.config(state="normal")
            self.stop_btn.config(state="normal")
        else:
            self.start_btn.config(state="normal")
            self.pause_btn.config(state="disabled")
            self.resume_btn.config(state="disabled")
            self.stop_btn.config(state="disabled")
    
    def _on_start(self):
        if self.start_callback:
            self.start_callback()
    
    def _on_pause(self):
        if self.pause_callback:
            self.pause_callback()
    
    def _on_resume(self):
        if self.resume_callback:
            self.resume_callback()
    
    def _on_stop(self):
        if self.stop_callback:
            self.stop_callback()
    
    def _on_speed_change(self, value):
        speed = float(value)
        self.speed_label.config(text=f"{speed:.1f}x")
        if self.speed_callback:
            self.speed_callback(speed)
    
    def _on_add_job(self):
        if self.add_job_callback:
            self.add_job_callback()
    
    def _on_add_machine(self):
        if self.add_machine_callback:
            self.add_machine_callback()
    
    def _on_export(self):
        if self.export_callback:
            self.export_callback()


class StatusBar:
    """Modern status bar with performance indicators"""
    
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        
        # Status indicators
        ttk.Label(self.frame, text="Status:", font=("Segoe UI", 9)).pack(side=LEFT)
        
        self.status_indicator = ttk.Label(self.frame, text="Stopped", 
                                         foreground="#dc3545", font=("Segoe UI", 9, "bold"))
        self.status_indicator.pack(side=LEFT, padx=(5, 20))
        
        ttk.Label(self.frame, text="Performance:", font=("Segoe UI", 9)).pack(side=LEFT)
        self.perf_label = ttk.Label(self.frame, text="-- FPS", font=("Segoe UI", 9))
        self.perf_label.pack(side=LEFT, padx=5)
        
        # Progress indicator
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.frame, mode='indeterminate', 
                                           bootstyle="info-striped", length=100)
        self.progress_bar.pack(side=RIGHT, padx=(20, 0))
    
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
    
    def set_status(self, status: str, color: str = "#000000"):
        """Set status text and color"""
        self.status_indicator.config(text=status, foreground=color)
    
    def set_fps(self, fps: float):
        """Update FPS display"""
        self.perf_label.config(text=f"{fps:.1f} FPS")
    
    def start_progress(self):
        """Start progress animation"""
        self.progress_bar.start(10)
    
    def stop_progress(self):
        """Stop progress animation"""
        self.progress_bar.stop()


class QuickStatsPanel:
    """Quick statistics panel for sidebar"""
    
    def __init__(self, parent, factory: Factory, sim_manager: SimulationManager):
        self.factory = factory
        self.sim_manager = sim_manager
        
        # Main container
        self.frame = ttk.LabelFrame(parent, text="Quick Stats", padding=10)
        
        # Create stat displays
        self.create_stat_displays()
    
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
    
    def create_stat_displays(self):
        """Create quick stat displays"""
        # Machine count
        count_frame = ttk.Frame(self.frame)
        count_frame.pack(fill=X, pady=5)
        ttk.Label(count_frame, text="Machines:", font=("Segoe UI", 10)).pack(side=LEFT)
        self.machine_count_label = ttk.Label(count_frame, text="0", font=("Segoe UI", 10, "bold"))
        self.machine_count_label.pack(side=RIGHT)
        
        # Active jobs
        jobs_frame = ttk.Frame(self.frame)
        jobs_frame.pack(fill=X, pady=5)
        ttk.Label(jobs_frame, text="Active Jobs:", font=("Segoe UI", 10)).pack(side=LEFT)
        self.jobs_count_label = ttk.Label(jobs_frame, text="0", font=("Segoe UI", 10, "bold"))
        self.jobs_count_label.pack(side=RIGHT)
        
        # Completed jobs
        completed_frame = ttk.Frame(self.frame)
        completed_frame.pack(fill=X, pady=5)
        ttk.Label(completed_frame, text="Completed:", font=("Segoe UI", 10)).pack(side=LEFT)
        self.completed_label = ttk.Label(completed_frame, text="0", font=("Segoe UI", 10, "bold"))
        self.completed_label.pack(side=RIGHT)
    
    def update_stats(self):
        """Update quick statistics"""
        self.machine_count_label.config(text=str(len(self.factory.machines)))
        self.jobs_count_label.config(text=str(len(self.factory.jobs)))
        self.completed_label.config(text=str(len(self.factory.completed_jobs)))