/**
 * SECURITY DASHBOARD - Hacker Monitor Style
 * ==========================================
 * Dashboard de segurança em tempo real estilo SOC (Security Operations Center)
 * Inspirado em dashboards de bancos e fintechs
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, AlertTriangle, Activity, Lock, Globe,
  Users, Zap, TrendingUp, TrendingDown, Clock,
  MapPin, Server, Terminal, Eye, EyeOff
} from 'lucide-react';

// Types
interface SecurityMetrics {
  security_score: number;
  active_attacks: number;
  blocked_attacks: number;
  online_users: number;
  failed_logins_1m: number;
  blocked_ips: number;
  status: 'stable' | 'warning' | 'critical';
}

interface Attack {
  id: string;
  type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  source_ip: string;
  target: string;
  timestamp: string;
  blocked: boolean;
  country: string;
}

interface Vulnerability {
  id: string;
  title: string;
  severity: string;
  status: 'open' | 'fixed' | 'false_positive';
  discovered_at: string;
}

// Mock data generator
const generateMockAttacks = (): Attack[] => [
  {
    id: 'ATT-001',
    type: 'Brute Force',
    severity: 'high',
    source_ip: '192.168.1.100',
    target: '/auth/login',
    timestamp: new Date().toISOString(),
    blocked: true,
    country: 'CN'
  },
  {
    id: 'ATT-002',
    type: 'SQL Injection',
    severity: 'critical',
    source_ip: '10.0.0.50',
    target: '/api/users',
    timestamp: new Date(Date.now() - 30000).toISOString(),
    blocked: true,
    country: 'RU'
  },
  {
    id: 'ATT-003',
    type: 'XSS Attempt',
    severity: 'medium',
    source_ip: '172.16.0.20',
    target: '/comments',
    timestamp: new Date(Date.now() - 60000).toISOString(),
    blocked: true,
    country: 'BR'
  }
];

const generateMockVulnerabilities = (): Vulnerability[] => [
  {
    id: 'VULN-001',
    title: 'Weak Password Policy',
    severity: 'high',
    status: 'open',
    discovered_at: new Date(Date.now() - 86400000).toISOString()
  },
    {
    id: 'VULN-002',
    title: 'Missing Rate Limiting',
    severity: 'medium',
    status: 'fixed',
    discovered_at: new Date(Date.now() - 172800000).toISOString()
  }
];

export default function SecurityDashboard() {
  const [metrics, setMetrics] = useState<SecurityMetrics>({
    security_score: 94,
    active_attacks: 3,
    blocked_attacks: 127,
    online_users: 1423,
    failed_logins_1m: 12,
    blocked_ips: 45,
    status: 'stable'
  });

  const [attacks, setAttacks] = useState<Attack[]>(generateMockAttacks());
  const [vulnerabilities, setVulnerabilities] = useState<Vulnerability[]>(generateMockVulnerabilities());
  const [selectedTimeRange, setSelectedTimeRange] = useState('1h');
  const [isRealTime, setIsRealTime] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Auto-refresh
  useEffect(() => {
    if (!isRealTime) return;

    const interval = setInterval(() => {
      // Simulate real-time updates
      setMetrics(prev => ({
        ...prev,
        security_score: Math.max(90, Math.min(100, prev.security_score + (Math.random() - 0.5) * 2)),
        failed_logins_1m: Math.floor(Math.random() * 20),
        online_users: prev.online_users + Math.floor((Math.random() - 0.5) * 10)
      }));

      // Occasionally add new attack
      if (Math.random() > 0.7) {
        const newAttack: Attack = {
          id: `ATT-${String(Date.now()).slice(-3)}`,
          type: ['Brute Force', 'SQL Injection', 'XSS', 'Bot Detection'][Math.floor(Math.random() * 4)],
          severity: ['low', 'medium', 'high', 'critical'][Math.floor(Math.random() * 4)] as any,
          source_ip: `192.168.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
          target: '/auth/login',
          timestamp: new Date().toISOString(),
          blocked: true,
          country: ['US', 'CN', 'RU', 'BR', 'DE'][Math.floor(Math.random() * 5)]
        };

        setAttacks(prev => [newAttack, ...prev.slice(0, 9)]);
      }

      setLastUpdate(new Date());
    }, 3000);

    return () => clearInterval(interval);
  }, [isRealTime]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'stable': return 'text-green-400 bg-green-400/10 border-green-400/30';
      case 'warning': return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30';
      case 'critical': return 'text-red-400 bg-red-400/10 border-red-400/30';
      default: return 'text-gray-400 bg-gray-400/10';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-400 border-red-400/50';
      case 'high': return 'text-orange-400 border-orange-400/50';
      case 'medium': return 'text-yellow-400 border-yellow-400/50';
      default: return 'text-blue-400 border-blue-400/50';
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 flex items-center justify-center">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-green-500 animate-pulse" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                Security Operations Center
              </h1>
              <p className="text-sm text-white/50">
                Real-time threat monitoring • SIL v3.0
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Status Badge */}
            <div className={`px-4 py-2 rounded-lg border flex items-center gap-2 ${getStatusColor(metrics.status)}`}>
              <Activity className="w-4 h-4" />
              <span className="font-medium capitalize">{metrics.status}</span>
            </div>

            {/* Real-time Toggle */}
            <button
              onClick={() => setIsRealTime(!isRealTime)}
              className={`px-4 py-2 rounded-lg border flex items-center gap-2 transition-all ${
                isRealTime ? 'border-cyan-500/50 text-cyan-400 bg-cyan-500/10' : 'border-white/10 text-white/50'
              }`}
            >
              {isRealTime ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
              <span className="text-sm">{isRealTime ? 'Live' : 'Paused'}</span>
            </button>

            {/* Time Range */}
            <select
              value={selectedTimeRange}
              onChange={(e) => setSelectedTimeRange(e.target.value)}
              className="px-4 py-2 rounded-lg border border-white/10 bg-white/5 text-sm focus:outline-none focus:border-cyan-500/50"
            >
              <option value="1h">Last 1 hour</option>
              <option value="24h">Last 24 hours</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
            </select>
          </div>
        </div>

        <p className="mt-2 text-xs text-white/30">
          Last updated: {lastUpdate.toLocaleTimeString()}
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {/* Security Score */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6 rounded-xl border border-white/10"
        >
          <div className="flex items-center justify-between mb-4">
            <Shield className="w-5 h-5 text-cyan-400" />
            <span className={`text-xs font-medium ${metrics.security_score >= 90 ? 'text-green-400' : 'text-yellow-400'}`}>
              {metrics.security_score >= 90 ? <TrendingUp className="w-4 h-4 inline mr-1" /> : <TrendingDown className="w-4 h-4 inline mr-1" />}
              {metrics.security_score >= 90 ? 'Excellent' : 'Attention Needed'}
            </span>
          </div>
          <div className="text-3xl font-bold text-white mb-1">
            {Math.round(metrics.security_score)}/100
          </div>
          <div className="text-sm text-white/50">Security Score</div>

          {/* Progress bar */}
          <div className="mt-3 h-2 bg-white/10 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-cyan-500 to-purple-500"
              initial={{ width: 0 }}
              animate={{ width: `${metrics.security_score}%` }}
              transition={{ duration: 1 }}
            />
          </div>
        </motion.div>

        {/* Active Attacks */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card p-6 rounded-xl border border-white/10"
        >
          <div className="flex items-center justify-between mb-4">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <span className="text-xs text-red-400 font-medium">
              <Zap className="w-4 h-4 inline mr-1" />
              Active
            </span>
          </div>
          <div className="text-3xl font-bold text-white mb-1">
            {metrics.active_attacks}
          </div>
          <div className="text-sm text-white/50">Active Attacks</div>
          <div className="mt-2 text-xs text-green-400">
            {metrics.blocked_attacks} blocked today
          </div>
        </motion.div>

        {/* Online Users */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-card p-6 rounded-xl border border-white/10"
        >
          <div className="flex items-center justify-between mb-4">
            <Users className="w-5 h-5 text-purple-400" />
            <span className="text-xs text-green-400 font-medium">
              <TrendingUp className="w-4 h-4 inline mr-1" />
              +12%
            </span>
          </div>
          <div className="text-3xl font-bold text-white mb-1">
            {metrics.online_users.toLocaleString()}
          </div>
          <div className="text-sm text-white/50">Active Users</div>
          <div className="mt-2 text-xs text-white/30">
            Peak: 2,847 today
          </div>
        </motion.div>

        {/* Blocked IPs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-card p-6 rounded-xl border border-white/10"
        >
          <div className="flex items-center justify-between mb-4">
            <Lock className="w-5 h-5 text-orange-400" />
            <span className="text-xs text-orange-400 font-medium">
              <Globe className="w-4 h-4 inline mr-1" />
              Global
            </span>
          </div>
          <div className="text-3xl font-bold text-white mb-1">
            {metrics.blocked_ips}
          </div>
          <div className="text-sm text-white/50">Blocked IPs</div>
          <div className="mt-2 text-xs text-white/30">
            Last 24 hours
          </div>
        </motion.div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Live Attack Feed */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="lg:col-span-2 glass-card rounded-xl border border-white/10 overflow-hidden"
        >
          <div className="p-4 border-b border-white/10 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal className="w-5 h-5 text-cyan-400" />
              <h3 className="font-semibold">Live Attack Feed</h3>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
              <span className="text-xs text-white/50">Real-time</span>
            </div>
          </div>

          <div className="max-h-[500px] overflow-y-auto">
            <AnimatePresence>
              {attacks.map((attack, index) => (
                <motion.div
                  key={attack.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.05 }}
                  className="p-4 border-b border-white/5 hover:bg-white/5 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className={`w-2 h-2 rounded-full mt-2 ${
                        attack.severity === 'critical' ? 'bg-red-500' :
                        attack.severity === 'high' ? 'bg-orange-500' :
                        attack.severity === 'medium' ? 'bg-yellow-500' :
                        'bg-blue-500'
                      }`} />
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-sm">{attack.type}</span>
                          <span className={`text-xs px-2 py-0.5 rounded border ${getSeverityColor(attack.severity)}`}>
                            {attack.severity.toUpperCase()}
                          </span>
                          {attack.blocked && (
                            <span className="text-xs px-2 py-0.5 rounded bg-green-500/20 text-green-400 border border-green-500/30">
                              BLOCKED
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-white/50 flex items-center gap-3">
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            {attack.source_ip} ({attack.country})
                          </span>
                          <span>→</span>
                          <span>{attack.target}</span>
                          <span>•</span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {new Date(attack.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Vulnerabilities */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="glass-card rounded-xl border border-white/10 overflow-hidden"
          >
            <div className="p-4 border-b border-white/10">
              <h3 className="font-semibold flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-yellow-400" />
                Vulnerabilities
              </h3>
            </div>

            <div className="max-h-[300px] overflow-y-auto">
              {vulnerabilities.map((vuln) => (
                <div
                  key={vuln.id}
                  className="p-4 border-b border-white/5 hover:bg-white/5 transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <span className="font-medium text-sm">{vuln.title}</span>
                    <span className={`text-xs px-2 py-0.5 rounded border ${getSeverityColor(vuln.severity)}`}>
                      {vuln.severity.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-white/50">
                    <span className={`px-2 py-0.5 rounded ${
                      vuln.status === 'fixed' ? 'bg-green-500/20 text-green-400' :
                      vuln.status === 'open' ? 'bg-red-500/20 text-red-400' :
                      'bg-gray-500/20 text-gray-400'
                    }`}>
                      {vuln.status.replace('_', ' ')}
                    </span>
                    <span>•</span>
                    <span>{new Date(vuln.discovered_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* System Status */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-card p-6 rounded-xl border border-white/10"
          >
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Server className="w-5 h-5 text-cyan-400" />
              System Status
            </h3>

            <div className="space-y-3">
              {[
                { name: 'Auth Service', status: 'operational', latency: '12ms' },
                { name: 'API Gateway', status: 'operational', latency: '8ms' },
                { name: 'AI Security', status: 'operational', latency: '45ms' },
                { name: 'Database', status: 'operational', latency: '3ms' },
                { name: 'Redis Cache', status: 'operational', latency: '1ms' },
              ].map((service) => (
                <div key={service.name} className="flex items-center justify-between">
                  <span className="text-sm text-white/70">{service.name}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-white/40">{service.latency}</span>
                    <div className="w-2 h-2 rounded-full bg-green-500" />
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Quick Actions */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-card p-6 rounded-xl border border-white/10"
          >
            <h3 className="font-semibold mb-4">Quick Actions</h3>

            <div className="grid grid-cols-2 gap-3">
              <button className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm font-medium hover:bg-red-500/20 transition-colors">
                Emergency Lockdown
              </button>
              <button className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30 text-yellow-400 text-sm font-medium hover:bg-yellow-500/20 transition-colors">
                Run Security Scan
              </button>
              <button className="p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-sm font-medium hover:bg-cyan-500/20 transition-colors">
                View Logs
              </button>
              <button className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-400 text-sm font-medium hover:bg-purple-500/20 transition-colors">
                Generate Report
              </button>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Footer Stats */}
      <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Uptime', value: '99.99%', icon: Activity },
          { label: 'Avg Response', value: '45ms', icon: Clock },
          { label: 'Threats Blocked', value: '12.5K', icon: Shield },
          { label: 'False Positives', value: '0.02%', icon: TrendingDown },
        ].map((stat, index) => (
          <div key={stat.label} className="flex items-center gap-3 p-4 rounded-lg bg-white/5 border border-white/10">
            <stat.icon className="w-5 h-5 text-cyan-400" />
            <div>
              <div className="text-lg font-bold">{stat.value}</div>
              <div className="text-xs text-white/50">{stat.label}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
