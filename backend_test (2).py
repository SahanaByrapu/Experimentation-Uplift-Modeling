#!/usr/bin/env python3
"""
Backend API Testing for A/B Test Analysis Platform
Tests all API endpoints with comprehensive validation
"""

import requests
import json
import sys
from datetime import datetime

# Use the public URL from frontend/.env
BACKEND_URL = "https://ab-test-uplift.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class ABTestAPITester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
    def log_test(self, test_name, success, message=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED")
        else:
            self.failed_tests.append({"test": test_name, "error": message})
            print(f"❌ {test_name}: FAILED - {message}")

    def test_health_check(self):
        """Test API health endpoint"""
        try:
            response = requests.get(f"{API_BASE}/health", timeout=10)
            success = response.status_code == 200
            self.log_test("Health Check", success, 
                         f"Status: {response.status_code}" if not success else "")
            return success
        except Exception as e:
            self.log_test("Health Check", False, str(e))
            return False

    def test_root_endpoint(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{API_BASE}/", timeout=10)
            success = response.status_code == 200 and "A/B Test Analysis API" in response.json().get("message", "")
            self.log_test("Root Endpoint", success, 
                         f"Status: {response.status_code}" if not success else "")
            return success
        except Exception as e:
            self.log_test("Root Endpoint", False, str(e))
            return False

    def test_seed_sample_data(self):
        """Test seeding sample data"""
        try:
            response = requests.post(f"{API_BASE}/seed-sample", timeout=30)
            success = response.status_code == 200 and "records" in response.json()
            self.log_test("Seed Sample Data", success, 
                         f"Status: {response.status_code}" if not success else f"Seeded {response.json().get('records', 0)} records")
            return success, response.json().get('records', 0) if success else 0
        except Exception as e:
            self.log_test("Seed Sample Data", False, str(e))
            return False, 0

    def test_overview_endpoint(self):
        """Test overview data endpoint"""
        try:
            response = requests.get(f"{API_BASE}/overview", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ["total_users", "control_users", "treatment_users", "overall_conversion_rate", "conversion_stats"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    error_msg = f"Missing fields: {missing_fields}"
                else:
                    # Check if we have expected user count (5000)
                    total_users = data.get("total_users", 0)
                    expected_users = 5000
                    if total_users != expected_users:
                        print(f"⚠️  Expected {expected_users} users, got {total_users}")
                    error_msg = f"Total users: {total_users}"
            else:
                error_msg = f"Status: {response.status_code}"
                
            self.log_test("Overview Endpoint", success, error_msg if not success else f"Users: {data.get('total_users', 0)}")
            return success
        except Exception as e:
            self.log_test("Overview Endpoint", False, str(e))
            return False

    def test_analysis_endpoint(self):
        """Test statistical analysis endpoint"""
        try:
            response = requests.get(f"{API_BASE}/analysis", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_analyses = ["z_test", "chi_square", "page_views_analysis", "time_spent_analysis", "power_analysis", "recommendation"]
                missing_analyses = [analysis for analysis in required_analyses if analysis not in data]
                
                if missing_analyses:
                    success = False
                    error_msg = f"Missing analyses: {missing_analyses}"
                else:
                    # Check z-test results
                    z_test = data.get("z_test", {})
                    p_value = z_test.get("p_value")
                    lift = z_test.get("relative_lift")
                    error_msg = f"p-value: {p_value:.6f}, lift: {lift:.2f}%" if p_value and lift else "Analysis complete"
            else:
                error_msg = f"Status: {response.status_code}"
                
            self.log_test("Statistical Analysis", success, error_msg if not success else error_msg)
            return success
        except Exception as e:
            self.log_test("Statistical Analysis", False, str(e))
            return False

    def test_segments_device(self):
        """Test device segmentation endpoint"""
        try:
            response = requests.get(f"{API_BASE}/segments/device", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                segments = data.get("segments", {})
                expected_devices = ["Desktop", "Mobile"]
                found_devices = list(segments.keys())
                
                if not all(device in found_devices for device in expected_devices):
                    success = False
                    error_msg = f"Expected devices {expected_devices}, found {found_devices}"
                else:
                    error_msg = f"Segments: {found_devices}"
            else:
                error_msg = f"Status: {response.status_code}"
                
            self.log_test("Device Segmentation", success, error_msg if not success else error_msg)
            return success
        except Exception as e:
            self.log_test("Device Segmentation", False, str(e))
            return False

    def test_segments_location(self):
        """Test location segmentation endpoint"""
        try:
            response = requests.get(f"{API_BASE}/segments/location", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                segments = data.get("segments", {})
                expected_locations = ["England", "Scotland", "Wales", "Northern Ireland"]
                found_locations = list(segments.keys())
                
                missing_locations = [loc for loc in expected_locations if loc not in found_locations]
                if missing_locations:
                    print(f"⚠️  Missing locations: {missing_locations}")
                    
                error_msg = f"Locations: {found_locations}"
            else:
                error_msg = f"Status: {response.status_code}"
                
            self.log_test("Location Segmentation", success, error_msg if not success else error_msg)
            return success
        except Exception as e:
            self.log_test("Location Segmentation", False, str(e))
            return False

    def test_segments_customer_type(self):
        """Test customer engagement segmentation endpoint"""
        try:
            response = requests.get(f"{API_BASE}/segments/customer-type", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                segments = data.get("segments", {})
                expected_types = ["High Engagement", "Medium Engagement", "Low Engagement"]
                found_types = list(segments.keys())
                
                if not any(engagement_type in found_types for engagement_type in expected_types):
                    success = False
                    error_msg = f"Expected engagement types, found {found_types}"
                else:
                    error_msg = f"Engagement levels: {found_types}"
            else:
                error_msg = f"Status: {response.status_code}"
                
            self.log_test("Customer Type Segmentation", success, error_msg if not success else error_msg)
            return success
        except Exception as e:
            self.log_test("Customer Type Segmentation", False, str(e))
            return False

    def test_power_analysis_calculation(self):
        """Test power analysis calculation endpoint"""
        try:
            payload = {
                "baseline_rate": 0.09,
                "minimum_detectable_effect": 0.15,
                "alpha": 0.05,
                "power": 0.8
            }
            
            response = requests.post(f"{API_BASE}/power-analysis", 
                                   json=payload, 
                                   headers={"Content-Type": "application/json"},
                                   timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ["required_sample_size_per_group", "total_sample_size", "effect_size"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    error_msg = f"Missing fields: {missing_fields}"
                else:
                    sample_size = data.get("required_sample_size_per_group", 0)
                    error_msg = f"Sample size per group: {sample_size:,}"
            else:
                error_msg = f"Status: {response.status_code}"
                
            self.log_test("Power Analysis Calculation", success, error_msg if not success else error_msg)
            return success
        except Exception as e:
            self.log_test("Power Analysis Calculation", False, str(e))
            return False

    def test_conversion_chart_data(self):
        """Test conversion chart data endpoint"""
        try:
            response = requests.get(f"{API_BASE}/charts/conversion", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ["groups", "conversion_rates", "sample_sizes", "relative_lift", "p_value"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    error_msg = f"Missing fields: {missing_fields}"
                else:
                    groups = data.get("groups", [])
                    rates = data.get("conversion_rates", [])
                    error_msg = f"Groups: {groups}, Rates: {rates}"
            else:
                error_msg = f"Status: {response.status_code}"
                
            self.log_test("Conversion Chart Data", success, error_msg if not success else error_msg)
            return success
        except Exception as e:
            self.log_test("Conversion Chart Data", False, str(e))
            return False

    def test_data_retrieval(self):
        """Test data retrieval endpoint"""
        try:
            response = requests.get(f"{API_BASE}/data", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                count = data.get("count", 0)
                data_records = data.get("data", [])
                
                if count == 0 or not data_records:
                    success = False
                    error_msg = "No data records found"
                else:
                    # Check first record structure
                    first_record = data_records[0]
                    required_fields = ["user_id", "group", "conversion", "device", "location"]
                    missing_fields = [field for field in required_fields if field not in first_record]
                    
                    if missing_fields:
                        success = False
                        error_msg = f"Data missing fields: {missing_fields}"
                    else:
                        error_msg = f"Records: {count:,}"
            else:
                error_msg = f"Status: {response.status_code}"
                
            self.log_test("Data Retrieval", success, error_msg if not success else error_msg)
            return success
        except Exception as e:
            self.log_test("Data Retrieval", False, str(e))
            return False

    def run_all_tests(self):
        """Run all API tests in sequence"""
        print("🧪 Starting A/B Test Analysis API Testing")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Basic connectivity tests
        health_ok = self.test_health_check()
        root_ok = self.test_root_endpoint()
        
        if not (health_ok and root_ok):
            print("\n❌ Basic connectivity failed. Stopping tests.")
            return False
        
        # Seed data first
        seed_ok, record_count = self.test_seed_sample_data()
        if not seed_ok:
            print("\n❌ Failed to seed sample data. Some tests may fail.")
        
        # Core functionality tests
        self.test_overview_endpoint()
        self.test_analysis_endpoint()
        
        # Segmentation tests
        self.test_segments_device()
        self.test_segments_location()
        self.test_segments_customer_type()
        
        # Calculation tests
        self.test_power_analysis_calculation()
        
        # Chart data tests
        self.test_conversion_chart_data()
        
        # Data tests
        self.test_data_retrieval()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for failure in self.failed_tests:
                print(f"   • {failure['test']}: {failure['error']}")
        else:
            print("\n🎉 All tests passed!")
            
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = ABTestAPITester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())