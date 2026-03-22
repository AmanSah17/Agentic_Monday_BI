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
          {/* 1. Client Concentration */}
          <div key="a" className="bg-surface-container/90 rounded-2xl border border-outline-variant/20 shadow-xl flex flex-col overflow-hidden">
            <div className="drag-handle cursor-grab active:cursor-grabbing bg-surface-container-high p-3 border-b border-outline-variant/10 font-bold text-on-surface text-sm flex justify-between items-center">
              <span>1. Client Concentration (Pareto)</span>
              <span className="text-[10px] opacity-40 font-normal">Top Revenue Drivers</span>
            </div>
            <div className="flex-1 p-4 flex flex-col gap-3">
              <div className="flex-1">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={analytics.clientConcentration || []}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="total_pipeline_value"
                      nameKey="client_name"
                    >
                      {(analytics.clientConcentration || []).map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#1e1e2d', border: 'none', borderRadius: '8px' }} formatter={(v: number) => `₹${(v/1e6).toFixed(2)}M`} />
                    <Legend wrapperStyle={{ fontSize: '10px' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="text-[11px] text-outline p-2 bg-white/5 rounded leading-relaxed">
                <strong>Logic:</strong> Identifies your most valuable account relationships. 
                <ul className="list-disc ml-4 opacity-80">
                   <li>Monitors portfolio risk (over-reliance on single clients).</li>
                   <li>Prioritizes high-value pipeline opportunities.</li>
                </ul>
              </div>
            </div>
          </div>

          {/* 2. Operational Volume vs Fulfillment */}
          <div key="b" className="bg-surface-container/90 rounded-2xl border border-outline-variant/20 shadow-xl flex flex-col overflow-hidden">
            <div className="drag-handle cursor-grab active:cursor-grabbing bg-surface-container-high p-3 border-b border-outline-variant/10 font-bold text-on-surface text-sm flex justify-between items-center">
              <span>2. Volume vs Fulfillment</span>
              <span className="text-[10px] opacity-40 font-normal">Operational Conversion</span>
            </div>
            <div className="flex-1 p-4 flex flex-col gap-3">
              <div className="flex-1">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.volumeFulfillment || []}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="sector" tick={{ fontSize: 10, fill: '#888' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: '#888' }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#1e1e2d', border: 'none', borderRadius: '8px' }} />
                    <Legend wrapperStyle={{ fontSize: '10px' }} />
                    <Bar dataKey="ops_quantity" name="Ops Qty" fill="#6161ff" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="billed_quantity" name="Billed Qty" fill="#00d4ff" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="text-[11px] text-outline p-2 bg-white/5 rounded leading-relaxed">
                <strong>Logic:</strong> Measures the "last mile" of project delivery.
                <ul className="list-disc ml-4 opacity-80">
                   <li>Gap between Blue and Aqua bars highlights unbilled efforts.</li>
                   <li>Sector-wise distribution of operational workload.</li>
                </ul>
              </div>
            </div>
          </div>

          {/* 3. Avg Deal Size by Nature */}
          <div key="c" className="bg-surface-container/90 rounded-2xl border border-outline-variant/20 shadow-xl flex flex-col overflow-hidden">
            <div className="drag-handle cursor-grab active:cursor-grabbing bg-surface-container-high p-3 border-b border-outline-variant/10 font-bold text-on-surface text-sm flex justify-between items-center">
              <span>3. Deal Size by Nature</span>
              <span className="text-[10px] opacity-40 font-normal">Pricing Intelligence</span>
            </div>
            <div className="flex-1 p-4 flex flex-col gap-3">
              <div className="flex-1">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart layout="vertical" data={analytics.dealSizeDistribution || []}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} vertical={false} stroke="rgba(255,255,255,0.05)" />
                    <XAxis type="number" hide />
                    <YAxis dataKey="product_type" type="category" width={70} tick={{ fontSize: 9, fill: '#888' }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#1e1e2d', border: 'none', borderRadius: '8px' }} formatter={(v: number) => `₹${(v/1e6).toFixed(2)}M`} />
                    <Bar dataKey="avg_deal_size" name="Avg Size" fill="#9b59b6" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="text-[11px] text-outline p-2 bg-white/5 rounded leading-relaxed">
                <strong>Logic:</strong> Segments pipeline value by product/nature of work.
                <ul className="list-disc ml-4 opacity-80">
                   <li>Identifies which "Nature of Work" yields the largest deal sizes.</li>
                   <li>Helps in strategic resource allocation toward big-ticket items.</li>
                </ul>
              </div>
            </div>
          </div>

          {/* 4. Revenue Leakage Waterfall */}
          <div key="d" className="bg-surface-container/90 rounded-2xl border border-outline-variant/20 shadow-xl flex flex-col overflow-hidden">
            <div className="drag-handle cursor-grab active:cursor-grabbing bg-surface-container-high p-3 border-b border-outline-variant/10 font-bold text-on-surface text-sm flex justify-between items-center">
              <span>4. Revenue Leakage Analysis</span>
              <span className="text-[10px] opacity-40 font-normal">Quoted vs Billed vs Collected</span>
            </div>
            <div className="flex-1 p-4 flex flex-col gap-3">
              <div className="flex-1">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={analytics.revenueLeakage || []}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="sector" tick={{ fontSize: 10, fill: '#888' }} axisLine={false} tickLine={false} />
                    <YAxis tickFormatter={(v) => `₹${(v/1e6).toFixed(0)}M`} tick={{ fontSize: 10, fill: '#888' }} axisLine={false} tickLine={false} width={50} />
                    <Tooltip contentStyle={{ backgroundColor: '#1e1e2d', border: 'none', borderRadius: '8px', color: '#fff' }} formatter={(v: number) => `₹${(v/1e6).toFixed(2)}M`} />
                    <Legend wrapperStyle={{ fontSize: '10px' }} />
                    <Bar dataKey="quoted_value" name="Quoted" fill="#3a3a5a" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="billed_value" name="Billed" fill="#6161ff" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="collected_value" name="Collected" fill="#4ecdc4" radius={[4, 4, 0, 0]} />
                    <Line type="monotone" dataKey="unbilled_leakage" name="Unbilled Leak" stroke="#ff6b6b" strokeWidth={2} dot={{ r: 3 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
              <div className="text-[11px] text-outline p-2 bg-white/5 rounded leading-relaxed">
                <strong>Logic:</strong> Tracks financial conversion from Quote to Collection. 
                <ul className="list-disc ml-4 opacity-80">
                   <li>Identifies sectors where billing lags behind work (Unbilled Leakage).</li>
                   <li>Reveals cash flow bottlenecks in the collection cycle.</li>
                </ul>
              </div>
            </div>
          </div>

          {/* 5. Execution Velocity & Deals Status (FIXED) */}
          <div key="e" className="bg-surface-container/90 rounded-2xl border border-outline-variant/20 shadow-xl flex flex-col overflow-hidden">
            <div className="drag-handle cursor-grab active:cursor-grabbing bg-surface-container-high p-3 border-b border-outline-variant/10 font-bold text-on-surface text-sm flex justify-between items-center">
              <span>5. Operations & Deals Matrix</span>
              <span className="text-[10px] opacity-40 font-normal">Horizontal Througput</span>
            </div>
            <div className="flex-1 p-4 flex flex-col gap-3 min-h-0">
               <div className="flex-1 min-h-[150px] overflow-y-auto">
                <ResponsiveContainer width="100%" height={Math.max(300, (analytics.executionVelocity?.length || 0) * 35)}>
                  <BarChart 
                    layout="vertical"
                    data={analytics.executionVelocity || []} 
                    margin={{ left: 80, right: 20, top: 10, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(255,255,255,0.05)" />
                    <XAxis type="number" stroke="rgba(255,255,255,0.5)" fontSize={10} tickLine={false} axisLine={false} hide />
                    <YAxis 
                      type="category"
                      dataKey="execution_status" 
                      stroke="rgba(255,255,255,0.5)" 
                      fontSize={9} 
                      tickLine={false} 
                      axisLine={false}
                      width={80}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1e1e2d', border: 'none', borderRadius: '8px', color: '#fff' }}
                      itemStyle={{ color: '#fff' }}
                    />
                    <Legend iconType="circle" wrapperStyle={{ fontSize: '10px' }} />
                    <Bar dataKey="project_count" name="Volume" fill="#6161ff" radius={[0, 4, 4, 0]} barSize={12} />
                    <Bar dataKey="avg_days_to_bill" name="Avg Days" fill="#e67e22" radius={[0, 4, 4, 0]} barSize={12} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="text-[11px] text-outline p-2 bg-white/5 rounded leading-relaxed">
                <strong>Logic:</strong> A unified view of sales (Deals) and production (Work Orders).
                <ul className="list-disc ml-4 opacity-80">
                   <li><strong>Horizontal Layout</strong>: Accommodates 25+ detailed status categories.</li>
                   <li>Exposes bottlenecks where items accumulate (high Volume) or stall (high Avg Days).</li>
                </ul>
              </div>
            </div>
          </div>

          {/* 6. Predictive Pipeline */}
          <div key="f" className="bg-surface-container/90 rounded-2xl border border-outline-variant/20 shadow-xl flex flex-col overflow-hidden">
            <div className="drag-handle cursor-grab active:cursor-grabbing bg-surface-container-high p-3 border-b border-outline-variant/10 font-bold text-on-surface text-sm flex justify-between items-center">
              <span>6. Predictive Pipeline</span>
              <span className="text-[10px] opacity-40 font-normal">Revenue Forecasting</span>
            </div>
            <div className="flex-1 p-4 flex flex-col gap-3">
              <div className="flex-1">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.predictivePipeline || []} margin={{ left: 10, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="deal_status" tick={{ fontSize: 10, fill: '#888' }} angle={-15} textAnchor="end" height={40} />
                    <YAxis tickFormatter={(v) => `₹${(v/1e6).toFixed(0)}M`} tick={{ fontSize: 10, fill: '#888' }} width={50} />
                    <Tooltip cursor={{ fill: '#2a2a3a' }} contentStyle={{ backgroundColor: '#1e1e2d', border: 'none', borderRadius: '8px' }} formatter={(v: number) => `₹${(v/1e6).toFixed(2)}M`} />
                    <Bar dataKey="pipeline_revenue" name="Pipeline Revenue" fill="#ffcb05" radius={[4, 4, 0, 0]}>
                      {(analytics.predictivePipeline || []).map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[(index+5) % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="text-[11px] text-outline p-2 bg-white/5 rounded leading-relaxed">
                <strong>Logic:</strong> Projected revenue across Sales Stages.
                <ul className="list-disc ml-4 opacity-80">
                   <li>Distinguishes between Won revenue and Probable pipeline.</li>
                   <li>Essential for mid-term financial planning and risk assessment.</li>
                </ul>
              </div>
            </div>
          </div>

          {/* 7. Owner Performance Matrix */}
          <div key="g" className="bg-surface-container/90 rounded-2xl border border-outline-variant/20 shadow-xl flex flex-col overflow-hidden">
            <div className="drag-handle cursor-grab active:cursor-grabbing bg-surface-container-high p-3 border-b border-outline-variant/10 font-bold text-on-surface text-sm flex justify-between items-center">
              <span>7. Leaderboard</span>
              <span className="text-[10px] opacity-40 font-normal">Individual Efficiency</span>
            </div>
            <div className="flex-1 p-4 flex flex-col gap-3">
              <div className="flex-1">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart layout="vertical" data={analytics.ownerPerformance || []}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} vertical={false} stroke="rgba(255,255,255,0.05)" />
                    <XAxis type="number" hide />
                    <YAxis dataKey="owner_name" type="category" width={80} tick={{ fontSize: 9, fill: '#888' }} axisLine={false} tickLine={false} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1e1e2d', border: 'none', borderRadius: '8px', color: '#fff' }}
                      formatter={(v: any, name: string) => name.toLowerCase().includes('win') ? `${v}%` : `₹${(Number(v)/1e6).toFixed(2)}M`}
                    />
                    <Legend wrapperStyle={{ fontSize: '10px' }} />
                    <Bar dataKey="pipeline_value" name="Active Pipeline (₹)" fill="#00d4ff" radius={[0, 4, 4, 0]} />
                    <Line type="monotone" dataKey="win_probability_num" name="Win Probability %" stroke="#ffcb05" strokeWidth={2} dot={{ r: 4 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
              <div className="text-[11px] text-outline p-2 bg-white/5 rounded leading-relaxed">
                <strong>Logic:</strong> Individual sales performance tracking.
                <ul className="list-disc ml-4 opacity-80">
                   <li>Correlates deal volume (Bars) with closing confidence (Line).</li>
                   <li>Identifies top-tier closers and mentorship opportunities.</li>
                </ul>
              </div>
            </div>
          </div>
        </ResponsiveGridLayout>
      </div>
    </div>
  );
};
