"""
Result Visualizer
================

Generate publication-quality figures from experimental data.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from braas.core.enums import ExperimentType
from braas.pipeline.analysis.processor import ELISAResult, qPCRResult, CellViabilityResult


# -----------------------------------------------------------------------------
# Figure Configuration
# -----------------------------------------------------------------------------

# Publication quality settings
FIGURE_DPI = 300
FIGURE_FORMAT = 'png'
FONT_FAMILY = 'Times New Roman'
FONT_SIZE = 10

# Color schemes
COLORS = {
    'primary': '#2C3E50',
    'secondary': '#7F8C8D',
    'accent': '#E74C3C',
    'success': '#27AE60',
    'warning': '#F39C12',
    'error': '#C0392B',
}


def configure_matplotlib() -> None:
    """Configure matplotlib for publication-quality figures."""
    plt.rcParams.update({
        'font.family': FONT_FAMILY,
        'font.size': FONT_SIZE,
        'axes.labelsize': FONT_SIZE,
        'axes.titlesize': FONT_SIZE + 2,
        'xtick.labelsize': FONT_SIZE - 1,
        'ytick.labelsize': FONT_SIZE - 1,
        'legend.fontsize': FONT_SIZE - 1,
        'figure.dpi': FIGURE_DPI,
        'savefig.dpi': FIGURE_DPI,
        'savefig.format': FIGURE_FORMAT,
        'axes.linewidth': 0.8,
        'axes.spines.top': False,
        'axes.spines.right': False,
    })


configure_matplotlib()


# -----------------------------------------------------------------------------
# Output Directory
# -----------------------------------------------------------------------------

def get_output_dir() -> Path:
    """Get or create the figures output directory."""
    output_dir = Path.home() / "braas-ai-pipeline" / "outputs" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


# -----------------------------------------------------------------------------
# Result Visualizer
# -----------------------------------------------------------------------------

class ResultVisualizer:
    """Generate publication-quality figures from analysis results."""
    
    def __init__(self, output_dir: Path | None = None) -> None:
        """Initialize the visualizer.
        
        Args:
            output_dir: Directory to save figures. Defaults to outputs/figures/
        """
        self._output_dir = output_dir or get_output_dir()
        self._default_figsize = (8, 6)
    
    def _generate_filename(self, prefix: str, experiment_type: str | None = None) -> str:
        """Generate unique filename for saved figure."""
        import uuid
        base = f"{prefix}"
        if experiment_type:
            base = f"{experiment_type}_{prefix}"
        unique_id = uuid.uuid4().hex[:8]
        return f"{base}_{unique_id}.{FIGURE_FORMAT}"
    
    def _save_figure(self, fig: plt.Figure, filename: str) -> str:
        """Save figure and return the path."""
        filepath = self._output_dir / filename
        fig.savefig(filepath, dpi=FIGURE_DPI, bbox_inches='tight', format=FIGURE_FORMAT)
        plt.close(fig)
        return str(filepath)
    
    def create_standard_curve(
        self,
        data: np.ndarray,
        experiment_type: ExperimentType | str
    ) -> str:
        """Create standard curve plot for ELISA or similar assays.
        
        Args:
            data: Array with [concentrations, absorbances]
            experiment_type: Type of experiment
        
        Returns:
            Path to saved PNG file
        """
        fig, ax = plt.subplots(figsize=self._default_figsize)
        
        concentrations = data[:, 0]
        absorbances = data[:, 1]
        
        # Plot data points
        ax.scatter(concentrations, absorbances, color=COLORS['primary'], 
                   s=60, zorder=5, label='Standards')
        
        # Fit and plot curve (4PL or polynomial)
        x_fit = np.linspace(min(concentrations), max(concentrations), 100)
        
        try:
            from scipy.optimize import curve_fit
            from braas.pipeline.analysis.processor import four_param_logistic
            
            popt, _ = curve_fit(four_param_logistic, concentrations, absorbances,
                               p0=[0, 1, np.median(concentrations), max(absorbances)],
                               maxfev=5000)
            y_fit = four_param_logistic(x_fit, *popt)
            fit_label = '4PL Fit'
        except Exception:
            # Fallback to polynomial
            coeffs = np.polyfit(concentrations, absorbances, 2)
            y_fit = np.polyval(coeffs, x_fit)
            fit_label = 'Polynomial Fit'
        
        ax.plot(x_fit, y_fit, color=COLORS['secondary'], linewidth=1.5,
                label=fit_label, linestyle='--')
        
        # Formatting
        ax.set_xlabel('Concentration (pg/mL)', fontweight='normal')
        ax.set_ylabel('Absorbance (450nm)', fontweight='normal')
        ax.set_title('Standard Curve', fontweight='bold', pad=15)
        ax.legend(loc='best', frameon=False)
        ax.grid(True, alpha=0.3, linestyle=':')
        
        # Log scale for x-axis if appropriate
        if concentrations[-1] / concentrations[0] > 100:
            ax.set_xscale('log')
        
        plt.tight_layout()
        
        filename = self._generate_filename('standard_curve', str(experiment_type))
        return self._save_figure(fig, filename)
    
    def create_dose_response(self, ic50_data: np.ndarray) -> str:
        """Create dose-response curve plot.
        
        Args:
            ic50_data: Array with [concentration, viability_pct]
        
        Returns:
            Path to saved PNG file
        """
        fig, ax = plt.subplots(figsize=self._default_figsize)
        
        concentrations = ic50_data[:, 0]
        viability = ic50_data[:, 1]
        
        # Sort by concentration
        sort_idx = np.argsort(concentrations)
        concentrations = concentrations[sort_idx]
        viability = viability[sort_idx]
        
        # Plot data
        ax.plot(concentrations, viability, 'o-', color=COLORS['primary'],
                markersize=6, linewidth=1.5, label='Data')
        
        # Fit 4PL curve
        try:
            from scipy.optimize import curve_fit
            from braas.pipeline.analysis.processor import four_param_logistic
            
            popt, _ = curve_fit(
                four_param_logistic, concentrations, viability,
                p0=[100, 1, np.median(concentrations), 0],
                bounds=([0, 0, 0, 0], [100, 10, 1e6, 100]),
                maxfev=5000
            )
            
            x_fit = np.logspace(np.log10(min(concentrations)), 
                               np.log10(max(concentrations)), 100)
            y_fit = four_param_logistic(x_fit, *popt)
            
            ax.plot(x_fit, y_fit, '--', color=COLORS['secondary'],
                    linewidth=1.5, label='4PL Fit')
            
            # Mark IC50
            ic50 = popt[2]
            y_ic50 = four_param_logistic(ic50, *popt)
            ax.axhline(y=50, color=COLORS['warning'], linestyle=':', alpha=0.7)
            ax.axvline(x=ic50, color=COLORS['warning'], linestyle=':', alpha=0.7)
            ax.plot(ic50, y_ic50, 's', color=COLORS['accent'], markersize=10,
                   zorder=5, label=f'IC50 = {ic50:.2f}')
            
        except Exception:
            pass
        
        ax.set_xlabel('Concentration', fontweight='normal')
        ax.set_ylabel('Viability (%)', fontweight='normal')
        ax.set_title('Dose-Response Curve', fontweight='bold', pad=15)
        ax.legend(loc='best', frameon=False)
        ax.grid(True, alpha=0.3, linestyle=':')
        ax.set_xscale('log')
        
        plt.tight_layout()
        
        filename = self._generate_filename('dose_response')
        return self._save_figure(fig, filename)
    
    def create_bar_chart(self, group_data: dict[str, np.ndarray]) -> str:
        """Create bar chart with error bars for grouped data.
        
        Args:
            group_data: Dictionary mapping group names to value arrays
        
        Returns:
            Path to saved PNG file
        """
        fig, ax = plt.subplots(figsize=self._default_figsize)
        
        groups = list(group_data.keys())
        means = [np.mean(group_data[g]) for g in groups]
        stds = [np.std(group_data[g]) for g in groups]
        
        x_pos = np.arange(len(groups))
        bars = ax.bar(x_pos, means, yerr=stds, capsize=5,
                     color=[COLORS['primary']] * len(groups),
                     edgecolor='black', linewidth=0.8,
                     error_kw={'elinewidth': 1, 'capthick': 1})
        
        # Add value labels on bars
        for i, (bar, mean, std) in enumerate(zip(bars, means, stds)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + std + 1,
                   f'{mean:.1f}', ha='center', va='bottom', fontsize=9)
        
        ax.set_xticks(x_pos)
        ax.set_xticklabels(groups)
        ax.set_ylabel('Value', fontweight='normal')
        ax.set_title('Group Comparison', fontweight='bold', pad=15)
        ax.grid(True, alpha=0.3, linestyle=':', axis='y')
        
        # Add significance brackets if applicable
        n_groups = len(groups)
        if n_groups == 2:
            max_height = max(means) + max(stds)
            ax.annotate('', xy=(0, max_height * 1.1), xytext=(1, max_height * 1.1),
                       arrowprops=dict(arrowstyle='-', color='black'))
            ax.text(0.5, max_height * 1.15, '*', ha='center', fontsize=14)
        
        plt.tight_layout()
        
        filename = self._generate_filename('bar_chart')
        return self._save_figure(fig, filename)
    
    def create_heatmap(self, multi_param_data: np.ndarray) -> str:
        """Create heatmap for multi-parameter data.
        
        Args:
            multi_param_data: 2D array of values
        
        Returns:
            Path to saved PNG file
        """
        fig, ax = plt.subplots(figsize=self._default_figsize)
        
        # Create heatmap
        im = ax.imshow(multi_param_data, cmap='RdYlBu_r', aspect='auto')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label('Intensity', fontsize=9)
        
        # Add value annotations
        n_rows, n_cols = multi_param_data.shape
        for i in range(n_rows):
            for j in range(n_cols):
                value = multi_param_data[i, j]
                text_color = 'white' if value > np.mean(multi_param_data) else 'black'
                ax.text(j, i, f'{value:.1f}', ha='center', va='center',
                       color=text_color, fontsize=8)
        
        ax.set_xlabel('Condition', fontweight='normal')
        ax.set_ylabel('Biomarker', fontweight='normal')
        ax.set_title('Multi-Parameter Heatmap', fontweight='bold', pad=15)
        
        plt.tight_layout()
        
        filename = self._generate_filename('heatmap')
        return self._save_figure(fig, filename)
    
    def create_time_series(self, timecourse_data: np.ndarray) -> str:
        """Create time series plot for kinetic data.
        
        Args:
            timecourse_data: Array with [time, value, ...] or [time, value, sem]
        
        Returns:
            Path to saved PNG file
        """
        fig, ax = plt.subplots(figsize=self._default_figsize)
        
        time = timecourse_data[:, 0]
        
        if timecourse_data.shape[1] >= 3:
            # Has SEM - plot mean with error band
            mean_vals = timecourse_data[:, 1]
            sem_vals = timecourse_data[:, 2]
            
            ax.plot(time, mean_vals, 'o-', color=COLORS['primary'],
                   markersize=6, linewidth=1.5, label='Mean')
            ax.fill_between(time, mean_vals - sem_vals, mean_vals + sem_vals,
                          color=COLORS['primary'], alpha=0.2)
        else:
            # Single trace
            values = timecourse_data[:, 1]
            ax.plot(time, values, 'o-', color=COLORS['primary'],
                   markersize=6, linewidth=1.5)
        
        ax.set_xlabel('Time (hours)', fontweight='normal')
        ax.set_ylabel('Response', fontweight='normal')
        ax.set_title('Time Course', fontweight='bold', pad=15)
        ax.grid(True, alpha=0.3, linestyle=':')
        
        plt.tight_layout()
        
        filename = self._generate_filename('time_series')
        return self._save_figure(fig, filename)
    
    def create_qpcr_amplification(self, amp_data: np.ndarray) -> str:
        """Create qPCR amplification curve plot.
        
        Args:
            amp_data: Array with [cycle, fluorescence, ...]
        
        Returns:
            Path to saved PNG file
        """
        fig, ax = plt.subplots(figsize=self._default_figsize)
        
        cycles = amp_data[:, 0]
        n_samples = amp_data.shape[1] - 1
        
        # Plot each sample
        for i in range(n_samples):
            fluorescence = amp_data[:, i + 1]
            label = f'Sample {i + 1}' if n_samples <= 5 else None
            ax.plot(cycles, fluorescence, linewidth=1.2, label=label)
        
        # Calculate and plot threshold
        threshold = np.mean(fluorescence[:5]) * 10 if n_samples > 0 else 0.1
        ax.axhline(y=threshold, color=COLORS['error'], linestyle='--',
                  linewidth=1, label='Threshold')
        
        ax.set_xlabel('Cycle', fontweight='normal')
        ax.set_ylabel('Fluorescence', fontweight='normal')
        ax.set_title('qPCR Amplification Curves', fontweight='bold', pad=15)
        ax.legend(loc='best', frameon=False, ncol=2 if n_samples > 3 else 1)
        ax.grid(True, alpha=0.3, linestyle=':')
        
        # Set x-axis to use integers
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        
        plt.tight_layout()
        
        filename = self._generate_filename('qpcr_amplification')
        return self._save_figure(fig, filename)
    
    def create_elisa_results(self, elisa_result: ELISAResult) -> str:
        """Create comprehensive ELISA results plot with standard curve and sample concentrations.
        
        Args:
            elisa_result: ELISAResult from analysis
        
        Returns:
            Path to saved PNG file
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Panel 1: Standard curve
        std_params = elisa_result.std_curve_params
        if 'a' in std_params and 'b' in std_params:
            # Reconstruct standard curve from fit parameters
            # This is simplified - actual implementation would need concentration data
            x_range = np.logspace(-2, 4, 100)
            
            try:
                from braas.pipeline.analysis.processor import four_param_logistic
                a, b, c, d = std_params['a'], std_params['b'], std_params['c'], std_params['d']
                y_fit = four_param_logistic(x_range, a, b, c, d)
                ax1.plot(x_range, y_fit, '--', color=COLORS['secondary'], linewidth=1.5)
            except Exception:
                pass
        
        ax1.set_xlabel('Concentration (pg/mL)', fontweight='normal')
        ax1.set_ylabel('Absorbance (450nm)', fontweight='normal')
        ax1.set_title('Standard Curve', fontweight='bold', pad=10)
        ax1.set_xscale('log')
        ax1.grid(True, alpha=0.3, linestyle=':')
        
        # Add fit parameters text
        param_text = '\n'.join([
            f"a={std_params.get('a', 0):.2f}",
            f"b={std_params.get('b', 0):.2f}",
            f"c={std_params.get('c', 0):.2f}",
            f"d={std_params.get('d', 0):.2f}"
        ])
        ax1.text(0.95, 0.05, param_text, transform=ax1.transAxes,
                fontsize=8, verticalalignment='bottom', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Panel 2: Sample concentrations
        concentrations = elisa_result.concentrations
        if len(concentrations) > 0:
            ax2.bar(range(len(concentrations)), concentrations,
                   color=COLORS['primary'], edgecolor='black', linewidth=0.8)
            ax2.axhline(y=np.mean(concentrations), color=COLORS['success'],
                       linestyle='--', linewidth=1.5, label=f'Mean: {np.mean(concentrations):.2f}')
            ax2.legend(loc='best', frameon=False)
        else:
            ax2.text(0.5, 0.5, 'No sample data', transform=ax2.transAxes,
                    ha='center', va='center')
        
        ax2.set_xlabel('Sample', fontweight='normal')
        ax2.set_ylabel('Concentration (pg/mL)', fontweight='normal')
        ax2.set_title('Sample Concentrations', fontweight='bold', pad=10)
        ax2.grid(True, alpha=0.3, linestyle=':', axis='y')
        
        # Add quality metrics
        quality_text = f'LOD: {elisa_result.lod:.3f}\nLOQ: {elisa_result.loq:.3f}\nCV: {elisa_result.cv_percent:.1f}%'
        fig.text(0.02, 0.02, quality_text, fontsize=8,
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
        
        plt.tight_layout()
        
        filename = self._generate_filename('elisa_results')
        return self._save_figure(fig, filename)


# Need matplotlib
import matplotlib.pyplot as plt
