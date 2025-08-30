"""
GUI components for factory visualization and control
"""
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from typing import Optional, Callable
from models.factory import Factory
from models.machine import Machine
from simulation.simulation_manager import SimulationManager


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
            relief='flat',
            scrollregion=(0, 0, 1200, 800)
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
        
        # Grid settings
        self.grid_size = 20
        self.show_grid = False
        
        # Callbacks
        self.config_callback: Optional[Callable] = None
        
        # Bind events
        self.setup_bindings()
        
    def setup_bindings(self):
        """Setup canvas event bindings"""
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<MouseWheel>", self.on_scroll)
        self.canvas.bind("<Button-3>", self.on_right_click)
    
    def pack(self, **kwargs):
        """Pack the canvas frame"""
        self.canvas_frame.pack(**kwargs)
    
    def draw_grid(self):
        """วาดเส้น Grid"""
        if not self.show_grid:
            return
        
        self.canvas.delete("grid")
        canvas_width = 1200
        canvas_height = 800
        
        # Vertical lines
        for x in range(0, canvas_width, self.grid_size):
            self.canvas.create_line(
                x, 0, x, canvas_height,
                fill="#e9ecef", width=1, tags="grid"
            )
        
        # Horizontal lines
        for y in range(0, canvas_height, self.grid_size):
            self.canvas.create_line(
                0, y, canvas_width, y,
                fill="#e9ecef", width=1, tags="grid"
            )
    
    def draw_machine(self, machine: Machine):
        """วาดเครื่องจักร - Modern style"""
        x1, y1, x2, y2 = machine.get_bounds()
        
        # Shadow effect
        self.canvas.create_rectangle(
            x1 + 3, y1 + 3, x2 + 3, y2 + 3,
            fill="#cccccc", outline="", tags="machine"
        )
        
        # Main body with gradient effect
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=machine.status_color,
            outline="#495057",
            width=2,
            tags="machine"
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
            tags="machine"
        )
        
        # Machine name
        self.canvas.create_text(
            x1 + 60, y1 + 15,
            text=machine.name,
            font=("Segoe UI", 10, "bold"),
            fill="#212529",
            tags="machine"
        )
        
        # Status information
        queue_len = machine.get_queue_length()
        util = machine.get_utilization(self.sim_manager.current_time)
        
        self.canvas.create_text(
            x1 + 60, y1 + 35,
            text=f"Queue: {queue_len}",
            font=("Segoe UI", 9),
            fill="#495057",
            tags="machine"
        )
        
        self.canvas.create_text(
            x1 + 60, y1 + 50,
            text=f"Util: {util:.1f}%",
            font=("Segoe UI", 9),
            fill="#495057",
            tags="machine"
        )
        
        # Production line indicator (if part of a line)
        if hasattr(machine, 'production_line') and machine.production_line:
            self.canvas.create_text(
                x1 + 60, y1 + 65,
                text=f"Line: {machine.production_line}",
                font=("Segoe UI", 8),
                fill="#007bff",
                tags="machine"
            )
        
        # Working indicator
        if machine.is_working:
            self.canvas.create_oval(
                x2 - 15, y1 + 5, x2 - 5, y1 + 15,
                fill="#28a745", outline="#155724", width=2,
                tags="machine"
            )
        
        # Queue visualization
        if queue_len > 0:
            queue_width = min(queue_len * 3, 30)
            self.canvas.create_rectangle(
                x1, y2 - 5, x1 + queue_width, y2,
                fill="#ffc107", outline="",
                tags="machine"
            )
    
    def update_display(self):
        """อัปเดตการแสดงผล - Optimized"""
        # Clear only machine objects
        self.canvas.delete("machine")
        self.canvas.delete("selection")
        self.canvas.delete("production_line")
        
        # Draw production lines first
        self.draw_production_lines()
        
        # Draw machines
        for machine in self.factory.machines.values():
            self.draw_machine(machine)
        
        # Highlight selected machine
        if self.selected_machine:
            self.highlight_machine(self.selected_machine)
    
    def highlight_machine(self, machine: Machine):
        """เน้นเครื่องจักรที่เลือก"""
        x1, y1, x2, y2 = machine.get_bounds()
        
        # Glow effect
        for i in range(3):
            self.canvas.create_rectangle(
                x1 - (i+1)*2, y1 - (i+1)*2, x2 + (i+1)*2, y2 + (i+1)*2,
                outline="#007bff", width=2, fill="",
                tags="selection"
            )
    
    def draw_production_lines(self):
        """Draw production line connections"""
        for line in self.factory.production_lines.values():
            self.draw_production_line(line)
    
    def draw_production_line(self, line):
        """Draw a single production line with connections"""
        if len(line.machines) < 2:
            return
        
        # Draw connections between machines
        for i in range(len(line.machines) - 1):
            machine1 = line.machines[i]
            machine2 = line.machines[i + 1]
            
            # Get connection points
            x1, y1 = machine1.x + 60, machine1.y  # Right side of machine1
            x2, y2 = machine2.x - 60, machine2.y  # Left side of machine2
            
            # Draw connection line
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill="#007bff", width=3,
                arrow=tk.LAST, arrowshape=(16, 20, 6),
                tags="production_line"
            )
            
            # Add flow indicator (animated dot would be nice)
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            self.canvas.create_oval(
                mid_x - 3, mid_y - 3, mid_x + 3, mid_y + 3,
                fill="#28a745", outline="#155724",
                tags="production_line"
            )
        
        # Draw line label
        if line.machines:
            first_machine = line.machines[0]
            self.canvas.create_text(
                first_machine.x, first_machine.y - 40,
                text=f"📋 {line.name}",
                font=("Segoe UI", 10, "bold"),
                fill="#007bff",
                tags="production_line"
            )
    
    def on_click(self, event):
        """จัดการการคลิก"""
        self.last_click_pos = (event.x, event.y)
        clicked_machine = self.get_machine_at_position(event.x, event.y)
        
        if clicked_machine:
            self.selected_machine = clicked_machine
            self.dragging_machine = clicked_machine
        else:
            self.selected_machine = None
        
        self.update_display()
    
    def on_drag(self, event):
        """จัดการการลาก"""
        if self.dragging_machine:
            self.dragging_machine.x = event.x
            self.dragging_machine.y = event.y
            
            self.update_display()
    
    def on_release(self, event):
        """ปล่อยการลาก"""
        self.dragging_machine = None
    
    def on_double_click(self, event):
        """Double click เพื่อกำหนดค่า"""
        machine = self.get_machine_at_position(event.x, event.y)
        if machine and self.config_callback:
            self.config_callback(machine)
    
    def on_right_click(self, event):
        """Right click context menu"""
        machine = self.get_machine_at_position(event.x, event.y)
        if machine:
            self.show_context_menu(event, machine)
    
    def on_scroll(self, event):
        """Mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def get_machine_at_position(self, x: int, y: int) -> Optional[Machine]:
        """หาเครื่องจักรที่ตำแหน่งที่คลิก"""
        return self.factory.get_machine_by_position(x, y)
    
    def show_context_menu(self, event, machine: Machine):
        """แสดง context menu"""
        context_menu = tk.Menu(self.canvas, tearoff=0)
        context_menu.add_command(label=f"Configure {machine.name}", 
                               command=lambda: self.config_callback(machine) if self.config_callback else None)
        context_menu.add_command(label="Clear Queue", 
                               command=lambda: machine.clear_queue())
        context_menu.add_separator()
        context_menu.add_command(label="Show Details", 
                               command=lambda: self.show_machine_details(machine))
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def show_machine_details(self, machine: Machine):
        """แสดงรายละเอียดเครื่องจักร"""
        details = machine.get_status_summary()
        message = f"""Machine Details:
        
Name: {details['name']}
Type: {details['type']}
Status: {'Working' if details['working'] else 'Idle'}
Queue Length: {details['queue_length']}
Current Job: {details['current_job'] or 'None'}
Total Output: {details['total_output']}
Position: {details['position']}
        """
        messagebox.showinfo("Machine Details", message)
    
    def toggle_grid(self):
        """เปิด/ปิด grid"""
        self.show_grid = not self.show_grid
        self.update_display()
