"""
Job model for factory simulation
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Job:
    """งานที่ต้องผลิต - Enhanced with quality tracking"""
    id: int
    batch_size: int
    arrival_time: float
    required_machines: List[str]
    current_step: int = 0
    start_time: Optional[float] = None
    completion_time: Optional[float] = None
    priority: int = 1  # 1=Normal, 2=High, 3=Critical
    
    # Quality attributes
    is_defective: bool = False
    needs_rework: bool = False
    rework_count: int = 0
    
    # Cost tracking
    material_cost: float = 0.0
    processing_cost: float = 0.0
    total_cost: float = 0.0
    
    def get_priority_weight(self) -> float:
        """คำนวณน้ำหนักความสำคัญ"""
        priority_weights = {1: 1.0, 2: 1.5, 3: 2.0}
        return priority_weights.get(self.priority, 1.0)
    
    def is_completed(self) -> bool:
        """ตรวจสอบว่างานเสร็จสิ้นหรือไม่"""
        return self.completion_time is not None
    
    def get_processing_time(self) -> float:
        """คำนวณเวลาที่ใช้ในการประมวลผล"""
        if self.start_time and self.completion_time:
            return self.completion_time - self.start_time
        return 0.0
    
    def get_next_machine(self) -> Optional[str]:
        """ได้เครื่องจักรถัดไป"""
        if self.current_step < len(self.required_machines):
            return self.required_machines[self.current_step]
        return None
    
    def advance_step(self) -> bool:
        """ไปขั้นตอนถัดไป"""
        if self.current_step < len(self.required_machines):
            self.current_step += 1
            return True
        return False
    
    def get_progress_percentage(self) -> float:
        """คำนวณเปอร์เซ็นต์ความคืบหน้า"""
        if not self.required_machines:
            return 0.0
        return (self.current_step / len(self.required_machines)) * 100
    
    def __str__(self) -> str:
        return f"Job-{self.id} (Batch: {self.batch_size}, Priority: {self.priority})"
