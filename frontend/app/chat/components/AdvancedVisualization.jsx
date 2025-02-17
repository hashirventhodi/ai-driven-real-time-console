"use client";

import React, { useMemo } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell, ReferenceLine,
  ResponsiveContainer, ComposedChart
} from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';

const COLORS = [
  '#0088FE', '#00C49F', '#FFBB28', '#FF8042', 
  '#8884d8', '#82ca9d', '#ffc658', '#ff8042',
  '#00C49F', '#FFBB28', '#FF8042', '#0088FE'
];

// Process data and add colors; also generate a fallback "name" if needed
const processData = (data, config) => {
  if (!data || !data.length) return [];

  const { axes } = config;
  return data.map((item, index) => {
    const processed = { ...item };

    Object.keys(item).forEach(key => {
      if (typeof item[key] === 'number') {
        processed[key] = Number(item[key].toFixed(2));
      }
    });

    if (!processed.name) {
      if (item.firstName && item.lastName) {
        processed.name = `${item.firstName} ${item.lastName}`;
      } else if (axes && axes.x) {
        processed.name = String(item[axes.x]);
      }
    }

    processed.color = COLORS[index % COLORS.length];
    return processed;
  });
};

// Generate annotations based on config (e.g., average lines)
const generateAnnotations = (data, config) => {
  const annotations = [];
  
  if (config.annotations) {
    config.annotations.forEach(annotation => {
      switch (annotation.mode) {
        case 'average': {
          const values = data.map(item => Number(item[config.axes.y.replace(/\s+DESC\s*$/, '')]));
          const avg = values.reduce((a, b) => a + b, 0) / values.length;
          annotations.push({
            type: 'line',
            value: avg,
            label: annotation.label || 'Average',
            style: annotation.style || { stroke: '#666', strokeDasharray: '3 3' }
          });
          break;
        }
        // Other annotation modes (e.g., trend/regression) can be added here.
        default:
          break;
      }
    });
  }
  
  return annotations;
};

const ChartWrapper = ({ children }) => (
  <div className="w-full h-[500px]">
    <ResponsiveContainer>{children}</ResponsiveContainer>
  </div>
);

const AdvancedVisualization = ({ data, visualization, title }) => {
  // Process the data based on the provided visualization configuration
  const processedData = useMemo(() => processData(data, visualization), [data, visualization]);
  const annotations = useMemo(() => generateAnnotations(processedData, visualization), [processedData, visualization]);

  // Function to export the data as CSV
  const downloadData = () => {
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

  // Remove any sorting keyword (e.g., " DESC") from axis keys
  const getAxisKey = key => key ? key.replace(/\s+DESC\s*$/, '') : key;

  // Render functions for each visualization type
  const renderBarChart = () => (
    <ChartWrapper>
      <ComposedChart data={processedData} margin={{ top: 20, right: 30, left: 60, bottom: 60 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="name" 
          angle={-45} 
          textAnchor="end" 
          height={80}
          interval={0}
        />
        <YAxis />
        <Tooltip 
          content={({ payload, label }) => (
            <div className="bg-white p-2 border rounded shadow">
              <p className="font-medium">{label}</p>
              {payload?.map((entry, index) => (
                <p key={index} style={{ color: entry.color }}>
                  {entry.name}: {Number(entry.value).toLocaleString()}
                </p>
              ))}
            </div>
          )}
        />
        <Legend />
        <Bar 
          dataKey={getAxisKey(visualization.axes.y)}
          fill="#0088FE"
          name={getAxisKey(visualization.axes.y)}
        >
          {processedData.map((entry, index) => (
            <Cell key={index} fill={entry.color} />
          ))}
        </Bar>
        {annotations.map((annotation, index) => (
          annotation.type === 'line' && (
            <ReferenceLine
              key={index}
              y={annotation.value}
              stroke={annotation.style.stroke}
              strokeDasharray={annotation.style.strokeDasharray}
              label={annotation.label}
            />
          )
        ))}
      </ComposedChart>
    </ChartWrapper>
  );

  const renderPieChart = () => (
    <ChartWrapper>
      <PieChart>
        <Pie
          data={processedData}
          dataKey={getAxisKey(visualization.axes.y)}
          nameKey="name"
          cx="50%"
          cy="50%"
          outerRadius={200}
          innerRadius={visualization.settings?.donut ? 100 : 0}
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

  const renderLineChart = () => (
    <ChartWrapper>
      <LineChart data={processedData} margin={{ top: 20, right: 30, left: 60, bottom: 60 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="name"
          angle={-45}
          textAnchor="end"
          height={80}
          interval={0}
        />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line
          type="monotone"
          dataKey={getAxisKey(visualization.axes.y)}
          stroke="#0088FE"
          name={getAxisKey(visualization.axes.y)}
          dot={visualization.settings?.showPoints}
        />
        {annotations.map((annotation, index) => (
          annotation.type === 'line' && (
            <ReferenceLine
              key={index}
              y={annotation.value}
              stroke={annotation.style.stroke}
              strokeDasharray={annotation.style.strokeDasharray}
              label={annotation.label}
            />
          )
        ))}
      </LineChart>
    </ChartWrapper>
  );

  const renderScatterChart = () => (
    <ChartWrapper>
      <ScatterChart margin={{ top: 20, right: 30, left: 60, bottom: 60 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="name"
          angle={-45}
          textAnchor="end"
          height={80}
          interval={0}
        />
        <YAxis dataKey={getAxisKey(visualization.axes.y)} />
        <Tooltip />
        <Legend />
        <Scatter
          name={getAxisKey(visualization.axes.y)}
          data={processedData}
          fill="#0088FE"
        >
          {processedData.map((entry, index) => (
            <Cell key={index} fill={entry.color} />
          ))}
        </Scatter>
      </ScatterChart>
    </ChartWrapper>
  );

  const renderTable = () => (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {Object.keys(processedData[0] || {}).filter(key => !key.startsWith('_')).map(key => (
              <th
                key={key}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
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

  // Dynamically render only the chart specified by the API response
  const renderChart = () => {
    switch(visualization.type) {
      case 'bar':
        return renderBarChart();
      case 'pie':
        return renderPieChart();
      case 'line':
        return renderLineChart();
      case 'scatter':
        return renderScatterChart();
      case 'table':
        return renderTable();
      default:
        return <div>Unsupported visualization type</div>;
    }
  };

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>{title}</CardTitle>
        <div className="flex space-x-2">
          <Button variant="outline" size="sm" onClick={downloadData}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {renderChart()}
      </CardContent>
    </Card>
  );
};

export default AdvancedVisualization;
