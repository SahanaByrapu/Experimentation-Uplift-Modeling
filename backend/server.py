from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.power import TTestIndPower, NormalIndPower
from statsmodels.stats.proportion import proportions_ztest, proportion_confint
import io

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Models
class ExperimentData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int
    group: str
    page_views: int
    time_spent: float
    conversion: bool
    device: str
    location: str

class AnalysisRequest(BaseModel):
    metric: str = "conversion"
    confidence_level: float = 0.95

class PowerAnalysisRequest(BaseModel):
    baseline_rate: float
    minimum_detectable_effect: float
    alpha: float = 0.05
    power: float = 0.8
    ratio: float = 1.0

class SegmentRequest(BaseModel):
    segment_by: str  # "device", "location", "customer_type"

# Statistical Analysis Functions
def calculate_conversion_stats(df: pd.DataFrame, group_col: str = "group", conversion_col: str = "conversion"):
    """Calculate conversion rates and basic stats for each group"""
    stats_dict = {}
    for group in df[group_col].unique():
        group_data = df[df[group_col] == group]
        conversions = group_data[conversion_col].sum()
        total = len(group_data)
        rate = conversions / total if total > 0 else 0
        stats_dict[group] = {
            "conversions": int(conversions),
            "total": int(total),
            "conversion_rate": float(rate),
            "rate_percentage": float(rate * 100)
        }
    return stats_dict

def perform_chi_square_test(df: pd.DataFrame):
    """Perform chi-square test for independence"""
    contingency = pd.crosstab(df['group'], df['conversion'])
    chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
    return {
        "chi2_statistic": float(chi2),
        "p_value": float(p_value),
        "degrees_of_freedom": int(dof),
        "expected_frequencies": expected.tolist()
    }

def perform_t_test(df: pd.DataFrame, metric: str):
    """Perform independent t-test for continuous metrics"""
    group_a = df[df['group'] == 'A'][metric].values
    group_b = df[df['group'] == 'B'][metric].values
    
    t_stat, p_value = stats.ttest_ind(group_a, group_b)
    
    # Effect size (Cohen's d)
    pooled_std = np.sqrt(((len(group_a)-1)*np.std(group_a, ddof=1)**2 + 
                          (len(group_b)-1)*np.std(group_b, ddof=1)**2) / 
                         (len(group_a)+len(group_b)-2))
    cohens_d = (np.mean(group_b) - np.mean(group_a)) / pooled_std if pooled_std > 0 else 0
    
    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "cohens_d": float(cohens_d),
        "group_a_mean": float(np.mean(group_a)),
        "group_b_mean": float(np.mean(group_b)),
        "group_a_std": float(np.std(group_a, ddof=1)),
        "group_b_std": float(np.std(group_b, ddof=1)),
        "mean_difference": float(np.mean(group_b) - np.mean(group_a)),
        "relative_lift": float((np.mean(group_b) - np.mean(group_a)) / np.mean(group_a) * 100) if np.mean(group_a) > 0 else 0
    }

def perform_z_test_proportions(df: pd.DataFrame):
    """Perform z-test for proportions (conversion rates)"""
    group_a = df[df['group'] == 'A']
    group_b = df[df['group'] == 'B']
    
    count_a = group_a['conversion'].sum()
    count_b = group_b['conversion'].sum()
    nobs_a = len(group_a)
    nobs_b = len(group_b)
    
    z_stat, p_value = proportions_ztest([count_b, count_a], [nobs_b, nobs_a], alternative='two-sided')
    
    # Confidence intervals
    ci_a = proportion_confint(count_a, nobs_a, alpha=0.05, method='wilson')
    ci_b = proportion_confint(count_b, nobs_b, alpha=0.05, method='wilson')
    
    rate_a = count_a / nobs_a if nobs_a > 0 else 0
    rate_b = count_b / nobs_b if nobs_b > 0 else 0
    
    return {
        "z_statistic": float(z_stat),
        "p_value": float(p_value),
        "control_rate": float(rate_a),
        "treatment_rate": float(rate_b),
        "absolute_difference": float(rate_b - rate_a),
        "relative_lift": float((rate_b - rate_a) / rate_a * 100) if rate_a > 0 else 0,
        "control_ci": [float(ci_a[0]), float(ci_a[1])],
        "treatment_ci": [float(ci_b[0]), float(ci_b[1])]
    }

def calculate_power_analysis(baseline_rate: float, mde: float, alpha: float = 0.05, 
                            power: float = 0.8, ratio: float = 1.0):
    """Calculate required sample size for given parameters"""
    effect_size = abs(mde * baseline_rate) / np.sqrt(baseline_rate * (1 - baseline_rate))
    
    analysis = TTestIndPower()
    sample_size = analysis.solve_power(effect_size=effect_size, alpha=alpha, 
                                        power=power, ratio=ratio, alternative='two-sided')
    
    return {
        "required_sample_size_per_group": int(np.ceil(sample_size)),
        "total_sample_size": int(np.ceil(sample_size * (1 + ratio))),
        "effect_size": float(effect_size),
        "baseline_rate": float(baseline_rate),
        "mde_percentage": float(mde * 100),
        "target_rate": float(baseline_rate * (1 + mde)),
        "alpha": float(alpha),
        "power": float(power)
    }

def calculate_achieved_power(df: pd.DataFrame, alpha: float = 0.05):
    """Calculate achieved statistical power given current data"""
    group_a = df[df['group'] == 'A']
    group_b = df[df['group'] == 'B']
    
    n_a = len(group_a)
    n_b = len(group_b)
    
    rate_a = group_a['conversion'].mean()
    rate_b = group_b['conversion'].mean()
    
    # Calculate effect size
    pooled_rate = (group_a['conversion'].sum() + group_b['conversion'].sum()) / (n_a + n_b)
    effect_size = abs(rate_b - rate_a) / np.sqrt(pooled_rate * (1 - pooled_rate)) if pooled_rate > 0 and pooled_rate < 1 else 0
    
    analysis = TTestIndPower()
    achieved_power = analysis.solve_power(effect_size=effect_size if effect_size > 0 else 0.001, 
                                          nobs1=n_a, alpha=alpha, ratio=n_b/n_a if n_a > 0 else 1,
                                          alternative='two-sided')
    
    return {
        "achieved_power": float(achieved_power),
        "sample_size_control": int(n_a),
        "sample_size_treatment": int(n_b),
        "observed_effect_size": float(effect_size),
        "is_adequately_powered": bool(achieved_power >= 0.8)
    }

def generate_recommendation(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate AI-powered recommendation based on analysis"""
    p_value = analysis_results.get('z_test', {}).get('p_value', 1.0)
    relative_lift = analysis_results.get('z_test', {}).get('relative_lift', 0)
    achieved_power = analysis_results.get('power_analysis', {}).get('achieved_power', 0)
    
    # Determine statistical significance
    is_significant = p_value < 0.05
    
    # Determine practical significance (at least 5% lift)
    is_practical = abs(relative_lift) >= 5
    
    # Determine if adequately powered
    is_powered = achieved_power >= 0.8
    
    # Generate recommendation
    if is_significant and relative_lift > 0 and is_practical:
        decision = "SHIP"
        confidence = "HIGH" if is_powered else "MEDIUM"
        reasoning = f"The treatment shows a statistically significant positive effect with {relative_lift:.1f}% lift in conversion rate."
        action = "Roll out the new feature to all users."
    elif is_significant and relative_lift < 0:
        decision = "DO NOT SHIP"
        confidence = "HIGH" if is_powered else "MEDIUM"
        reasoning = f"The treatment shows a statistically significant negative effect with {relative_lift:.1f}% decline in conversion rate."
        action = "Revert to the control version and investigate the negative impact."
    elif not is_significant and not is_powered:
        decision = "EXTEND EXPERIMENT"
        confidence = "LOW"
        reasoning = f"The experiment lacks statistical power ({achieved_power*100:.1f}%). More data is needed."
        action = f"Continue running the experiment until achieving 80% power."
    elif not is_significant and is_powered:
        decision = "NO EFFECT"
        confidence = "HIGH"
        reasoning = "With adequate statistical power, no significant difference was detected between groups."
        action = "The feature has no measurable impact. Consider alternative approaches or ship based on other factors."
    else:
        decision = "INCONCLUSIVE"
        confidence = "LOW"
        reasoning = "Results are inconclusive. Consider running the experiment longer or with a larger sample."
        action = "Gather more data or re-evaluate the experiment design."
    
    return {
        "decision": decision,
        "confidence": confidence,
        "reasoning": reasoning,
        "recommended_action": action,
        "factors": {
            "statistically_significant": is_significant,
            "practically_significant": is_practical,
            "adequately_powered": is_powered,
            "p_value": p_value,
            "relative_lift": relative_lift,
            "achieved_power": achieved_power
        }
    }

def analyze_segment(df: pd.DataFrame, segment_col: str) -> Dict[str, Any]:
    """Analyze results by segment"""
    segments = {}
    for segment in df[segment_col].unique():
        segment_df = df[df[segment_col] == segment]
        
        conversion_stats = calculate_conversion_stats(segment_df)
        
        # Only perform z-test if we have both groups
        if len(segment_df['group'].unique()) == 2:
            z_test = perform_z_test_proportions(segment_df)
        else:
            z_test = None
        
        segments[segment] = {
            "sample_size": len(segment_df),
            "conversion_stats": conversion_stats,
            "z_test": z_test
        }
    
    return segments

# Sample data generation (matching Kaggle dataset structure)
def generate_sample_data() -> pd.DataFrame:
    """Generate sample A/B test data similar to Kaggle dataset"""
    np.random.seed(42)
    n_users = 5000
    
    user_ids = list(range(10001, 10001 + n_users))
    groups = np.random.choice(['A', 'B'], n_users)
    devices = np.random.choice(['Desktop', 'Mobile'], n_users, p=[0.51, 0.49])
    locations = np.random.choice(['England', 'Scotland', 'Wales', 'Northern Ireland'], n_users, p=[0.25, 0.26, 0.25, 0.24])
    
    # Page views (1-14)
    page_views = np.random.randint(1, 15, n_users)
    
    # Time spent (40-449 seconds)
    time_spent = np.random.randint(40, 450, n_users)
    
    # Conversion rates slightly different for groups
    # Group A (Control): ~9% conversion
    # Group B (Treatment): ~10.5% conversion
    conversions = []
    for i, group in enumerate(groups):
        base_rate = 0.09 if group == 'A' else 0.105
        # Device effect: Mobile slightly lower
        if devices[i] == 'Mobile':
            base_rate *= 0.95
        # Location effect
        if locations[i] == 'Scotland':
            base_rate *= 1.05
        conversions.append(np.random.random() < base_rate)
    
    df = pd.DataFrame({
        'user_id': user_ids,
        'group': groups,
        'page_views': page_views,
        'time_spent': time_spent,
        'conversion': conversions,
        'device': devices,
        'location': locations
    })
    
    return df

# Routes
@api_router.get("/")
async def root():
    return {"message": "A/B Test Analysis API"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}

@api_router.post("/upload")
async def upload_data(file: UploadFile = File(...)):
    """Upload CSV data for analysis"""
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Validate required columns
        required_cols = ['User ID', 'Group', 'Page Views', 'Time Spent', 'Conversion', 'Device', 'Location']
        if not all(col in df.columns for col in required_cols):
            raise HTTPException(status_code=400, detail=f"Missing required columns. Expected: {required_cols}")
        
        # Rename columns to match our schema
        df = df.rename(columns={
            'User ID': 'user_id',
            'Group': 'group',
            'Page Views': 'page_views',
            'Time Spent': 'time_spent',
            'Conversion': 'conversion',
            'Device': 'device',
            'Location': 'location'
        })
        
        # Convert conversion to boolean
        df['conversion'] = df['conversion'].apply(lambda x: x == 'Yes' if isinstance(x, str) else bool(x))
        
        # Store in MongoDB
        await db.experiment_data.delete_many({})  # Clear existing data
        records = df.to_dict('records')
        await db.experiment_data.insert_many(records)
        
        return {"message": "Data uploaded successfully", "records": len(records)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/seed-sample")
async def seed_sample_data():
    """Seed the database with sample data"""
    df = generate_sample_data()
    await db.experiment_data.delete_many({})
    records = df.to_dict('records')
    await db.experiment_data.insert_many(records)
    return {"message": "Sample data seeded successfully", "records": len(records)}

@api_router.get("/data")
async def get_data():
    """Get all experiment data"""
    data = await db.experiment_data.find({}, {"_id": 0}).to_list(10000)
    return {"data": data, "count": len(data)}

@api_router.get("/overview")
async def get_overview():
    """Get experiment overview with key metrics"""
    data = await db.experiment_data.find({}, {"_id": 0}).to_list(10000)
    
    if not data:
        return {"error": "No data available. Please upload data first."}
    
    df = pd.DataFrame(data)
    
    conversion_stats = calculate_conversion_stats(df)
    
    overview = {
        "total_users": len(df),
        "control_users": len(df[df['group'] == 'A']),
        "treatment_users": len(df[df['group'] == 'B']),
        "overall_conversion_rate": float(df['conversion'].mean() * 100),
        "conversion_stats": conversion_stats,
        "avg_page_views": float(df['page_views'].mean()),
        "avg_time_spent": float(df['time_spent'].mean()),
        "device_distribution": df['device'].value_counts().to_dict(),
        "location_distribution": df['location'].value_counts().to_dict()
    }
    
    return overview

@api_router.get("/analysis")
async def get_full_analysis():
    """Get comprehensive statistical analysis"""
    data = await db.experiment_data.find({}, {"_id": 0}).to_list(10000)
    
    if not data:
        return {"error": "No data available"}
    
    df = pd.DataFrame(data)
    
    # Conversion analysis
    conversion_stats = calculate_conversion_stats(df)
    z_test = perform_z_test_proportions(df)
    chi_square = perform_chi_square_test(df)
    
    # Continuous metrics analysis
    page_views_test = perform_t_test(df, 'page_views')
    time_spent_test = perform_t_test(df, 'time_spent')
    
    # Power analysis
    power_analysis = calculate_achieved_power(df)
    
    analysis = {
        "conversion_stats": conversion_stats,
        "z_test": z_test,
        "chi_square": chi_square,
        "page_views_analysis": page_views_test,
        "time_spent_analysis": time_spent_test,
        "power_analysis": power_analysis
    }
    
    # Generate recommendation
    analysis["recommendation"] = generate_recommendation(analysis)
    
    return analysis

@api_router.post("/power-analysis")
async def power_analysis_endpoint(request: PowerAnalysisRequest):
    """Calculate required sample size"""
    result = calculate_power_analysis(
        baseline_rate=request.baseline_rate,
        mde=request.minimum_detectable_effect,
        alpha=request.alpha,
        power=request.power,
        ratio=request.ratio
    )
    return result

@api_router.get("/segments/customer-type")
async def get_customer_type_analysis():
    """Analyze by customer engagement level (proxy for new vs loyal)"""
    data = await db.experiment_data.find({}, {"_id": 0}).to_list(10000)
    
    if not data:
        return {"error": "No data available"}
    
    df = pd.DataFrame(data)
    
    # Define customer types based on page views and time spent
    median_views = df['page_views'].median()
    median_time = df['time_spent'].median()
    
    df['customer_type'] = df.apply(
        lambda x: 'High Engagement' if x['page_views'] >= median_views and x['time_spent'] >= median_time 
        else ('Low Engagement' if x['page_views'] < median_views and x['time_spent'] < median_time 
              else 'Medium Engagement'),
        axis=1
    )
    
    segments = analyze_segment(df, 'customer_type')
    
    return {
        "segment_by": "customer_type",
        "segments": segments,
        "thresholds": {
            "median_page_views": float(median_views),
            "median_time_spent": float(median_time)
        }
    }

@api_router.get("/segments/{segment_by}")
async def get_segment_analysis(segment_by: str):
    """Get analysis segmented by device, location, or customer behavior"""
    valid_segments = ['device', 'location']
    
    if segment_by not in valid_segments:
        raise HTTPException(status_code=400, detail=f"Invalid segment. Choose from: {valid_segments}")
    
    data = await db.experiment_data.find({}, {"_id": 0}).to_list(10000)
    
    if not data:
        return {"error": "No data available"}
    
    df = pd.DataFrame(data)
    
    segments = analyze_segment(df, segment_by)
    
    return {"segment_by": segment_by, "segments": segments}

@api_router.get("/charts/conversion")
async def get_conversion_chart_data():
    """Get data for conversion rate visualization"""
    data = await db.experiment_data.find({}, {"_id": 0}).to_list(10000)
    
    if not data:
        return {"error": "No data available"}
    
    df = pd.DataFrame(data)
    
    conversion_stats = calculate_conversion_stats(df)
    z_test = perform_z_test_proportions(df)
    
    return {
        "groups": list(conversion_stats.keys()),
        "conversion_rates": [conversion_stats[g]['rate_percentage'] for g in conversion_stats],
        "sample_sizes": [conversion_stats[g]['total'] for g in conversion_stats],
        "confidence_intervals": {
            "A": z_test['control_ci'],
            "B": z_test['treatment_ci']
        },
        "relative_lift": z_test['relative_lift'],
        "p_value": z_test['p_value']
    }

@api_router.get("/charts/segment/{segment_by}")
async def get_segment_chart_data(segment_by: str):
    """Get data for segment visualization"""
    if segment_by == 'customer_type':
        result = await get_customer_type_analysis()
    else:
        result = await get_segment_analysis(segment_by)
    
    chart_data = []
    for segment_name, segment_data in result['segments'].items():
        conv_stats = segment_data['conversion_stats']
        for group, stats in conv_stats.items():
            chart_data.append({
                "segment": segment_name,
                "group": group,
                "conversion_rate": stats['rate_percentage'],
                "sample_size": stats['total']
            })
    
    return {"chart_data": chart_data, "segment_by": segment_by}

@api_router.get("/charts/distribution/{metric}")
async def get_distribution_chart_data(metric: str):
    """Get distribution data for page views or time spent"""
    valid_metrics = ['page_views', 'time_spent']
    
    if metric not in valid_metrics:
        raise HTTPException(status_code=400, detail=f"Invalid metric. Choose from: {valid_metrics}")
    
    data = await db.experiment_data.find({}, {"_id": 0}).to_list(10000)
    
    if not data:
        return {"error": "No data available"}
    
    df = pd.DataFrame(data)
    
    result = {
        "metric": metric,
        "groups": {}
    }
    
    for group in ['A', 'B']:
        group_data = df[df['group'] == group][metric]
        result["groups"][group] = {
            "values": group_data.tolist(),
            "mean": float(group_data.mean()),
            "std": float(group_data.std()),
            "median": float(group_data.median()),
            "min": float(group_data.min()),
            "max": float(group_data.max())
        }
    
    return result

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
