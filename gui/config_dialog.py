"""
Configuration dialog for simulation parameters
"""
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from typing import Callable, Optional
from config.simulation_config import SimulationConfig, ConfigPresets


class ConfigurationDialog:
    """Dialog for editing simulation configuration"""
    
    def __init__(self, parent, config: SimulationConfig, callback: Optional[Callable] = None):
        self.parent = parent
        self.config = config.to_dict()  # Work with a copy
        self.callback = callback
        self.result = None
        
        # Create dialog window
        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("⚙️ Simulation Configuration")
        self.dialog.geometry("800x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Make dialog modal
        self.dialog.focus_set()
        
        self.setup_ui()
        
        # Center dialog
        self.center_dialog()
        
    def center_dialog(self):
        """Center the dialog on parent window"""
        self.dialog.update_idletasks()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Setup the user interface"""
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Create notebook for categories
        self.notebook = ttk.Notebook(main_frame, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        # Setup tabs
        self.setup_global_tab()
        self.setup_cost_tab()
        self.setup_quality_tab()
        self.setup_performance_tab()
        self.setup_presets_tab()
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(10, 0))
        
        # Buttons
        ttk.Button(button_frame, text="💾 Save", bootstyle="success", 
                  command=self.save_config).pack(side=RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="❌ Cancel", bootstyle="secondary", 
                  command=self.cancel).pack(side=RIGHT)
        ttk.Button(button_frame, text="🔄 Reset", bootstyle="warning", 
                  command=self.reset_config).pack(side=LEFT)
        ttk.Button(button_frame, text="✅ Validate", bootstyle="info", 
                  command=self.validate_config).pack(side=LEFT, padx=(5, 0))
    
    def setup_global_tab(self):
        """Setup global parameters tab"""
        global_frame = ttk.Frame(self.notebook)
        self.notebook.add(global_frame, text="🌍 Global")
        
        # Create scrollable frame
        canvas = tk.Canvas(global_frame)
        scrollbar = ttk.Scrollbar(global_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Global parameters
        params = [
            ("sim_hours", "Simulation Hours", "float", "Hours to simulate"),
            ("target_prod", "Target Production", "int", "Target number of pieces"),
            ("quality_target", "Quality Target (%)", "float", "Target quality percentage"),
            ("batch_size", "Batch Size", "int", "Default batch size"),
            ("buffer_capacity", "Buffer Capacity", "int", "Maximum buffer size"),
            ("transport_speed", "Transport Speed", "float", "Pieces per minute"),
        ]
        
        self.global_vars = {}
        for i, (key, label, var_type, tooltip) in enumerate(params):
            self.create_parameter_row(scrollable_frame, key, label, var_type, tooltip, i)
            self.global_vars[key] = getattr(self, f"{key}_var")
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_cost_tab(self):
        """Setup cost parameters tab"""
        cost_frame = ttk.Frame(self.notebook)
        self.notebook.add(cost_frame, text="💰 Cost")
        
        # Create scrollable frame
        canvas = tk.Canvas(cost_frame)
        scrollbar = ttk.Scrollbar(cost_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Cost parameters
        params = [
            ("material_cost", "Material Cost per Piece", "float", "Cost of raw materials"),
            ("setup_cost", "Setup Cost", "float", "One-time setup cost"),
            ("inventory_cost", "Inventory Cost (%)", "float", "Inventory holding cost"),
            ("defect_cost", "Defect Cost per Piece", "float", "Cost of defective parts"),
            ("labor_rate", "Labor Rate per Hour", "float", "Hourly labor cost"),
            ("operators_per_machine", "Operators per Machine", "int", "Number of operators"),
            ("overhead_rate", "Overhead Rate per Hour", "float", "Overhead costs"),
            ("machine_cost", "Machine Cost per Hour", "float", "Machine operating cost"),
            ("energy_cost", "Energy Cost per kWh", "float", "Energy cost"),
        ]
        
        self.cost_vars = {}
        for i, (key, label, var_type, tooltip) in enumerate(params):
            self.create_parameter_row(scrollable_frame, key, label, var_type, tooltip, i)
            self.cost_vars[key] = getattr(self, f"{key}_var")
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_quality_tab(self):
        """Setup quality parameters tab"""
        quality_frame = ttk.Frame(self.notebook)
        self.notebook.add(quality_frame, text="🎯 Quality")
        
        # Create scrollable frame
        canvas = tk.Canvas(quality_frame)
        scrollbar = ttk.Scrollbar(quality_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Quality parameters
        params = [
            ("defect_rate", "Defect Rate", "float", "Probability of defects (0-1)"),
            ("rework_rate", "Rework Rate", "float", "Probability of rework (0-1)"),
            ("downtime_rate", "Downtime Rate", "float", "Random downtime probability"),
            ("maintenance_rate", "Maintenance Rate", "float", "Scheduled maintenance rate"),
        ]
        
        self.quality_vars = {}
        for i, (key, label, var_type, tooltip) in enumerate(params):
            self.create_parameter_row(scrollable_frame, key, label, var_type, tooltip, i)
            self.quality_vars[key] = getattr(self, f"{key}_var")
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_performance_tab(self):
        """Setup performance targets tab"""
        perf_frame = ttk.Frame(self.notebook)
        self.notebook.add(perf_frame, text="📈 Performance")
        
        # Create scrollable frame
        canvas = tk.Canvas(perf_frame)
        scrollbar = ttk.Scrollbar(perf_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Performance parameters
        params = [
            ("utilization_target", "Utilization Target (%)", "float", "Target machine utilization"),
            ("oee_target", "OEE Target (%)", "float", "Overall Equipment Effectiveness target"),
            ("throughput_target", "Throughput Target", "float", "Target pieces per hour"),
        ]
        
        self.perf_vars = {}
        for i, (key, label, var_type, tooltip) in enumerate(params):
            self.create_parameter_row(scrollable_frame, key, label, var_type, tooltip, i)
            self.perf_vars[key] = getattr(self, f"{key}_var")
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_presets_tab(self):
        """Setup configuration presets tab"""
        presets_frame = ttk.Frame(self.notebook)
        self.notebook.add(presets_frame, text="📋 Presets")
        
        ttk.Label(presets_frame, text="Load Predefined Configurations", 
                 font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        # Preset buttons
        presets = [
            ("High Volume Production", ConfigPresets.high_volume_production, 
             "Optimized for high-volume manufacturing"),
            ("Precision Manufacturing", ConfigPresets.precision_manufacturing,
             "High precision, low defect rate"),
            ("Cost Optimized", ConfigPresets.cost_optimized,
             "Minimized costs, efficient operations"),
            ("Flexible Manufacturing", ConfigPresets.flexible_manufacturing,
             "Single piece flow, flexible setup")
        ]
        
        for name, preset_func, description in presets:
            frame = ttk.LabelFrame(presets_frame, text=name, padding=10)
            frame.pack(fill=X, padx=10, pady=5)
            
            ttk.Label(frame, text=description, font=("Segoe UI", 9)).pack(anchor=W)
            ttk.Button(frame, text="Load Preset", bootstyle="primary-outline",
                      command=lambda pf=preset_func: self.load_preset(pf)).pack(anchor=E, pady=(5, 0))
    
    def create_parameter_row(self, parent, key: str, label: str, var_type: str, tooltip: str, row: int):
        """Create a parameter input row"""
        frame = ttk.Frame(parent)
        frame.pack(fill=X, padx=10, pady=5)
        
        # Label
        ttk.Label(frame, text=label, width=25).pack(side=LEFT)
        
        # Input field
        if var_type == "float":
            var = tk.DoubleVar(value=self.config.get(key, 0.0))
            entry = ttk.Entry(frame, textvariable=var, width=15)
        elif var_type == "int":
            var = tk.IntVar(value=self.config.get(key, 0))
            entry = ttk.Entry(frame, textvariable=var, width=15)
        else:
            var = tk.StringVar(value=str(self.config.get(key, "")))
            entry = ttk.Entry(frame, textvariable=var, width=15)
        
        entry.pack(side=LEFT, padx=(10, 5))
        
        # Store variable reference
        setattr(self, f"{key}_var", var)
        
        # Tooltip label
        ttk.Label(frame, text=tooltip, font=("Segoe UI", 8), 
                 foreground="#6c757d").pack(side=LEFT, padx=(10, 0))
    
    def load_preset(self, preset_func):
        """Load a configuration preset"""
        if messagebox.askyesno("Confirm", "Load preset configuration? This will overwrite current settings."):
            preset_config = preset_func()
            self.config = preset_config.to_dict()
            self.update_ui_values()
            messagebox.showinfo("Success", "Preset configuration loaded")
    
    def update_ui_values(self):
        """Update UI with current config values"""
        # Update all variable values
        for key, value in self.config.items():
            var_name = f"{key}_var"
            if hasattr(self, var_name):
                var = getattr(self, var_name)
                var.set(value)
    
    def collect_values(self) -> dict:
        """Collect values from UI"""
        values = {}
        
        # Collect from all tabs
        all_vars = {}
        if hasattr(self, 'global_vars'):
            all_vars.update(self.global_vars)
        if hasattr(self, 'cost_vars'):
            all_vars.update(self.cost_vars)
        if hasattr(self, 'quality_vars'):
            all_vars.update(self.quality_vars)
        if hasattr(self, 'perf_vars'):
            all_vars.update(self.perf_vars)
        
        for key, var in all_vars.items():
            try:
                values[key] = var.get()
            except tk.TclError:
                # Handle invalid values
                values[key] = self.config.get(key, 0)
        
        return values
    
    def validate_config(self):
        """Validate configuration values"""
        try:
            values = self.collect_values()
            temp_config = SimulationConfig.from_dict(values)
            issues = temp_config.validate()
            
            if issues:
                message = "Configuration issues found:\n\n" + "\n".join(f"• {issue}" for issue in issues)
                messagebox.showwarning("Validation Issues", message)
            else:
                messagebox.showinfo("Validation", "Configuration is valid!")
            
        except Exception as e:
            messagebox.showerror("Validation Error", f"Error validating configuration: {e}")
    
    def save_config(self):
        """Save configuration and close dialog"""
        try:
            values = self.collect_values()
            config = SimulationConfig.from_dict(values)
            
            # Validate
            issues = config.validate()
            if issues:
                message = "Configuration has issues:\n\n" + "\n".join(f"• {issue}" for issue in issues)
                if not messagebox.askyesno("Validation Issues", f"{message}\n\nSave anyway?"):
                    return
            
            self.result = config
            
            if self.callback:
                self.callback(config)
            
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error saving configuration: {e}")
    
    def reset_config(self):
        """Reset to default configuration"""
        if messagebox.askyesno("Confirm", "Reset to default configuration?"):
            self.config = SimulationConfig().to_dict()
            self.update_ui_values()
    
    def cancel(self):
        """Cancel and close dialog"""
        self.result = None
        self.dialog.destroy()
    
    def show(self) -> Optional[SimulationConfig]:
        """Show dialog and return result"""
        self.dialog.wait_window()
        return self.result
