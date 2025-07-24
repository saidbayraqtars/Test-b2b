#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for B2B E-commerce Platform
Tests all major endpoints and workflows
"""

import requests
import sys
import json
from datetime import datetime

class B2BAPITester:
    def __init__(self, base_url="https://9901ed96-b7f9-4ceb-87d9-be26f4ca4748.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tokens = {}
        self.users = {}
        self.test_data = {}
        self.tests_run = 0
        self.tests_passed = 0

    def log(self, message, level="INFO"):
        """Log test messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None, description=""):
        """Run a single API test"""
        url = f"{self.api_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        if description:
            self.log(f"   Description: {description}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    return True, response_data
                except:
                    return True, {}
            else:
                self.log(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data}")
                except:
                    self.log(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            self.log(f"❌ FAILED - Exception: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test basic health endpoint"""
        self.log("\n🏥 Testing Health Check...")
        success, data = self.run_test(
            "Health Check",
            "GET",
            "/health",
            200,
            description="Basic connectivity test"
        )
        return success

    def test_authentication(self):
        """Test authentication for all user roles"""
        self.log("\n🔐 Testing Authentication...")
        
        # Test users from init_data.py
        test_users = [
            {"email": "admin@b2bcommerce.com", "password": "admin123", "role": "admin"},
            {"email": "supplier@chemcorp.com", "password": "supplier123", "role": "supplier"},
            {"email": "buyer@manufacturing.com", "password": "buyer123", "role": "buyer"}
        ]
        
        all_passed = True
        for user in test_users:
            success, data = self.run_test(
                f"Login {user['role']}",
                "POST",
                "/login",
                200,
                data={"email": user["email"], "password": user["password"]},
                description=f"Login as {user['role']} user"
            )
            
            if success and 'access_token' in data:
                self.tokens[user['role']] = data['access_token']
                self.users[user['role']] = data['user']
                self.log(f"   ✅ Token stored for {user['role']}")
            else:
                all_passed = False
                self.log(f"   ❌ Failed to get token for {user['role']}")
        
        # Test invalid login
        success, _ = self.run_test(
            "Invalid Login",
            "POST",
            "/login",
            401,
            data={"email": "invalid@test.com", "password": "wrongpass"},
            description="Should fail with invalid credentials"
        )
        
        return all_passed and success

    def test_user_info(self):
        """Test getting current user info"""
        self.log("\n👤 Testing User Info...")
        
        all_passed = True
        for role in ['admin', 'supplier', 'buyer']:
            if role in self.tokens:
                success, data = self.run_test(
                    f"Get {role} info",
                    "GET",
                    "/me",
                    200,
                    token=self.tokens[role],
                    description=f"Get current user info for {role}"
                )
                all_passed = all_passed and success
        
        return all_passed

    def test_categories(self):
        """Test category endpoints"""
        self.log("\n📂 Testing Categories...")
        
        # Get categories (public endpoint)
        success, data = self.run_test(
            "Get Categories",
            "GET",
            "/categories",
            200,
            description="Fetch all product categories"
        )
        
        if success and data:
            self.test_data['categories'] = data
            self.log(f"   Found {len(data)} categories")
        
        return success

    def test_products(self):
        """Test product endpoints"""
        self.log("\n📦 Testing Products...")
        
        # Get all products
        success, data = self.run_test(
            "Get All Products",
            "GET",
            "/products",
            200,
            description="Fetch all products"
        )
        
        if success and data:
            self.test_data['products'] = data
            self.log(f"   Found {len(data)} products")
            
            # Test getting specific product
            if data:
                product_id = data[0]['id']
                success2, _ = self.run_test(
                    "Get Specific Product",
                    "GET",
                    f"/products/{product_id}",
                    200,
                    description="Fetch specific product by ID"
                )
                success = success and success2
        
        # Test supplier's products (requires supplier token)
        if 'supplier' in self.tokens:
            success3, supplier_products = self.run_test(
                "Get Supplier Products",
                "GET",
                "/my-products",
                200,
                token=self.tokens['supplier'],
                description="Get products owned by supplier"
            )
            success = success and success3
            if success3:
                self.log(f"   Supplier has {len(supplier_products)} products")
        
        return success

    def test_rfqs(self):
        """Test RFQ (Request for Quote) endpoints"""
        self.log("\n📋 Testing RFQs...")
        
        all_passed = True
        
        # Test creating RFQ as buyer
        if 'buyer' in self.tokens and self.test_data.get('products'):
            product_id = self.test_data['products'][0]['id']
            rfq_data = {
                "product_id": product_id,
                "quantity": 50,
                "message": "Test RFQ for automated testing",
                "expires_in_days": 7
            }
            
            success, rfq_response = self.run_test(
                "Create RFQ (Buyer)",
                "POST",
                "/rfqs",
                200,
                data=rfq_data,
                token=self.tokens['buyer'],
                description="Buyer creates new RFQ"
            )
            
            if success:
                self.test_data['test_rfq'] = rfq_response
                self.log(f"   Created RFQ with ID: {rfq_response.get('id')}")
            
            all_passed = all_passed and success
        
        # Test getting RFQs for different roles
        for role in ['buyer', 'supplier', 'admin']:
            if role in self.tokens:
                success, rfqs = self.run_test(
                    f"Get RFQs ({role})",
                    "GET",
                    "/rfqs",
                    200,
                    token=self.tokens[role],
                    description=f"Get RFQs visible to {role}"
                )
                
                if success:
                    self.log(f"   {role} can see {len(rfqs)} RFQs")
                
                all_passed = all_passed and success
        
        return all_passed

    def test_quotes(self):
        """Test quote submission endpoints"""
        self.log("\n💰 Testing Quotes...")
        
        all_passed = True
        
        # Test submitting quote as supplier
        if 'supplier' in self.tokens and self.test_data.get('test_rfq'):
            rfq_id = self.test_data['test_rfq']['id']
            quote_data = {
                "rfq_id": rfq_id,
                "price_per_unit": 45.99,
                "delivery_time": "2-3 weeks",
                "message": "Competitive pricing with fast delivery"
            }
            
            success, quote_response = self.run_test(
                "Submit Quote (Supplier)",
                "POST",
                "/quotes",
                200,
                data=quote_data,
                token=self.tokens['supplier'],
                description="Supplier submits quote for RFQ"
            )
            
            if success:
                self.test_data['test_quote'] = quote_response
                self.log(f"   Created quote with ID: {quote_response.get('id')}")
            
            all_passed = all_passed and success
            
            # Test getting quotes for the RFQ
            success2, quotes = self.run_test(
                "Get Quotes for RFQ",
                "GET",
                f"/quotes/{rfq_id}",
                200,
                token=self.tokens['buyer'],
                description="Buyer views quotes for their RFQ"
            )
            
            if success2:
                self.log(f"   Found {len(quotes)} quotes for RFQ")
            
            all_passed = all_passed and success2
        
        return all_passed

    def test_orders(self):
        """Test order creation endpoints"""
        self.log("\n🛒 Testing Orders...")
        
        all_passed = True
        
        # Test creating order from quote (as buyer)
        if 'buyer' in self.tokens and self.test_data.get('test_quote'):
            quote_id = self.test_data['test_quote']['id']
            order_data = {
                "quote_id": quote_id,
                "shipping_address": "123 Test Street, Test City, TC 12345"
            }
            
            success, order_response = self.run_test(
                "Create Order (Buyer)",
                "POST",
                "/orders",
                200,
                data=order_data,
                token=self.tokens['buyer'],
                description="Buyer creates order from quote"
            )
            
            if success:
                self.test_data['test_order'] = order_response
                self.log(f"   Created order with ID: {order_response.get('id')}")
            
            all_passed = all_passed and success
        
        # Test getting orders for different roles
        for role in ['buyer', 'supplier', 'admin']:
            if role in self.tokens:
                success, orders = self.run_test(
                    f"Get Orders ({role})",
                    "GET",
                    "/orders",
                    200,
                    token=self.tokens[role],
                    description=f"Get orders visible to {role}"
                )
                
                if success:
                    self.log(f"   {role} can see {len(orders)} orders")
                
                all_passed = all_passed and success
        
        return all_passed

    def test_dashboard_stats(self):
        """Test dashboard statistics endpoints"""
        self.log("\n📊 Testing Dashboard Stats...")
        
        all_passed = True
        
        for role in ['admin', 'supplier', 'buyer']:
            if role in self.tokens:
                success, stats = self.run_test(
                    f"Dashboard Stats ({role})",
                    "GET",
                    "/dashboard/stats",
                    200,
                    token=self.tokens[role],
                    description=f"Get dashboard statistics for {role}"
                )
                
                if success:
                    self.log(f"   {role} stats: {stats}")
                
                all_passed = all_passed and success
        
        return all_passed

    def test_role_based_access(self):
        """Test role-based access control"""
        self.log("\n🔒 Testing Role-Based Access Control...")
        
        all_passed = True
        
        # Test buyer trying to create product (should fail)
        if 'buyer' in self.tokens and self.test_data.get('categories'):
            category_id = self.test_data['categories'][0]['id']
            product_data = {
                "name": "Unauthorized Product",
                "description": "This should fail",
                "category_id": category_id,
                "price": 100.0,
                "stock_quantity": 10
            }
            
            success, _ = self.run_test(
                "Buyer Create Product (Should Fail)",
                "POST",
                "/products",
                403,  # Forbidden
                data=product_data,
                token=self.tokens['buyer'],
                description="Buyer should not be able to create products"
            )
            all_passed = all_passed and success
        
        # Test supplier trying to create RFQ (should fail)
        if 'supplier' in self.tokens and self.test_data.get('products'):
            product_id = self.test_data['products'][0]['id']
            rfq_data = {
                "product_id": product_id,
                "quantity": 10,
                "message": "This should fail"
            }
            
            success, _ = self.run_test(
                "Supplier Create RFQ (Should Fail)",
                "POST",
                "/rfqs",
                403,  # Forbidden
                data=rfq_data,
                token=self.tokens['supplier'],
                description="Supplier should not be able to create RFQs"
            )
            all_passed = all_passed and success
        
        return all_passed

    def run_all_tests(self):
        """Run all backend API tests"""
        self.log("🚀 Starting B2B E-commerce Backend API Tests")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        test_results = []
        
        # Run all test suites
        test_suites = [
            ("Health Check", self.test_health_check),
            ("Authentication", self.test_authentication),
            ("User Info", self.test_user_info),
            ("Categories", self.test_categories),
            ("Products", self.test_products),
            ("RFQs", self.test_rfqs),
            ("Quotes", self.test_quotes),
            ("Orders", self.test_orders),
            ("Dashboard Stats", self.test_dashboard_stats),
            ("Role-Based Access", self.test_role_based_access)
        ]
        
        for suite_name, test_func in test_suites:
            try:
                result = test_func()
                test_results.append((suite_name, result))
                if result:
                    self.log(f"✅ {suite_name} - ALL PASSED")
                else:
                    self.log(f"❌ {suite_name} - SOME FAILED")
            except Exception as e:
                self.log(f"💥 {suite_name} - EXCEPTION: {str(e)}")
                test_results.append((suite_name, False))
        
        # Print final results
        self.log("\n" + "="*60)
        self.log("📊 FINAL TEST RESULTS")
        self.log("="*60)
        
        passed_suites = sum(1 for _, result in test_results if result)
        total_suites = len(test_results)
        
        for suite_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"   {status} - {suite_name}")
        
        self.log(f"\n📈 SUMMARY:")
        self.log(f"   Test Suites: {passed_suites}/{total_suites} passed")
        self.log(f"   Individual Tests: {self.tests_passed}/{self.tests_run} passed")
        self.log(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if passed_suites == total_suites and self.tests_passed == self.tests_run:
            self.log("\n🎉 ALL TESTS PASSED! Backend API is working correctly.")
            return 0
        else:
            self.log(f"\n⚠️  Some tests failed. Please check the issues above.")
            return 1

def main():
    """Main test execution"""
    tester = B2BAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())