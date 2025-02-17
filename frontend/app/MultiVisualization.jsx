"use client";

import React, { useState } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell, ReferenceLine,
  ResponsiveContainer, ComposedChart
} from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';

const COLORS = [
  '#0088FE', '#00C49F', '#FFBB28', '#FF8042', 
  '#8884d8', '#82ca9d', '#ffc658', '#ff8042',
  '#00C49F', '#FFBB28', '#FF8042', '#0088FE'
];

/**
 * Process data for visualization.
 * Formats numeric fields, assigns a "name" (fallback from employeeName or x-axis),
 * and assigns a consistent color.
 */
const processData = (data, vizConfig) => {
    if (!data || !data.length) return [];
    const { axes } = vizConfig;
    return data.map((item, index) => {
      const processed = { ...item };
      Object.keys(item).forEach(key => {
        if (typeof item[key] === 'number' && item[key] !== null) {
          processed[key] = Number(item[key].toFixed(2));
        }
      });
      // Use detected x-axis field for name
      const xAxisKey = axes?.x ? axes.x.split(' as ')[0].trim() : null; // Handle aliases
      if (xAxisKey && item[xAxisKey] !== undefined) {
        processed.name = String(item[xAxisKey]);
      } else if (item.employeeName) {
        processed.name = item.employeeName;
      } else {
        processed.name = "N/A";
      }
      processed.color = COLORS[index % COLORS.length];
      return processed;
    });
  };

const ChartWrapper = ({ children }) => (
  <div className="w-full h-[500px]">
    <ResponsiveContainer>{children}</ResponsiveContainer>
  </div>
);

/**
 * MultiVisualization component receives:
 * - data: the query result rows,
 * - visualizations: an array of visualization configuration options,
 * - title: the title of the visualization.
 */
const MultiVisualization = ({ data, visualizations, title }) => {
  const [activeTab, setActiveTab] = useState("option-0");

  // Helper to render the chart/table based on the configuration.
  const renderChart = (vizConfig) => {
    const processedData = processData(data, vizConfig);
    // A helper to extract axis keys. If undefined, returns empty string.
    const getAxisKey = (key) => {
        if (!key) return "";
        // Remove "ASC" or "DESC" from the key, ignoring case
        return key.replace(/\s+(asc|desc)\s*$/i, "");
      };
    
    switch (vizConfig.type) {
      case 'bar':
        return (
          <ChartWrapper>
            <ComposedChart data={processedData} margin={{ top: 20, right: 30, left: 60, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} interval={0} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey={getAxisKey(vizConfig.axes.y)} fill="#0088FE">
                {processedData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Bar>
              {vizConfig.annotations && vizConfig.annotations.map((annotation, index) =>
                annotation.type === 'line' && (
                  <ReferenceLine
                    key={index}
                    y={annotation.value}
                    stroke={annotation.style.stroke}
                    strokeDasharray={annotation.style.strokeDasharray}
                    label={annotation.label}
                  />
                )
              )}
            </ComposedChart>
          </ChartWrapper>
        );
      case 'pie':
        return (
            <ChartWrapper>
            <PieChart>
              <Pie
                data={processedData}
                dataKey={getAxisKey(vizConfig.axes.y)}
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={200}
                innerRadius={vizConfig.settings?.donut ? 100 : 0}
                label={({ name, value, percent }) =>
                  `${name}: ${Number(value).toLocaleString()} (${(percent * 100).toFixed(1)}%)`
                }
              >
                {processedData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ChartWrapper>
        );
      case 'line':
        return (
          <ChartWrapper>
            <LineChart data={processedData} margin={{ top: 20, right: 30, left: 60, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} interval={0} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type={vizConfig.settings?.interpolation || "monotone"}
                dataKey={getAxisKey(vizConfig.axes.y)}
                stroke="#0088FE"
                dot={vizConfig.settings?.showPoints}
              />
              {vizConfig.annotations && vizConfig.annotations.map((annotation, index) =>
                annotation.type === 'line' && (
                  <ReferenceLine
                    key={index}
                    y={annotation.value}
                    stroke={annotation.style.stroke}
                    strokeDasharray={annotation.style.strokeDasharray}
                    label={annotation.label}
                  />
                )
              )}
            </LineChart>
          </ChartWrapper>
        );
      case 'scatter':
        return (
          <ChartWrapper>
            <ScatterChart margin={{ top: 20, right: 30, left: 60, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} interval={0} />
              <YAxis dataKey={getAxisKey(vizConfig.axes.y)} />
              <Tooltip />
              <Legend />
              <Scatter data={processedData} fill="#0088FE">
                {processedData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Scatter>
            </ScatterChart>
          </ChartWrapper>
        );
      case 'table':
      default:
        return (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {Object.keys(processedData[0] || {}).filter(key => !key.startsWith('_')).map(key => (
                    <th key={key} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {key}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {processedData.map((row, i) => (
                  <tr key={i}>
                    {Object.entries(row)
                      .filter(([key]) => !key.startsWith('_'))
                      .map(([key, value], j) => (
                        <td key={j} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {typeof value === 'number' ? value.toLocaleString() : value}
                        </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
    }
  };

  // Export CSV for the currently active visualization.
  const handleExport = () => {
    const currentViz = visualizations[parseInt(activeTab.split('-')[1], 10)];
    if (!currentViz) return;
    const processedData = processData(data, currentViz);
    const csv = [
      Object.keys(processedData[0]).filter(key => !key.startsWith('_')).join(','),
      ...processedData.map(row =>
        Object.entries(row)
          .filter(([key]) => !key.startsWith('_'))
          .map(([_, value]) => (typeof value === 'number' ? value : `"${value}"`))
          .join(',')
      )
    ].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.toLowerCase().replace(/\s+/g, '-')}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>{title}</CardTitle>
        <div className="flex space-x-2">
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            {visualizations.map((viz, index) => (
              <TabsTrigger key={index} value={`option-${index}`}>
                {viz.type.charAt(0).toUpperCase() + viz.type.slice(1)}
              </TabsTrigger>
            ))}
          </TabsList>
          {visualizations.map((viz, index) => (
            <TabsContent key={index} value={`option-${index}`}>
              {renderChart(viz)}
            </TabsContent>
          ))}
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default MultiVisualization;
