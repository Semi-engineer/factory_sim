# Factory Simulation - Modern Edition

A modern real-time factory simulation with interactive GUI built using Python, tkinter, and ttkbootstrap.

## Features

- **Real-time simulation** of factory operations
- **Interactive factory layout** with drag-and-drop machine positioning
- **Performance analytics** with real-time charts
- **Modern GUI** using ttkbootstrap theme
- **Machine management** with different types (CNC, Lathe, Drill, Assembly, etc.)
- **Job scheduling** with priority-based queueing
- **Bottleneck detection** and optimization suggestions
- **Export capabilities** for data analysis

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Semi-engineer/factory_sim.git
cd factory_sim
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the main application:
```bash
python main.py
```

## Project Structure

```
factory_sim/
├── main.py                    # Main application entry point
├── requirements.txt           # Python dependencies
├── models/                    # Core data models
│   ├── __init__.py
│   ├── job.py                # Job class definition
│   ├── machine.py            # Machine class definition
│   └── factory.py            # Factory management class
├── simulation/                # Simulation logic
│   ├── __init__.py
│   └── simulation_manager.py # Simulation control and statistics
└── gui/                       # User interface components
    ├── __init__.py
    ├── factory_canvas.py     # Factory floor visualization
    └── charts_panel.py       # Analytics and charts
```

## Classes Overview

### Models
- **Job**: Represents a production job with batch size, priority, and machine sequence
- **Machine**: Represents factory machines with processing capabilities and statistics
- **Factory**: Manages all machines and jobs, handles routing and statistics

### Simulation
- **SimulationManager**: Controls simulation state, timing, and data collection

### GUI
- **ModernFactoryCanvas**: Interactive factory floor visualization
- **ModernChartsPanel**: Real-time performance charts and analytics

## Key Features

### Machine Types
- CNC machines
- Lathes
- Drill presses
- Assembly stations
- Inspection stations
- Packaging stations

### Job Management
- Priority-based job scheduling (Normal, High, Critical)
- Multi-step job routing through different machines
- Real-time progress tracking

### Analytics
- Throughput monitoring
- Machine utilization tracking
- Work-in-Process (WIP) levels
- Bottleneck identification

### User Interface
- Tabbed interface with Factory Layout, Analytics, and Machine Details
- Real-time dashboard with key metrics
- Interactive machine positioning
- Modern dark theme using ttkbootstrap

## Getting Started

1. **Start the application** by running `python main.py`
2. **Add jobs** using the "Add Job" button in the control panel
3. **Start simulation** with the play button
4. **Monitor performance** in the Analytics tab
5. **Adjust machine positions** by dragging them on the factory floor
6. **View detailed statistics** in the Machine Details tab

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Requirements

- Python 3.7+
- tkinter (usually comes with Python)
- ttkbootstrap
- matplotlib
- numpy

See `requirements.txt` for specific versions.
