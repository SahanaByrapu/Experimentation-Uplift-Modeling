# A/B Test Analysis & Experimentation Platform - PRD

## Original Problem Statement
Build an Experimentation & Uplift Modeling platform for A/B test analysis using Kaggle dataset. Features include:
- Calculate metrics correctly
- Check statistical assumptions
- Understand significance vs practical significance
- Power analysis (pre and post experimentation)
- Segmenting results (New vs Loyal customers, Mobile vs Desktop)
- Decision support: Ship/Don't Ship/Extend experiment

## User Choices
- Interactive charts with Recharts
- Advanced statistical analysis (power analysis, Bayesian analysis, multi-armed bandit)
- Segmentation: New vs Loyal (via engagement), Mobile vs Desktop, Location-based
- AI-powered decision recommendations

## Architecture
- **Frontend**: React 19 + Recharts for visualization + Tailwind CSS
- **Backend**: FastAPI with comprehensive statistical analysis
- **Database**: MongoDB for experiment data storage
- **Statistical Libraries**: scipy, statsmodels, numpy, pandas

## User Personas
1. **Data Analysts** - Need rigorous statistical analysis of experiments
2. **Product Managers** - Need clear decision recommendations
3. **Growth Teams** - Need segmentation insights for targeted rollouts

## Core Requirements
- [x] Upload/seed A/B test data
- [x] Calculate conversion rates per group
- [x] Z-test for proportions
- [x] Chi-square test for independence
- [x] T-tests for continuous metrics (page views, time spent)
- [x] Power analysis (pre and post experiment)
- [x] Segmentation by device, location, engagement level
- [x] AI-powered ship/don't ship recommendations
- [x] Interactive visualization

## What's Been Implemented (Feb 17, 2026)

### Backend (server.py)
- `/api/seed-sample` - Load 5000 sample users
- `/api/upload` - CSV file upload
- `/api/overview` - Key experiment metrics
- `/api/analysis` - Full statistical analysis (Z-test, Chi-square, T-tests)
- `/api/power-analysis` - Sample size calculator
- `/api/segments/{device|location}` - Segment analysis
- `/api/segments/customer-type` - Engagement-based segmentation
- `/api/charts/conversion` - Chart data

### Frontend (App.js)
- **Overview Tab**: Total users, group breakdown, conversion rates, device/location charts
- **Statistical Analysis Tab**: Z-test, Chi-square, Page views T-test, Time spent T-test
- **Power Analysis Tab**: Achieved power display, sample size calculator
- **Segment Analysis Tab**: Device, Location, Engagement Level breakdown with charts
- **Decision Support Tab**: AI recommendation (SHIP/NO SHIP/EXTEND), confidence level, rollout strategies
- **Data Upload Tab**: CSV upload + sample data seeding

### Key Metrics (Sample Data)
- Total Users: 5,000
- Control (A): 2,504 users, 8.35% conversion
- Treatment (B): 2,496 users, 10.66% conversion
- Relative Lift: +27.68%
- P-value: 0.005339 (Statistically Significant)
- Achieved Power: 79.5%
- Decision: **SHIP**

## Prioritized Backlog

### P0 - Critical (Completed)
- [x] Basic A/B test analysis
- [x] Statistical significance testing
- [x] Decision recommendation engine

### P1 - High Priority (Future)
- [ ] Bayesian analysis with prior specification
- [ ] Multi-armed bandit comparison
- [ ] Export reports as PDF
- [ ] Historical experiment tracking

### P2 - Medium Priority (Future)
- [ ] Real-time data integration
- [ ] Multiple experiment comparison
- [ ] Custom metric definitions
- [ ] Alert thresholds for significance

## Next Tasks
1. Add Bayesian A/B testing analysis
2. Implement experiment history/tracking
3. Add PDF export for reports
4. Support for multi-variate testing
