#!/usr/bin/env python3
"""
Oracle Fallback Patch
當 Oracle 服務器不可用時，快速失敗並使用 Mock 數據
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def apply_oracle_fallback_patch():
    """應用 Oracle 快速失敗補丁"""
    
    patch_content = '''
    @staticmethod
    def get_connection():
        """Get Oracle database connection with fast timeout"""
        if not ORACLE_AVAILABLE:
            raise ImportError("Oracle client is not installed. Please install oracledb to use Oracle functionality.")
        
        settings = get_settings()
        
        try:
            # Quick network test first
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)  # 3 second timeout for network test
            result = sock.connect_ex((settings.oracle_host, settings.oracle_port))
            sock.close()
            
            if result != 0:
                logger.warning(f"Oracle server {settings.oracle_host}:{settings.oracle_port} is not reachable. Using fallback mode.")
                raise ConnectionError("Oracle server not reachable")
            
            # Initialize Oracle client if using oracledb
            if ORACLE_CLIENT == 'oracledb':
                oracledb.init_oracle_client()
            
            # Create connection string
            dsn = oracledb.makedsn(
                host=settings.oracle_host,
                port=settings.oracle_port,
                service_name=settings.oracle_service_name
            )
            
            # Create connection with timeout (5 seconds)
            connection = oracledb.connect(
                user=settings.oracle_username,
                password=settings.oracle_password,
                dsn=dsn,
                timeout=5  # 5 second connection timeout
            )
            return connection
            
        except Exception as e:
            logger.warning(f"Oracle connection failed: {e}. Falling back to mock mode.")
            raise
    '''
    
    print("Oracle 快速失敗補丁已準備好")
    print("這將修改 Oracle 連接以：")
    print("1. 先進行 3 秒網絡測試")
    print("2. 連接超時設為 5 秒")
    print("3. 失敗時快速切換到 Mock 模式")
    
    return patch_content

if __name__ == "__main__":
    apply_oracle_fallback_patch() 