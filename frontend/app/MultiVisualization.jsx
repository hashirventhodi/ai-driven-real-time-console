"use client";

import React, { useState, useMemo } from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell,
  ReferenceLine,
  ReferenceDot,
  ResponsiveContainer,
  ComposedChart,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";

/* ----------------------------------
  1. Global Configuration & Utilities
------------------------------------ */

// You can customize these color palettes
const COLORS = {
  primary: [
    "#2563eb",
    "#3b82f6",
    "#60a5fa",
    "#93c5fd",
    "#bfdbfe",
    "#1d4ed8",
    "#2563eb",
    "#3b82f6",
    "#60a5fa",
    "#93c5fd",
  ],
  categorical: [
    "#2563eb",
    "#059669",
    "#d97706",
    "#dc2626",
    "#7c3aed",
    "#db2777",
    "#2563eb",
    "#059669",
    "#d97706",
    "#dc2626",
  ],
};

const CONFIG = {
  chart: {
    margin: { top: 20, right: 30, left: 60, bottom: 60 },
    height: 500,
    labelAngle: -45, // rotates the X-axis labels
  },
};

/**
 * Utility functions: 
 * - Format numeric values
 * - Clean up axis keys
 */
const utils = {
  cleanKey: (key) => key?.replace(/\s+(asc|desc)\s*$/i, "").trim(),

  formatNumber: (val) =>
    typeof val === "number" ? Number(val.toFixed(2)) : val,

  /**
   * For multi-series detection, we want to find numeric columns 
   * that are not the X-axis (and not any special field like 'color', 'name', etc.).
   */
  getNumericColumns: (sampleRow, xKey) => {
    if (!sampleRow) return [];
    const numericCols = [];
    for (const col of Object.keys(sampleRow)) {
      if (
        col !== xKey &&
        col !== "color" &&
        col !== "name" &&
        typeof sampleRow[col] === "number"
      ) {
        numericCols.push(col);
      }
    }
    return numericCols;
  },
};

/* ----------------------------------------
  2. Data Processing Hook (Unified Logic)
------------------------------------------ */

/**
 * Processes raw data into a standard shape for all chart types.
 *
 * - Every row is copied except fields starting with "_".
 * - We always define `name` (for category labels).
 * - We always define `value` (for single-measure uses, e.g., Pie).
 * - Numeric fields are formatted to 2 decimals by default.
 * - A 'color' is assigned to each row for stable color usage.
 */
const useProcessedData = (data, vizConfig) => {
  return useMemo(() => {
    if (!data || !Array.isArray(data) || !data.length) return [];

    const { axes } = vizConfig || {};
    const xAxisKey = axes?.x ? utils.cleanKey(axes.x) : null;
    const yAxisKey = axes?.y ? utils.cleanKey(axes.y) : null;

    return data.map((row, index) => {
      const processed = {};

      // Copy all fields except those starting with '_'
      Object.entries(row).forEach(([key, value]) => {
        if (!key.startsWith("_")) {
          processed[key] = utils.formatNumber(value);
        }
      });

      // Ensure we have "name" for category-based charts (bar, line, pie)
      processed.name = xAxisKey
        ? String(processed[xAxisKey] ?? `Category ${index + 1}`)
        : `Category ${index + 1}`;

      // Ensure we have a single "value" for Pie or fallback usage.
      // If the y-axis is numeric, use that. Otherwise see if there's a "value" or "percentage".
      processed.value =
        typeof processed[yAxisKey] === "number"
          ? processed[yAxisKey]
          : processed.value ?? processed.percentage ?? 0;

      // Assign color
      processed.color = COLORS.categorical[index % COLORS.categorical.length];

      return processed;
    });
  }, [data, vizConfig]);
};

/* ------------------------------------
  3. Helper to Render Annotations
-------------------------------------- */

/**
 * Renders Recharts annotation components (e.g. ReferenceLine, ReferenceDot) 
 * based on the configuration objects found in vizConfig.annotations.
 * 
 * Example annotation objects might look like:
 * { 
 *   type: 'line', 
 *   mode: 'average', 
 *   label: 'Average', 
 *   style: { stroke: '#666', strokeDasharray: '3 3' } 
 * }
 * { 
 *   type: 'line', 
 *   mode: 'trend', 
 *   style: { stroke: 'red' } 
 * }
 * { 
 *   type: 'dot', 
 *   x: 'SomeXValue', 
 *   y: 'SomeYValue',
 *   style: { stroke: 'blue' }
 * }
 */
const renderAnnotations = ({
  annotations,
  chartType,
  data,
  xAxisKey,
  yAxisKey,
}) => {
  if (!Array.isArray(annotations) || !annotations.length) return null;

  // Some example logic to handle different annotation types
  // You can expand this for your own use cases
  return annotations.map((anno, idx) => {
    const key = `anno-${idx}`;
    const styleProps = anno.style || {};

    // For a "line" with mode: 'average', we compute the average of the first numeric column (or y-axis)
    if (anno.type === "line" && anno.mode === "average" && yAxisKey) {
      const avg = data.reduce((acc, d) => acc + (d[yAxisKey] || 0), 0) / data.length || 0;
      return (
        <ReferenceLine
          key={key}
          y={avg}
          stroke={styleProps.stroke || "#666"}
          strokeDasharray={styleProps.strokeDasharray || "3 3"}
          label={anno.label || "Avg"}
        />
      );
    }

    // A "line" with mode: 'trend' or 'regression' might require custom regression logic 
    // For a simple placeholder, we'll just do a horizontal line at the min or max
    if (anno.type === "line" && (anno.mode === "trend" || anno.mode === "regression")) {
      // Example: draw a line at the max Y
      const maxVal = Math.max(...data.map((d) => d[yAxisKey] || 0));
      return (
        <ReferenceLine
          key={key}
          y={maxVal}
          stroke={styleProps.stroke || "rgba(255,0,0,0.5)"}
          strokeDasharray={styleProps.strokeDasharray || "5,5"}
          label={anno.label || "Trend/Max"}
        />
      );
    }

    // Or a line with a fixed "y" value
    if (anno.type === "line" && typeof anno.y === "number") {
      return (
        <ReferenceLine
          key={key}
          y={anno.y}
          stroke={styleProps.stroke || "#888"}
          strokeDasharray={styleProps.strokeDasharray || "3,3"}
          label={anno.label}
        />
      );
    }

    // A "dot" annotation
    if (anno.type === "dot" && anno.x !== undefined && anno.y !== undefined) {
      return (
        <ReferenceDot
          key={key}
          x={anno.x}
          y={anno.y}
          r={styleProps.r || 5}
          stroke={styleProps.stroke || "red"}
          fill={styleProps.fill || "white"}
          label={anno.label}
        />
      );
    }

    // If none of the above cases match, just skip or handle generically
    return null;
  });
};

/* ----------------------------------------------
  4. Chart Components (Bar, Pie, Line, Scatter)
----------------------------------------------- */

const ChartWrapper = ({ children }) => (
  <div className="w-full h-[500px]">
    <ResponsiveContainer>{children}</ResponsiveContainer>
  </div>
);

/** 
 * 4.1. Bar Chart 
 * Renders multiple <Bar> series if multiple numeric columns exist.
 */
const BarChartComponent = ({ data, config }) => {
  if (!data.length) return <div>No data available</div>;

  const xAxisKey = utils.cleanKey(config.axes?.x);
  // get all numeric columns except x-axis
  const numericCols = utils.getNumericColumns(data[0], xAxisKey);

  return (
    <ChartWrapper>
      <ComposedChart data={data} margin={CONFIG.chart.margin}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey={xAxisKey}
          angle={CONFIG.chart.labelAngle}
          textAnchor="end"
          height={80}
          interval={0}
        />
        <YAxis />
        <Tooltip />
        <Legend />
        {/* Render multiple Bars, one per numeric column */}
        {numericCols.map((col, idx) => (
          <Bar
            key={col}
            dataKey={col}
            fill={COLORS.primary[idx % COLORS.primary.length]}
          >
            {data.map((entry, i) => (
              <Cell key={`cell-${i}`} fill={entry.color} />
            ))}
          </Bar>
        ))}

        {/* Render any annotations */}
        {renderAnnotations({
          annotations: config.annotations,
          chartType: "bar",
          data,
          xAxisKey,
          yAxisKey: numericCols.length ? numericCols[0] : null,
        })}
      </ComposedChart>
    </ChartWrapper>
  );
};

/** 
 * 4.2. Pie Chart 
 * Expects each row has `name` and `value`.
 */
const PieChartComponent = ({ data, config }) => {
  if (!data.length) return <div>No data available</div>;

  return (
    <ChartWrapper>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="50%"
          outerRadius={200}
          innerRadius={config.settings?.donut ? 100 : 0}
          label={({ name, value }) => `${name}: ${value}`}
        >
          {data.map((entry, index) => (
            <Cell key={`pie-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
        {/* Annotations typically don't apply to Pie, but you could add custom logic here. */}
      </PieChart>
    </ChartWrapper>
  );
};

/** 
 * 4.3. Line Chart 
 * Renders multiple <Line> series if multiple numeric columns exist.
 */
const LineChartComponent = ({ data, config }) => {
  if (!data.length) return <div>No data available</div>;

  const xAxisKey = utils.cleanKey(config.axes?.x);
  const numericCols = utils.getNumericColumns(data[0], xAxisKey);

  return (
    <ChartWrapper>
      <LineChart data={data} margin={CONFIG.chart.margin}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey={xAxisKey}
          angle={CONFIG.chart.labelAngle}
          textAnchor="end"
          height={80}
          interval={0}
        />
        <YAxis />
        <Tooltip />
        <Legend />
        {numericCols.map((col, idx) => (
          <Line
            key={col}
            type={config.settings?.interpolation || "monotone"}
            dataKey={col}
            stroke={COLORS.primary[idx % COLORS.primary.length]}
            dot={config.settings?.showPoints}
          />
        ))}

        {/* Render any annotations */}
        {renderAnnotations({
          annotations: config.annotations,
          chartType: "line",
          data,
          xAxisKey,
          yAxisKey: numericCols.length ? numericCols[0] : null,
        })}
      </LineChart>
    </ChartWrapper>
  );
};

/** 
 * 4.4. Scatter Chart 
 * Usually needs two numeric axes (x,y).
 */
const ScatterChartComponent = ({ data, config }) => {
  if (!data.length) return <div>No data available</div>;

  const xAxisKey = utils.cleanKey(config.axes?.x);
  const yAxisKey = utils.cleanKey(config.axes?.y);

  // Validate that x & y are numeric
  if (!xAxisKey || !yAxisKey) {
    return <div>Scatter chart requires both X and Y numeric axes.</div>;
  }
  if (typeof data[0][xAxisKey] !== "number" || typeof data[0][yAxisKey] !== "number") {
    return <div>Scatter chart axes must map to numeric columns.</div>;
  }

  return (
    <ChartWrapper>
      <ScatterChart margin={CONFIG.chart.margin}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          type="number"
          dataKey={xAxisKey}
          name={xAxisKey}
          angle={CONFIG.chart.labelAngle}
          textAnchor="end"
          height={80}
        />
        <YAxis type="number" dataKey={yAxisKey} name={yAxisKey} />
        <Tooltip />
        <Legend />
        <Scatter
          name={`${xAxisKey} vs ${yAxisKey}`}
          data={data}
          fill={COLORS.primary[0]}
        />
        {/* Render any annotations */}
        {renderAnnotations({
          annotations: config.annotations,
          chartType: "scatter",
          data,
          xAxisKey,
          yAxisKey,
        })}
      </ScatterChart>
    </ChartWrapper>
  );
};

/** 
 * 4.5. Table 
 * Simple table of all visible columns (excluding "color", "name").
 */
const TableComponent = ({ data }) => {
  if (!data.length) {
    return <div>No data available</div>;
  }

  const columns = Object.keys(data[0] || {}).filter(col => 
    !col.startsWith("_") && !["color", "name", "value"].includes(col)
  );
  

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col) => (
              <th
                key={col}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((row, i) => (
            <tr key={i}>
              {columns.map((col) => (
                <td key={col} className="px-6 py-4 whitespace-nowrap text-sm">
                  {row[col] !== undefined ? String(row[col]) : ""}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

/* ----------------------------------------
  5. The Main MultiVisualization Component
------------------------------------------ */

/**
 * MultiVisualization
 * - Renders multiple chart options (tabs) in a single card.
 * - Each chart config is an element of `visualizations`.
 * - `data` is the array of rows returned from the SQL query.
 * - `title` is used as the card title and CSV filename prefix.
 */
const MultiVisualization = ({ data, visualizations, title }) => {
  const [activeTab, setActiveTab] = useState("option-0");
  // Get the config for the currently active tab
  const currentViz = visualizations?.[parseInt(activeTab.split("-")[1], 10)];

  // Pre-process data for the active visualization
  const processedData = useProcessedData(data, currentViz || {});

  // CSV export logic
  const handleExport = () => {
    if (!currentViz || !processedData.length) return;

    // Collect columns for CSV
    const columns = Object.keys(data[0] || {}).filter(col => 
      !col.startsWith("_") && !["color", "name", "value"].includes(col)
    );

    const csv = [
      columns.join(","), // header row
      ...processedData.map((row) =>
        columns
          .map((col) => {
            const val = row[col] ?? "";
            // Escape quotes in strings
            return typeof val === "string" ? `"${val.replace(/"/g, '""')}"` : val;
          })
          .join(",")
      ),
    ].join("\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${title.toLowerCase().replace(/\s+/g, "-")}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  // Render whichever chart is selected
  const renderChart = (vizConfig) => {
    if (!processedData.length) {
      return <div>No data to display</div>;
    }
    switch (vizConfig.type) {
      case "bar":
        return <BarChartComponent data={processedData} config={vizConfig} />;
      case "line":
        return <LineChartComponent data={processedData} config={vizConfig} />;
      case "pie":
        return <PieChartComponent data={processedData} config={vizConfig} />;
      case "scatter":
        return <ScatterChartComponent data={processedData} config={vizConfig} />;
      case "table":
      default:
        return <TableComponent data={processedData} />;
    }
  };

  // If no visualizations provided, fallback to just a table
  if (!visualizations?.length) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <TableComponent data={data} />
        </CardContent>
      </Card>
    );
  }

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
                {/* You could do a more human-readable label if desired */}
                {viz.type ? viz.type.toUpperCase() : `Option ${index + 1}`}
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
