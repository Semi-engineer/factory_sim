"""
Main application module for Factory RTS Simulation
Brings together all components in a modular architecture
"""

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import time
from typing import Optional

# Import our modular components
from models import Factory, Machine
from simulation_engine import SimulationManager, SimulationThread, PerformanceAnalyzer
from gui_components import (
    ModernFactoryCanvas, ModernChartsPanel, LiveDashboard, 
    MachineTable, ControlPanel, StatusBar, QuickStatsPanel
)
from dialogs import (
    AddJobDialog, AddMachineDialog, MachineConfigDialog, MachineDetailsDialog,
    SuggestionsDialog, OEEAnalysisDialog, TemplateSelectionDialog,
    ExportDialog, ImportDialog, HelpDialog, AboutDialog, create_machine_context_menu
)
from data_manager import DefaultFactoryTemplates


class FactorySimulationApp:
    """Main application class with modular architecture"""
    
    def __init__(self):
        # Initialize core components
        self.factory = Factory()
        self.sim_manager = SimulationManager(self.factory)
        self.sim_thread = SimulationThread(self.sim_manager)
        
        # Create main window
        self.root = ttk.Window(themename="cosmo")
        self.root.title("Factory RTS Simulation - Modular Edition")
        self.root.geometry("1600x1000")
        self.root.minsize(1200, 800)
        
        # Update timer
        self.last_gui_update = 0
        self.gui_update_interval = 0.2  # Update GUI every 200ms
        
        # Initialize GUI components
        self.setup_gui()
        self.setup_callbacks()
        self.setup_default_factory()
        self.setup_event_handlers()
        
    def setup_gui(self):
        """Setup the main GUI layout"""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Top control panel
        self.control_panel = ControlPanel(main_container)
        self.control_panel.pack(fill=X, pady=(0, 10))
        
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(main_container, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        # Setup tabs
        self.setup_factory_tab()
        self.setup_analytics_tab()
        self.setup_machine_details_tab()
        
        # Status bar
        self.status_bar = StatusBar(main_container)
        self.status_bar.pack(fill=X)
        
        # Setup menu bar
        self.setup_menu_bar()
    
    def setup_factory_tab(self):
        """Setup factory layout tab"""
        factory_tab = ttk.Frame(self.notebook)
        self.notebook.add(factory_tab, text="Factory Layout")
        
        # Create paned window
        paned = ttk.PanedWindow(factory_tab, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # Factory canvas
        canvas_container = ttk.LabelFrame(paned, text="Factory Floor", padding=5)
        self.factory_canvas = ModernFactoryCanvas(canvas_container, self.factory, self.sim_manager)
        self.factory_canvas.pack(fill=BOTH, expand=True)
        paned.add(canvas_container, weight=3)
        
        # Side panel with dashboard and quick stats
        side_container = ttk.Frame(paned)
        paned.add(side_container, weight=1)
        
        self.dashboard = LiveDashboard(side_container, self.factory, self.sim_manager)
        self.dashboard.pack(fill=X, pady=(0, 10))
        
        self.quick_stats = QuickStatsPanel(side_container, self.factory, self.sim_manager)
        self.quick_stats.pack(fill=X)
    
    def setup_analytics_tab(self):
        """Setup analytics tab"""
        analytics_tab = ttk.Frame(self.notebook)
        self.notebook.add(analytics_tab, text="Analytics")
        
        self.charts_panel = ModernChartsPanel(analytics_tab, self.sim_manager)
        self.charts_panel.pack(fill=BOTH, expand=True, padx=5, pady=5)
    
    def setup_machine_details_tab(self):
        """Setup machine details tab"""
        details_tab = ttk.Frame(self.notebook)
        self.notebook.add(details_tab, text="Machine Details")
        
        self.machine_table = MachineTable(details_tab, self.factory, self.sim_manager)
        self.machine_table.pack(fill=BOTH, expand=True)
    
    def setup_callbacks(self):
        """Setup callbacks for all components"""
        # Control panel callbacks
        self.control_panel.start_callback = self.start_simulation
        self.control_panel.pause_callback = self.pause_simulation
        self.control_panel.resume_callback = self.resume_simulation
        self.control_panel.stop_callback = self.stop_simulation
        self.control_panel.speed_callback = self.set_simulation_speed
        self.control_panel.add_job_callback = self.show_add_job_dialog
        self.control_panel.add_machine_callback = self.show_add_machine_dialog
        self.control_panel.export_callback = self.show_export_dialog
        
        # Factory canvas callbacks
        self.factory_canvas.config_callback = self.show_machine_config_dialog
        
        # Dashboard callbacks
        self.dashboard.bottleneck_callback = self.find_bottleneck
        self.dashboard.suggestions_callback = self.show_suggestions_dialog
        self.dashboard.oee_callback = self.show_oee_dialog
        
        # Machine table callbacks
        self.machine_table.on_machine_select_callback = self.on_machine_selected
        self.machine_table.on_machine_configure_callback = self.show_machine_config_dialog
        
        # Simulation callbacks
        self.sim_manager.on_job_completed_callback = self.on_job_completed
        self.sim_manager.on_bottleneck_detected_callback = self.on_bottleneck_detected
        
        # Simulation thread callbacks
        self.sim_thread.on_fps_update_callback = self.on_fps_updated
    
    def setup_default_factory(self):
        """Setup default factory layout"""
        # Use simple line template as default
        machines = DefaultFactoryTemplates.create_simple_line()
        for machine in machines:
            self.factory.add_machine(machine)
        
        # Add some sample jobs
        self.sim_manager.add_sample_jobs()
    
    def setup_event_handlers(self):
        """Setup event handlers"""
        # Window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Keyboard shortcuts
        self.root.bind("<Control-n>", lambda e: self.new_factory())
        self.root.bind("<Control-o>", lambda e: self.show_import_dialog())
        self.root.bind("<Control-s>", lambda e: self.show_export_dialog())
        self.root.bind("<space>", lambda e: self.toggle_simulation())
        self.root.bind("<Control-r>", lambda e: self.reset_simulation())
        
        # Focus to enable keyboard shortcuts
        self.root.focus_set()
        
        # Start GUI update loop
        self.schedule_gui_updates()
    
    def setup_menu_bar(self):
        """Setup application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Factory", command=self.new_factory, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Import Layout", command=self.show_import_dialog, accelerator="Ctrl+O")
        file_menu.add_command(label="Export Data", command=self.show_export_dialog, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Load Template", command=self.show_template_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Simulation Menu
        sim_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Simulation", menu=sim_menu)
        sim_menu.add_command(label="Start", command=self.start_simulation)
        sim_menu.add_command(label="Pause", command=self.pause_simulation)
        sim_menu.add_command(label="Resume", command=self.resume_simulation)
        sim_menu.add_command(label="Stop", command=self.stop_simulation)
        sim_menu.add_separator()
        sim_menu.add_command(label="Reset", command=self.reset_simulation, accelerator="Ctrl+R")
        
        # Factory Menu
        factory_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Factory", menu=factory_menu)
        factory_menu.add_command(label="Add Job", command=self.show_add_job_dialog)
        factory_menu.add_command(label="Add Machine", command=self.show_add_machine_dialog)
        factory_menu.add_separator()
        factory_menu.add_command(label="Find Bottleneck", command=self.find_bottleneck)
        factory_menu.add_command(label="Optimization Suggestions", command=self.show_suggestions_dialog)
        
        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="OEE Analysis", command=self.show_oee_dialog)
        tools_menu.add_command(label="Performance Analytics", command=lambda: self.notebook.select(1))
        
        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self.show_help_dialog)
        help_menu.add_command(label="About", command=self.show_about_dialog)
    
    # Simulation Control Methods
    def start_simulation(self):
        """Start the simulation"""
        self.sim_manager.start()
        self.sim_thread.start()
        
        self.control_panel.set_simulation_state(True, False)
        self.status_bar.set_status("Running", "#28a745")
        self.status_bar.start_progress()
    
    def pause_simulation(self):
        """Pause the simulation"""
        self.sim_manager.pause()
        
        self.control_panel.set_simulation_state(True, True)
        self.status_bar.set_status("Paused", "#ffc107")
        self.status_bar.stop_progress()
    
    def resume_simulation(self):
        """Resume the simulation"""
        self.sim_manager.resume()
        
        self.control_panel.set_simulation_state(True, False)
        self.status_bar.set_status("Running", "#28a745")
        self.status_bar.start_progress()
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.sim_manager.stop()
        self.sim_thread.stop()
        
        self.control_panel.set_simulation_state(False, False)
        self.status_bar.set_status("Stopped", "#dc3545")
        self.status_bar.stop_progress()
    
    def reset_simulation(self):
        """Reset the simulation"""
        if messagebox.askyesno("Reset Simulation", "Reset all simulation data?"):
            self.stop_simulation()
            self.sim_manager.reset()
            self.sim_manager.add_sample_jobs()
    
    def toggle_simulation(self):
        """Toggle simulation start/pause"""
        if self.sim_manager.is_running:
            if self.sim_manager.is_paused:
                self.resume_simulation()
            else:
                self.pause_simulation()
        else:
            self.start_simulation()
    
    def set_simulation_speed(self, speed: float):
        """Set simulation speed"""
        self.sim_manager.set_speed(speed)
    
    # Dialog Methods
    def show_add_job_dialog(self):
        """Show add job dialog"""
        AddJobDialog(self.root, self.factory, self.on_job_created)
    
    def show_add_machine_dialog(self):
        """Show add machine dialog"""
        AddMachineDialog(self.root, self.factory, self.on_machine_created)
    
    def show_machine_config_dialog(self, machine: Machine):
        """Show machine configuration dialog"""
        MachineConfigDialog(self.root, machine, self.factory, self.on_machine_updated)
    
    def show_machine_details_dialog(self, machine: Machine):
        """Show machine details dialog"""
        MachineDetailsDialog(self.root, machine, self.sim_manager)
    
    def show_suggestions_dialog(self):
        """Show optimization suggestions dialog"""
        SuggestionsDialog(self.root, self.factory, self.sim_manager)
    
    def show_oee_dialog(self):
        """Show OEE analysis dialog"""
        OEEAnalysisDialog(self.root, self.factory, self.sim_manager)
    
    def show_template_dialog(self):
        """Show template selection dialog"""
        TemplateSelectionDialog(self.root, self.factory, self.on_template_applied)
    
    def show_export_dialog(self):
        """Show export dialog"""
        ExportDialog(self.root, self.factory, self.sim_manager)

    def show_import_dialog(self):
        """Show import dialog"""
        ImportDialog(self.root, self.factory, self.on_factory_imported)

    def show_help_dialog(self):
        """Show help dialog"""
        HelpDialog(self.root)

    def show_about_dialog(self):
        """Show about dialog"""
        AboutDialog(self.root)

    # Event Handlers and Callbacks
    def on_closing(self):
        """Handle window close event"""
        if messagebox.askokcancel("Quit", "Do you want to exit the simulation?"):
            self.sim_thread.stop()
            self.root.destroy()

    def on_job_created(self, job):
        """Callback when a new job is created"""
        self.sim_manager.add_job(job)
        self.status_bar.set_status("Job added", "#17a2b8")

    def on_machine_created(self, machine):
        """Callback when a new machine is created"""
        self.factory.add_machine(machine)
        self.status_bar.set_status("Machine added", "#17a2b8")
        self.factory_canvas.redraw()

    def on_machine_updated(self, machine):
        """Callback when a machine is updated"""
        self.factory_canvas.redraw()
        self.machine_table.refresh()

    def on_machine_selected(self, machine):
        """Callback when a machine is selected in the table"""
        self.show_machine_details_dialog(machine)

    def on_job_completed(self, job):
        """Callback when a job is completed"""
        self.status_bar.set_status(f"Job '{job.name}' completed", "#28a745")
        self.quick_stats.refresh()

    def on_bottleneck_detected(self, machine):
        """Callback when a bottleneck is detected"""
        self.status_bar.set_status(f"Bottleneck: {machine.name}", "#ffc107")
        self.dashboard.highlight_bottleneck(machine)

    def find_bottleneck(self):
        """Find and highlight bottleneck machine"""
        bottleneck = self.sim_manager.find_bottleneck()
        if bottleneck:
            self.factory_canvas.highlight_machine(bottleneck)
            self.status_bar.set_status(f"Bottleneck: {bottleneck.name}", "#ffc107")
        else:
            self.status_bar.set_status("No bottleneck detected", "#17a2b8")

    def on_template_applied(self, machines):
        """Callback when a template is applied"""
        self.factory.clear()
        for machine in machines:
            self.factory.add_machine(machine)
        self.sim_manager.reset()
        self.sim_manager.add_sample_jobs()
        self.factory_canvas.redraw()
        self.machine_table.refresh()
        self.status_bar.set_status("Template applied", "#17a2b8")

    def on_factory_imported(self, machines, jobs):
        """Callback when a factory layout is imported"""
        self.factory.clear()
        for machine in machines:
            self.factory.add_machine(machine)
        self.sim_manager.reset()
        for job in jobs:
            self.sim_manager.add_job(job)
        self.factory_canvas.redraw()
        self.machine_table.refresh()
        self.status_bar.set_status("Factory imported", "#17a2b8")

    def on_fps_updated(self, fps):
        """Callback for FPS updates from simulation thread"""
        self.status_bar.set_fps(fps)

    def schedule_gui_updates(self):
        """Schedule periodic GUI updates"""
        self.update_gui()
        self.root.after(int(self.gui_update_interval * 1000), self.schedule_gui_updates)

    def update_gui(self):
        """Update GUI components periodically"""
        now = time.time()
        if now - self.last_gui_update >= self.gui_update_interval:
            self.factory_canvas.redraw()  # Changed from update() to redraw()
            self.dashboard.refresh()
            self.quick_stats.refresh()
            self.machine_table.refresh()
            self.status_bar.update()
            self.last_gui_update = now

    def run(self):
        """Run the main application loop"""
        self.root.mainloop()

    def new_factory(self):
        """Create a new factory layout (reset everything)"""
        if messagebox.askyesno("New Factory", "Start a new factory? This will clear the current layout and jobs."):
            self.stop_simulation()
            self.factory.clear()
            self.sim_manager.reset()
            self.setup_default_factory()
            self.factory_canvas.redraw()
            self.machine_table.refresh()
            self.status_bar.set_status("New factory created", "#17a2b8")


if __name__ == "__main__":
    app = FactorySimulationApp()
    app.run()