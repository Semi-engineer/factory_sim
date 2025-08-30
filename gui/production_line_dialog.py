"""
Production Line management dialog
"""
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from typing import Optional, List, Callable
from models.production_line import ProductionLine, ProductionRoute
from models.machine import Machine
from models.factory import Factory


class ProductionLineDialog:
    """Dialog for creating and managing production lines"""
    
    def __init__(self, parent, factory: Factory, callback: Optional[Callable] = None):
        self.parent = parent
        self.factory = factory
        self.callback = callback
        self.result = None
        
        # Create dialog window
        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("🏭 Production Line Manager")
        self.dialog.geometry("1000x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.current_line: Optional[ProductionLine] = None
        self.available_machines: List[Machine] = []
        
        self.setup_ui()
        self.load_available_machines()
        self.refresh_lines_list()
        
    def setup_ui(self):
        """Setup user interface"""
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Create paned window
        paned = ttk.PanedWindow(main_frame, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        # Left panel - Lines list
        self.setup_lines_panel(paned)
        
        # Right panel - Line details
        self.setup_details_panel(paned)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X)
        
        ttk.Button(button_frame, text="📝 New Line", bootstyle="success", 
                  command=self.create_new_line).pack(side=LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="📋 Sample Line", bootstyle="info", 
                  command=self.create_sample_line).pack(side=LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="🗑️ Delete Line", bootstyle="danger", 
                  command=self.delete_line).pack(side=LEFT)
        
        ttk.Button(button_frame, text="✅ Save", bootstyle="success", 
                  command=self.save_changes).pack(side=RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="❌ Cancel", bootstyle="secondary", 
                  command=self.cancel).pack(side=RIGHT)
        
    def setup_lines_panel(self, parent):
        """Setup production lines list panel"""
        lines_frame = ttk.LabelFrame(parent, text="📋 Production Lines", padding=10)
        
        # Lines listbox
        self.lines_listbox = tk.Listbox(lines_frame, height=15)
        self.lines_listbox.pack(fill=BOTH, expand=True, pady=(0, 10))
        self.lines_listbox.bind('<<ListboxSelect>>', self.on_line_select)
        
        # Line info
        info_frame = ttk.LabelFrame(lines_frame, text="ℹ️ Line Info", padding=5)
        info_frame.pack(fill=X)
        
        self.info_text = tk.Text(info_frame, height=8, wrap=tk.WORD, font=("Consolas", 9))
        self.info_text.pack(fill=BOTH, expand=True)
        
        parent.add(lines_frame, weight=1)
        
    def setup_details_panel(self, parent):
        """Setup line details panel"""
        details_frame = ttk.LabelFrame(parent, text="⚙️ Line Configuration", padding=10)
        
        # Create notebook for tabs
        self.details_notebook = ttk.Notebook(details_frame)
        self.details_notebook.pack(fill=BOTH, expand=True)
        
        # Basic info tab
        self.setup_basic_tab()
        
        # Machines tab
        self.setup_machines_tab()
        
        # Layout tab
        self.setup_layout_tab()
        
        # Analysis tab
        self.setup_analysis_tab()
        
        parent.add(details_frame, weight=2)
        
    def setup_basic_tab(self):
        """Setup basic information tab"""
        basic_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(basic_frame, text="📝 Basic Info")
        
        # Line ID
        ttk.Label(basic_frame, text="Line ID:").grid(row=0, column=0, sticky=W, pady=5)
        self.line_id_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.line_id_var, width=20).grid(row=0, column=1, padx=10, pady=5)
        
        # Line Name
        ttk.Label(basic_frame, text="Line Name:").grid(row=1, column=0, sticky=W, pady=5)
        self.line_name_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.line_name_var, width=30).grid(row=1, column=1, padx=10, pady=5)
        
        # Takt Time
        ttk.Label(basic_frame, text="Demand (pieces/hour):").grid(row=2, column=0, sticky=W, pady=5)
        self.demand_var = tk.DoubleVar(value=60.0)
        ttk.Entry(basic_frame, textvariable=self.demand_var, width=15).grid(row=2, column=1, padx=10, pady=5)
        
        # Conveyor Speed
        ttk.Label(basic_frame, text="Conveyor Speed (pieces/min):").grid(row=3, column=0, sticky=W, pady=5)
        self.conveyor_speed_var = tk.DoubleVar(value=1.0)
        ttk.Entry(basic_frame, textvariable=self.conveyor_speed_var, width=15).grid(row=3, column=1, padx=10, pady=5)
        
    def setup_machines_tab(self):
        """Setup machines configuration tab"""
        machines_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(machines_frame, text="🔧 Machines")
        
        # Available machines
        available_frame = ttk.LabelFrame(machines_frame, text="Available Machines", padding=5)
        available_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 5))
        
        self.available_listbox = tk.Listbox(available_frame, height=15)
        self.available_listbox.pack(fill=BOTH, expand=True, pady=(0, 5))
        
        # Control buttons
        control_frame = ttk.Frame(machines_frame)
        control_frame.pack(side=LEFT, padx=5)
        
        ttk.Button(control_frame, text="➡️ Add", command=self.add_machine_to_line).pack(pady=2)
        ttk.Button(control_frame, text="⬅️ Remove", command=self.remove_machine_from_line).pack(pady=2)
        ttk.Button(control_frame, text="⬆️ Move Up", command=self.move_machine_up).pack(pady=2)
        ttk.Button(control_frame, text="⬇️ Move Down", command=self.move_machine_down).pack(pady=2)
        
        # Line machines
        line_machines_frame = ttk.LabelFrame(machines_frame, text="Line Machines (Sequence)", padding=5)
        line_machines_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=(5, 0))
        
        self.line_machines_listbox = tk.Listbox(line_machines_frame, height=15)
        self.line_machines_listbox.pack(fill=BOTH, expand=True)
        
    def setup_layout_tab(self):
        """Setup layout configuration tab"""
        layout_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(layout_frame, text="📐 Layout")
        
        # Layout type
        ttk.Label(layout_frame, text="Layout Type:").grid(row=0, column=0, sticky=W, pady=5)
        self.layout_var = tk.StringVar(value="horizontal")
        layout_combo = ttk.Combobox(layout_frame, textvariable=self.layout_var, 
                                   values=["horizontal", "vertical", "L-shape", "U-shape"], 
                                   state="readonly", width=15)
        layout_combo.grid(row=0, column=1, padx=10, pady=5)
        layout_combo.bind('<<ComboboxSelected>>', self.on_layout_change)
        
        # Start position
        ttk.Label(layout_frame, text="Start X:").grid(row=1, column=0, sticky=W, pady=5)
        self.start_x_var = tk.IntVar(value=50)
        ttk.Entry(layout_frame, textvariable=self.start_x_var, width=10).grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(layout_frame, text="Start Y:").grid(row=2, column=0, sticky=W, pady=5)
        self.start_y_var = tk.IntVar(value=200)
        ttk.Entry(layout_frame, textvariable=self.start_y_var, width=10).grid(row=2, column=1, padx=10, pady=5)
        
        # Spacing
        ttk.Label(layout_frame, text="Spacing:").grid(row=3, column=0, sticky=W, pady=5)
        self.spacing_var = tk.IntVar(value=180)
        ttk.Entry(layout_frame, textvariable=self.spacing_var, width=10).grid(row=3, column=1, padx=10, pady=5)
        
        # Apply button
        ttk.Button(layout_frame, text="🔄 Apply Layout", bootstyle="primary", 
                  command=self.apply_layout).grid(row=4, column=0, columnspan=2, pady=20)
        
    def setup_analysis_tab(self):
        """Setup analysis tab"""
        analysis_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(analysis_frame, text="📊 Analysis")
        
        # Analysis buttons
        button_frame = ttk.Frame(analysis_frame)
        button_frame.pack(fill=X, pady=10)
        
        ttk.Button(button_frame, text="🔍 Analyze Bottlenecks", bootstyle="warning", 
                  command=self.analyze_bottlenecks).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="⚖️ Balance Line", bootstyle="info", 
                  command=self.balance_line).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="📈 Calculate Metrics", bootstyle="success", 
                  command=self.calculate_metrics).pack(side=LEFT, padx=5)
        
        # Analysis results
        self.analysis_text = tk.Text(analysis_frame, height=20, wrap=tk.WORD, font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(analysis_frame, orient="vertical", command=self.analysis_text.yview)
        self.analysis_text.configure(yscrollcommand=scrollbar.set)
        
        self.analysis_text.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
    def load_available_machines(self):
        """Load available machines from factory"""
        self.available_machines = [
            machine for machine in self.factory.machines.values()
            if not hasattr(machine, 'production_line') or not machine.production_line
        ]
        
        self.available_listbox.delete(0, tk.END)
        for machine in self.available_machines:
            self.available_listbox.insert(tk.END, f"{machine.name} ({machine.machine_type})")
    
    def refresh_lines_list(self):
        """Refresh production lines list"""
        self.lines_listbox.delete(0, tk.END)
        for line_id, line in self.factory.production_lines.items():
            self.lines_listbox.insert(tk.END, f"{line_id}: {line.name}")
    
    def on_line_select(self, event):
        """Handle line selection"""
        selection = self.lines_listbox.curselection()
        if selection:
            line_index = selection[0]
            line_ids = list(self.factory.production_lines.keys())
            if line_index < len(line_ids):
                line_id = line_ids[line_index]
                self.current_line = self.factory.production_lines[line_id]
                self.load_line_details()
    
    def load_line_details(self):
        """Load current line details into UI"""
        if not self.current_line:
            return
        
        # Basic info
        self.line_id_var.set(self.current_line.line_id)
        self.line_name_var.set(self.current_line.name)
        self.conveyor_speed_var.set(self.current_line.conveyor_speed)
        
        # Layout
        self.layout_var.set(self.current_line.direction)
        self.start_x_var.set(self.current_line.start_x)
        self.start_y_var.set(self.current_line.start_y)
        self.spacing_var.set(self.current_line.spacing)
        
        # Machines in line
        self.line_machines_listbox.delete(0, tk.END)
        for machine in self.current_line.machines:
            self.line_machines_listbox.insert(tk.END, f"{machine.name} ({machine.machine_type})")
        
        # Update info
        self.update_line_info()
    
    def update_line_info(self):
        """Update line information display"""
        if not self.current_line:
            self.info_text.delete(1.0, tk.END)
            return
        
        summary = self.current_line.get_line_summary()
        info = f"""Line ID: {summary['line_id']}
Name: {summary['name']}
Machines: {summary['machine_count']}
Routes: {summary['routes_count']}
Efficiency: {summary['efficiency']:.1f}%
Throughput: {summary['throughput']:.2f}
Takt Time: {summary['takt_time']:.2f} min
Direction: {summary['direction']}
Total WIP: {summary['total_wip']}

Bottlenecks: {', '.join(summary['bottlenecks']) if summary['bottlenecks'] else 'None'}
        """
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)
    
    def create_new_line(self):
        """Create new production line"""
        line_id = f"LINE-{len(self.factory.production_lines) + 1:02d}"
        line_name = f"Production Line {len(self.factory.production_lines) + 1}"
        
        new_line = ProductionLine(line_name, line_id)
        self.factory.add_production_line(new_line)
        
        self.refresh_lines_list()
        messagebox.showinfo("Success", f"Created new production line: {line_id}")
    
    def create_sample_line(self):
        """Create sample production line"""
        sample_line = self.factory.create_sample_production_line()
        self.refresh_lines_list()
        messagebox.showinfo("Success", f"Created sample production line: {sample_line.line_id}")
    
    def delete_line(self):
        """Delete selected production line"""
        if not self.current_line:
            messagebox.showwarning("Warning", "Please select a production line to delete")
            return
        
        if messagebox.askyesno("Confirm", f"Delete production line {self.current_line.line_id}?"):
            self.factory.remove_production_line(self.current_line.line_id)
            self.current_line = None
            self.refresh_lines_list()
            self.load_available_machines()
            messagebox.showinfo("Success", "Production line deleted")
    
    def add_machine_to_line(self):
        """Add machine to production line"""
        if not self.current_line:
            messagebox.showwarning("Warning", "Please select a production line")
            return
        
        selection = self.available_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a machine to add")
            return
        
        machine_index = selection[0]
        machine = self.available_machines[machine_index]
        
        self.current_line.add_machine(machine)
        self.load_available_machines()
        self.load_line_details()
    
    def remove_machine_from_line(self):
        """Remove machine from production line"""
        if not self.current_line:
            return
        
        selection = self.line_machines_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a machine to remove")
            return
        
        machine_index = selection[0]
        if machine_index < len(self.current_line.machines):
            machine = self.current_line.machines[machine_index]
            self.current_line.remove_machine(machine)
            self.load_available_machines()
            self.load_line_details()
    
    def move_machine_up(self):
        """Move machine up in sequence"""
        if not self.current_line:
            return
        
        selection = self.line_machines_listbox.curselection()
        if not selection or selection[0] == 0:
            return
        
        machine_index = selection[0]
        machines = self.current_line.machines
        machines[machine_index], machines[machine_index - 1] = machines[machine_index - 1], machines[machine_index]
        
        self.current_line._update_machine_positions()
        self.load_line_details()
    
    def move_machine_down(self):
        """Move machine down in sequence"""
        if not self.current_line:
            return
        
        selection = self.line_machines_listbox.curselection()
        if not selection or selection[0] >= len(self.current_line.machines) - 1:
            return
        
        machine_index = selection[0]
        machines = self.current_line.machines
        machines[machine_index], machines[machine_index + 1] = machines[machine_index + 1], machines[machine_index]
        
        self.current_line._update_machine_positions()
        self.load_line_details()
    
    def on_layout_change(self, event):
        """Handle layout change"""
        if self.current_line:
            self.apply_layout()
    
    def apply_layout(self):
        """Apply layout settings"""
        if not self.current_line:
            return
        
        self.current_line.set_layout(
            self.layout_var.get(),
            self.start_x_var.get(),
            self.start_y_var.get(),
            self.spacing_var.get()
        )
        
        self.update_line_info()
        messagebox.showinfo("Success", "Layout applied")
    
    def analyze_bottlenecks(self):
        """Analyze bottlenecks in current line"""
        if not self.current_line:
            messagebox.showwarning("Warning", "Please select a production line")
            return
        
        bottlenecks = self.current_line.analyze_bottleneck()
        
        analysis = "🔍 BOTTLENECK ANALYSIS\n"
        analysis += "=" * 50 + "\n\n"
        
        if bottlenecks:
            analysis += f"Found {len(bottlenecks)} bottleneck(s):\n\n"
            for machine in bottlenecks:
                analysis += f"• {machine.name} ({machine.machine_type})\n"
                analysis += f"  - Cycle Time: {machine.base_time:.2f} min\n"
                analysis += f"  - Queue Length: {machine.get_queue_length()}\n"
                analysis += f"  - Utilization: {machine.get_utilization(100):.1f}%\n\n"
        else:
            analysis += "✅ No significant bottlenecks detected\n"
        
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(1.0, analysis)
    
    def balance_line(self):
        """Perform line balancing analysis"""
        if not self.current_line:
            messagebox.showwarning("Warning", "Please select a production line")
            return
        
        suggestions = self.current_line.balance_line()
        
        analysis = "⚖️ LINE BALANCING ANALYSIS\n"
        analysis += "=" * 50 + "\n\n"
        
        if suggestions:
            analysis += "Recommendations:\n\n"
            for i, suggestion in enumerate(suggestions, 1):
                analysis += f"{i}. {suggestion}\n\n"
        else:
            analysis += "✅ Line appears to be well balanced\n"
        
        # Calculate takt time
        demand = self.demand_var.get()
        if demand > 0:
            takt_time = self.current_line.calculate_takt_time(demand)
            analysis += f"\n📊 TAKT TIME ANALYSIS\n"
            analysis += f"Demand: {demand:.1f} pieces/hour\n"
            analysis += f"Takt Time: {takt_time:.2f} minutes/piece\n\n"
            
            analysis += "Machine vs Takt Time:\n"
            for machine in self.current_line.machines:
                status = "✅" if machine.base_time <= takt_time else "⚠️"
                analysis += f"{status} {machine.name}: {machine.base_time:.2f} min (Target: {takt_time:.2f})\n"
        
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(1.0, analysis)
    
    def calculate_metrics(self):
        """Calculate line performance metrics"""
        if not self.current_line:
            messagebox.showwarning("Warning", "Please select a production line")
            return
        
        efficiency = self.current_line.calculate_line_efficiency()
        throughput = self.current_line.calculate_throughput(1.0)  # Per hour
        
        analysis = "📈 PERFORMANCE METRICS\n"
        analysis += "=" * 50 + "\n\n"
        
        analysis += f"Line Efficiency: {efficiency:.1f}%\n"
        analysis += f"Throughput: {throughput:.2f} pieces/hour\n"
        analysis += f"Conveyor Speed: {self.current_line.conveyor_speed:.1f} pieces/min\n\n"
        
        analysis += "Individual Machine Performance:\n"
        for machine in self.current_line.machines:
            util = machine.get_utilization(1.0)
            machine_throughput = machine.get_throughput(1.0)
            analysis += f"• {machine.name}:\n"
            analysis += f"  - Utilization: {util:.1f}%\n"
            analysis += f"  - Throughput: {machine_throughput:.2f} pieces/hour\n"
            analysis += f"  - Queue: {machine.get_queue_length()} jobs\n\n"
        
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(1.0, analysis)
    
    def save_changes(self):
        """Save changes and close dialog"""
        if self.current_line:
            # Update basic properties
            self.current_line.name = self.line_name_var.get()
            self.current_line.conveyor_speed = self.conveyor_speed_var.get()
            
            # Calculate takt time
            demand = self.demand_var.get()
            if demand > 0:
                self.current_line.calculate_takt_time(demand)
        
        if self.callback:
            self.callback()
        
        self.dialog.destroy()
    
    def cancel(self):
        """Cancel and close dialog"""
        self.dialog.destroy()
    
    def show(self):
        """Show dialog"""
        self.dialog.wait_window()
