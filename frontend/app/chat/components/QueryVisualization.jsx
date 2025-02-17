import React, { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  PieChart,
  Pie,
  Cell,
  ReferenceLine
} from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

const QueryVisualization = ({ data, visualization, title }) => {
  const processedData = useMemo(() => {
    if (!data || !data.length) return [];
    
    // Format names for display
    return data.map(item => ({
      ...item,
      name: `${item.firstName} ${item.lastName}`,
      // Format numbers to 2 decimal places
      totalSales: Number(item.totalSales).toFixed(2)
    }));
  }, [data]);

  const averageValue = useMemo(() => {
    if (!data || !data.length) return 0;
    const sum = data.reduce((acc, item) => acc + Number(item.totalSales), 0);
    return sum / data.length;
  }, [data]);

  const renderVisualization = () => {
    switch (visualization.type) {
      case 'bar':
        return (
          <div className="w-full overflow-x-auto">
            <BarChart
              width={1000}
              height={500}
              data={processedData}
              margin={{ top: 20, right: 30, left: 60, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="name"
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar
                dataKey="totalSales"
                fill="#0088FE"
                name="Total Sales"
              />
              {visualization.annotations?.some(a => a.mode === 'average') && (
                <ReferenceLine
                  y={averageValue}
                  stroke="#666"
                  strokeDasharray="3 3"
                  label="Average"
                />
              )}
            </BarChart>
          </div>
        );

      case 'pie':
        return (
          <PieChart width={800} height={500}>
            <Pie
              data={processedData}
              dataKey="totalSales"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={200}
              innerRadius={visualization.settings?.donut ? 100 : 0}
              label={({ name, value }) => `${name}: $${Number(value).toLocaleString()}`}
            >
              {processedData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        );

      case 'line':
        return (
          <LineChart
            width={1000}
            height={500}
            data={processedData}
            margin={{ top: 20, right: 30, left: 60, bottom: 60 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="name"
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="totalSales"
              stroke="#0088FE"
              name="Total Sales"
              dot={visualization.settings?.showPoints}
            />
          </LineChart>
        );

      case 'scatter':
        return (
          <ScatterChart
            width={1000}
            height={500}
            margin={{ top: 20, right: 30, left: 60, bottom: 60 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="name"
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis dataKey="totalSales" />
            <Tooltip />
            <Legend />
            <Scatter
              name="Total Sales"
              data={processedData}
              fill="#0088FE"
            />
          </ScatterChart>
        );

      default:
        return (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="p-4 text-left">Employee</th>
                  <th className="p-4 text-left">Total Sales</th>
                </tr>
              </thead>
              <tbody>
                {processedData.map((item, index) => (
                  <tr key={index} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                    <td className="p-4">{item.name}</td>
                    <td className="p-4">${Number(item.totalSales).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>{title || 'Query Results'}</CardTitle>
      </CardHeader>
      <CardContent>
        {renderVisualization()}
      </CardContent>
    </Card>
  );
};

export default QueryVisualization;