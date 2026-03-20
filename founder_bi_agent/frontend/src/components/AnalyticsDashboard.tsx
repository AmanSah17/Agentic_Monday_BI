import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ScatterChart, Scatter
} from 'recharts';
import { TrendingUp, Calendar, DollarSign, Package, AlertCircle } from 'lucide-react';

interface AnalyticsData {
  dateRange: {
    min_date: string;
    max_date: string;
    distinct_dates: number;
    total_days: number;
    total_months: number;
  } | null;
  businessMetrics: {
    total_deals: number;
    total_pipeline_value: number;
    sector_count: number;
    total_wo: number;
    total_wo_value: number;
    total_billed: number;
    total_collected: number;
    collection_rate_pct: number;
  } | null;
  dealsPipeline: any[] | null;
  dealsBySector: any[] | null;
  woByStatus: any[] | null;
  woBySecter: any[] | null;
  billingFunnel: any[] | null;
  monthlyDeals: any[] | null;
  monthlyRevenue: any[] | null;
  dealStatus: any[] | null;
  invoiceStatus: any[] | null;
}

const COLORS = ['#6161ff', '#ffcb05', '#00d4ff', '#ff6b6b', '#4ecdc4', '#45b7d1'];

export const AnalyticsDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsData>({
    dateRange: null,
    businessMetrics: null,
    dealsPipeline: null,
    dealsBySector: null,
    woByStatus: null,
    woBySecter: null,
    billingFunnel: null,
    monthlyDeals: null,
    monthlyRevenue: null,
    dealStatus: null,
    invoiceStatus: null,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const endpoints = [
          { key: 'dateRange', url: '/analytics/date-ranges' },
          { key: 'businessMetrics', url: '/analytics/business-metrics' },
          { key: 'dealsPipeline', url: '/analytics/deals-pipeline' },
          { key: 'dealsBySector', url: '/analytics/deals-by-sector' },
          { key: 'woByStatus', url: '/analytics/work-orders-by-status' },
          { key: 'woBySecter', url: '/analytics/work-orders-by-sector' },
          { key: 'billingFunnel', url: '/analytics/billing-summary' },
          { key: 'monthlyDeals', url: '/analytics/monthly-deals' },
          { key: 'monthlyRevenue', url: '/analytics/monthly-revenue' },
          { key: 'dealStatus', url: '/analytics/deal-status' },
          { key: 'invoiceStatus', url: '/analytics/invoice-status' },
        ];

        const results: Partial<AnalyticsData> = {};

        for (const endpoint of endpoints) {
          try {
            const response = await fetch(`http://localhost:8010${endpoint.url}`);
            if (response.ok) {
              const data = await response.json();
              results[endpoint.key as keyof AnalyticsData] = data.data || data;
            }
          } catch (err) {
            console.warn(`Failed to fetch ${endpoint.key}:`, err);
          }
        }

        setAnalytics(results as AnalyticsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load analytics');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-container"></div>
          <p className="mt-4 text-outline-variant">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="bg-error/10 p-6 rounded-lg flex items-center gap-4">
          <AlertCircle className="w-6 h-6 text-error" />
          <p className="text-error">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full overflow-auto bg-surface p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold text-on-surface mb-2">Business Analytics Dashboard</h1>
          <p className="text-outline-variant">
            Comprehensive insights into Deals and Work Orders
          </p>
        </motion.div>

        {/* Key Metrics Grid */}
        {analytics.businessMetrics && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
          >
            <MetricCard
              title="Total Deals"
              value={analytics.businessMetrics.total_deals}
              icon={Package}
              color="primary"
            />
            <MetricCard
              title="Pipeline Value"
              value={`₹${(analytics.businessMetrics.total_pipeline_value / 1e6).toFixed(2)}M`}
              icon={TrendingUp}
              color="success"
            />
            <MetricCard
              title="Total Collected"
              value={`₹${(analytics.businessMetrics.total_collected / 1e3).toFixed(0)}K`}
              icon={DollarSign}
              color="tertiary"
            />
            <MetricCard
              title="Collection Rate"
              value={`${analytics.businessMetrics.collection_rate_pct}%`}
              icon={TrendingUp}
              color="error"
            />
          </motion.div>
        )}

        {/* Date Range Info */}
        {analytics.dateRange && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-surface-container rounded-lg p-4 mb-8 border border-outline-variant/20"
          >
            <div className="flex items-center gap-2 mb-2">
              <Calendar className="w-5 h-5 text-outline-variant" />
              <h3 className="font-semibold text-on-surface">Data Coverage</h3>
            </div>
            <p className="text-outline-variant text-sm">
              {analytics.dateRange.min_date} to {analytics.dateRange.max_date} 
              ({analytics.dateRange.total_months} months, {analytics.dateRange.total_days} days)
            </p>
          </motion.div>
        )}

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Deals by Pipeline Stage */}
          {analytics.dealsPipeline && analytics.dealsPipeline.length > 0 && (
            <ChartCard title="Deals by Pipeline Stage">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analytics.dealsPipeline}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3a" />
                  <XAxis dataKey="stage" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e1e2e', border: '1px solid #6161ff' }} />
                  <Bar dataKey="deal_count" fill="#6161ff" />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          )}

          {/* Deals by Sector */}
          {analytics.dealsBySector && analytics.dealsBySector.length > 0 && (
            <ChartCard title="Revenue by Sector">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={analytics.dealsBySector}
                    dataKey="total_value"
                    nameKey="sector"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                  >
                    {analytics.dealsBySector.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>
          )}

          {/* Work Orders by Status */}
          {analytics.woByStatus && analytics.woByStatus.length > 0 && (
            <ChartCard title="Work Orders by Status">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analytics.woByStatus}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3a" />
                  <XAxis dataKey="status" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e1e2e', border: '1px solid #6161ff' }} />
                  <Bar dataKey="wo_count" fill="#00d4ff" />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          )}

          {/* Monthly Revenue Trend */}
          {analytics.monthlyRevenue && analytics.monthlyRevenue.length > 0 && (
            <ChartCard title="Monthly Revenue Trend">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={analytics.monthlyRevenue}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3a" />
                  <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e1e2e', border: '1px solid #6161ff' }} />
                  <Legend />
                  <Line type="monotone" dataKey="project_value" stroke="#ffcb05" strokeWidth={2} />
                  <Line type="monotone" dataKey="billed_value" stroke="#4ecdc4" strokeWidth={2} />
                  <Line type="monotone" dataKey="collected_value" stroke="#45b7d1" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
          )}

          {/* Deal Status Distribution */}
          {analytics.dealStatus && analytics.dealStatus.length > 0 && (
            <ChartCard title="Deal Status Distribution">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={analytics.dealStatus}
                    dataKey="deal_count"
                    nameKey="status"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                  >
                    {analytics.dealStatus.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>
          )}

          {/* Monthly Deals Trend */}
          {analytics.monthlyDeals && analytics.monthlyDeals.length > 0 && (
            <ChartCard title="Monthly Deals Created">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={analytics.monthlyDeals}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3a" />
                  <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e1e2e', border: '1px solid #6161ff' }} />
                  <Line type="monotone" dataKey="deals_created" stroke="#6161ff" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
          )}
        </div>
      </div>
    </div>
  );
};

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className: string }>;
  color: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon: Icon, color }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    className="bg-surface-container rounded-lg p-4 border border-outline-variant/20"
  >
    <div className="flex items-start justify-between">
      <div>
        <p className="text-outline-variant text-sm font-medium">{title}</p>
        <p className="text-2xl font-bold text-on-surface mt-2">{value}</p>
      </div>
      <div className={`p-3 rounded-lg bg-${color}/10`}>
        <Icon className={`w-5 h-5 text-${color}`} />
      </div>
    </div>
  </motion.div>
);

interface ChartCardProps {
  title: string;
  children: React.ReactNode;
}

const ChartCard: React.FC<ChartCardProps> = ({ title, children }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    className="bg-surface-container rounded-lg p-6 border border-outline-variant/20"
  >
    <h3 className="text-lg font-semibold text-on-surface mb-4">{title}</h3>
    {children}
  </motion.div>
);
