"""
Chart Generation Service for Audit Reports

Generates visual charts from audit data and returns them as base64-encoded images
that can be embedded directly in HTML and Word documents.
"""
import io
import base64
import logging
from typing import Dict, List, Optional, Any
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generate charts for audit reports."""
    
    # Andzen Brand Color System - 2022 Guidelines
    COLORS = {
        'black': '#000000',        # Andzen Black
        'charcoal': '#262626',     # Andzen Charcoal
        'green': '#65DA4F',        # Andzen Green (Primary)
        'white': '#FFFFFF',        # Andzen White
        'grey': '#B7B9BC',         # Accent Grey
        'orange': '#EB9E1D',       # Accent Orange
        'primary': '#262626',      # Dark backgrounds
        'secondary': '#65DA4F',    # Highlights
        'success': '#65DA4F',      # Positive metrics
        'warning': '#EB9E1D',      # Opportunities
        'danger': '#E74C3C',       # Critical issues
        'info': '#65DA4F',         # Information
        'gray': '#B7B9BC',         # Secondary text
        'light_gray': '#F5F5F5'    # Subtle backgrounds
    }
    
    ENGAGEMENT_COLORS = {
        'very_engaged': '#65DA4F',      # Andzen Green
        'somewhat_engaged': '#B7B9BC',  # Grey
        'barely_engaged': '#EB9E1D',    # Orange
        'not_engaged': '#262626'        # Charcoal
    }
    
    def __init__(self):
        """Initialize chart generator with Andzen brand settings."""
        self.dpi = 300  # High-quality charts
        self.fig_size = (12, 7)  # Generous sizing
        # Use clean, minimal style that we'll customize
        plt.style.use('seaborn-v0_8-whitegrid')
        
        # Set global font to match brand (Montserrat fallback to Arial)
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Montserrat', 'Arial', 'DejaVu Sans']
        plt.rcParams['font.size'] = 11
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['axes.titlesize'] = 16
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        plt.rcParams['legend.fontsize'] = 11
        plt.rcParams['figure.titlesize'] = 18
        
        # Brand colors for backgrounds and grids
        plt.rcParams['axes.facecolor'] = '#FFFFFF'
        plt.rcParams['figure.facecolor'] = '#FFFFFF'
        plt.rcParams['axes.edgecolor'] = '#262626'
        plt.rcParams['grid.color'] = '#E5E7EB'
        plt.rcParams['grid.alpha'] = 0.3
        plt.rcParams['axes.labelcolor'] = '#262626'
        plt.rcParams['xtick.color'] = '#262626'
        plt.rcParams['ytick.color'] = '#262626'
        plt.rcParams['text.color'] = '#262626'
    
    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string."""
        try:
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=self.dpi, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close(fig)
            return f"data:image/png;base64,{image_base64}"
        except Exception as e:
            logger.error(f"Error converting figure to base64: {e}")
            plt.close(fig)
            return ""
    
    def generate_engagement_breakdown_chart(
        self, 
        engagement_data: Dict[str, float],
        client_name: str = ""
    ) -> str:
        """
        Generate engagement breakdown line chart.
        
        Args:
            engagement_data: Dict with engagement percentages
                {
                    'very_engaged_pct': 25.5,
                    'somewhat_engaged_pct': 30.2,
                    'barely_engaged_pct': 20.1,
                    'not_engaged_pct': 24.2
                }
            client_name: Client name for chart title
        
        Returns:
            Base64-encoded image string
        """
        try:
            fig, ax = plt.subplots(figsize=self.fig_size)
            
            # Extract data
            categories = ['Very Engaged', 'Somewhat Engaged', 'Barely Engaged', 'Not Engaged']
            percentages = [
                engagement_data.get('very_engaged_pct', 0),
                engagement_data.get('somewhat_engaged_pct', 0),
                engagement_data.get('barely_engaged_pct', 0),
                engagement_data.get('not_engaged_pct', 0)
            ]
            
            # Colors for each segment
            colors = [
                self.ENGAGEMENT_COLORS['very_engaged'],
                self.ENGAGEMENT_COLORS['somewhat_engaged'],
                self.ENGAGEMENT_COLORS['barely_engaged'],
                self.ENGAGEMENT_COLORS['not_engaged']
            ]
            
            # Create bar chart (more readable than line for this data)
            x_pos = np.arange(len(categories))
            bars = ax.bar(x_pos, percentages, color=colors, alpha=0.8, edgecolor='black', linewidth=1.2)
            
            # Add value labels on top of bars
            for i, (bar, pct) in enumerate(zip(bars, percentages)):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{pct:.1f}%',
                       ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            # Add benchmark line (50% should be Very + Somewhat Engaged)
            healthy_engaged = percentages[0] + percentages[1]
            ax.axhline(y=50, color='gray', linestyle='--', linewidth=2, alpha=0.7, 
                      label=f'Healthy Benchmark (50%)\nYour Total: {healthy_engaged:.1f}%')
            
            # Styling
            ax.set_xlabel('Engagement Level', fontsize=12, fontweight='bold')
            ax.set_ylabel('Percentage of Database (%)', fontsize=12, fontweight='bold')
            title = f'{client_name} ' if client_name else ''
            ax.set_title(f'{title}List Engagement Breakdown', fontsize=14, fontweight='bold', pad=20)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(categories, rotation=0, ha='center')
            ax.set_ylim(0, max(percentages) * 1.2)
            ax.legend(loc='upper right', fontsize=9)
            ax.grid(True, alpha=0.3, axis='y')
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating engagement breakdown chart: {e}")
            return ""
    
    def generate_flow_performance_chart(
        self,
        flow_data: Dict[str, float],
        benchmarks: Dict[str, Dict[str, float]],
        flow_name: str = "Flow"
    ) -> str:
        """
        Generate flow performance comparison chart.
        
        Args:
            flow_data: Dict with flow metrics
                {
                    'open_rate': 45.2,
                    'click_rate': 12.5,
                    'conversion_rate': 3.8
                }
            benchmarks: Dict with benchmark data
                {
                    'average': {'open_rate': 40.0, 'click_rate': 10.0, 'conversion_rate': 3.0},
                    'top_10': {'open_rate': 55.0, 'click_rate': 15.0, 'conversion_rate': 5.0}
                }
            flow_name: Name of the flow
        
        Returns:
            Base64-encoded image string
        """
        try:
            fig, ax = plt.subplots(figsize=self.fig_size)
            
            # Metrics to display
            metrics = ['Open Rate', 'Click Rate', 'Conversion Rate']
            metric_keys = ['open_rate', 'click_rate', 'conversion_rate']
            
            # Extract data
            flow_values = [flow_data.get(key, 0) for key in metric_keys]
            avg_values = [benchmarks.get('average', {}).get(key, 0) for key in metric_keys]
            top10_values = [benchmarks.get('top_10', {}).get(key, 0) for key in metric_keys]
            
            # Set up bar positions
            x = np.arange(len(metrics))
            width = 0.25
            
            # Create grouped bars with Andzen brand colors
            bars1 = ax.bar(x - width, flow_values, width, label=f'{flow_name}', 
                          color=self.COLORS['green'], alpha=1.0, edgecolor='#000000', linewidth=1.5)
            bars2 = ax.bar(x, avg_values, width, label='Industry Average',
                          color=self.COLORS['grey'], alpha=0.7, edgecolor='#262626', linewidth=1)
            bars3 = ax.bar(x + width, top10_values, width, label='Top 10%',
                          color=self.COLORS['charcoal'], alpha=0.9, edgecolor='#000000', linewidth=1)
            
            # Add value labels on bars
            def add_labels(bars):
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}%',
                           ha='center', va='bottom', fontsize=9, fontweight='bold')
            
            add_labels(bars1)
            add_labels(bars2)
            add_labels(bars3)
            
            # Styling
            ax.set_xlabel('Performance Metrics', fontsize=12, fontweight='bold')
            ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold')
            ax.set_title(f'{flow_name} Performance vs Benchmarks', fontsize=14, fontweight='bold', pad=20)
            ax.set_xticks(x)
            ax.set_xticklabels(metrics)
            ax.legend(loc='upper left', fontsize=10)
            ax.grid(True, alpha=0.3, axis='y')
            ax.set_ylim(0, max(max(flow_values), max(avg_values), max(top10_values)) * 1.25)
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating flow performance chart: {e}")
            return ""
    
    def generate_kav_revenue_chart(
        self,
        kav_data: Dict[str, Any],
        client_name: str = ""
    ) -> str:
        """
        Generate KAV revenue breakdown chart (Campaigns vs Flows).
        
        Args:
            kav_data: Dict with KAV metrics
                {
                    'campaign_revenue': 150000,
                    'flow_revenue': 100000,
                    'campaign_pct': 60.0,
                    'flow_pct': 40.0,
                    'total_revenue': 250000
                }
            client_name: Client name for chart title
        
        Returns:
            Base64-encoded image string
        """
        try:
            logger.info(f"Starting KAV chart generation - campaign: {kav_data.get('campaign_revenue', 0)}, flow: {kav_data.get('flow_revenue', 0)}")
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
            
            # Extract data
            campaign_rev = kav_data.get('campaign_revenue', 0)
            flow_rev = kav_data.get('flow_revenue', 0)
            campaign_pct = kav_data.get('campaign_pct', 0)
            flow_pct = kav_data.get('flow_pct', 0)
            
            # Safety check
            if campaign_rev == 0 and flow_rev == 0:
                logger.warning("Both campaign and flow revenue are 0, skipping chart generation")
                plt.close(fig)
                return ""
            
            logger.info(f"Generating pie chart: {campaign_pct:.1f}% campaigns, {flow_pct:.1f}% flows")
            
            # Chart 1: Pie chart showing percentage breakdown with Andzen colors
            sizes = [campaign_pct, flow_pct]
            labels = [f'Campaigns\n{campaign_pct:.1f}%', f'Flows\n{flow_pct:.1f}%']
            colors = [self.COLORS['charcoal'], self.COLORS['green']]  # Andzen brand colors
            explode = (0.05, 0.05)
            
            wedges, texts, autotexts = ax1.pie(sizes, explode=explode, labels=labels, colors=colors,
                                               autopct='', startangle=90, 
                                               textprops={'fontsize': 12, 'fontweight': 'bold', 'color': '#FFFFFF'})
            ax1.set_title('Revenue Distribution', fontsize=14, fontweight='bold', pad=15, color='#262626')
            
            # Chart 2: Bar chart showing absolute revenue with brand colors
            categories = ['Campaigns', 'Flows']
            revenues = [campaign_rev, flow_rev]
            bars = ax2.bar(categories, revenues, color=colors, alpha=1.0, 
                          edgecolor='#000000', linewidth=1.5)
            
            # Add value labels
            for bar, rev in zip(bars, revenues):
                height = bar.get_height()
                label = f'${rev:,.0f}' if rev < 1000000 else f'${rev/1000:.1f}K'
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        label,
                        ha='center', va='bottom', fontsize=11, fontweight='bold')
            
            ax2.set_ylabel('Revenue ($)', fontsize=12, fontweight='bold')
            ax2.set_title('Revenue by Channel', fontsize=13, fontweight='bold', pad=15)
            ax2.grid(True, alpha=0.3, axis='y')
            ax2.set_ylim(0, max(revenues) * 1.2)
            
            # Overall title
            title = f'{client_name} ' if client_name else ''
            fig.suptitle(f'{title}KAV Revenue: Campaigns vs Flows', fontsize=15, fontweight='bold', y=0.98)
            
            plt.tight_layout()
            base64_img = self._fig_to_base64(fig)
            logger.info(f"✓ KAV chart generated successfully ({len(base64_img)} chars)")
            return base64_img
            
        except Exception as e:
            import traceback
            logger.error(f"✗ Error generating KAV revenue chart: {e}\n{traceback.format_exc()}")
            return ""
    
    def generate_flow_revenue_trend_chart(
        self,
        flows: List[Dict[str, Any]],
        top_n: int = 5
    ) -> str:
        """
        Generate horizontal bar chart showing top flows by revenue.
        
        Args:
            flows: List of flow dicts with 'name' and 'revenue'
            top_n: Number of top flows to display
        
        Returns:
            Base64-encoded image string
        """
        try:
            # Sort by revenue and get top N
            sorted_flows = sorted(flows, key=lambda x: x.get('revenue', 0), reverse=True)[:top_n]
            
            if not sorted_flows:
                return ""
            
            fig, ax = plt.subplots(figsize=(10, max(6, len(sorted_flows) * 0.8)))
            
            flow_names = [flow.get('name', 'Unknown') for flow in sorted_flows]
            revenues = [flow.get('revenue', 0) for flow in sorted_flows]
            
            # Create horizontal bar chart
            y_pos = np.arange(len(flow_names))
            colors = [self.COLORS['primary'] if i == 0 else self.COLORS['secondary'] 
                     for i in range(len(flow_names))]
            
            bars = ax.barh(y_pos, revenues, color=colors, alpha=0.8, edgecolor='black', linewidth=1)
            
            # Add value labels
            for i, (bar, rev) in enumerate(zip(bars, revenues)):
                width = bar.get_width()
                label = f'${rev:,.0f}' if rev < 1000000 else f'${rev/1000:.1f}K'
                ax.text(width, bar.get_y() + bar.get_height()/2.,
                       f' {label}',
                       ha='left', va='center', fontsize=10, fontweight='bold')
            
            # Styling
            ax.set_yticks(y_pos)
            ax.set_yticklabels(flow_names, fontsize=10)
            ax.set_xlabel('Revenue ($)', fontsize=12, fontweight='bold')
            ax.set_title(f'Top {len(sorted_flows)} Flows by Revenue', fontsize=14, fontweight='bold', pad=20)
            ax.grid(True, alpha=0.3, axis='x')
            ax.set_xlim(0, max(revenues) * 1.15)
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating flow revenue trend chart: {e}")
            return ""


# Singleton instance
_chart_generator = None

def get_chart_generator() -> ChartGenerator:
    """Get or create chart generator singleton."""
    global _chart_generator
    if _chart_generator is None:
        _chart_generator = ChartGenerator()
    return _chart_generator

