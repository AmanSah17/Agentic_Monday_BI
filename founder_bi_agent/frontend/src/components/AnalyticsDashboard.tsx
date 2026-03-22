import React, { useState, useEffect, useRef } from 'react';
import * as RGL from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import { motion } from 'motion/react';
import { 
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ComposedChart, Line
} from 'recharts';
import { Calendar, AlertCircle, Loader2 } from 'lucide-react';

// Safely extract the Responsive component from the CJS/ESM module object
const ResponsiveGridLayout = RGL.Responsive || (RGL as any).default?.Responsive || (RGL as any).default;
const COLORS = ['#6161ff', '#ffcb05', '#00d4ff', '#ff6b6b', '#4ecdc4', '#45b7d1', '#9b59b6', '#e67e22', '#2ecc71', '#f1c40f'];

interface AnalyticsData {
  dateRange: any;
  clientConcentration: any[] | null;
  volumeFulfillment: any[] | null;
  dealSizeDistribution: any[] | null;
  revenueLeakage: any[] | null;
  executionVelocity: any[] | null;
  predictivePipeline: any[] | null;
  ownerPerformance: any[] | null;
}

const DEFAULT_LAYOUT: any[] = [
  { i: 'a', x: 0, y: 0, w: 4, h: 3, minW: 3, minH: 2 },
  { i: 'b', x: 4, y: 0, w: 4, h: 3, minW: 3, minH: 2 },
  { i: 'c', x: 8, y: 0, w: 4, h: 3, minW: 3, minH: 2 },
  { i: 'd', x: 0, y: 3, w: 8, h: 4, minW: 6, minH: 3 },
  { i: 'e', x: 8, y: 3, w: 4, h: 4, minW: 3, minH: 3 },
  { i: 'f', x: 0, y: 7, w: 6, h: 4, minW: 4, minH: 3 },
  { i: 'g', x: 6, y: 7, w: 6, h: 4, minW: 4, minH: 3 },
];

export const AnalyticsDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [layouts, flexLayouts] = useState({ lg: DEFAULT_LAYOUT });
  
  const containerRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(1200);

  useEffect(() => {
    const observer = new ResizeObserver((entries) => {
      if (entries[0]) {
        setWidth(entries[0].contentRect.width);
      }
    });

    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/analytics/dashboard-all`);
        if (!response.ok) {
          throw new Error('Failed to fetch dashboard data');
        }
        const parsed = await response.json();
        
        // Sanitize win probability strings into numbers to prevent SVG crashes
        if (parsed.data?.ownerPerformance) {
            parsed.data.ownerPerformance = parsed.data.ownerPerformance.map((item: any) => ({
                ...item,
                win_probability_num: parseFloat(String(item.win_probability).replace('%', '')) || 0
            }));
        }

        setAnalytics(parsed.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Network failure');
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full space-y-4">
        <Loader2 className="w-16 h-16 text-primary animate-spin" />
        <p className="text-lg text-primary font-medium">Compiling Draggable Data...</p>
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="bg-error/10 p-6 rounded-lg flex items-center gap-4">
          <AlertCircle className="w-8 h-8 text-error" />
          <p className="text-error text-lg">{error || 'Data Error'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full overflow-auto bg-surface p-6" ref={containerRef}>
      <div className="max-w-[1600px] mx-auto space-y-4">
        <div className="flex justify-between items-end border-b border-outline-variant/20 pb-4 mb-4">
          <div>
            <h1 className="text-4xl font-bold tracking-tight text-on-surface mb-2">V2 Data Science Dashboard</h1>
            <p className="text-outline-variant text-md">Drag, drop, and resize chart tiles seamlessly.</p>
          </div>
          {analytics.dateRange && (
            <div className="flex items-center gap-2 text-outline-variant bg-surface-container px-4 py-2 rounded-full border border-outline-variant/30">
              <Calendar className="w-5 h-5 text-primary" />
              <span>{analytics.dateRange.min_date} to {analytics.dateRange.max_date}</span>
            </div>
          )}
        </div>

        <ResponsiveGridLayout
          width={width}
          className="layout"
          layouts={layouts}
          breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
          cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
          rowHeight={100}
          onLayoutChange={(l: any, allLayouts: any) => flexLayouts(allLayouts)}
          draggableHandle=".drag-handle"
          isResizable={true}
        >
          {/* 1. Client Pareto */}
          <div key="a" className="bg-surface-container/90 rounded-2xl border border-outline-variant/20 shadow-xl flex flex-col overflow-hidden">
            <div className="drag-handle cursor-grab active:cursor-grabbing bg-surface-container-high p-3 border-b border-outline-variant/10 font-bold text-on-surface text-sm">
              1. Client Concentration (Pareto)
            </div>
            <div className="flex-1 p-2">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={analytics.clientConcentration || []} dataKey="total_pipeline_value" nameKey="client_name" cx="50%" cy="50%" innerRadius="40%" outerRadius="80%">
                    {(analytics.clientConcentration || []).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }} itemStyle={{ color: '#fff' }} formatter={(v: number) => `₹${(v/1e6).toFixed(2)}M`} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 2. Volume vs Fulfillment */}
          <div key="b" className="bg-surface-container/90 rounded-2xl border border-outline-variant/20 shadow-xl flex flex-col overflow-hidden">
            <div className="drag-handle cursor-grab active:cursor-grabbing bg-surface-container-high p-3 border-b border-outline-variant/10 font-bold text-on-surface text-sm">
              2. Operational Volume vs Billed
            </div>
            <div className="flex-1 p-2">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={analytics.volumeFulfillment || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#2a2a3a" />
                  <XAxis dataKey="sector" tick={{ fontSize: 10, fill: '#888' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: '#888' }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e1e2d', border: 'none', borderRadius: '8px' }} />
                  <Bar dataKey="ops_quantity" name="Ops Qty" fill="#3a3a5a" radius={[4, 4, 0, 0]} />
                  <Line type="monotone" dataKey="billed_quantity" name="Billed Qty" stroke="#ffcb05" strokeWidth={3} dot={{ r: 3 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 3. Deal Size Distribution */}
          <div key="c" className="bg-surface-container/90 rounded-2xl border border-outline-variant/20 shadow-xl flex flex-col overflow-hidden">
            <div className="drag-handle cursor-grab active:cursor-grabbing bg-surface-container-high p-3 border-b border-outline-variant/10 font-bold text-on-surface text-sm">
              3. Avg Deal Size by Nature
            </div>
            <div className="flex-1 p-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={analytics.dealSizeDistribution || []} layout="vertical" margin={{ top: 0, right: 20, left: 10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#2a2a3a" />
                  <XAxis type="number" hide />
                  <YAxis dataKey="product_type" type="category" width={80} tick={{ fontSize: 10, fill: '#888' }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e1e2d', border: 'none', borderRadius: '8px' }} formatter={(v: number) => `₹${(v/1e6).toFixed(2)}M`} />
                  <Bar dataKey="avg_deal_size" name="Avg Deal Size" fill="#9b59b6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 4. Revenue Leakage Waterfall */}
          <div key="d" className="bg-surface-container/90 rounded-2xl border border-outline-variant/20 shadow-xl flex flex-col overflow-hidden">
            <div className="drag-handle cursor-grab active:cursor-grabbing bg-surface-container-high p-3 border-b border-outline-variant/10 font-bold text-on-surface text-sm">
              4. Revenue Leakage Analysis (Quoted vs Billed vs Collected)
            </div>
            <div className="flex-1 p-4">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={analytics.revenueLeakage || []}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#2a2a3a" />
                  <XAxis dataKey="sector" tick={{ fontSize: 11, fill: '#888' }} axisLine={false} tickLine={false} />
                  <YAxis tickFormatter={(v) => `₹${(v/1e6).toFixed(0)}M`} tick={{ fontSize: 11, fill: '#888' }} axisLine={false} tickLine={false} width={70} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e1e2e', border: 'none', borderRadius: '8px' }} formatter={(v: number) => `₹${(v/1e6).toFixed(2)}M`} />
                  <Legend wrapperStyle={{ fontSize: '12px' }} />
                  <Bar dataKey="quoted_value" name="Quoted Value" fill="#3a3a5a" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="billed_value" name="Billed Excl Leakage" fill="#6161ff" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="collected_value" name="Actually Collected" fill="#4ecdc4" radius={[4, 4, 0, 0]} />
                  <Line type="monotone" dataKey="unbilled_leakage" name="Unbilled Leakage" stroke="#ff6b6b" strokeWidth={2} dot={{ r: 4 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 5. Execution Velocity */}
          <div key="e" className="bg-surface-container/90 rounded-2xl border border-outline-variant/20 shadow-xl flex flex-col overflow-hidden">
            <div className="drag-handle cursor-grab active:cursor-grabbing bg-surface-container-high p-3 border-b border-outline-variant/10 font-bold text-on-surface text-sm">
              5. Execution Velocity (Bottlenecks)
            </div>
            <div className="flex-1 p-4">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={analytics.executionVelocity || []} margin={{ left: -20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                  <XAxis 
                    dataKey="execution_status" 
                    stroke="rgba(255,255,255,0.5)" 
                    fontSize={10} 
                    tickLine={false} 
                    axisLine={false}
                    interval={0}
                    angle={-45}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis stroke="rgba(255,255,255,0.5)" fontSize={10} tickLine={false} axisLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e1e2d', border: 'none', borderRadius: '8px', color: '#fff' }}
                    itemStyle={{ color: '#fff' }}
                  />
                  <Legend iconType="circle" wrapperStyle={{ fontSize: '10px', paddingTop: '10px' }} />
                  <Bar dataKey="project_count" name="Volume" fill="#6161ff" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="avg_days_to_bill" name="Avg Velocity (Days)" fill="#e67e22" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 6. Predictive Pipeline (Safe BarChart) */}
          <div key="f" className="bg-surface-container/90 rounded-2xl border border-outline-variant/20 shadow-xl flex flex-col overflow-hidden">
            <div className="drag-handle cursor-grab active:cursor-grabbing bg-surface-container-high p-3 border-b border-outline-variant/10 font-bold text-on-surface text-sm">
              6. Predictive Pipeline (Status vs Size)
            </div>
            <div className="flex-1 p-4">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={analytics.predictivePipeline || []} margin={{ left: 10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#2a2a3a" />
                  <XAxis dataKey="deal_status" tick={{ fontSize: 11, fill: '#888' }} angle={-15} textAnchor="end" />
                  <YAxis tickFormatter={(v) => `₹${(v/1e6).toFixed(0)}M`} tick={{ fontSize: 11, fill: '#888' }} width={60} />
                  <Tooltip cursor={{ fill: '#2a2a3a' }} contentStyle={{ backgroundColor: '#1e1e2d', border: 'none', borderRadius: '8px' }} formatter={(v: number) => `₹${(v/1e6).toFixed(2)}M`} />
                  <Bar dataKey="pipeline_revenue" name="Pipeline Revenue" fill="#ffcb05" radius={[4, 4, 0, 0]}>
                    {(analytics.predictivePipeline || []).map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[(index+5) % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 7. Owner Performance (Safe ComposedChart) */}
          <div key="g" className="bg-surface-container/90 rounded-2xl border border-outline-variant/20 shadow-xl flex flex-col overflow-hidden">
            <div className="drag-handle cursor-grab active:cursor-grabbing bg-surface-container-high p-3 border-b border-outline-variant/10 font-bold text-on-surface text-sm">
              7. Owner Performance Matrix
            </div>
            <div className="flex-1 p-4">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={analytics.ownerPerformance || []} layout="vertical" margin={{ left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#2a2a3a" />
                  <XAxis type="number" hide />
                  <YAxis dataKey="owner_name" type="category" tick={{ fontSize: 11, fill: '#888' }} axisLine={false} tickLine={false} width={80} />
                  <Tooltip cursor={{ fill: '#2a2a3a' }} contentStyle={{ backgroundColor: '#1e1e2d', border: 'none', borderRadius: '8px' }} formatter={(v: number) => `₹${(v/1e6).toFixed(2)}M`} />
                  <Legend />
                  <Bar dataKey="pipeline_value" name="Active Pipeline (₹)" fill="#45b7d1" radius={[0, 4, 4, 0]} />
                  <Line type="monotone" dataKey="win_probability_num" name="Win Probability %" stroke="#f1c40f" strokeWidth={3} dot={{ r: 4 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

        </ResponsiveGridLayout>
      </div>
    </div>
  );
};
