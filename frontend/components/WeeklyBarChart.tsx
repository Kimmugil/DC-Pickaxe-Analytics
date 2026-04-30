'use client'

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from 'recharts'

interface Props {
  dailyCounts: Record<string, number>
}

export function WeeklyBarChart({ dailyCounts }: Props) {
  const data = Object.entries(dailyCounts)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, count]) => {
      const d = new Date(date)
      const label = `${d.getMonth() + 1}/${d.getDate()}`
      return { label, count }
    })

  return (
    <ResponsiveContainer width="100%" height={72}>
      <BarChart data={data} margin={{ top: 4, right: 0, left: -28, bottom: 0 }}>
        <XAxis
          dataKey="label"
          tick={{ fontSize: 10, fill: '#9CA3AF' }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tick={{ fontSize: 10, fill: '#9CA3AF' }}
          tickLine={false}
          axisLine={false}
          allowDecimals={false}
        />
        <Tooltip
          contentStyle={{ fontSize: 12, padding: '4px 8px', border: '1px solid #E5E7EB' }}
          formatter={(v: number) => [`${v}건`, '게시글']}
          labelStyle={{ color: '#374151' }}
        />
        <Bar dataKey="count" fill="#3B82F6" radius={[2, 2, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
