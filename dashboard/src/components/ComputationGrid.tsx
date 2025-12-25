"use client";

import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface IssueData {
    pages: number[];
    isComplete: boolean;
    totalPages: number;
}

interface ComputationGridProps {
    data: Record<string, IssueData>;
}

const ComputationGrid: React.FC<ComputationGridProps> = ({ data }) => {
    const svgRef = useRef<SVGSVGElement>(null);

    const startYear = 1925;
    const startMonth = 8; // August
    const endYear = 2009;
    const endMonth = 5; // May

    const years = d3.range(startYear, endYear + 1);
    const months = d3.range(1, 13);

    const cellSize = 14;
    const margin = { top: 60, right: 40, bottom: 40, left: 80 };
    const width = years.length * cellSize + margin.left + margin.right;
    const height = months.length * cellSize + margin.top + margin.bottom;

    useEffect(() => {
        if (!svgRef.current) return;

        const svg = d3.select(svgRef.current);
        svg.selectAll('*').remove();

        const g = svg.append('g')
            .attr('transform', `translate(${margin.left}, ${margin.top})`);

        // Add Year labels (X axis) - Transposed
        g.selectAll('.year-label')
            .data(years)
            .enter()
            .append('text')
            .attr('x', (d, i) => i * cellSize + cellSize / 2)
            .attr('y', -10)
            .attr('text-anchor', 'start')
            .attr('transform', (d, i) => `rotate(-45, ${i * cellSize + cellSize / 2}, -10)`)
            .attr('class', 'text-[9px] fill-zinc-400 dark:fill-zinc-600 font-bold')
            .text((d) => (d % 5 === 0 || d === startYear || d === endYear) ? d : '');

        // Add Month labels (Y axis) - Transposed
        g.selectAll('.month-label')
            .data(months)
            .enter()
            .append('text')
            .attr('x', -10)
            .attr('y', (d, i) => i * cellSize + cellSize / 2)
            .attr('dy', '0.35em')
            .attr('text-anchor', 'end')
            .attr('class', 'text-[10px] fill-zinc-400 dark:fill-zinc-600 font-bold')
            .text((d) => d3.timeFormat('%B')(new Date(2000, d - 1)));

        // Draw the grid
        years.forEach((year, yearIdx) => {
            months.forEach((month, monthIdx) => {
                // Skip months before start and after end
                if (year === startYear && month < startMonth) return;
                if (year === endYear && month > endMonth) return;

                const issueId = `${year}-${month.toString().padStart(2, '0')}`;
                const issue = data[issueId];

                const cell = g.append('g')
                    .attr('transform', `translate(${yearIdx * cellSize}, ${monthIdx * cellSize})`);

                // Base rectangle (empty state)
                cell.append('rect')
                    .attr('width', cellSize - 1)
                    .attr('height', cellSize - 1)
                    .attr('rx', 0)
                    .attr('class', 'fill-zinc-100 dark:fill-zinc-900/50');

                if (issue) {
                    if (issue.isComplete) {
                        cell.select('rect')
                            .attr('class', 'fill-emerald-500');
                    } else if (issue.pages.length > 0) {
                        // Standard left-to-right fill within the cell
                        const totalPages = issue.totalPages || (Math.max(...issue.pages, 1) + 1);
                        const pWidth = (cellSize - 1) / totalPages;

                        cell.selectAll('.page-rect')
                            .data(issue.pages)
                            .enter()
                            .append('rect')
                            .attr('x', (d) => d * pWidth)
                            .attr('y', 0)
                            .attr('width', Math.max(pWidth, 0.5))
                            .attr('height', cellSize - 1)
                            .attr('class', 'fill-blue-500');
                    }
                }
            });
        });

    }, [data]);

    return (
        <div className="overflow-auto bg-background p-6 rounded-sm border border-border shadow-sm max-h-[70vh]">
            <svg
                ref={svgRef}
                width={width}
                height={height}
                className="mx-auto"
            />
        </div>
    );
};

export default ComputationGrid;
