#!/usr/bin/env python3
"""
Phase-Based Trading System for ARBTRONX
Implements structured 4-phase compounding plan with specific ROI targets
"""

import asyncio
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TradingPhase(Enum):
    PHASE_1 = "phase_1"  # $200 → $1,000
    PHASE_2 = "phase_2"  # $1,000 → $5,000
    PHASE_3 = "phase_3"  # $5,000 → $20,000
    PHASE_4 = "phase_4"  # $20,000 → $100,000
    COMPLETED = "completed"

@dataclass
class PhaseConfig:
    """Configuration for each trading phase"""
    phase: TradingPhase
    start_capital: float
    target_capital: float
    target_roi_per_cycle: float
    target_profit_per_cycle: float
    target_cycles: int
    max_duration_days: int
    risk_level: str
    grid_spacing_range: Tuple[float, float]
    max_concurrent_grids: int

@dataclass
class CycleResult:
    """Result of a completed trading cycle"""
    cycle_id: str
    phase: TradingPhase
    start_time: datetime
    end_time: datetime
    start_capital: float
    end_capital: float
    profit: float
    roi_percentage: float
    pairs_traded: List[str]
    success: bool
    notes: str

@dataclass
class PhaseProgress:
    """Progress tracking for current phase"""
    current_phase: TradingPhase
    phase_start_time: datetime
    start_capital: float
    current_capital: float
    target_capital: float
    completed_cycles: int
    target_cycles: int
    total_profit: float
    average_roi: float
    success_rate: float
    estimated_completion: Optional[datetime]
    days_elapsed: int
    cycles_per_week: float

class PhaseBasedTradingSystem:
    """Phase-based trading system with structured progression"""
    
    def __init__(self, smart_engine):
        self.smart_engine = smart_engine
        self.current_phase = TradingPhase.PHASE_1
        self.phase_start_time = datetime.now()
        self.start_capital = 200.0
        self.current_capital = 200.0
        
        # Phase configurations
        self.phase_configs = {
            TradingPhase.PHASE_1: PhaseConfig(
                phase=TradingPhase.PHASE_1,
                start_capital=200.0,
                target_capital=1000.0,
                target_roi_per_cycle=0.25,  # 25%
                target_profit_per_cycle=50.0,
                target_cycles=8,
                max_duration_days=45,  # ~6 weeks
                risk_level="conservative",
                grid_spacing_range=(0.3, 0.6),
                max_concurrent_grids=2
            ),
            TradingPhase.PHASE_2: PhaseConfig(
                phase=TradingPhase.PHASE_2,
                start_capital=1000.0,
                target_capital=5000.0,
                target_roi_per_cycle=0.25,  # 25%
                target_profit_per_cycle=250.0,
                target_cycles=8,
                max_duration_days=45,  # ~6 weeks
                risk_level="moderate",
                grid_spacing_range=(0.4, 0.7),
                max_concurrent_grids=3
            ),
            TradingPhase.PHASE_3: PhaseConfig(
                phase=TradingPhase.PHASE_3,
                start_capital=5000.0,
                target_capital=20000.0,
                target_roi_per_cycle=0.25,  # 25%
                target_profit_per_cycle=1250.0,
                target_cycles=6,
                max_duration_days=35,  # ~5 weeks
                risk_level="moderate",
                grid_spacing_range=(0.5, 0.8),
                max_concurrent_grids=4
            ),
            TradingPhase.PHASE_4: PhaseConfig(
                phase=TradingPhase.PHASE_4,
                start_capital=20000.0,
                target_capital=100000.0,
                target_roi_per_cycle=0.20,  # 20%
                target_profit_per_cycle=4000.0,
                target_cycles=6,
                max_duration_days=35,  # ~5 weeks
                risk_level="aggressive",
                grid_spacing_range=(0.6, 1.0),
                max_concurrent_grids=5
            )
        }
        
        # Tracking data
        self.completed_cycles: List[CycleResult] = []
        self.current_cycle_start: Optional[datetime] = None
        self.current_cycle_capital: float = 200.0
        
        # Performance metrics
        self.total_cycles_completed = 0
        self.total_profit = 0.0
        self.phase_transitions: List[Dict] = []
        
    async def initialize(self):
        """Initialize the phase-based trading system"""
        try:
            logger.info("📊 Initializing Phase-Based Trading System...")
            logger.info(f"🎯 Starting Phase 1: ${self.start_capital} → ${self.phase_configs[TradingPhase.PHASE_1].target_capital}")
            logger.info(f"📈 Target: {self.phase_configs[TradingPhase.PHASE_1].target_cycles} cycles @ 25% ROI each")
            
            # Start first cycle
            await self._start_new_cycle()
            
            # Start monitoring loop
            asyncio.create_task(self._phase_monitoring_loop())
            
            logger.info("✅ Phase-Based Trading System initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Phase-Based Trading System: {e}")
            return False
    
    async def _start_new_cycle(self):
        """Start a new trading cycle"""
        try:
            self.current_cycle_start = datetime.now()
            self.current_cycle_capital = self.current_capital
            
            config = self.phase_configs[self.current_phase]
            cycle_number = len([c for c in self.completed_cycles if c.phase == self.current_phase]) + 1
            
            logger.info(f"🚀 Starting {self.current_phase.value.upper()} Cycle #{cycle_number}")
            logger.info(f"   Capital: ${self.current_capital:.2f}")
            logger.info(f"   Target Profit: ${config.target_profit_per_cycle:.2f} (25% ROI)")
            logger.info(f"   Max Grids: {config.max_concurrent_grids}")
            
            # Configure smart engine for this phase
            await self._configure_smart_engine_for_phase()
            
        except Exception as e:
            logger.error(f"Error starting new cycle: {e}")
    
    async def _configure_smart_engine_for_phase(self):
        """Configure smart engine parameters for current phase"""
        try:
            config = self.phase_configs[self.current_phase]
            
            # Adjust grid parameters based on phase
            if hasattr(self.smart_engine, 'phase_config'):
                self.smart_engine.phase_config = {
                    'max_concurrent_grids': config.max_concurrent_grids,
                    'grid_spacing_range': config.grid_spacing_range,
                    'risk_level': config.risk_level,
                    'target_roi': config.target_roi_per_cycle,
                    'capital_per_grid': self.current_capital / config.max_concurrent_grids
                }
            
            logger.info(f"⚙️  Smart engine configured for {self.current_phase.value}")
            logger.info(f"   Risk level: {config.risk_level}")
            logger.info(f"   Grid spacing: {config.grid_spacing_range[0]}-{config.grid_spacing_range[1]}%")
            logger.info(f"   Capital per grid: ${self.current_capital / config.max_concurrent_grids:.2f}")
            
        except Exception as e:
            logger.error(f"Error configuring smart engine: {e}")
    
    async def complete_cycle(self, profit: float, pairs_traded: List[str], success: bool = True, notes: str = ""):
        """Complete current trading cycle and update progress"""
        try:
            if not self.current_cycle_start:
                logger.warning("No active cycle to complete")
                return
            
            # Calculate cycle metrics
            end_time = datetime.now()
            cycle_duration = end_time - self.current_cycle_start
            roi_percentage = (profit / self.current_cycle_capital) * 100
            
            # Create cycle result
            cycle_result = CycleResult(
                cycle_id=f"{self.current_phase.value}_cycle_{len(self.completed_cycles) + 1}",
                phase=self.current_phase,
                start_time=self.current_cycle_start,
                end_time=end_time,
                start_capital=self.current_cycle_capital,
                end_capital=self.current_cycle_capital + profit,
                profit=profit,
                roi_percentage=roi_percentage,
                pairs_traded=pairs_traded,
                success=success,
                notes=notes
            )
            
            # Update capital and tracking
            self.current_capital += profit
            self.total_profit += profit
            self.completed_cycles.append(cycle_result)
            self.total_cycles_completed += 1
            
            # Log cycle completion
            logger.info(f"✅ Cycle completed: {cycle_result.cycle_id}")
            logger.info(f"   Duration: {cycle_duration}")
            logger.info(f"   Profit: ${profit:.2f} ({roi_percentage:.1f}% ROI)")
            logger.info(f"   New Capital: ${self.current_capital:.2f}")
            
            # Check for phase advancement
            await self._check_phase_advancement()
            
            # Start next cycle if not completed
            if self.current_phase != TradingPhase.COMPLETED:
                await asyncio.sleep(5)  # Brief pause between cycles
                await self._start_new_cycle()
            
        except Exception as e:
            logger.error(f"Error completing cycle: {e}")
    
    async def _check_phase_advancement(self):
        """Check if current phase is complete and advance if needed"""
        try:
            config = self.phase_configs[self.current_phase]
            phase_cycles = [c for c in self.completed_cycles if c.phase == self.current_phase]
            
            # Check completion criteria
            capital_target_met = self.current_capital >= config.target_capital
            cycles_target_met = len(phase_cycles) >= config.target_cycles
            
            if capital_target_met or cycles_target_met:
                await self._advance_to_next_phase()
            
        except Exception as e:
            logger.error(f"Error checking phase advancement: {e}")
    
    async def _advance_to_next_phase(self):
        """Advance to the next trading phase"""
        try:
            old_phase = self.current_phase
            phase_duration = datetime.now() - self.phase_start_time
            
            # Record phase transition
            transition = {
                'from_phase': old_phase.value,
                'to_phase': None,
                'completion_time': datetime.now().isoformat(),
                'duration_days': phase_duration.days,
                'start_capital': self.phase_configs[old_phase].start_capital,
                'end_capital': self.current_capital,
                'total_profit': self.current_capital - self.phase_configs[old_phase].start_capital,
                'cycles_completed': len([c for c in self.completed_cycles if c.phase == old_phase])
            }
            
            # Determine next phase
            if self.current_phase == TradingPhase.PHASE_1:
                self.current_phase = TradingPhase.PHASE_2
            elif self.current_phase == TradingPhase.PHASE_2:
                self.current_phase = TradingPhase.PHASE_3
            elif self.current_phase == TradingPhase.PHASE_3:
                self.current_phase = TradingPhase.PHASE_4
            elif self.current_phase == TradingPhase.PHASE_4:
                self.current_phase = TradingPhase.COMPLETED
            
            transition['to_phase'] = self.current_phase.value
            self.phase_transitions.append(transition)
            
            # Log phase advancement
            logger.info(f"🎉 PHASE COMPLETED: {old_phase.value.upper()}")
            logger.info(f"   Duration: {phase_duration.days} days")
            logger.info(f"   Capital Growth: ${self.phase_configs[old_phase].start_capital:.2f} → ${self.current_capital:.2f}")
            logger.info(f"   Profit: ${self.current_capital - self.phase_configs[old_phase].start_capital:.2f}")
            
            if self.current_phase != TradingPhase.COMPLETED:
                logger.info(f"🚀 ADVANCING TO: {self.current_phase.value.upper()}")
                logger.info(f"   New Target: ${self.phase_configs[self.current_phase].target_capital:.2f}")
                self.phase_start_time = datetime.now()
            else:
                logger.info("🏆 ALL PHASES COMPLETED! Target of $100,000 reached!")
            
        except Exception as e:
            logger.error(f"Error advancing phase: {e}")
    
    async def _phase_monitoring_loop(self):
        """Monitor phase progress and provide updates"""
        while self.current_phase != TradingPhase.COMPLETED:
            try:
                await self._log_phase_progress()
                await asyncio.sleep(3600)  # Update every hour
            except Exception as e:
                logger.error(f"Phase monitoring error: {e}")
                await asyncio.sleep(3600)
    
    async def _log_phase_progress(self):
        """Log current phase progress"""
        try:
            config = self.phase_configs[self.current_phase]
            phase_cycles = [c for c in self.completed_cycles if c.phase == self.current_phase]
            
            progress_percentage = (self.current_capital / config.target_capital) * 100
            cycles_progress = (len(phase_cycles) / config.target_cycles) * 100
            
            logger.info(f"📊 {self.current_phase.value.upper()} Progress:")
            logger.info(f"   Capital: ${self.current_capital:.2f} / ${config.target_capital:.2f} ({progress_percentage:.1f}%)")
            logger.info(f"   Cycles: {len(phase_cycles)} / {config.target_cycles} ({cycles_progress:.1f}%)")
            
            if phase_cycles:
                avg_roi = sum(c.roi_percentage for c in phase_cycles) / len(phase_cycles)
                logger.info(f"   Average ROI: {avg_roi:.1f}%")
            
        except Exception as e:
            logger.error(f"Error logging phase progress: {e}")
    
    def get_phase_status(self) -> Dict:
        """Get comprehensive phase status"""
        try:
            config = self.phase_configs[self.current_phase]
            phase_cycles = [c for c in self.completed_cycles if c.phase == self.current_phase]
            
            # Calculate metrics
            days_elapsed = (datetime.now() - self.phase_start_time).days
            progress_percentage = (self.current_capital / config.target_capital) * 100
            cycles_progress = (len(phase_cycles) / config.target_cycles) * 100
            
            # Calculate performance metrics
            avg_roi = sum(c.roi_percentage for c in phase_cycles) / len(phase_cycles) if phase_cycles else 0
            success_rate = sum(1 for c in phase_cycles if c.success) / len(phase_cycles) * 100 if phase_cycles else 0
            cycles_per_week = len(phase_cycles) / max(days_elapsed / 7, 0.1)
            
            # Estimate completion
            remaining_cycles = config.target_cycles - len(phase_cycles)
            estimated_days_remaining = remaining_cycles / max(cycles_per_week / 7, 0.1) if cycles_per_week > 0 else None
            estimated_completion = datetime.now() + timedelta(days=estimated_days_remaining) if estimated_days_remaining else None
            
            return {
                'current_phase': self.current_phase.value,
                'phase_config': asdict(config),
                'progress': {
                    'current_capital': self.current_capital,
                    'target_capital': config.target_capital,
                    'progress_percentage': progress_percentage,
                    'completed_cycles': len(phase_cycles),
                    'target_cycles': config.target_cycles,
                    'cycles_progress': cycles_progress,
                    'days_elapsed': days_elapsed,
                    'max_duration_days': config.max_duration_days
                },
                'performance': {
                    'total_profit': self.total_profit,
                    'average_roi': avg_roi,
                    'success_rate': success_rate,
                    'cycles_per_week': cycles_per_week,
                    'estimated_completion': estimated_completion.isoformat() if estimated_completion else None
                },
                'recent_cycles': [asdict(c) for c in phase_cycles[-3:]],  # Last 3 cycles
                'phase_transitions': self.phase_transitions,
                'total_cycles_completed': self.total_cycles_completed,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting phase status: {e}")
            return {'error': str(e), 'current_phase': 'unknown'}
    
    def get_roadmap_progress(self) -> Dict:
        """Get overall roadmap progress across all phases"""
        try:
            total_target = 100000.0  # Final target
            overall_progress = (self.current_capital / total_target) * 100
            
            phase_summaries = []
            for phase in TradingPhase:
                if phase == TradingPhase.COMPLETED:
                    continue
                    
                config = self.phase_configs[phase]
                phase_cycles = [c for c in self.completed_cycles if c.phase == phase]
                
                if phase.value == self.current_phase.value:
                    status = "active"
                elif self.current_capital >= config.target_capital:
                    status = "completed"
                else:
                    status = "pending"
                
                phase_summaries.append({
                    'phase': phase.value,
                    'status': status,
                    'start_capital': config.start_capital,
                    'target_capital': config.target_capital,
                    'target_cycles': config.target_cycles,
                    'completed_cycles': len(phase_cycles),
                    'target_roi': config.target_roi_per_cycle * 100,
                    'actual_avg_roi': sum(c.roi_percentage for c in phase_cycles) / len(phase_cycles) if phase_cycles else 0
                })
            
            return {
                'overall_progress': overall_progress,
                'current_capital': self.current_capital,
                'target_capital': total_target,
                'total_cycles_completed': self.total_cycles_completed,
                'target_total_cycles': 28,
                'phase_summaries': phase_summaries,
                'estimated_duration_months': 3,  # 2-4 months target
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting roadmap progress: {e}")
            return {'error': str(e)}

# Global instance
phase_trading_system = None

def initialize_phase_trading_system(smart_engine):
    """Initialize the phase-based trading system"""
    global phase_trading_system
    phase_trading_system = PhaseBasedTradingSystem(smart_engine)
    return phase_trading_system
