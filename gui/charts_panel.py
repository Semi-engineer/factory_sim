"""
Charts panel for displaying analytics and performance metrics
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import time
from typing import Optional
from simulation.simulation_manager import SimulationManager


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
            ax.set_facecolor('#fafafa')
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().configure(bg='white')
        
        # Performance optimization
        self.last_update_time = 0
        self.update_interval = 1.0  # Update every 1 second
        
        # Chart data cache
        self._cached_plots = {}
        
    def pack(self, **kwargs):
        """Pack the canvas widget"""
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
            machines = list(self.sim_manager.factory.machines.values())
            machine_names = [m.name for m in machines]
            machine_utils = [m.get_utilization(self.sim_manager.current_time) for m in machines]
            
            bars = self.ax4.bar(machine_names, machine_utils, 
                              color=['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1', '#fd7e14'][:len(machines)])
            
            self.ax4.set_title('Machine Utilization', fontweight='bold', pad=15)
            self.ax4.set_ylabel('Utilization (%)')
            self.ax4.set_ylim(0, 100)
            self.ax4.tick_params(axis='x', rotation=45)
            
            # Add value labels on bars
            for bar, util in zip(bars, machine_utils):
                height = bar.get_height()
                self.ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                            f'{util:.1f}%', ha='center', va='bottom', fontsize=8)
        
        # Redraw canvas
        self.canvas.draw_idle()  # Use idle draw for better performance
        self.last_update_time = current_time
    
    def save_charts(self, filename: str):
        """บันทึกกราฟเป็นไฟล์"""
        try:
            self.fig.savefig(filename, dpi=300, bbox_inches='tight')
            return True
        except Exception as e:
            print(f"Error saving charts: {e}")
            return False
    
    def clear_charts(self):
        """ล้างกราฟทั้งหมด"""
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.clear()
            ax.grid(True, alpha=0.3)
            ax.set_facecolor('#fafafa')
        
        self.canvas.draw_idle()
    
    def get_chart_summary(self) -> dict:
        """ได้สรุปข้อมูลกราฟ"""
        if not self.sim_manager.time_history:
            return {}
        
        latest_metrics = self.sim_manager.get_latest_metrics()
        
        return {
            "latest_throughput": latest_metrics["throughput"],
            "latest_utilization": latest_metrics["utilization"],
            "latest_wip": latest_metrics["wip"],
            "simulation_time": latest_metrics["time"],
            "data_points": len(self.sim_manager.time_history),
            "max_throughput": max(self.sim_manager.throughput_history) if self.sim_manager.throughput_history else 0,
            "max_utilization": max(self.sim_manager.utilization_history) if self.sim_manager.utilization_history else 0,
            "max_wip": max(self.sim_manager.wip_history) if self.sim_manager.wip_history else 0
        }
