"""
Dialog windows for factory simulation
Contains all popup dialogs and configuration windows
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from typing import Optional, Callable, List, Dict, Any
from models import Machine, Factory, Job
from simulation_engine import SimulationManager, PerformanceAnalyzer
from data_manager import DefaultFactoryTemplates


class AddJobDialog:
    """Modern Add Job Dialog"""
    
    def __init__(self, parent, factory: Factory, on_job_created: Callable = None):
        self.factory = factory
        self.on_job_created = on_job_created
        
        # Create dialog
        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("Add New Job")
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Create dialog sections
        self.create_job_details_section(main_frame)
        self.create_machine_sequence_section(main_frame)
        self.create_action_buttons(main_frame)
        
        # Variables
        self.batch_size_var = tk.IntVar(value=20)
        self.priority_var = tk.StringVar(value="Normal")
        
    def create_job_details_section(self, parent):
        """Create job details input section"""
        details_frame = ttk.LabelFrame(parent, text="Job Details", padding=15)
        details_frame.pack(fill=X, pady=(0, 15))
        
        # Batch size
        ttk.Label(details_frame, text="Batch Size:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky=W, pady=5)
        batch_entry = ttk.Entry(details_frame, textvariable=self.batch_size_var, width=15)
        batch_entry.grid(row=0, column=1, sticky=W, padx=(10, 0), pady=5)
        
        # Priority
        ttk.Label(details_frame, text="Priority:", font=("Segoe UI", 10)).grid(row=1, column=0, sticky=W, pady=5)
        priority_combo = ttk.Combobox(details_frame, textvariable=self.priority_var, width=12,
                                     values=["Normal", "High", "Critical"], state="readonly")
        priority_combo.grid(row=1, column=1, sticky=W, padx=(10, 0), pady=5)
    
    def create_machine_sequence_section(self, parent):
        """Create machine sequence selection"""
        sequence_frame = ttk.LabelFrame(parent, text="Machine Sequence", padding=15)
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
        
        ttk.Button(control_frame, text="Add →", command=self.move_machine_to_sequence).pack(pady=2)
        ttk.Button(control_frame, text="↑ Up", command=self.move_sequence_up).pack(pady=2)
        ttk.Button(control_frame, text="↓ Down", command=self.move_sequence_down).pack(pady=2)
        ttk.Button(control_frame, text="Remove", command=self.remove_from_sequence).pack(pady=2)
        
        # Selected sequence
        ttk.Label(sequence_frame, text="Job Sequence:", font=("Segoe UI", 10)).pack(anchor=W, pady=(10, 0))
        self.sequence_listbox = tk.Listbox(sequence_frame, height=6)
        self.sequence_listbox.pack(fill=X, pady=5)
    
    def create_action_buttons(self, parent):
        """Create action buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=X)
        
        ttk.Button(button_frame, text="Create Job", bootstyle="success", 
                  command=self.create_job).pack(side=RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", bootstyle="secondary", 
                  command=self.dialog.destroy).pack(side=RIGHT)
    
    def move_machine_to_sequence(self):
        """Move machine to sequence"""
        selection = self.available_listbox.curselection()
        if selection:
            machine_name = self.available_listbox.get(selection[0])
            self.sequence_listbox.insert(tk.END, machine_name)
    
    def move_sequence_up(self):
        """Move sequence item up"""
        selection = self.sequence_listbox.curselection()
        if selection and selection[0] > 0:
            idx = selection[0]
            item = self.sequence_listbox.get(idx)
            self.sequence_listbox.delete(idx)
            self.sequence_listbox.insert(idx - 1, item)
            self.sequence_listbox.selection_set(idx - 1)
    
    def move_sequence_down(self):
        """Move sequence item down"""
        selection = self.sequence_listbox.curselection()
        if selection and selection[0] < self.sequence_listbox.size() - 1:
            idx = selection[0]
            item = self.sequence_listbox.get(idx)
            self.sequence_listbox.delete(idx)
            self.sequence_listbox.insert(idx + 1, item)
            self.sequence_listbox.selection_set(idx + 1)
    
    def remove_from_sequence(self):
        """Remove item from sequence"""
        selection = self.sequence_listbox.curselection()
        if selection:
            self.sequence_listbox.delete(selection[0])
    
    def create_job(self):
        """Create job from dialog inputs"""
        try:
            batch_size = self.batch_size_var.get()
            priority_text = self.priority_var.get()
            
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
                self.dialog.destroy()
                if self.on_job_created:
                    self.on_job_created(job)
                messagebox.showinfo("Success", f"Job #{job.id} created successfully!")
            else:
                messagebox.showerror("Error", "Failed to route job")
                
        except Exception as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")


class AddMachineDialog:
    """Modern Add Machine Dialog"""
    
    def __init__(self, parent, factory: Factory, on_machine_created: Callable = None):
        self.factory = factory
        self.on_machine_created = on_machine_created
        
        # Create dialog
        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("Add New Machine")
        self.dialog.geometry("450x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Create sections
        self.create_machine_info_section(main_frame)
        self.create_performance_section(main_frame)
        self.create_position_section(main_frame)
        self.create_action_buttons(main_frame)
        
        # Variables
        self.name_var = tk.StringVar()
        self.type_var = tk.StringVar(value="CNC")
        self.base_time_var = tk.DoubleVar(value=2.0)
        self.setup_time_var = tk.DoubleVar(value=10.0)
        self.x_var = tk.IntVar(value=200)
        self.y_var = tk.IntVar(value=200)
    
    def create_machine_info_section(self, parent):
        """Create machine information section"""
        info_frame = ttk.LabelFrame(parent, text="Machine Information", padding=15)
        info_frame.pack(fill=X, pady=(0, 15))
        
        # Name
        ttk.Label(info_frame, text="Machine Name:").grid(row=0, column=0, sticky=W, pady=5)
        ttk.Entry(info_frame, textvariable=self.name_var, width=20).grid(row=0, column=1, sticky=W, padx=(10, 0), pady=5)
        
        # Type
        ttk.Label(info_frame, text="Machine Type:").grid(row=1, column=0, sticky=W, pady=5)
        type_combo = ttk.Combobox(info_frame, textvariable=self.type_var, width=17,
                                 values=["CNC", "Lathe", "Drill", "Assembly", "Inspection", "Packaging", "Input", "Output"])
        type_combo.grid(row=1, column=1, sticky=W, padx=(10, 0), pady=5)
    
    def create_performance_section(self, parent):
        """Create performance parameters section"""
        perf_frame = ttk.LabelFrame(parent, text="Performance Parameters", padding=15)
        perf_frame.pack(fill=X, pady=(0, 15))
        
        # Base time
        ttk.Label(perf_frame, text="Base Time (min/part):").grid(row=0, column=0, sticky=W, pady=5)
        ttk.Entry(perf_frame, textvariable=self.base_time_var, width=20).grid(row=0, column=1, sticky=W, padx=(10, 0), pady=5)
        
        # Setup time
        ttk.Label(perf_frame, text="Setup Time (min):").grid(row=1, column=0, sticky=W, pady=5)
        ttk.Entry(perf_frame, textvariable=self.setup_time_var, width=20).grid(row=1, column=1, sticky=W, padx=(10, 0), pady=5)
    
    def create_position_section(self, parent):
        """Create position settings section"""
        pos_frame = ttk.LabelFrame(parent, text="Position", padding=15)
        pos_frame.pack(fill=X, pady=(0, 15))
        
        ttk.Label(pos_frame, text="X Position:").grid(row=0, column=0, sticky=W, pady=5)
        ttk.Entry(pos_frame, textvariable=self.x_var, width=20).grid(row=0, column=1, sticky=W, padx=(10, 0), pady=5)
        
        ttk.Label(pos_frame, text="Y Position:").grid(row=1, column=0, sticky=W, pady=5)
        ttk.Entry(pos_frame, textvariable=self.y_var, width=20).grid(row=1, column=1, sticky=W, padx=(10, 0), pady=5)
    
    def create_action_buttons(self, parent):
        """Create action buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Add Machine", bootstyle="success",
                  command=self.create_machine).pack(side=RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", bootstyle="secondary",
                  command=self.dialog.destroy).pack(side=RIGHT)
    
    def create_machine(self):
        """Create machine from dialog inputs"""
        try:
            name = self.name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Machine name is required")
                return
            
            if name in self.factory.machines:
                messagebox.showerror("Error", "Machine name already exists")
                return
            
            machine = Machine(
                name=name,
                machine_type=self.type_var.get(),
                base_time=self.base_time_var.get(),
                setup_time=self.setup_time_var.get(),
                x=self.x_var.get(),
                y=self.y_var.get()
            )
            
            self.factory.add_machine(machine)
            self.dialog.destroy()
            
            if self.on_machine_created:
                self.on_machine_created(machine)
            
            messagebox.showinfo("Success", f"Machine {name} added successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")


class MachineConfigDialog:
    """Machine configuration dialog"""
    
    def __init__(self, parent, machine: Machine, factory: Factory, on_machine_updated: Callable = None):
        self.machine = machine
        self.factory = factory
        self.on_machine_updated = on_machine_updated
        
        # Create dialog
        self.dialog = ttk.Toplevel(parent)
        self.dialog.title(f"Configure {machine.name}")
        self.dialog.geometry("400x350")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Create sections
        self.create_parameters_section(main_frame)
        self.create_position_section(main_frame)
        self.create_action_buttons(main_frame)
        
        # Variables
        self.base_time_var = tk.DoubleVar(value=machine.base_time)
        self.setup_time_var = tk.DoubleVar(value=machine.setup_time)
        self.x_var = tk.IntVar(value=machine.x)
        self.y_var = tk.IntVar(value=machine.y)
    
    def create_parameters_section(self, parent):
        """Create parameters section"""
        # Parameters
        ttk.Label(parent, text="Base Time (min/part):").pack(anchor=W, pady=2)
        ttk.Entry(parent, textvariable=self.base_time_var).pack(fill=X, pady=(0, 10))
        
        ttk.Label(parent, text="Setup Time (min):").pack(anchor=W, pady=2)
        ttk.Entry(parent, textvariable=self.setup_time_var).pack(fill=X, pady=(0, 10))
    
    def create_position_section(self, parent):
        """Create position section"""
        # Position
        pos_frame = ttk.Frame(parent)
        pos_frame.pack(fill=X, pady=10)
        
        ttk.Label(pos_frame, text="X:").pack(side=LEFT)
        ttk.Entry(pos_frame, textvariable=self.x_var, width=10).pack(side=LEFT, padx=(5, 20))
        
        ttk.Label(pos_frame, text="Y:").pack(side=LEFT)
        ttk.Entry(pos_frame, textvariable=self.y_var, width=10).pack(side=LEFT, padx=5)
    
    def create_action_buttons(self, parent):
        """Create action buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=X, pady=(20, 0))
        
        ttk.Button(button_frame, text="Apply", bootstyle="success", 
                  command=self.apply_changes).pack(side=RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Delete", bootstyle="danger", 
                  command=self.delete_machine).pack(side=RIGHT)
        ttk.Button(button_frame, text="Cancel", bootstyle="secondary", 
                  command=self.dialog.destroy).pack(side=RIGHT, padx=(0, 5))
    
    def apply_changes(self):
        """Apply configuration changes"""
        try:
            self.machine.base_time = self.base_time_var.get()
            self.machine.setup_time = self.setup_time_var.get()
            self.machine.x = self.x_var.get()
            self.machine.y = self.y_var.get()
            
            self.dialog.destroy()
            
            if self.on_machine_updated:
                self.on_machine_updated(self.machine)
                
        except Exception as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
    
    def delete_machine(self):
        """Delete machine with confirmation"""
        if messagebox.askyesno("Confirm", f"Delete {self.machine.name}?"):
            self.factory.remove_machine(self.machine.name)
            self.dialog.destroy()
            
            if self.on_machine_updated:
                self.on_machine_updated(None)  # Signal deletion


class MachineDetailsDialog:
    """Detailed machine analysis dialog"""
    
    def __init__(self, parent, machine: Machine, sim_manager: SimulationManager):
        self.machine = machine
        self.sim_manager = sim_manager
        
        # Create dialog
        self.dialog = ttk.Toplevel(parent)
        self.dialog.title(f"{machine.name} - Detailed Analysis")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Create sections
        self.create_current_metrics_section(main_frame)
        self.create_performance_analysis_section(main_frame)
        
        # Close button
        ttk.Button(main_frame, text="Close", command=self.dialog.destroy).pack(pady=(20, 0))
    
    def create_current_metrics_section(self, parent):
        """Create current metrics display"""
        current_frame = ttk.LabelFrame(parent, text="Current Metrics", padding=10)
        current_frame.pack(fill=X, pady=(0, 10))
        
        util = self.machine.get_utilization(self.sim_manager.current_time)
        throughput = self.machine.get_throughput(self.sim_manager.current_time)
        cycle_time = self.machine.calculate_cycle_time(20)
        
        metrics_text = f"""Queue Length: {self.machine.get_queue_length()} jobs
Utilization: {util:.2f}%
Throughput: {throughput:.2f} parts/min
Cycle Time: {cycle_time:.2f} min (batch size 20)
Total Output: {self.machine.total_output} parts
Working Time: {self.machine.total_working_time:.1f} min
Status: {'Working' if self.machine.is_working else 'Idle'}"""
        
        ttk.Label(current_frame, text=metrics_text.strip(), justify=LEFT).pack(anchor=W)
    
    def create_performance_analysis_section(self, parent):
        """Create performance analysis section"""
        analysis_frame = ttk.LabelFrame(parent, text="Performance Analysis", padding=10)
        analysis_frame.pack(fill=BOTH, expand=True)
        
        util = self.machine.get_utilization(self.sim_manager.current_time)
        
        # Performance status
        if util > 90:
            status = "OVERLOADED - Consider load balancing"
        elif util > 70:
            status = "HIGH UTILIZATION - Monitor closely"
        elif util > 30:
            status = "GOOD UTILIZATION"
        else:
            status = "UNDERUTILIZED - Check job routing"
        
        ttk.Label(analysis_frame, text=f"Status: {status}", font=("Segoe UI", 10)).pack(anchor=W, pady=5)
        
        # Recommendations
        recommendations = []
        if self.machine.get_queue_length() > 10:
            recommendations.append("• Consider adding parallel machine")
        if util < 20:
            recommendations.append("• Check if machine is properly utilized")
        if self.machine.calculate_cycle_time(1) > 10:
            recommendations.append("• Review setup time optimization")
        
        if recommendations:
            ttk.Label(analysis_frame, text="Recommendations:", font=("Segoe UI", 10, "bold")).pack(anchor=W, pady=(10, 5))
            rec_text = "\n".join(recommendations)
            ttk.Label(analysis_frame, text=rec_text, justify=LEFT).pack(anchor=W)


class SuggestionsDialog:
    """Optimization suggestions dialog"""
    
    def __init__(self, parent, factory: Factory, sim_manager: SimulationManager):
        self.factory = factory
        self.sim_manager = sim_manager
        
        # Create dialog
        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("Optimization Suggestions")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Generate and display suggestions
        analyzer = PerformanceAnalyzer(factory, sim_manager)
        suggestions = analyzer.generate_suggestions()
        
        # Create text widget
        text_widget = tk.Text(main_frame, wrap=tk.WORD, font=("Segoe UI", 10), height=20)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Insert suggestions
        for i, suggestion in enumerate(suggestions, 1):
            text_widget.insert(tk.END, f"{i}. {suggestion}\n\n")
        
        text_widget.config(state=tk.DISABLED)
        
        ttk.Button(self.dialog, text="Close", command=self.dialog.destroy).pack(pady=10)


class OEEAnalysisDialog:
    """OEE Analysis dialog"""
    
    def __init__(self, parent, factory: Factory, sim_manager: SimulationManager):
        self.factory = factory
        self.sim_manager = sim_manager
        
        # Create dialog
        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("OEE (Overall Equipment Effectiveness)")
        self.dialog.geometry("700x500")
        self.dialog.transient(parent)
        
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Create OEE table
        self.create_oee_table(main_frame)
        
        ttk.Button(main_frame, text="Close", command=self.dialog.destroy).pack(pady=10)
    
    def create_oee_table(self, parent):
        """Create OEE analysis table"""
        columns = ("Machine", "Availability", "Performance", "Quality", "OEE", "Rating")
        oee_tree = ttk.Treeview(parent, columns=columns, show="headings", height=12)
        
        for col in columns:
            oee_tree.heading(col, text=col)
            oee_tree.column(col, width=100)
        
        # Calculate OEE for each machine
        analyzer = PerformanceAnalyzer(self.factory, self.sim_manager)
        
        for machine in self.factory.machines.values():
            oee_data = analyzer.calculate_oee(machine)
            
            # Determine rating and color
            oee_value = oee_data["oee"]
            if oee_value >= 85:
                rating = "Excellent"
                tags = ("excellent",)
            elif oee_value >= 65:
                rating = "Good"
                tags = ("good",)
            elif oee_value >= 40:
                rating = "Fair"
                tags = ("fair",)
            else:
                rating = "Poor"
                tags = ("poor",)
            
            oee_tree.insert("", tk.END, values=(
                machine.name,
                f"{oee_data['availability']:.1f}%",
                f"{oee_data['performance']:.1f}%",
                f"{oee_data['quality']:.1f}%",
                f"{oee_data['oee']:.1f}%",
                rating
            ), tags=tags)
        
        # Configure colors
        oee_tree.tag_configure("excellent", background="#d4edda")
        oee_tree.tag_configure("good", background="#cce5ff")
        oee_tree.tag_configure("fair", background="#fff3cd")
        oee_tree.tag_configure("poor", background="#ffe6e6")
        
        oee_tree.pack(fill=BOTH, expand=True, pady=(0, 10))


class TemplateSelectionDialog:
    """Factory template selection dialog"""
    
    def __init__(self, parent, factory: Factory, on_template_selected: Callable = None):
        self.factory = factory
        self.on_template_selected = on_template_selected
        
        # Create dialog
        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("Select Factory Template")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Template selection
        self.create_template_selection(main_frame)
        self.create_preview_section(main_frame)
        self.create_action_buttons(main_frame)
        
        # Variables
        self.selected_template = tk.StringVar()
    
    def create_template_selection(self, parent):
        """Create template selection section"""
        selection_frame = ttk.LabelFrame(parent, text="Available Templates", padding=15)
        selection_frame.pack(fill=X, pady=(0, 15))
        
        templates = DefaultFactoryTemplates.get_template_names()
        
        for template in templates:
            rb = ttk.Radiobutton(selection_frame, text=template, variable=self.selected_template,
                                value=template, command=self.update_preview)
            rb.pack(anchor=W, pady=2)
        
        # Set default selection
        if templates:
            self.selected_template.set(templates[0])
    
    def create_preview_section(self, parent):
        """Create template preview section"""
        self.preview_frame = ttk.LabelFrame(parent, text="Template Preview", padding=15)
        self.preview_frame.pack(fill=BOTH, expand=True, pady=(0, 15))
        
        self.preview_text = tk.Text(self.preview_frame, height=8, wrap=tk.WORD, font=("Courier", 9))
        self.preview_text.pack(fill=BOTH, expand=True)
        
        # Initial preview
        self.update_preview()
    
    def create_action_buttons(self, parent):
        """Create action buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=X)
        
        ttk.Button(button_frame, text="Apply Template", bootstyle="success",
                  command=self.apply_template).pack(side=RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", bootstyle="secondary",
                  command=self.dialog.destroy).pack(side=RIGHT)
    
    def update_preview(self):
        """Update template preview"""
        template_name = self.selected_template.get()
        if not template_name:
            return
        
        machines = DefaultFactoryTemplates.create_template_by_name(template_name)
        
        preview_text = f"Template: {template_name}\n"
        preview_text += f"Machines: {len(machines)}\n\n"
        
        for machine in machines:
            preview_text += f"• {machine.name} ({machine.machine_type})\n"
            preview_text += f"  Base Time: {machine.base_time} min\n"
            preview_text += f"  Setup Time: {machine.setup_time} min\n"
            preview_text += f"  Position: ({machine.x}, {machine.y})\n\n"
        
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(1.0, preview_text)
        self.preview_text.config(state=tk.DISABLED)
    
    def apply_template(self):
        """Apply selected template"""
        template_name = self.selected_template.get()
        if not template_name:
            messagebox.showerror("Error", "Please select a template")
            return
        
        # Confirm if factory has existing machines
        if self.factory.machines:
            if not messagebox.askyesno("Confirm", "This will replace all existing machines. Continue?"):
                return
        
        # Clear existing factory
        self.factory.machines.clear()
        
        # Apply template
        machines = DefaultFactoryTemplates.create_template_by_name(template_name)
        for machine in machines:
            self.factory.add_machine(machine)
        
        self.dialog.destroy()
        
        if self.on_template_selected:
            self.on_template_selected(template_name)
        
        messagebox.showinfo("Success", f"Template '{template_name}' applied successfully!")


class ExportDialog:
    """Data export dialog"""
    
    def __init__(self, parent, factory: Factory, sim_manager: SimulationManager):
        self.factory = factory
        self.sim_manager = sim_manager
        
        # Create dialog
        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("Export Data")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Create sections
        self.create_export_options(main_frame)
        self.create_action_buttons(main_frame)
        
        # Variables
        self.export_machines = tk.BoolVar(value=True)
        self.export_timeseries = tk.BoolVar(value=True)
        self.export_layout = tk.BoolVar(value=True)
    
    def create_export_options(self, parent):
        """Create export options"""
        options_frame = ttk.LabelFrame(parent, text="Export Options", padding=15)
        options_frame.pack(fill=BOTH, expand=True, pady=(0, 15))
        
        ttk.Checkbutton(options_frame, text="Machine Data (CSV)", 
                       variable=self.export_machines).pack(anchor=W, pady=5)
        ttk.Checkbutton(options_frame, text="Time Series Data (CSV)", 
                       variable=self.export_timeseries).pack(anchor=W, pady=5)
        ttk.Checkbutton(options_frame, text="Factory Layout (JSON)", 
                       variable=self.export_layout).pack(anchor=W, pady=5)
        
        # Status info
        status_text = f"Current simulation time: {self.sim_manager.current_time:.1f} min\n"
        status_text += f"Total machines: {len(self.factory.machines)}\n"
        status_text += f"Data points: {len(self.sim_manager.time_history)}"
        
        ttk.Label(options_frame, text=status_text, font=("Courier", 9)).pack(anchor=W, pady=(10, 0))
    
    def create_action_buttons(self, parent):
        """Create action buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=X)
        
        ttk.Button(button_frame, text="Export", bootstyle="success",
                  command=self.perform_export).pack(side=RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", bootstyle="secondary",
                  command=self.dialog.destroy).pack(side=RIGHT)
    
    def perform_export(self):
        """Perform the export operation"""
        from data_manager import DataExporter
        
        try:
            exporter = DataExporter(self.factory, self.sim_manager)
            exported_files = []
            
            if self.export_machines.get():
                filename = exporter.export_machine_data()
                exported_files.append(f"Machine Data: {filename}")
            
            if self.export_layout.get():
                filename = exporter.export_layout_config()
                exported_files.append(f"Layout: {filename}")
            
            if self.export_timeseries.get() and self.sim_manager.time_history:
                filename = exporter.export_timeseries_data()
                exported_files.append(f"Time Series: {filename}")
            
            if exported_files:
                file_list = "\n".join(exported_files)
                messagebox.showinfo("Export Success", f"Data exported successfully!\n\n{file_list}")
                self.dialog.destroy()
            else:
                messagebox.showwarning("No Export", "Please select at least one export option")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data:\n{str(e)}")


class ImportDialog:
    """Data import dialog"""
    
    def __init__(self, parent, factory: Factory, on_import_complete: Callable = None):
        self.factory = factory
        self.on_import_complete = on_import_complete
        
        # Create dialog
        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("Import Data")
        self.dialog.geometry("400x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Create sections
        self.create_import_options(main_frame)
        self.create_action_buttons(main_frame)
    
    def create_import_options(self, parent):
        """Create import options"""
        options_frame = ttk.LabelFrame(parent, text="Import Options", padding=15)
        options_frame.pack(fill=BOTH, expand=True, pady=(0, 15))
        
        ttk.Button(options_frame, text="Import Layout (JSON)", bootstyle="primary-outline",
                  command=self.import_json_layout).pack(fill=X, pady=5)
        ttk.Button(options_frame, text="Import Machines (CSV)", bootstyle="secondary-outline",
                  command=self.import_csv_machines).pack(fill=X, pady=5)
        
        # Warning
        warning_text = "⚠️ Importing will replace current factory configuration"
        ttk.Label(options_frame, text=warning_text, font=("Segoe UI", 9), 
                 foreground="#dc3545").pack(pady=(10, 0))
    
    def create_action_buttons(self, parent):
        """Create action buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=X)
        
        ttk.Button(button_frame, text="Close", bootstyle="secondary",
                  command=self.dialog.destroy).pack(side=RIGHT)
    
    def import_json_layout(self):
        """Import JSON layout file"""
        filename = filedialog.askopenfilename(
            title="Select JSON Layout File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                from data_manager import DataImporter
                importer = DataImporter(self.factory)
                
                if importer.import_layout_from_json(filename):
                    messagebox.showinfo("Import Success", "Layout imported successfully!")
                    self.dialog.destroy()
                    if self.on_import_complete:
                        self.on_import_complete("json")
                        
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import layout:\n{str(e)}")
    
    def import_csv_machines(self):
        """Import CSV machines file"""
        filename = filedialog.askopenfilename(
            title="Select CSV Machines File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                from data_manager import DataImporter
                importer = DataImporter(self.factory)
                
                if importer.import_machines_from_csv(filename):
                    messagebox.showinfo("Import Success", "Machines imported successfully!")
                    self.dialog.destroy()
                    if self.on_import_complete:
                        self.on_import_complete("csv")
                        
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import machines:\n{str(e)}")


class HelpDialog:
    """User guide dialog"""
    
    def __init__(self, parent):
        # Create dialog
        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("User Guide")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Create help content
        self.create_help_content(main_frame)
        
        ttk.Button(main_frame, text="Close", command=self.dialog.destroy).pack(pady=10)
    
    def create_help_content(self, parent):
        """Create help content"""
        help_text = """Factory RTS Simulation - User Guide

SIMULATION CONTROLS:
• Start/Pause/Resume/Stop simulation
• Adjust speed (0.1x to 5.0x)
• Real-time performance monitoring

MACHINE MANAGEMENT:
• Drag machines to reposition
• Double-click to configure
• Right-click for context menu
• Add/remove machines dynamically

JOB MANAGEMENT:
• Create jobs with custom batch sizes
• Set priority levels (Normal/High/Critical)
• Define multi-step production sequences
• Monitor job progress in real-time

ANALYTICS:
• Real-time throughput monitoring
• Utilization tracking per machine
• WIP (Work In Process) analysis
• Bottleneck detection
• OEE (Overall Equipment Effectiveness)

KEY METRICS:
• Cycle Time = Base Time + (Setup Time / Batch Size)
• Utilization = (Working Time / Total Time) × 100%
• Throughput = Total Output / Simulation Time
• WIP = Sum of all queues + active jobs

OPTIMIZATION TIPS:
• Balance machine utilization (60-80% ideal)
• Minimize WIP levels
• Identify and resolve bottlenecks
• Optimize batch sizes for setup time
• Monitor OEE for equipment effectiveness

DATA MANAGEMENT:
• Export simulation data (CSV, JSON)
• Import factory layouts
• Use templates for quick setup
• Save and load configurations

KEYBOARD SHORTCUTS:
• Ctrl+N: New factory
• Ctrl+O: Open layout
• Ctrl+S: Save layout
• Space: Start/Pause simulation
• Ctrl+R: Reset simulation
        """
        
        text_widget = tk.Text(main_frame, wrap=tk.WORD, font=("Segoe UI", 10))
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        text_widget.insert(tk.END, help_text.strip())
        text_widget.config(state=tk.DISABLED)


class AboutDialog:
    """About dialog"""
    
    def __init__(self, parent):
        # Create dialog
        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("About Factory RTS Simulation")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.resizable(False, False)
        
        main_frame = ttk.Frame(self.dialog, padding=30)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Factory RTS Simulation", 
                               font=("Segoe UI", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Version
        version_label = ttk.Label(main_frame, text="Version 2.0", 
                                 font=("Segoe UI", 12))
        version_label.pack(pady=(0, 20))
        
        # Description
        description = """A modern real-time factory simulation
with advanced analytics and optimization.

Features:
• Real-time discrete event simulation
• Modern UI with ttkbootstrap
• Advanced performance metrics
• Interactive factory layout
• Bottleneck detection
• OEE analysis

Built with Python, tkinter, and matplotlib"""
        
        desc_label = ttk.Label(main_frame, text=description, justify=CENTER)
        desc_label.pack(pady=(0, 20))
        
        # Close button
        ttk.Button(main_frame, text="Close", command=self.dialog.destroy).pack()


# Context menu helper
def create_machine_context_menu(parent, machine: Machine, callbacks: Dict[str, Callable]):
    """Create context menu for machine"""
    context_menu = tk.Menu(parent, tearoff=0)
    
    if "configure" in callbacks:
        context_menu.add_command(label="Configure", command=lambda: callbacks["configure"](machine))
    if "details" in callbacks:
        context_menu.add_command(label="View Details", command=lambda: callbacks["details"](machine))
    if "clear_queue" in callbacks:
        context_menu.add_command(label="Clear Queue", command=lambda: callbacks["clear_queue"](machine))
    
    context_menu.add_separator()
    
    if "delete" in callbacks:
        context_menu.add_command(label="Delete", command=lambda: callbacks["delete"](machine))
    
    return context_menu
