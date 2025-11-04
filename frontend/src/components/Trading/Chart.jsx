import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const Chart = ({ data, pair }) => {
  return (
    <div className="card">
      <h3 style={{ marginBottom: '20px' }}>{pair} Price Chart</h3>

      {!data || data.length === 0 ? (
        <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <p style={{ color: 'var(--text-secondary)' }}>No chart data available</p>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="time"
              stroke="var(--text-secondary)"
              tick={{ fill: 'var(--text-secondary)' }}
            />
            <YAxis
              stroke="var(--text-secondary)"
              tick={{ fill: 'var(--text-secondary)' }}
              domain={['auto', 'auto']}
            />
            <Tooltip
              contentStyle={{
                background: 'var(--dark-light)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                color: 'var(--text)'
              }}
              labelStyle={{ color: 'var(--text-secondary)' }}
            />
            <Line
              type="monotone"
              dataKey="price"
              stroke="var(--primary)"
              strokeWidth={2}
              dot={false}
              animationDuration={300}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};

export default Chart;