#!/usr/bin/env python3
"""
Script to display hashrate distribution as a pie chart

Visualizes the hashrate values set in washiblock.cpp.
- Node 0-8: Fixed values
- Node 9-999: Remaining percentage distributed equally
"""

import matplotlib.pyplot as plt
import numpy as np

# Font settings
plt.rcParams['font.family'] = ['DejaVu Sans']

def calculate_hashrate_distribution():
    """
    Calculate hashrate distribution using the same logic as washiblock.cpp
    """
    node_count = 1000
    
    # Fixed hashrates for the first 9 nodes (from C++ code)
    fixed_hashrates = [
        16.534,  # Node 0
        12.56,   # Node 1
        11.288,  # Node 2
        2.226,   # Node 3
        1.272,   # Node 4
        0.636,   # Node 5
        0.318,   # Node 6
        0.318,   # Node 7
        0.159    # Node 8
    ]
    
    # Sum of fixed hashrates
    hashrate_sum = sum(fixed_hashrates)
    print(f"Sum of fixed hashrates: {hashrate_sum}")
    
    # Hashrate for each remaining node (9-999)
    remaining_nodes = node_count - 9
    remaining_hashrate_per_node = (100 - hashrate_sum) / remaining_nodes
    print(f"Hashrate per remaining node: {remaining_hashrate_per_node}")
    
    return fixed_hashrates, remaining_hashrate_per_node, remaining_nodes

def create_pie_chart():
    """
    Create pie chart of hashrate distribution
    """
    fixed_hashrates, remaining_per_node, remaining_nodes = calculate_hashrate_distribution()
    
    # Prepare data for pie chart
    labels = []
    sizes = []
    colors = []
    
    # Data for top nodes (individual display)
    for i, hashrate in enumerate(fixed_hashrates):
        labels.append(f'Node {i}\n({hashrate:.3f}%)')
        sizes.append(hashrate)
    
    # Display remaining nodes together
    total_remaining = remaining_per_node * remaining_nodes
    labels.append(f'Other Nodes\n(Node 9-999)\n({total_remaining:.3f}%)')
    sizes.append(total_remaining)
    
    # Color palette settings (improved for better distinction)
    node_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                   '#8c564b', '#e377c2', '#17becf', '#bcbd22']  # Node 7を水色に変更
    # Add light gray color for "Other Nodes"
    colors = node_colors + ['#d0d0d0']  # 薄いグレーに変更
    
    # For clockwise display starting from 12 o'clock position
    # No need to reverse - we'll use counterclock=False and adjust startangle
    
    # Create pie chart
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Set explode to emphasize top nodes
    explode = [0.05 if size > 10 else 0.02 for size in sizes[:-1]] + [0]  # Don't separate the last "Others"
    
    # Create custom labels - hide labels for Node 4-8 to avoid overlap
    display_labels = []
    for i, label in enumerate(labels):
        if i >= 4 and i <= 8:  # Node 4-8
            display_labels.append('')  # Empty label
        else:
            display_labels.append(label)
    
    # Create custom autopct function to hide percentages for Node 4-8
    def autopct_func(pct):
        return f'{pct:.2f}%' if pct > 2.0 else ''  # Hide small percentages
    
    wedges, texts, autotexts = ax.pie(sizes, labels=display_labels, autopct=autopct_func, 
                                     startangle=90, colors=colors, explode=explode,
                                     textprops={'fontsize': 10}, counterclock=False)
    
    # Add legend for hashrate distribution
    legend_labels = []
    for i, hashrate in enumerate(fixed_hashrates):
        legend_labels.append(f'Node {i}: {hashrate:.3f}%')
    
    # Add entry for other nodes
    legend_labels.append(f'Node 9-999: each {remaining_per_node:.6f}%, total {total_remaining:.3f}%')
    
    # Place legend on the right side
    ax.legend(wedges, legend_labels, title="Hashrate Distribution", loc="center left", 
              bbox_to_anchor=(1, 0.5, 0.5, 0.5), fontsize=9)
    
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
    fixed_hashrates, remaining_per_node, remaining_nodes = calculate_hashrate_distribution()
    
    print("\n=== Hashrate Distribution Statistics ===")
    print(f"Total nodes: 1000")
    print(f"Top nodes: 9")
    print(f"Other nodes: {remaining_nodes}")
    print()
    
    print("Top nodes hashrate:")
    for i, hashrate in enumerate(fixed_hashrates):
        print(f"  Node {i}: {hashrate:.3f}%")
    
    total_fixed = sum(fixed_hashrates)
    total_remaining = remaining_per_node * remaining_nodes
    
    print(f"\nTop nodes total: {total_fixed:.3f}%")
    print(f"Other nodes total: {total_remaining:.3f}%")
    print(f"Grand total: {total_fixed + total_remaining:.3f}%")
    print(f"Per other node: {remaining_per_node:.6f}%")
    
    # Concentration analysis
    print(f"\nConcentration analysis:")
    print(f"Top 1 node share: {fixed_hashrates[0]:.3f}%")
    print(f"Top 3 nodes share: {sum(fixed_hashrates[:3]):.3f}%")
    print(f"Top 5 nodes share: {sum(fixed_hashrates[:5]):.3f}%")

if __name__ == "__main__":
    print("Hashrate Distribution Pie Chart Generator")
    print("=" * 50)
    
    # Display statistical information
    print_statistics()
    
    # Create pie chart
    print("\nCreating pie chart...")
    create_pie_chart()
    
    print("\nProcess completed!")
