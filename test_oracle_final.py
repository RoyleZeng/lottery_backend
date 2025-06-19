#!/usr/bin/env python3
"""
Test Oracle connection after fix
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lottery_api.data_access_object.db import OracleDatabase

def test_oracle_connection():
    print("Testing Oracle connection...")
    
    try:
        # Test Oracle connection
        oracle_db = OracleDatabase()
        print("✓ Oracle database instance created")
        
        # Test a simple query
        test_student_ids = ['S0123456', 'S0654321']  # Test with fake IDs
        result = oracle_db.get_students_batch(test_student_ids)
        print(f"✓ Oracle query executed successfully")
        print(f"  Query result: {len(result)} records returned")
        
        if result:
            print("  Sample result:")
            for student in result[:2]:  # Show first 2 results
                print(f"    - {student}")
        else:
            print("  No records found (expected for test IDs)")
            
        print("\n🎉 Oracle connection is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Oracle connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_oracle_connection()
    sys.exit(0 if success else 1) 