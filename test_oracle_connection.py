#!/usr/bin/env python3
"""
Oracle Database Connection Test Script
測試 Oracle 數據庫連接
"""
import os
import sys
import time
import socket
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_network_connectivity():
    """測試網絡連接"""
    print("🌐 Testing network connectivity...")
    
    oracle_host = "140.120.3.90"
    oracle_port = 1521
    
    # Test ping
    print(f"  📡 Testing ping to {oracle_host}...")
    ping_result = os.system(f"ping -c 3 {oracle_host} > /dev/null 2>&1")
    if ping_result == 0:
        print("  ✅ Ping successful")
    else:
        print("  ❌ Ping failed")
        return False
    
    # Test port connectivity
    print(f"  🔌 Testing port {oracle_port} connectivity...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((oracle_host, oracle_port))
        sock.close()
        
        if result == 0:
            print("  ✅ Port is reachable")
            return True
        else:
            print("  ❌ Port is not reachable")
            return False
    except Exception as e:
        print(f"  ❌ Port test failed: {e}")
        return False

def test_oracle_client():
    """測試 Oracle 客戶端庫"""
    print("\n📚 Testing Oracle client libraries...")
    
    # Test oracledb
    try:
        import oracledb
        print("  ✅ oracledb library imported successfully")
        print(f"  📦 oracledb version: {oracledb.__version__}")
        
        # Test client initialization
        try:
            oracledb.init_oracle_client()
            print("  ✅ Oracle client initialized successfully")
            return True, 'oracledb'
        except Exception as e:
            print(f"  ❌ Oracle client initialization failed: {e}")
            return False, None
            
    except ImportError:
        print("  ❌ oracledb library not found")
        
        # Fallback to cx_Oracle
        try:
            import cx_Oracle
            print("  ✅ cx_Oracle library imported successfully")
            print(f"  📦 cx_Oracle version: {cx_Oracle.__version__}")
            return True, 'cx_Oracle'
        except ImportError:
            print("  ❌ cx_Oracle library not found")
            return False, None

def test_oracle_connection():
    """測試 Oracle 數據庫連接"""
    print("\n🔗 Testing Oracle database connection...")
    
    # Connection parameters
    oracle_config = {
        "host": "140.120.3.90",
        "port": 1521,
        "service_name": "nchu",
        "username": "studlottery",
        "password": "Lottery2025"
    }
    
    try:
        import oracledb
        
        # Initialize client
        oracledb.init_oracle_client()
        
        # Create DSN
        dsn = oracledb.makedsn(
            host=oracle_config["host"],
            port=oracle_config["port"],
            service_name=oracle_config["service_name"]
        )
        print(f"  🎯 DSN: {dsn}")
        
        # Try to connect with timeout
        print("  🔄 Attempting connection (10s timeout)...")
        start_time = time.time()
        
        connection = oracledb.connect(
            user=oracle_config["username"],
            password=oracle_config["password"],
            dsn=dsn,
            timeout=10
        )
        
        end_time = time.time()
        print(f"  ✅ Connection successful! ({end_time - start_time:.2f}s)")
        
        # Test a simple query
        print("  🔍 Testing simple query...")
        cursor = connection.cursor()
        cursor.execute("SELECT SYSDATE FROM DUAL")
        result = cursor.fetchone()
        print(f"  📅 Server time: {result[0]}")
        
        # Test student table access
        print("  👥 Testing student table access...")
        cursor.execute("""
            SELECT COUNT(*) FROM SCHOOL.STFSTUD 
            WHERE ROWNUM <= 1
        """)
        count = cursor.fetchone()[0]
        print(f"  📊 Student table accessible (sample count: {count})")
        
        cursor.close()
        connection.close()
        print("  ✅ Connection closed successfully")
        return True
        
    except Exception as e:
        end_time = time.time()
        print(f"  ❌ Connection failed after {end_time - start_time:.2f}s")
        print(f"  🔍 Error details: {e}")
        print(f"  🏷️  Error type: {type(e).__name__}")
        return False

def test_application_integration():
    """測試應用程序集成"""
    print("\n🔧 Testing application integration...")
    
    try:
        from lottery_api.data_access_object.db import OracleDatabase
        
        # Test get_connection method
        print("  🔗 Testing OracleDatabase.get_connection()...")
        start_time = time.time()
        
        connection = OracleDatabase.get_connection()
        end_time = time.time()
        
        print(f"  ✅ Application connection successful! ({end_time - start_time:.2f}s)")
        
        # Test student lookup
        print("  🔍 Testing student lookup...")
        test_student_id = "S0123456"
        student_info = OracleDatabase.get_student_info(test_student_id)
        
        if student_info:
            print(f"  ✅ Student lookup successful")
            print(f"  📝 Sample data: {student_info}")
        else:
            print(f"  ℹ️  No data found for test student ID (expected)")
        
        connection.close()
        return True
        
    except Exception as e:
        end_time = time.time()
        print(f"  ❌ Application integration failed after {end_time - start_time:.2f}s")
        print(f"  🔍 Error details: {e}")
        return False

def main():
    """主測試函數"""
    print("=" * 60)
    print("🧪 Oracle Database Connection Test")
    print(f"⏰ Test started at: {datetime.now()}")
    print("=" * 60)
    
    # Test network
    network_ok = test_network_connectivity()
    
    # Test Oracle client
    client_ok, client_type = test_oracle_client()
    
    # Test direct connection
    if network_ok and client_ok:
        connection_ok = test_oracle_connection()
    else:
        print("\n⏭️  Skipping connection test due to prerequisites failure")
        connection_ok = False
    
    # Test application integration
    if connection_ok:
        app_ok = test_application_integration()
    else:
        print("\n⏭️  Skipping application test due to connection failure")
        app_ok = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"🌐 Network connectivity: {'✅ PASS' if network_ok else '❌ FAIL'}")
    print(f"📚 Oracle client: {'✅ PASS' if client_ok else '❌ FAIL'} ({client_type or 'N/A'})")
    print(f"🔗 Database connection: {'✅ PASS' if connection_ok else '❌ FAIL'}")
    print(f"🔧 Application integration: {'✅ PASS' if app_ok else '❌ FAIL'}")
    
    overall_status = all([network_ok, client_ok, connection_ok, app_ok])
    print(f"\n🎯 Overall result: {'✅ ALL TESTS PASSED' if overall_status else '❌ SOME TESTS FAILED'}")
    
    if not overall_status:
        print("\n💡 TROUBLESHOOTING TIPS:")
        if not network_ok:
            print("   • Check firewall settings")
            print("   • Verify Oracle server is running")
            print("   • Contact network administrator")
        if not client_ok:
            print("   • Install Oracle client: pip install oracledb")
            print("   • Check Oracle Instant Client installation")
        if not connection_ok:
            print("   • Verify Oracle credentials")
            print("   • Check Oracle service status")
            print("   • Review Oracle listener configuration")
    
    return overall_status

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 