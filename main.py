"""
Main GUI application for the factory simulation
"""
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog
import threading
import time
from typing import Optional, List

from models.factory import Factory
from models.machine import Machine
from models.job import Job
from simulation.simulation_manager import SimulationManager
from gui.factory_canvas import ModernFactoryCanvas
from gui.charts_panel import ModernChartsPanel
from gui.config_dialog import ConfigurationDialog
from gui.production_line_dialog import ProductionLineDialog
from config.simulation_config import SimulationConfig, ConfigPresets


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
        self.config = SimulationConfig()  # Default configuration
        
        # GUI state
        self.selected_machine = None
        self.update_timer = None
        self.step_count = 0
        
        # Simulation thread
        self.simulation_thread = None
        self.thread_running = False
        
        # Setup
        self.setup_default_machines()
        self.setup_menu_bar()
        self.setup_modern_gui()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_default_machines(self):
        """สร้างเครื่องจักรตัวอย่าง"""
        machines = [
            Machine("CNC-01", "CNC", 2.5, 10, 100, 150, self.config),
            Machine("CNC-02", "CNC", 2.8, 12, 100, 300, self.config),
            Machine("Lathe-01", "Lathe", 3.2, 15, 350, 150, self.config),
            Machine("Drill-01", "Drill", 1.8, 8, 600, 150, self.config),
            Machine("Assembly-01", "Assembly", 4.5, 25, 850, 150, self.config),
            Machine("Inspection-01", "Inspection", 1.2, 5, 850, 300, self.config),
        ]
        
        for machine in machines:
            self.factory.add_machine(machine)
    
    def setup_menu_bar(self):
        """สร้าง Menu Bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Simulation", command=self.reset_simulation, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Load Layout...", command=self.load_layout, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Layout...", command=self.save_layout, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Export Data...", command=self.export_data, accelerator="Ctrl+E")
        file_menu.add_command(label="Export Charts...", command=self.export_charts)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing, accelerator="Alt+F4")
        
        # Edit Menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Add Machine...", command=self.add_machine_dialog, accelerator="Ctrl+M")
        edit_menu.add_command(label="Add Job...", command=self.add_job_dialog, accelerator="Ctrl+J")
        edit_menu.add_separator()
        edit_menu.add_command(label="Configuration...", command=self.show_config_dialog, accelerator="Ctrl+P")
        edit_menu.add_separator()
        edit_menu.add_command(label="Clear All Jobs", command=self.clear_all_jobs)
        edit_menu.add_command(label="Reset Statistics", command=self.reset_statistics)
        
        # Simulation Menu
        sim_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Simulation", menu=sim_menu)
        sim_menu.add_command(label="Start", command=self.start_simulation, accelerator="Space")
        sim_menu.add_command(label="Pause", command=self.pause_simulation, accelerator="P")
        sim_menu.add_command(label="Resume", command=self.resume_simulation, accelerator="R")
        sim_menu.add_command(label="Stop", command=self.stop_simulation, accelerator="S")
        sim_menu.add_separator()
        sim_menu.add_command(label="🏭 Production Lines", command=self.show_production_line_dialog)
        sim_menu.add_separator()
        sim_menu.add_command(label="Speed 0.5x", command=lambda: self.set_speed(0.5))
        sim_menu.add_command(label="Speed 1x", command=lambda: self.set_speed(1.0))
        sim_menu.add_command(label="Speed 2x", command=lambda: self.set_speed(2.0))
        sim_menu.add_command(label="Speed 5x", command=lambda: self.set_speed(5.0))
        
        # Analysis Menu
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="Find Bottlenecks", command=self.find_bottleneck)
        analysis_menu.add_command(label="Performance Report", command=self.show_performance_report)
        analysis_menu.add_command(label="Machine Utilization", command=self.show_machine_utilization)
        analysis_menu.add_command(label="Suggestions", command=self.show_suggestions)
        
        # View Menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Factory Layout", command=lambda: self.notebook.select(0))
        view_menu.add_command(label="Analytics", command=lambda: self.notebook.select(1))
        view_menu.add_command(label="Machine Details", command=lambda: self.notebook.select(2))
        view_menu.add_separator()
        view_menu.add_command(label="Toggle Grid", command=self.toggle_grid)
        view_menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Reset Zoom", command=self.reset_zoom, accelerator="Ctrl+0")
        
        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self.show_help)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
        
        # Bind keyboard shortcuts
        self.setup_keyboard_shortcuts()
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.root.bind('<Control-n>', lambda e: self.reset_simulation())
        self.root.bind('<Control-o>', lambda e: self.load_layout())
        self.root.bind('<Control-s>', lambda e: self.save_layout())
        self.root.bind('<Control-e>', lambda e: self.export_data())
        self.root.bind('<Control-m>', lambda e: self.add_machine_dialog())
        self.root.bind('<Control-j>', lambda e: self.add_job_dialog())
        self.root.bind('<Control-p>', lambda e: self.show_config_dialog())
        self.root.bind('<space>', lambda e: self.toggle_simulation())
        self.root.bind('<Key-p>', lambda e: self.pause_simulation())
        self.root.bind('<Key-r>', lambda e: self.resume_simulation())
        self.root.bind('<Key-s>', lambda e: self.stop_simulation())
        self.root.bind('<Control-plus>', lambda e: self.zoom_in())
        self.root.bind('<Control-minus>', lambda e: self.zoom_out())
        self.root.bind('<Control-0>', lambda e: self.reset_zoom())
    
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
        
        # Start update timer
        self.schedule_updates()
    
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
        ttk.Button(actions_frame, text="🎲 Sample Jobs", bootstyle="outline-info",
                  command=self.create_sample_jobs).pack(fill=X, pady=2)
    
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
        
        columns = ("Name", "Type", "Queue", "Utilization", "Throughput", "Status")
        self.machine_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        column_widths = {"Name": 120, "Type": 100, "Queue": 80, "Utilization": 100, 
                        "Throughput": 120, "Status": 100}
        
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
    
    def setup_status_bar(self, parent):
        """Modern status bar"""
        self.status_frame = ttk.Frame(parent)
        self.status_frame.pack(fill=X, pady=(10, 0))
        
        # Status indicators
        ttk.Label(self.status_frame, text="Status:", font=("Segoe UI", 9)).pack(side=LEFT)
        
        self.status_indicator = ttk.Label(self.status_frame, text="● Stopped", 
                                         foreground="#dc3545", font=("Segoe UI", 9, "bold"))
        self.status_indicator.pack(side=LEFT, padx=(5, 20))
        
        ttk.Label(self.status_frame, text="Factory:", font=("Segoe UI", 9)).pack(side=LEFT)
        self.factory_status_label = ttk.Label(self.status_frame, text="Ready", font=("Segoe UI", 9))
        self.factory_status_label.pack(side=LEFT, padx=5)
    
    def schedule_updates(self):
        """Schedule GUI updates"""
        self.update_gui()
        self.update_timer = self.root.after(100, self.schedule_updates)  # Update every 100ms
    
    def update_gui(self):
        """Optimized GUI update"""
        try:
            # Update live dashboard
            metrics = self.sim_manager.get_latest_metrics()
            self.time_label.config(text=f"{metrics['time']:.1f} min")
            self.throughput_label.config(text=f"{metrics['throughput']:.2f} parts/min")
            self.utilization_label.config(text=f"{metrics['utilization']:.1f}%")
            self.wip_label.config(text=str(metrics['wip']))
            
            # Update factory canvas
            self.factory_canvas.update_display()
            
            # Update charts
            self.charts_panel.update_charts()
            
            # Update machine table
            self.update_machine_table()
            
            # Update factory status
            summary = self.factory.get_factory_summary()
            status_text = f"{summary['total_machines']} machines, {summary['total_jobs']} jobs, {summary['completed_jobs']} completed"
            self.factory_status_label.config(text=status_text)
            
        except Exception as e:
            print(f"GUI update error: {e}")
    
    def update_machine_table(self):
        """Update machine details table"""
        # Clear existing items
        for item in self.machine_tree.get_children():
            self.machine_tree.delete(item)
        
        # Add machine data
        for machine in self.factory.machines.values():
            # Apply filters
            if self.filter_var.get() != "All" and machine.machine_type != self.filter_var.get():
                continue
            
            search_term = self.search_var.get().lower()
            if search_term and search_term not in machine.name.lower():
                continue
            
            # Get machine data
            util = machine.get_utilization(self.sim_manager.current_time)
            throughput = machine.get_throughput(self.sim_manager.current_time)
            status = "Working" if machine.is_working else "Idle"
            
            values = (
                machine.name,
                machine.machine_type,
                machine.get_queue_length(),
                f"{util:.1f}%",
                f"{throughput:.2f}",
                status
            )
            
            self.machine_tree.insert("", "end", values=values)
    
    def start_simulation(self):
        """เริ่มการจำลอง"""
        if not self.thread_running:
            self.thread_running = True
            self.sim_manager.start()
            
            # Start simulation thread
            self.simulation_thread = threading.Thread(target=self.simulation_loop, daemon=True)
            self.simulation_thread.start()
            
            # Update UI
            self.start_btn.config(state="disabled")
            self.pause_btn.config(state="normal")
            self.resume_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.status_indicator.config(text="● Running", foreground="#28a745")
    
    def simulation_loop(self):
        """Simulation loop running in separate thread"""
        last_time = time.time()
        target_fps = 30
        frame_time = 1.0 / target_fps
        
        while self.thread_running:
            current_time = time.time()
            dt = current_time - last_time
            
            if dt >= frame_time:
                # Step simulation
                self.sim_manager.step(dt)
                last_time = current_time
            
            time.sleep(0.001)  # Small sleep to prevent high CPU usage
    
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
    
    def add_job_dialog(self):
        """Dialog สำหรับเพิ่มงาน"""
        dialog = ttk.Toplevel(self.root)
        dialog.title("Add New Job")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Job details
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Batch size
        ttk.Label(main_frame, text="Batch Size:").grid(row=0, column=0, sticky=W, pady=5)
        batch_var = tk.IntVar(value=10)
        ttk.Entry(main_frame, textvariable=batch_var, width=15).grid(row=0, column=1, padx=10, pady=5)
        
        # Priority
        ttk.Label(main_frame, text="Priority:").grid(row=1, column=0, sticky=W, pady=5)
        priority_var = tk.StringVar(value="Normal")
        priority_combo = ttk.Combobox(main_frame, textvariable=priority_var, 
                                     values=["Normal", "High", "Critical"], state="readonly")
        priority_combo.grid(row=1, column=1, padx=10, pady=5)
        
        # Machine sequence
        ttk.Label(main_frame, text="Machines (comma separated):").grid(row=2, column=0, sticky=W, pady=5)
        machines_var = tk.StringVar(value="CNC-01,Lathe-01,Assembly-01")
        ttk.Entry(main_frame, textvariable=machines_var, width=30).grid(row=2, column=1, padx=10, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        def create_job():
            try:
                batch_size = batch_var.get()
                priority_map = {"Normal": 1, "High": 2, "Critical": 3}
                priority = priority_map[priority_var.get()]
                machines = [m.strip() for m in machines_var.get().split(",") if m.strip()]
                
                if not machines:
                    messagebox.showerror("Error", "Please specify at least one machine")
                    return
                
                # Validate machines exist
                for machine_name in machines:
                    if machine_name not in self.factory.machines:
                        messagebox.showerror("Error", f"Machine '{machine_name}' not found")
                        return
                
                job = self.factory.create_job(batch_size, machines, priority)
                self.factory.route_job(job)
                
                messagebox.showinfo("Success", f"Job {job.id} created successfully")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create job: {e}")
        
        ttk.Button(button_frame, text="Create Job", bootstyle="success", 
                  command=create_job).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", bootstyle="secondary", 
                  command=dialog.destroy).pack(side=LEFT, padx=5)
    
    def add_machine_dialog(self):
        """Dialog สำหรับเพิ่มเครื่องจักร"""
        messagebox.showinfo("Info", "Machine addition dialog - To be implemented")
    
    def configure_machine(self, machine: Machine):
        """กำหนดค่าเครื่องจักร"""
        messagebox.showinfo("Info", f"Configure {machine.name} - To be implemented")
    
    def find_bottleneck(self):
        """หา bottleneck"""
        bottlenecks = self.factory.get_bottleneck_machines()
        if bottlenecks:
            names = [m.name for m in bottlenecks]
            messagebox.showinfo("Bottleneck Analysis", f"Bottleneck machines: {', '.join(names)}")
        else:
            messagebox.showinfo("Bottleneck Analysis", "No bottlenecks detected")
    
    def show_suggestions(self):
        """แสดงคำแนะนำ"""
        suggestions = []
        
        # Check for idle machines
        idle_machines = self.factory.get_idle_machines()
        if idle_machines:
            suggestions.append(f"Consider adding jobs for idle machines: {', '.join([m.name for m in idle_machines])}")
        
        # Check for bottlenecks
        bottlenecks = self.factory.get_bottleneck_machines()
        if bottlenecks:
            suggestions.append(f"Consider adding capacity or reducing setup time for: {', '.join([m.name for m in bottlenecks])}")
        
        if not suggestions:
            suggestions.append("Factory is running efficiently!")
        
        messagebox.showinfo("Suggestions", "\n\n".join(suggestions))
    
    def create_sample_jobs(self):
        """สร้างงานตัวอย่าง"""
        sample_sequences = [
            ["CNC-01", "Lathe-01", "Assembly-01"],
            ["CNC-02", "Drill-01", "Inspection-01"],
            ["Lathe-01", "Assembly-01", "Inspection-01"]
        ]
        
        for i, sequence in enumerate(sample_sequences):
            job = self.factory.create_job(
                batch_size=10 + i * 5,
                required_machines=sequence,
                priority=1 if i < 2 else 2
            )
            self.factory.route_job(job)
        
        messagebox.showinfo("Success", "Sample jobs created successfully")
    
    def export_data(self):
        """ส่งออกข้อมูล"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Export Simulation Data",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename:
                import json
                
                # Collect data
                data = {
                    "simulation_summary": self.sim_manager.get_simulation_summary(),
                    "factory_summary": self.factory.get_factory_summary(),
                    "machines": [machine.get_status_summary() for machine in self.factory.machines.values()],
                    "metrics": {
                        "time_history": list(self.sim_manager.time_history),
                        "throughput_history": list(self.sim_manager.throughput_history),
                        "utilization_history": list(self.sim_manager.utilization_history),
                        "wip_history": list(self.sim_manager.wip_history)
                    }
                }
                
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                
                messagebox.showinfo("Success", f"Data exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {e}")
    
    def save_layout(self):
        """บันทึกผังโรงงาน"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Save Factory Layout",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                import json
                
                layout_data = {
                    "machines": [
                        {
                            "name": machine.name,
                            "type": machine.machine_type,
                            "base_time": machine.base_time,
                            "setup_time": machine.setup_time,
                            "x": machine.x,
                            "y": machine.y
                        }
                        for machine in self.factory.machines.values()
                    ]
                }
                
                with open(filename, 'w') as f:
                    json.dump(layout_data, f, indent=2)
                
                messagebox.showinfo("Success", f"Layout saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save layout: {e}")
    
    def load_layout(self):
        """โหลดผังโรงงาน"""
        try:
            filename = filedialog.askopenfilename(
                title="Load Factory Layout",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                import json
                
                with open(filename, 'r') as f:
                    layout_data = json.load(f)
                
                # Clear existing machines
                self.factory.machines.clear()
                
                # Load machines
                for machine_data in layout_data.get("machines", []):
                    machine = Machine(
                        name=machine_data["name"],
                        machine_type=machine_data["type"],
                        base_time=machine_data["base_time"],
                        setup_time=machine_data["setup_time"],
                        x=machine_data["x"],
                        y=machine_data["y"]
                    )
                    self.factory.add_machine(machine)
                
                messagebox.showinfo("Success", f"Layout loaded from {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load layout: {e}")
    
    def export_charts(self):
        """ส่งออกกราฟ"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Export Charts",
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("All files", "*.*")]
            )
            
            if filename:
                success = self.charts_panel.save_charts(filename)
                if success:
                    messagebox.showinfo("Success", f"Charts exported to {filename}")
                else:
                    messagebox.showerror("Error", "Failed to export charts")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export charts: {e}")
    
    def clear_all_jobs(self):
        """ล้างงานทั้งหมด"""
        if messagebox.askyesno("Confirm", "Clear all jobs? This cannot be undone."):
            self.factory.clear_all_jobs()
            messagebox.showinfo("Success", "All jobs cleared")
    
    def reset_statistics(self):
        """รีเซ็ตสถิติ"""
        if messagebox.askyesno("Confirm", "Reset all statistics? This cannot be undone."):
            self.factory.reset_statistics()
            self.sim_manager.clear_history()
            messagebox.showinfo("Success", "Statistics reset")
    
    def reset_simulation(self):
        """รีเซ็ตการจำลอง"""
        if messagebox.askyesno("Confirm", "Reset simulation? This will stop current simulation and clear all data."):
            self.sim_manager.reset()
            messagebox.showinfo("Success", "Simulation reset")
    
    def set_speed(self, speed: float):
        """ตั้งค่าความเร็ว"""
        self.speed_var.set(speed)
        self.sim_manager.set_speed(speed)
        self.speed_label.config(text=f"{speed:.1f}x")
    
    def toggle_simulation(self):
        """สลับสถานะการจำลอง"""
        if self.sim_manager.is_running:
            if self.sim_manager.is_paused:
                self.resume_simulation()
            else:
                self.pause_simulation()
        else:
            self.start_simulation()
    
    def toggle_grid(self):
        """เปิด/ปิด grid"""
        self.factory_canvas.toggle_grid()
    
    def zoom_in(self):
        """ขยายภาพ"""
        messagebox.showinfo("Info", "Zoom in - To be implemented")
    
    def zoom_out(self):
        """ย่อภาพ"""
        messagebox.showinfo("Info", "Zoom out - To be implemented")
    
    def reset_zoom(self):
        """รีเซ็ตการขยาย"""
        messagebox.showinfo("Info", "Reset zoom - To be implemented")
    
    def show_performance_report(self):
        """แสดงรายงานประสิทธิภาพ"""
        metrics = self.sim_manager.get_latest_metrics()
        factory_summary = self.factory.get_factory_summary()
        
        report = f"""Performance Report
        
Simulation Time: {metrics['time']:.2f} minutes
Total Throughput: {metrics['throughput']:.2f} parts/min
Average Utilization: {metrics['utilization']:.1f}%
Work in Process: {metrics['wip']} jobs

Factory Summary:
- Total Machines: {factory_summary['total_machines']}
- Active Jobs: {factory_summary['total_jobs']}
- Completed Jobs: {factory_summary['completed_jobs']}
- Bottlenecks: {', '.join(factory_summary['bottlenecks']) if factory_summary['bottlenecks'] else 'None'}
- Idle Machines: {', '.join(factory_summary['idle_machines']) if factory_summary['idle_machines'] else 'None'}
        """
        
        messagebox.showinfo("Performance Report", report)
    
    def show_machine_utilization(self):
        """แสดงการใช้งานเครื่องจักร"""
        if not self.factory.machines:
            messagebox.showinfo("Info", "No machines in factory")
            return
        
        utilizations = []
        for machine in self.factory.machines.values():
            util = machine.get_utilization(self.sim_manager.current_time)
            utilizations.append(f"{machine.name}: {util:.1f}%")
        
        report = "Machine Utilization:\n\n" + "\n".join(utilizations)
        messagebox.showinfo("Machine Utilization", report)
    
    def show_help(self):
        """แสดงคู่มือใช้งาน"""
        help_text = """Factory Simulation Help

Getting Started:
1. Click 'Start' to begin simulation
2. Add jobs using 'Add Job' button
3. Monitor performance in Analytics tab
4. View machine details in Machine Details tab

Controls:
- Start/Pause/Resume/Stop simulation
- Adjust speed with slider
- Drag machines to reposition them
- Double-click machines to configure

Tips:
- Watch for bottlenecks (red indicators)
- Balance machine utilization
- Use priority jobs for urgent orders
- Export data for further analysis
        """
        messagebox.showinfo("Help", help_text)
    
    def show_shortcuts(self):
        """แสดงคีย์บอร์ดช็อตคัต"""
        shortcuts = """Keyboard Shortcuts

File:
Ctrl+N - New Simulation
Ctrl+O - Load Layout
Ctrl+S - Save Layout
Ctrl+E - Export Data

Edit:
Ctrl+M - Add Machine
Ctrl+J - Add Job

Simulation:
Space - Toggle Simulation
P - Pause
R - Resume
S - Stop

View:
Ctrl++ - Zoom In
Ctrl+- - Zoom Out
Ctrl+0 - Reset Zoom
        """
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)
    
    def show_about(self):
        """แสดงข้อมูลโปรแกรม"""
        about_text = """Factory Simulation - Modern Edition

Version: 2.0.0
A modern real-time factory simulation with interactive GUI

Features:
- Real-time simulation
- Interactive factory layout
- Performance analytics
- Modern GUI design
- Machine management
- Job scheduling
- Bottleneck detection

Built with Python, tkinter, and ttkbootstrap
        """
        messagebox.showinfo("About", about_text)
    
    def show_config_dialog(self):
        """แสดง configuration dialog"""
        def on_config_changed(new_config: SimulationConfig):
            self.config = new_config
            # Update all machines with new config
            for machine in self.factory.machines.values():
                machine.config = new_config
            messagebox.showinfo("Success", "Configuration updated successfully")
        
        dialog = ConfigurationDialog(self.root, self.config, on_config_changed)
        result = dialog.show()
        
        if result:
            self.config = result
    
    def show_production_line_dialog(self):
        """Show production line management dialog"""
        def on_lines_changed():
            self.canvas.update_display()
            self.update_machine_table()
        
        dialog = ProductionLineDialog(self.root, self.factory, on_lines_changed)
        dialog.show()
    
    def filter_machines(self, event=None):
        """กรองเครื่องจักร"""
        self.update_machine_table()
    
    def sort_column(self, column):
        """เรียงลำดับคอลัมน์"""
        # To be implemented
        pass
    
    def on_machine_table_select(self, event):
        """เลือกเครื่องจักรจากตาราง"""
        selection = self.machine_tree.selection()
        if selection:
            item = self.machine_tree.item(selection[0])
            machine_name = item['values'][0]
            self.selected_machine = self.factory.get_machine(machine_name)
            self.factory_canvas.selected_machine = self.selected_machine
    
    def on_machine_table_double_click(self, event):
        """Double click ในตาราง"""
        if self.selected_machine:
            self.configure_machine(self.selected_machine)
    
    def on_closing(self):
        """ปิดโปรแกรม"""
        self.stop_simulation()
        if self.update_timer:
            self.root.after_cancel(self.update_timer)
        self.root.destroy()
    
    def run(self):
        """เริ่มโปรแกรม"""
        self.root.mainloop()


def main():
    """ฟังก์ชันหลัก"""
    try:
        app = ModernFactorySimulationGUI()
        app.run()
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please install required packages: pip install ttkbootstrap matplotlib numpy")
        
    except Exception as e:
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
