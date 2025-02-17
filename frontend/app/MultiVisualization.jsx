"use client";

import React, { useState, useMemo } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell, ReferenceLine,
  ResponsiveContainer, ComposedChart
} from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';

// Enhanced color palette with better accessibility
const COLORS = {
  primary: [
    '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe',
    '#1d4ed8', '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd'
  ],
  categorical: [
    '#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed',
    '#db2777', '#2563eb', '#059669', '#d97706', '#dc2626'
  ]
};

// Configuration constants
const CONFIG = {
  chart: {
    margin: { top: 20, right: 30, left: 60, bottom: 60 },
    height: 500,
    labelAngle: -45
  },
  numberFormat: {
    percentage: (value) => `${Number(value).toFixed(1)}%`,
    number: (value) => Number(value).toLocaleString()
  }
};

// Utility functions
const utils = {
  cleanKey: (key) => key.replace(/\s+(asc|desc)\s*$/i, "").trim(),
  getDisplayName: (key) => key.split('_').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' '),
  formatValue: (value, isPercentage) => {
    if (typeof value !== 'number') return value;
    return isPercentage ? 
      CONFIG.numberFormat.percentage(value) :
      CONFIG.numberFormat.number(value);
  }
};

// Data processing hook
const useProcessedData = (data, vizConfig) => {
  return useMemo(() => {
    if (!data?.length) return [];
    
    const { axes } = vizConfig;
    const xAxisKey = axes?.x ? utils.cleanKey(axes.x) : null;
    const yAxisKey = axes?.y ? utils.cleanKey(axes.y) : null;
    
    return data.map((item, index) => {
      const processed = { ...item };
      
      // Format numeric values
      Object.entries(item).forEach(([key, value]) => {
        if (typeof value === 'number' && value !== null) {
          processed[key] = Number(value.toFixed(2));
        }
      });
      
      // Set name field for charts
      processed.name = String(
        item[xAxisKey] || 
        item.name || 
        item.label || 
        item.id || 
        `Item ${index + 1}`
      );
      
      // Assign color
      processed.color = COLORS.categorical[index % COLORS.categorical.length];
      
      return processed;
    });
  }, [data, vizConfig]);
};

// Chart wrapper component
const ChartWrapper = ({ children }) => (
  <div className="w-full h-[500px]">
    <ResponsiveContainer>{children}</ResponsiveContainer>
  </div>
);

// Individual chart components
const BarChartComponent = ({ data, config }) => (
  <ChartWrapper>
    <ComposedChart data={data} margin={CONFIG.chart.margin}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis 
        dataKey="name" 
        angle={CONFIG.chart.labelAngle} 
        textAnchor="end" 
        height={80} 
        interval={0}
      />
      <YAxis />
      <Tooltip 
        formatter={(value) => utils.formatValue(value, config.axes.y?.includes('percentage'))}
      />
      <Legend />
      <Bar dataKey={utils.cleanKey(config.axes.y)} fill={COLORS.primary[0]}>
        {data.map((entry, index) => (
          <Cell key={index} fill={entry.color} />
        ))}
      </Bar>
      {config.annotations?.map((annotation, index) =>
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

const PieChartComponent = ({ data, config }) => (
  <ChartWrapper>
    <PieChart>
      <Pie
        data={data}
        dataKey={utils.cleanKey(config.axes.y)}
        nameKey="name"
        cx="50%"
        cy="50%"
        outerRadius={200}
        innerRadius={config.settings?.donut ? 100 : 0}
        label={({ name, value, percent }) => 
          `${name}: ${utils.formatValue(value, config.axes.y?.includes('percentage'))} (${utils.formatValue(percent * 100, true)})`
        }
      >
        {data.map((entry, index) => (
          <Cell key={index} fill={entry.color} />
        ))}
      </Pie>
      <Tooltip />
      <Legend />
    </PieChart>
  </ChartWrapper>
);

const LineChartComponent = ({ data, config }) => (
  <ChartWrapper>
    <LineChart data={data} margin={CONFIG.chart.margin}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis 
        dataKey="name" 
        angle={CONFIG.chart.labelAngle} 
        textAnchor="end" 
        height={80} 
        interval={0}
      />
      <YAxis />
      <Tooltip 
        formatter={(value) => utils.formatValue(value, config.axes.y?.includes('percentage'))}
      />
      <Legend />
      <Line
        type={config.settings?.interpolation || "monotone"}
        dataKey={utils.cleanKey(config.axes.y)}
        stroke={COLORS.primary[0]}
        dot={config.settings?.showPoints}
      />
      {config.annotations?.map((annotation, index) =>
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

const TableComponent = ({ data }) => (
  <div className="overflow-x-auto">
    <table className="min-w-full divide-y divide-gray-200">
      <thead className="bg-gray-50">
        <tr>
          {Object.keys(data[0] || {})
            .filter(key => !key.startsWith('_') && key !== 'color')
            .map(key => (
              <th key={key} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {utils.getDisplayName(key)}
              </th>
            ))}
        </tr>
      </thead>
      <tbody className="bg-white divide-y divide-gray-200">
        {data.map((row, i) => (
          <tr key={i}>
            {Object.entries(row)
              .filter(([key]) => !key.startsWith('_') && key !== 'color')
              .map(([key, value], j) => (
                <td key={j} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {utils.formatValue(value, key.includes('percentage'))}
                </td>
              ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

// Main component
const MultiVisualization = ({ data, visualizations, title }) => {
  const [activeTab, setActiveTab] = useState("option-0");
  const currentViz = visualizations[parseInt(activeTab.split('-')[1], 10)];
  const processedData = useProcessedData(data, currentViz);

  const handleExport = () => {
    if (!currentViz) return;
    
    const csv = [
      Object.keys(processedData[0])
        .filter(key => !key.startsWith('_') && key !== 'color')
        .join(','),
      ...processedData.map(row =>
        Object.entries(row)
          .filter(([key]) => !key.startsWith('_') && key !== 'color')
          .map(([key, value]) => {
            const formatted = utils.formatValue(value, key.includes('percentage'));
            return typeof formatted === 'string' ? `"${formatted}"` : formatted;
          })
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

  const renderChart = (vizConfig) => {
    switch (vizConfig.type) {
      case 'bar':
        return <BarChartComponent data={processedData} config={vizConfig} />;
      case 'pie':
        return <PieChartComponent data={processedData} config={vizConfig} />;
      case 'line':
        return <LineChartComponent data={processedData} config={vizConfig} />;
      case 'table':
      default:
        return <TableComponent data={processedData} />;
    }
  };

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>{title}</CardTitle>
        <Button variant="outline" size="sm" onClick={handleExport}>
          <Download className="w-4 h-4 mr-2" />
          Export
        </Button>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            {visualizations.map((viz, index) => (
              <TabsTrigger key={index} value={`option-${index}`}>
                {utils.getDisplayName(viz.type)}
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