import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Activity, 
  Users, 
  Video, 
  Upload, 
  TrendingUp, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  ExternalLink,
  Zap,
  Brain,
  Sparkles
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

/**
 * API service class for handling dashboard data requests
 */
class DashboardAPI {
  constructor() {
    // Utilise la variable d'environnement ou fallback vers localhost
    this.baseURL = import.meta.env.REACT_APP_API_URL || 
                   (window.location.protocol + '//' + window.location.hostname + ':5000');
    
    console.log('API Base URL:', this.baseURL);
  }

  /**
   * Fetch dashboard data from API
   * @returns {Promise<Object>} Complete dashboard data
   */
  async fetchDashboardData() {
    try {
      const response = await fetch(`${this.baseURL}/api/dashboard`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        // Ajout pour gérer les CORS en Docker
        mode: 'cors',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Dashboard data received:', data);
      return data;
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      console.warn('Falling back to mock data');
      return this.getMockData(); // Fallback to mock data
    }
  }

  /**
   * Health check endpoint
   * @returns {Promise<boolean>} API health status
   */
  async checkHealth() {
    try {
      const response = await fetch(`${this.baseURL}/api/health`, {
        method: 'GET',
        timeout: 5000,
      });
      return response.ok;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }

  /**
   * Get mock data for development/fallback
   * @returns {Object} Mock dashboard data
   */
  getMockData() {
    return {
      stats: {
        total_reels: 245,
        posted_reels: 189,
        pending_reels: 56,
        success_rate: 77.1,
        recent_posts_24h: 12,
        recent_scrapes_24h: 18
      },
      config: {
        reels_scraper_enabled: true,
        auto_poster_enabled: true,
        file_remover_enabled: true,
        youtube_scraper_enabled: false,
        posting_interval: 30,
        scraper_interval: 720,
        fetch_limit: 5,
        accounts: ['creustel', 'elouen_la_baleine', 'victorhabchy'],
        username: 'choupinoumasque'
      },
      recent_reels: [
        { id: 1, code: 'DNLfzMJMeE5', account: 'elouen_la_baleine', is_posted: true, created_at: '2025-08-19T20:04:32' },
        { id: 2, code: 'C2akk2fNzbU', account: 'victorhabchy', is_posted: false, created_at: '2025-08-19T20:04:56' }
      ],
      timeline: [
        { date: '2025-08-13', day: 'Tue', posts: 8, scrapes: 12 },
        { date: '2025-08-14', day: 'Wed', posts: 12, scrapes: 15 },
        { date: '2025-08-15', day: 'Thu', posts: 6, scrapes: 8 },
        { date: '2025-08-16', day: 'Fri', posts: 15, scrapes: 20 },
        { date: '2025-08-17', day: 'Sat', posts: 10, scrapes: 14 },
        { date: '2025-08-18', day: 'Sun', posts: 7, scrapes: 10 },
        { date: '2025-08-19', day: 'Mon', posts: 12, scrapes: 18 }
      ],
      accounts: [
        { account: 'victorhabchy', total_reels: 128, posted_reels: 95, success_rate: 74.2 },
        { account: 'elouen_la_baleine', total_reels: 87, posted_reels: 71, success_rate: 81.6 },
        { account: 'creustel', total_reels: 30, posted_reels: 23, success_rate: 76.7 }
      ]
    };
  }
}

/**
 * Animated counter component for statistics
 */
const AnimatedCounter = ({ value, duration = 2000, suffix = '' }) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const startTime = Date.now();
    const endValue = parseInt(value) || 0;
    
    const updateCount = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);
      
      setCount(Math.floor(easeOutQuart * endValue));
      
      if (progress < 1) {
        requestAnimationFrame(updateCount);
      }
    };

    updateCount();
  }, [value, duration]);

  return <span>{count}{suffix}</span>;
};

/**
 * Stat card component with glassmorphism effect
 */
const StatCard = ({ title, value, suffix = '', icon: Icon, trend, color = 'blue' }) => {
  const colorClasses = {
    blue: 'from-blue-500/20 to-cyan-500/20 border-blue-500/30',
    green: 'from-green-500/20 to-emerald-500/20 border-green-500/30',
    purple: 'from-purple-500/20 to-pink-500/20 border-purple-500/30',
    orange: 'from-orange-500/20 to-red-500/20 border-orange-500/30'
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${colorClasses[color]} 
                  backdrop-blur-xl border border-white/10 p-6 shadow-2xl hover:shadow-3xl 
                  transition-all duration-300 hover:scale-105`}
    >
      {/* Animated background effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-50" />
      
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <div className={`p-3 rounded-xl bg-gradient-to-br ${colorClasses[color]} backdrop-blur-sm`}>
            <Icon className="w-6 h-6 text-white" />
          </div>
          {trend && (
            <div className={`text-sm font-medium ${trend > 0 ? 'text-green-400' : 'text-red-400'}`}>
              {trend > 0 ? '+' : ''}{trend}%
            </div>
          )}
        </div>
        
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-gray-300 uppercase tracking-wider">
            {title}
          </h3>
          <div className="text-3xl font-bold text-white">
            <AnimatedCounter value={value} suffix={suffix} />
          </div>
        </div>
      </div>
    </motion.div>
  );
};

/**
 * Activity timeline chart component
 */
const ActivityChart = ({ data }) => {
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-900/95 backdrop-blur-sm border border-gray-700 rounded-lg p-3 shadow-xl">
          <p className="text-gray-300 font-medium">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.dataKey}: {entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.8 }}
      className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-xl 
                 border border-gray-700/50 rounded-2xl p-6 shadow-2xl"
    >
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500/20 to-cyan-500/20">
          <TrendingUp className="w-5 h-5 text-cyan-400" />
        </div>
        <h3 className="text-xl font-semibold text-white">Activity Timeline</h3>
      </div>
      
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis 
            dataKey="day" 
            stroke="#9CA3AF"
            fontSize={12}
          />
          <YAxis stroke="#9CA3AF" fontSize={12} />
          <Tooltip content={<CustomTooltip />} />
          <Line 
            type="monotone" 
            dataKey="posts" 
            stroke="#06B6D4" 
            strokeWidth={3}
            dot={{ fill: '#06B6D4', strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6, fill: '#06B6D4' }}
          />
          <Line 
            type="monotone" 
            dataKey="scrapes" 
            stroke="#8B5CF6" 
            strokeWidth={3}
            dot={{ fill: '#8B5CF6', strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6, fill: '#8B5CF6' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </motion.div>
  );
};

/**
 * Account performance chart component
 */
const AccountChart = ({ data }) => {
  const COLORS = ['#06B6D4', '#8B5CF6', '#F59E0B', '#EF4444', '#10B981'];

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.8 }}
      className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-xl 
                 border border-gray-700/50 rounded-2xl p-6 shadow-2xl"
    >
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20">
          <Users className="w-5 h-5 text-purple-400" />
        </div>
        <h3 className="text-xl font-semibold text-white">Account Performance</h3>
      </div>
      
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis 
            dataKey="account" 
            stroke="#9CA3AF"
            fontSize={12}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis stroke="#9CA3AF" fontSize={12} />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'rgba(17, 24, 39, 0.95)',
              border: '1px solid #374151',
              borderRadius: '8px'
            }}
          />
          <Bar dataKey="total_reels" fill="#06B6D4" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </motion.div>
  );
};

/**
 * Recent reels component
 */
const RecentReels = ({ reels }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, delay: 0.2 }}
      className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-xl 
                 border border-gray-700/50 rounded-2xl p-6 shadow-2xl"
    >
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-lg bg-gradient-to-br from-green-500/20 to-emerald-500/20">
          <Video className="w-5 h-5 text-green-400" />
        </div>
        <h3 className="text-xl font-semibold text-white">Recent Reels</h3>
      </div>
      
      <div className="space-y-4">
        {reels.map((reel, index) => (
          <motion.div
            key={reel.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            className="flex items-center justify-between p-4 rounded-xl 
                       bg-gradient-to-r from-gray-800/50 to-gray-700/50 
                       border border-gray-600/30 hover:border-gray-500/50
                       transition-all duration-300"
          >
            <div className="flex items-center gap-4">
              <div className={`w-3 h-3 rounded-full ${reel.is_posted ? 'bg-green-500' : 'bg-orange-500'}`} />
              <div>
                <p className="text-white font-medium">@{reel.account}</p>
                <p className="text-gray-400 text-sm">{reel.code}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <div className={`px-3 py-1 rounded-full text-xs font-medium
                ${reel.is_posted 
                  ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                  : 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                }`}>
                {reel.is_posted ? 'Posted' : 'Pending'}
              </div>
              
              {reel.is_posted && (
                <a
                  href={`https://instagram.com/p/${reel.code}/`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-2 rounded-lg bg-gray-700/50 hover:bg-gray-600/50 
                           transition-colors duration-200"
                >
                  <ExternalLink className="w-4 h-4 text-gray-400" />
                </a>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

/**
 * Configuration status component
 */
const ConfigStatus = ({ config }) => {
  const services = [
    { name: 'Reels Scraper', enabled: config.reels_scraper_enabled, icon: Activity },
    { name: 'Auto Poster', enabled: config.auto_poster_enabled, icon: Upload },
    { name: 'File Remover', enabled: config.file_remover_enabled, icon: CheckCircle },
    { name: 'YouTube Scraper', enabled: config.youtube_scraper_enabled, icon: Video }
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, delay: 0.4 }}
      className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-xl 
                 border border-gray-700/50 rounded-2xl p-6 shadow-2xl"
    >
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-lg bg-gradient-to-br from-orange-500/20 to-red-500/20">
          <Zap className="w-5 h-5 text-orange-400" />
        </div>
        <h3 className="text-xl font-semibold text-white">System Status</h3>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        {services.map((service, index) => (
          <motion.div
            key={service.name}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            className={`p-4 rounded-xl border transition-all duration-300
              ${service.enabled 
                ? 'bg-green-500/10 border-green-500/30' 
                : 'bg-gray-700/30 border-gray-600/30'
              }`}
          >
            <div className="flex items-center gap-3">
              <service.icon 
                className={`w-5 h-5 ${service.enabled ? 'text-green-400' : 'text-gray-500'}`} 
              />
              <div>
                <p className="text-white text-sm font-medium">{service.name}</p>
                <p className={`text-xs ${service.enabled ? 'text-green-400' : 'text-gray-500'}`}>
                  {service.enabled ? 'Active' : 'Inactive'}
                </p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

/**
 * Main Dashboard component
 */
const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  const api = new DashboardAPI();

  /**
   * Fetch dashboard data from API
   */
  const fetchData = async () => {
    try {
      const dashboardData = await api.fetchDashboardData();
      setData(dashboardData);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Initial data fetch and periodic updates
  useEffect(() => {
    fetchData();
    
    // Update every 30 seconds
    const interval = setInterval(fetchData, 30000);
    
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 
                      flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className="w-16 h-16 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full"
        />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 
                      flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-white text-xl font-semibold mb-2">Failed to load data</h2>
          <p className="text-gray-400 mb-4">Please check if the API server is running</p>
          <button 
            onClick={() => window.location.reload()}
            className="px-6 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
      {/* Animated background effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 w-40 h-40 bg-pink-500/5 rounded-full blur-2xl" />
      </div>

      <div className="relative z-10 p-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="mb-8"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-500/20 to-purple-500/20 backdrop-blur-sm">
                <Brain className="w-8 h-8 text-cyan-400" />
              </div>
              <div>
                <h1 className="text-4xl font-bold text-white">
                  ReelsAutoPilot
                  <Sparkles className="inline-block w-6 h-6 text-yellow-400 ml-2" />
                </h1>
                <p className="text-gray-400">AI-Powered Instagram Automation Dashboard</p>
              </div>
            </div>
            
            <div className="text-right">
              <p className="text-gray-400 text-sm">Last updated</p>
              <p className="text-white font-medium">{lastUpdate.toLocaleTimeString()}</p>
            </div>
          </div>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Reels"
            value={data.stats.total_reels}
            icon={Video}
            color="blue"
          />
          <StatCard
            title="Posted Reels"
            value={data.stats.posted_reels}
            icon={CheckCircle}
            color="green"
          />
          <StatCard
            title="Success Rate"
            value={data.stats.success_rate}
            suffix="%"
            icon={TrendingUp}
            color="purple"
          />
          <StatCard
            title="24h Posts"
            value={data.stats.recent_posts_24h}
            icon={Clock}
            color="orange"
          />
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <ActivityChart data={data.timeline} />
          <AccountChart data={data.accounts} />
        </div>

        {/* Bottom Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <RecentReels reels={data.recent_reels} />
          <ConfigStatus config={data.config} />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;