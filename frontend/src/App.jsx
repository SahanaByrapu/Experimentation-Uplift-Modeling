import { useState, useEffect } from "react";
import "@/App.css";
import axios from "axios";
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import { 
  BarChart3, 
  TrendingUp, 
  Users, 
  Target, 
  Zap, 
  FileUp,
  ChevronRight,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Monitor,
  Smartphone,
  MapPin,
  Activity
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Chart colors
const COLORS = {
  control: '#71717a',
  treatment: '#FF3333',
  blue: '#002FA7',
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444'
};

// Custom Tooltip
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-tooltip">
        <p className="tooltip-label">{label}</p>
        {payload.map((entry, index) => (
          <p key={index} style={{ color: entry.color }}>
            {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}%
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// Sidebar Component
const Sidebar = ({ activeTab, setActiveTab }) => {
  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'analysis', label: 'Statistical Analysis', icon: TrendingUp },
    { id: 'power', label: 'Power Analysis', icon: Zap },
    { id: 'segments', label: 'Segment Analysis', icon: Users },
    { id: 'decision', label: 'Decision Support', icon: Target },
    { id: 'upload', label: 'Data Upload', icon: FileUp },
  ];

  return (
    <aside className="sidebar" data-testid="sidebar">
      <div className="sidebar-header">
        <h1 className="sidebar-title">A/B Test</h1>
        <span className="sidebar-subtitle">EXPERIMENTATION PLATFORM</span>
      </div>
      <nav className="sidebar-nav">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            data-testid={`nav-${id}`}
            className={`nav-item ${activeTab === id ? 'active' : ''}`}
            onClick={() => setActiveTab(id)}
          >
            <Icon size={18} strokeWidth={1.5} />
            <span>{label}</span>
            <ChevronRight size={14} className="nav-arrow" />
          </button>
        ))}
      </nav>
    </aside>
  );
};

// Metric Card Component
const MetricCard = ({ label, value, subvalue, trend, testId }) => (
  <div className="metric-card" data-testid={testId}>
    <span className="metric-label">{label}</span>
    <span className="metric-value">{value}</span>
    {subvalue && <span className="metric-subvalue">{subvalue}</span>}
    {trend !== undefined && (
      <span className={`metric-trend ${trend >= 0 ? 'positive' : 'negative'}`}>
        {trend >= 0 ? '+' : ''}{trend.toFixed(2)}%
      </span>
    )}
  </div>
);

// Overview Tab
const OverviewTab = ({ overview, chartData }) => {
  if (!overview) {
    return <div className="loading">Loading overview data...</div>;
  }

  const conversionData = chartData?.conversion;
  
  const barData = conversionData ? [
    { name: 'Control (A)', rate: conversionData.conversion_rates[0], fill: COLORS.control },
    { name: 'Treatment (B)', rate: conversionData.conversion_rates[1], fill: COLORS.treatment }
  ] : [];

  const deviceData = overview.device_distribution ? 
    Object.entries(overview.device_distribution).map(([name, value]) => ({ name, value })) : [];

  const locationData = overview.location_distribution ?
    Object.entries(overview.location_distribution).map(([name, value]) => ({ name, value })) : [];

  return (
    <div className="tab-content" data-testid="overview-tab">
      <h2 className="section-title">Experiment Overview</h2>
      
      <div className="metrics-grid">
        <MetricCard 
          label="TOTAL USERS" 
          value={overview.total_users?.toLocaleString()} 
          testId="metric-total-users"
        />
        <MetricCard 
          label="CONTROL GROUP (A)" 
          value={overview.control_users?.toLocaleString()}
          subvalue="White Background"
          testId="metric-control"
        />
        <MetricCard 
          label="TREATMENT GROUP (B)" 
          value={overview.treatment_users?.toLocaleString()}
          subvalue="Black Background"
          testId="metric-treatment"
        />
        <MetricCard 
          label="OVERALL CONVERSION" 
          value={`${overview.overall_conversion_rate?.toFixed(2)}%`}
          testId="metric-conversion"
        />
      </div>

      <div className="charts-grid">
        <div className="chart-card large" data-testid="conversion-chart">
          <h3 className="chart-title">Conversion Rate by Group</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" />
              <XAxis dataKey="name" tick={{ fontFamily: 'JetBrains Mono', fontSize: 12 }} />
              <YAxis tick={{ fontFamily: 'JetBrains Mono', fontSize: 12 }} label={{ value: 'Conversion Rate (%)', angle: -90, position: 'insideLeft' }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="rate" name="Rate">
                {barData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          {conversionData && (
            <div className="chart-stats">
              <span className="lift-badge">
                Lift: <strong className={conversionData.relative_lift > 0 ? 'positive' : 'negative'}>
                  {conversionData.relative_lift > 0 ? '+' : ''}{conversionData.relative_lift?.toFixed(2)}%
                </strong>
              </span>
              <span className="pvalue-badge">
                p-value: <strong className={conversionData.p_value < 0.05 ? 'significant' : ''}>
                  {conversionData.p_value?.toFixed(6)}
                </strong>
              </span>
            </div>
          )}
        </div>

        <div className="chart-card" data-testid="device-chart">
          <h3 className="chart-title">Device Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={deviceData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                dataKey="value"
              >
                {deviceData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={index === 0 ? COLORS.control : COLORS.treatment} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card" data-testid="location-chart">
          <h3 className="chart-title">Location Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={locationData} margin={{ top: 10, right: 10, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="value" fill={COLORS.blue} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

// Statistical Analysis Tab
const AnalysisTab = ({ analysis }) => {
  if (!analysis) {
    return <div className="loading">Loading analysis...</div>;
  }

  const { z_test, chi_square, page_views_analysis, time_spent_analysis } = analysis;

  return (
    <div className="tab-content" data-testid="analysis-tab">
      <h2 className="section-title">Statistical Analysis</h2>

      <div className="stats-grid">
        <div className="stat-card primary" data-testid="z-test-results">
          <h3 className="stat-title">Proportion Z-Test (Conversion)</h3>
          <div className="stat-row">
            <span className="stat-label">Z-Statistic</span>
            <span className="stat-value mono">{z_test?.z_statistic?.toFixed(4)}</span>
          </div>
          <div className="stat-row highlight">
            <span className="stat-label">P-Value</span>
            <span className={`stat-value mono ${z_test?.p_value < 0.05 ? 'significant' : ''}`}>
              {z_test?.p_value?.toFixed(6)}
            </span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Control Rate</span>
            <span className="stat-value mono">{(z_test?.control_rate * 100)?.toFixed(2)}%</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Treatment Rate</span>
            <span className="stat-value mono">{(z_test?.treatment_rate * 100)?.toFixed(2)}%</span>
          </div>
          <div className="stat-row highlight">
            <span className="stat-label">Relative Lift</span>
            <span className={`stat-value mono ${z_test?.relative_lift > 0 ? 'positive' : 'negative'}`}>
              {z_test?.relative_lift > 0 ? '+' : ''}{z_test?.relative_lift?.toFixed(2)}%
            </span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Control 95% CI</span>
            <span className="stat-value mono">
              [{(z_test?.control_ci?.[0] * 100)?.toFixed(2)}%, {(z_test?.control_ci?.[1] * 100)?.toFixed(2)}%]
            </span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Treatment 95% CI</span>
            <span className="stat-value mono">
              [{(z_test?.treatment_ci?.[0] * 100)?.toFixed(2)}%, {(z_test?.treatment_ci?.[1] * 100)?.toFixed(2)}%]
            </span>
          </div>
        </div>

        <div className="stat-card" data-testid="chi-square-results">
          <h3 className="stat-title">Chi-Square Test</h3>
          <div className="stat-row">
            <span className="stat-label">Chi² Statistic</span>
            <span className="stat-value mono">{chi_square?.chi2_statistic?.toFixed(4)}</span>
          </div>
          <div className="stat-row highlight">
            <span className="stat-label">P-Value</span>
            <span className={`stat-value mono ${chi_square?.p_value < 0.05 ? 'significant' : ''}`}>
              {chi_square?.p_value?.toFixed(6)}
            </span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Degrees of Freedom</span>
            <span className="stat-value mono">{chi_square?.degrees_of_freedom}</span>
          </div>
          <div className="significance-badge">
            {chi_square?.p_value < 0.05 ? (
              <span className="badge significant"><CheckCircle2 size={14} /> Significant</span>
            ) : (
              <span className="badge not-significant"><XCircle size={14} /> Not Significant</span>
            )}
          </div>
        </div>

        <div className="stat-card" data-testid="page-views-results">
          <h3 className="stat-title">Page Views T-Test</h3>
          <div className="stat-row">
            <span className="stat-label">T-Statistic</span>
            <span className="stat-value mono">{page_views_analysis?.t_statistic?.toFixed(4)}</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">P-Value</span>
            <span className="stat-value mono">{page_views_analysis?.p_value?.toFixed(6)}</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Cohen's d</span>
            <span className="stat-value mono">{page_views_analysis?.cohens_d?.toFixed(4)}</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Group A Mean</span>
            <span className="stat-value mono">{page_views_analysis?.group_a_mean?.toFixed(2)}</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Group B Mean</span>
            <span className="stat-value mono">{page_views_analysis?.group_b_mean?.toFixed(2)}</span>
          </div>
        </div>

        <div className="stat-card" data-testid="time-spent-results">
          <h3 className="stat-title">Time Spent T-Test</h3>
          <div className="stat-row">
            <span className="stat-label">T-Statistic</span>
            <span className="stat-value mono">{time_spent_analysis?.t_statistic?.toFixed(4)}</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">P-Value</span>
            <span className="stat-value mono">{time_spent_analysis?.p_value?.toFixed(6)}</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Cohen's d</span>
            <span className="stat-value mono">{time_spent_analysis?.cohens_d?.toFixed(4)}</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Group A Mean</span>
            <span className="stat-value mono">{time_spent_analysis?.group_a_mean?.toFixed(2)}s</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Group B Mean</span>
            <span className="stat-value mono">{time_spent_analysis?.group_b_mean?.toFixed(2)}s</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// Power Analysis Tab
const PowerTab = ({ analysis, powerCalc, onCalculatePower }) => {
  const [formData, setFormData] = useState({
    baseline_rate: 0.09,
    minimum_detectable_effect: 0.15,
    alpha: 0.05,
    power: 0.8
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onCalculatePower(formData);
  };

  return (
    <div className="tab-content" data-testid="power-tab">
      <h2 className="section-title">Power Analysis</h2>

      <div className="power-grid">
        <div className="power-card achieved" data-testid="achieved-power">
          <h3 className="stat-title">Post-Experiment Power</h3>
          <p className="power-description">Did you have enough data to be confident in your result?</p>
          
          {analysis?.power_analysis && (
            <>
              <div className="power-metric">
                <span className="power-value">{(analysis.power_analysis.achieved_power * 100).toFixed(1)}%</span>
                <span className="power-label">Achieved Power</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Control Sample</span>
                <span className="stat-value mono">{analysis.power_analysis.sample_size_control?.toLocaleString()}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Treatment Sample</span>
                <span className="stat-value mono">{analysis.power_analysis.sample_size_treatment?.toLocaleString()}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Observed Effect Size</span>
                <span className="stat-value mono">{analysis.power_analysis.observed_effect_size?.toFixed(4)}</span>
              </div>
              <div className="power-status">
                {analysis.power_analysis.is_adequately_powered ? (
                  <span className="status adequate"><CheckCircle2 size={16} /> Adequately Powered</span>
                ) : (
                  <span className="status inadequate"><AlertCircle size={16} /> Underpowered</span>
                )}
              </div>
            </>
          )}
        </div>

        <div className="power-card calculator" data-testid="power-calculator">
          <h3 className="stat-title">Pre-Experiment Planning</h3>
          <p className="power-description">How many users do you need?</p>
          
          <form onSubmit={handleSubmit} className="power-form">
            <div className="form-group">
              <label>Baseline Conversion Rate</label>
              <input
                type="number"
                step="0.01"
                value={formData.baseline_rate}
                onChange={(e) => setFormData({...formData, baseline_rate: parseFloat(e.target.value)})}
                data-testid="input-baseline"
              />
            </div>
            <div className="form-group">
              <label>Minimum Detectable Effect (%)</label>
              <input
                type="number"
                step="0.01"
                value={formData.minimum_detectable_effect}
                onChange={(e) => setFormData({...formData, minimum_detectable_effect: parseFloat(e.target.value)})}
                data-testid="input-mde"
              />
            </div>
            <div className="form-group">
              <label>Significance Level (α)</label>
              <input
                type="number"
                step="0.01"
                value={formData.alpha}
                onChange={(e) => setFormData({...formData, alpha: parseFloat(e.target.value)})}
                data-testid="input-alpha"
              />
            </div>
            <div className="form-group">
              <label>Statistical Power</label>
              <input
                type="number"
                step="0.05"
                value={formData.power}
                onChange={(e) => setFormData({...formData, power: parseFloat(e.target.value)})}
                data-testid="input-power"
              />
            </div>
            <button type="submit" className="btn-primary" data-testid="calculate-power-btn">
              Calculate Sample Size
            </button>
          </form>

          {powerCalc && (
            <div className="power-result" data-testid="power-result">
              <div className="result-highlight">
                <span className="result-value">{powerCalc.required_sample_size_per_group?.toLocaleString()}</span>
                <span className="result-label">Users per Group</span>
              </div>
              <div className="result-secondary">
                <span>Total: {powerCalc.total_sample_size?.toLocaleString()} users</span>
                <span>MDE: {powerCalc.mde_percentage?.toFixed(1)}%</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Segment Analysis Tab
const SegmentsTab = ({ segments }) => {
  const [activeSegment, setActiveSegment] = useState('device');

  const segmentConfig = {
    device: { icon: Monitor, label: 'Device Type' },
    location: { icon: MapPin, label: 'Location' },
    customer_type: { icon: Activity, label: 'Engagement Level' }
  };

  const currentData = segments?.[activeSegment];

  // Transform data for chart
  const chartData = currentData ? Object.entries(currentData).map(([name, data]) => ({
    name,
    'Control (A)': data.conversion_stats?.A?.rate_percentage || 0,
    'Treatment (B)': data.conversion_stats?.B?.rate_percentage || 0,
  })) : [];

  return (
    <div className="tab-content" data-testid="segments-tab">
      <h2 className="section-title">Segment Analysis</h2>

      <div className="segment-tabs">
        {Object.entries(segmentConfig).map(([key, { icon: Icon, label }]) => (
          <button
            key={key}
            className={`segment-tab ${activeSegment === key ? 'active' : ''}`}
            onClick={() => setActiveSegment(key)}
            data-testid={`segment-tab-${key}`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {currentData && (
        <div className="segments-grid">
          <div className="segment-chart" data-testid="segment-chart">
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" />
                <XAxis dataKey="name" tick={{ fontFamily: 'JetBrains Mono', fontSize: 11 }} />
                <YAxis tick={{ fontFamily: 'JetBrains Mono', fontSize: 11 }} label={{ value: 'Conversion Rate (%)', angle: -90, position: 'insideLeft', fontSize: 12 }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar dataKey="Control (A)" fill={COLORS.control} />
                <Bar dataKey="Treatment (B)" fill={COLORS.treatment} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="segment-details">
            {Object.entries(currentData).map(([segmentName, data]) => (
              <div key={segmentName} className="segment-card" data-testid={`segment-${segmentName}`}>
                <h4 className="segment-name">{segmentName}</h4>
                <div className="segment-stats">
                  <div className="segment-group">
                    <span className="group-label">Control (A)</span>
                    <span className="group-rate">{data.conversion_stats?.A?.rate_percentage?.toFixed(2)}%</span>
                    <span className="group-n">n={data.conversion_stats?.A?.total}</span>
                  </div>
                  <div className="segment-group treatment">
                    <span className="group-label">Treatment (B)</span>
                    <span className="group-rate">{data.conversion_stats?.B?.rate_percentage?.toFixed(2)}%</span>
                    <span className="group-n">n={data.conversion_stats?.B?.total}</span>
                  </div>
                </div>
                {data.z_test && (
                  <div className="segment-significance">
                    <span className={`p-value ${data.z_test.p_value < 0.05 ? 'significant' : ''}`}>
                      p = {data.z_test.p_value?.toFixed(4)}
                    </span>
                    <span className={`lift ${data.z_test.relative_lift > 0 ? 'positive' : 'negative'}`}>
                      {data.z_test.relative_lift > 0 ? '+' : ''}{data.z_test.relative_lift?.toFixed(1)}% lift
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Decision Support Tab
const DecisionTab = ({ analysis }) => {
  const recommendation = analysis?.recommendation;

  if (!recommendation) {
    return <div className="loading">Loading recommendation...</div>;
  }

  const decisionColors = {
    'SHIP': '#10B981',
    'DO NOT SHIP': '#EF4444',
    'EXTEND EXPERIMENT': '#F59E0B',
    'NO EFFECT': '#71717a',
    'INCONCLUSIVE': '#F59E0B'
  };

  const decisionIcons = {
    'SHIP': CheckCircle2,
    'DO NOT SHIP': XCircle,
    'EXTEND EXPERIMENT': AlertCircle,
    'NO EFFECT': AlertCircle,
    'INCONCLUSIVE': AlertCircle
  };

  const DecisionIcon = decisionIcons[recommendation.decision] || AlertCircle;

  return (
    <div className="tab-content" data-testid="decision-tab">
      <h2 className="section-title">Decision Support</h2>

      <div className="decision-container">
        <div 
          className="decision-card main"
          style={{ borderColor: decisionColors[recommendation.decision] }}
          data-testid="decision-card"
        >
          <div className="decision-header">
            <DecisionIcon 
              size={48} 
              color={decisionColors[recommendation.decision]}
              strokeWidth={1.5}
            />
            <div className="decision-title">
              <span className="decision-verdict" style={{ color: decisionColors[recommendation.decision] }}>
                {recommendation.decision}
              </span>
              <span className="decision-confidence">
                Confidence: {recommendation.confidence}
              </span>
            </div>
          </div>

          <div className="decision-reasoning">
            <h4>Analysis</h4>
            <p>{recommendation.reasoning}</p>
          </div>

          <div className="decision-action">
            <h4>Recommended Action</h4>
            <p>{recommendation.recommended_action}</p>
          </div>
        </div>

        <div className="decision-factors" data-testid="decision-factors">
          <h3 className="factors-title">Decision Factors</h3>
          
          <div className="factor-item">
            <span className="factor-label">Statistically Significant</span>
            <span className={`factor-value ${recommendation.factors.statistically_significant ? 'yes' : 'no'}`}>
              {recommendation.factors.statistically_significant ? 'Yes' : 'No'}
            </span>
          </div>
          
          <div className="factor-item">
            <span className="factor-label">Practically Significant (≥5% lift)</span>
            <span className={`factor-value ${recommendation.factors.practically_significant ? 'yes' : 'no'}`}>
              {recommendation.factors.practically_significant ? 'Yes' : 'No'}
            </span>
          </div>
          
          <div className="factor-item">
            <span className="factor-label">Adequately Powered (≥80%)</span>
            <span className={`factor-value ${recommendation.factors.adequately_powered ? 'yes' : 'no'}`}>
              {recommendation.factors.adequately_powered ? 'Yes' : 'No'}
            </span>
          </div>
          
          <div className="factor-item highlight">
            <span className="factor-label">P-Value</span>
            <span className="factor-value mono">{recommendation.factors.p_value?.toFixed(6)}</span>
          </div>
          
          <div className="factor-item highlight">
            <span className="factor-label">Relative Lift</span>
            <span className={`factor-value mono ${recommendation.factors.relative_lift > 0 ? 'positive' : 'negative'}`}>
              {recommendation.factors.relative_lift > 0 ? '+' : ''}{recommendation.factors.relative_lift?.toFixed(2)}%
            </span>
          </div>
          
          <div className="factor-item highlight">
            <span className="factor-label">Achieved Power</span>
            <span className="factor-value mono">{(recommendation.factors.achieved_power * 100)?.toFixed(1)}%</span>
          </div>
        </div>

        <div className="rollout-options" data-testid="rollout-options">
          <h3 className="factors-title">Rollout Strategy</h3>
          
          {recommendation.decision === 'SHIP' && (
            <div className="rollout-grid">
              <div className="rollout-option recommended">
                <h4>Full Rollout</h4>
                <p>Ship to 100% of users immediately</p>
              </div>
              <div className="rollout-option">
                <h4>Staged Rollout</h4>
                <p>Gradually increase from 25% → 50% → 100%</p>
              </div>
              <div className="rollout-option">
                <h4>Segment Rollout</h4>
                <p>Ship to high-performing segments first</p>
              </div>
            </div>
          )}
          
          {recommendation.decision === 'EXTEND EXPERIMENT' && (
            <div className="extend-info">
              <p>Based on current effect size, you need approximately <strong>2-3x more data</strong> to reach 80% statistical power.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Upload Tab
const UploadTab = ({ onUpload, onSeedSample, loading }) => {
  const [file, setFile] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    await onUpload(formData);
    setFile(null);
  };

  return (
    <div className="tab-content" data-testid="upload-tab">
      <h2 className="section-title">Data Management</h2>

      <div className="upload-grid">
        <div className="upload-card" data-testid="upload-file-card">
          <h3>Upload CSV File</h3>
          <p className="upload-description">
            Upload your A/B test data in CSV format. Required columns:
          </p>
          <ul className="required-columns">
            <li>User ID</li>
            <li>Group (A/B)</li>
            <li>Page Views</li>
            <li>Time Spent</li>
            <li>Conversion (Yes/No)</li>
            <li>Device</li>
            <li>Location</li>
          </ul>
          
          <div className="file-input-wrapper">
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              id="file-input"
              data-testid="file-input"
            />
            <label htmlFor="file-input" className="file-label">
              <FileUp size={20} />
              {file ? file.name : 'Choose CSV file'}
            </label>
          </div>
          
          <button
            className="btn-primary"
            onClick={handleUpload}
            disabled={!file || loading}
            data-testid="upload-btn"
          >
            {loading ? 'Uploading...' : 'Upload Data'}
          </button>
        </div>

        <div className="upload-card sample" data-testid="sample-data-card">
          <h3>Use Sample Data</h3>
          <p className="upload-description">
            Load sample A/B test data to explore the platform. This simulates 5,000 users 
            testing white vs black website backgrounds.
          </p>
          <div className="sample-info">
            <div className="info-item">
              <span className="info-label">Users</span>
              <span className="info-value">5,000</span>
            </div>
            <div className="info-item">
              <span className="info-label">Groups</span>
              <span className="info-value">A (Control), B (Treatment)</span>
            </div>
            <div className="info-item">
              <span className="info-label">Devices</span>
              <span className="info-value">Desktop, Mobile</span>
            </div>
            <div className="info-item">
              <span className="info-label">Locations</span>
              <span className="info-value">England, Scotland, Wales, N. Ireland</span>
            </div>
          </div>
          <button
            className="btn-secondary"
            onClick={onSeedSample}
            disabled={loading}
            data-testid="seed-sample-btn"
          >
            {loading ? 'Loading...' : 'Load Sample Data'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [overview, setOverview] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [segments, setSegments] = useState({});
  const [chartData, setChartData] = useState({});
  const [powerCalc, setPowerCalc] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [overviewRes, analysisRes, conversionRes] = await Promise.all([
        axios.get(`${API}/overview`),
        axios.get(`${API}/analysis`),
        axios.get(`${API}/charts/conversion`)
      ]);

      setOverview(overviewRes.data);
      setAnalysis(analysisRes.data);
      setChartData({ conversion: conversionRes.data });

      // Fetch segments
      const [deviceRes, locationRes, customerRes] = await Promise.all([
        axios.get(`${API}/segments/device`),
        axios.get(`${API}/segments/location`),
        axios.get(`${API}/segments/customer-type`)  // Uses dedicated endpoint
      ]);

      setSegments({
        device: deviceRes.data.segments,
        location: locationRes.data.segments,
        customer_type: customerRes.data.segments
      });

      setError(null);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('No data available. Please upload data or load sample data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleUpload = async (formData) => {
    setLoading(true);
    try {
      await axios.post(`${API}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      await fetchData();
    } catch (err) {
      setError('Upload failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSeedSample = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/seed-sample`);
      await fetchData();
    } catch (err) {
      setError('Failed to load sample data: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCalculatePower = async (params) => {
    try {
      const res = await axios.post(`${API}/power-analysis`, params);
      setPowerCalc(res.data);
    } catch (err) {
      console.error('Power calculation error:', err);
    }
  };

  const renderTab = () => {
    if (error && activeTab !== 'upload') {
      return (
        <div className="error-state" data-testid="error-state">
          <AlertCircle size={48} />
          <h3>No Data Available</h3>
          <p>{error}</p>
          <button className="btn-primary" onClick={() => setActiveTab('upload')}>
            Go to Data Upload
          </button>
        </div>
      );
    }

    switch (activeTab) {
      case 'overview':
        return <OverviewTab overview={overview} chartData={chartData} />;
      case 'analysis':
        return <AnalysisTab analysis={analysis} />;
      case 'power':
        return <PowerTab analysis={analysis} powerCalc={powerCalc} onCalculatePower={handleCalculatePower} />;
      case 'segments':
        return <SegmentsTab segments={segments} />;
      case 'decision':
        return <DecisionTab analysis={analysis} />;
      case 'upload':
        return <UploadTab onUpload={handleUpload} onSeedSample={handleSeedSample} loading={loading} />;
      default:
        return null;
    }
  };

  return (
    <div className="app-container" data-testid="app-container">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="main-content">
        {renderTab()}
      </main>
    </div>
  );
}

export default App;
