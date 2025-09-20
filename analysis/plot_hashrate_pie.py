#!/usr/bin/env python3
"""
Script to display hashrate distribution as a pie chart

Visualizes the hashrate values set in blockchain-simulator.cpp.
- Miner 0-9: Fixed values from real data
- Miner 10-999: Remaining percentage distributed equally
"""

import matplotlib.pyplot as plt
import numpy as np

# Font settings
plt.rcParams['font.family'] = ['DejaVu Sans']

def calculate_hashrate_distribution():
    """
    Calculate hashrate distribution using the same logic as blockchain-simulator.cpp
    """
    node_count = 1000
    
    # Fixed hashrates for the first 10 miners (from C++ code)
    fixed_hashrates = [
        27.9383,  # Miner 0
        15.3179,  # Miner 1
        12.4277,  # Miner 2
        10.9827,  # Miner 3
        8.47784,  # Miner 4
        4.62428,  # Miner 5
        4.04624,  # Miner 6
        3.85356,  # Miner 7
        2.40848,  # Miner 8
        1.92678   # Miner 9
    ]
    
    # Sum of fixed hashrates
    hashrate_sum = sum(fixed_hashrates)
    print(f"Sum of fixed hashrates: {hashrate_sum}")
    
    # Hashrate for each remaining miner (10-999)
    remaining_miners = node_count - 10
    remaining_hashrate_per_miner = (100 - hashrate_sum) / remaining_miners
    print(f"Hashrate per remaining miner: {remaining_hashrate_per_miner}")
    
    return fixed_hashrates, remaining_hashrate_per_miner, remaining_miners

def create_pie_chart():
    """
    Create pie chart of hashrate distribution
    """
    fixed_hashrates, remaining_per_miner, remaining_miners = calculate_hashrate_distribution()
    
    # Prepare data for pie chart
    labels = []
    sizes = []
    colors = []
    
    # Data for top miners (individual display)
    for i, hashrate in enumerate(fixed_hashrates):
        labels.append(f'miner {i}')
        sizes.append(hashrate)
    
    # Display remaining miners together
    total_remaining = remaining_per_miner * remaining_miners
    labels.append(f'Other miners\n(miner 10-999)')
    sizes.append(total_remaining)
    
    # Color palette settings (improved for better distinction)
    miner_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                    '#8c564b', '#e377c2', '#17becf', '#bcbd22', '#ff9896']  # 10色に拡張
    # Add light gray color for "Other Miners"
    colors = miner_colors + ['#d0d0d0']  # 薄いグレーに変更
    
    # For clockwise display starting from 12 o'clock position
    # No need to reverse - we'll use counterclock=False and adjust startangle
    
    # Create pie chart
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Set explode to emphasize top miners
    explode = [0.05 if size > 10 else 0.02 for size in sizes[:-1]] + [0]  # Don't separate the last "Others"
    
    # Display all labels for miners 0-9
    display_labels = labels
    
    # Create custom autopct function to show percentages for all miners
    def autopct_func(pct):
        return f'{pct:.2f}%'
    
    wedges, texts, autotexts = ax.pie(sizes, labels=display_labels, autopct=autopct_func, 
                                     startangle=90, colors=colors, explode=explode,
                                     textprops={'fontsize': 14}, counterclock=False)
    
    # Add legend for hashrate distribution
    legend_labels = []
    for i, hashrate in enumerate(fixed_hashrates):
        legend_labels.append(f'miner {i}: {hashrate:.3f}%')
    
    # Add entry for other miners
    legend_labels.append(f'miner 10-999: total {total_remaining:.3f}%')
    
    # Place legend on the right side
    ax.legend(wedges, legend_labels, title="Hashrate Distribution", loc="center left", 
              bbox_to_anchor=(1, 0.5, 0.5, 0.5), fontsize=14, title_fontsize=16)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save graph in PNG, SVG, and PDF formats
    output_png = '/home/motemotech/code/univ/ensyuu/sakurai/washiblock/analysis/hashrate_distribution.png'
    output_svg = '/home/motemotech/code/univ/ensyuu/sakurai/washiblock/analysis/hashrate_distribution.svg'
    output_pdf = '/home/motemotech/code/univ/ensyuu/sakurai/washiblock/analysis/hashrate_distribution.pdf'
    
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.savefig(output_svg, format='svg', bbox_inches='tight')
    plt.savefig(output_pdf, format='pdf', bbox_inches='tight')
    
    print(f"Pie chart saved: {output_png}")
    print(f"Pie chart saved: {output_svg}")
    print(f"Pie chart saved: {output_pdf}")
    
    # Display graph
    plt.show()

def print_statistics():
    """
    Display statistical information of hashrate distribution
    """
    fixed_hashrates, remaining_per_miner, remaining_miners = calculate_hashrate_distribution()
    
    print("\n=== Hashrate Distribution Statistics ===")
    print(f"Total miners: 1000")
    print(f"Top miners: 10")
    print(f"Other miners: {remaining_miners}")
    print()
    
    print("Top miners hashrate:")
    for i, hashrate in enumerate(fixed_hashrates):
        print(f"  miner {i}: {hashrate:.3f}%")
    
    total_fixed = sum(fixed_hashrates)
    total_remaining = remaining_per_miner * remaining_miners
    
    print(f"\nTop miners total: {total_fixed:.3f}%")
    print(f"Other miners total: {total_remaining:.3f}%")
    print(f"Grand total: {total_fixed + total_remaining:.3f}%")
    print(f"Per other miner: {remaining_per_miner:.6f}%")
    
    # Concentration analysis
    print(f"\nConcentration analysis:")
    print(f"Top 1 miner share: {fixed_hashrates[0]:.3f}%")
    print(f"Top 3 miners share: {sum(fixed_hashrates[:3]):.3f}%")
    print(f"Top 5 miners share: {sum(fixed_hashrates[:5]):.3f}%")
    print(f"Top 10 miners share: {sum(fixed_hashrates):.3f}%")

if __name__ == "__main__":
    print("Hashrate Distribution Pie Chart Generator")
    print("=" * 50)
    
    # Display statistical information
    print_statistics()
    
    # Create pie chart
    print("\nCreating pie chart...")
    create_pie_chart()
    
    print("\nProcess completed!")
