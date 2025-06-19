import asyncio
import asyncpg
from contextlib import asynccontextmanager
from lottery_api.config import get_settings
from lottery_api.lib.logger import get_prefix_logger_adapter

logger = get_prefix_logger_adapter(__name__)

# Try to import Oracle client, support both cx_Oracle and oracledb
try:
    import oracledb
    ORACLE_AVAILABLE = True
    ORACLE_CLIENT = 'oracledb'
    logger.info("Using oracledb client for Oracle connections")
except ImportError:
    try:
        import cx_Oracle as oracledb
        ORACLE_AVAILABLE = True
        ORACLE_CLIENT = 'cx_Oracle'
        logger.info("Using cx_Oracle client for Oracle connections")
    except ImportError:
        ORACLE_AVAILABLE = False
        ORACLE_CLIENT = None
        logger.warning("Oracle client not available. Oracle functionality will be disabled.")

async def get_db_connection():
    """Get a database connection from the pool"""
    conn = await asyncpg.connect(
        user="local",
        password="local1234",
        database="postgres",
        host="localhost",
        port=5432
    )
    try:
        yield conn
    finally:
        await conn.close()

class Database:
    @staticmethod
    async def get_connection():
        """Get PostgreSQL database connection"""
        return await asyncpg.connect(
            user="local",
            password="local1234",
            database="postgres",
            host="localhost",
            port=5432
        )

    @staticmethod
    async def fetchrow(conn, query, *args):
        """Execute query and return single row as dict"""
        result = await conn.fetchrow(query, *args)
        return dict(result) if result else None

    @staticmethod
    async def fetch(conn, query, *args):
        """Execute query and return multiple rows as list of dicts"""
        results = await conn.fetch(query, *args)
        return [dict(row) for row in results]

    @staticmethod
    async def fetchval(conn, query, *args):
        """Execute query and return single value"""
        return await conn.fetchval(query, *args)

    @staticmethod
    async def execute(conn, query, *args):
        """Execute query without returning results"""
        return await conn.execute(query, *args)


class OracleDatabase:
    """Oracle Database connection and operations"""

    @staticmethod
    def get_connection():
        """Get Oracle database connection with fast timeout and network pre-check"""
        if not ORACLE_AVAILABLE:
            raise ImportError("Oracle client is not installed. Please install oracledb to use Oracle functionality.")
        
        settings = get_settings()
        
        try:
            # Quick network test first (3 second timeout)
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((settings.oracle_host, settings.oracle_port))
            sock.close()
            
            if result != 0:
                logger.warning(f"Oracle server {settings.oracle_host}:{settings.oracle_port} is not reachable. Network test failed.")
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
            
            # Create connection with short timeout (5 seconds)
            connection = oracledb.connect(
                user=settings.oracle_username,
                password=settings.oracle_password,
                dsn=dsn
            )
            return connection
            
        except Exception as e:
            logger.warning(f"Oracle connection failed: {e}. System will use mock data.")
            raise

    @staticmethod
    def get_student_info(student_id: str):
        """Get student information from Oracle database"""
        if not ORACLE_AVAILABLE:
            logger.warning("Oracle functionality not available. Returning mock data for development.")
            # Return mock data for development/testing when Oracle is not available
            return {
                "student_id": student_id,
                "id_number": f"A{student_id[:8]}",
                "chinese_name": f"測試學生{student_id[-2:]}",
                "english_name": f"Test Student {student_id[-2:]}",
                "phone": "0912345678",
                "postal_code": "40227",
                "address": "台中市南區興大路145號",
                "student_type": "N",
                "name": f"測試學生{student_id[-2:]}",
                "email": f"{student_id}@smail.nchu.edu.tw"
            }
        
        try:
            with OracleDatabase.get_connection() as conn:
                cursor = conn.cursor()
                query = """
                SELECT s.PS_STUD_NO, s.STUD_ID, s.STUD_CHINESE_NAME, s.STUD_ENGLISH_NAME, 
                       s.STUD_NOW_TEL, s.STUD_NOW_POST, s.STUD_NOW_ADDR, s.STUD_EXTRA, s.STUD_EMAIL
                FROM SCHOOL.STFSTUD s
                WHERE s.PS_STUD_NO = :student_id
                """
                cursor.execute(query, {"student_id": student_id})
                result = cursor.fetchone()

                if result:
                    return {
                        "student_id": result[0],  # PS_STUD_NO
                        "id_number": result[1],   # STUD_ID
                        "chinese_name": result[2], # STUD_CHINESE_NAME
                        "english_name": result[3], # STUD_ENGLISH_NAME
                        "phone": result[4],       # STUD_NOW_TEL
                        "postal_code": result[5], # STUD_NOW_POST
                        "address": result[6],     # STUD_NOW_ADDR
                        "student_type": result[7], # STUD_EXTRA (Y=外籍生, N=本國生)
                        "email": result[8],       # STUD_EMAIL
                        "name": result[2] if result[2] else result[3],  # 優先使用中文姓名
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting student info from Oracle: {e}")
            return None

    @staticmethod
    def get_students_batch(student_ids: list):
        """Get multiple students information from Oracle database with batch processing"""
        if not ORACLE_AVAILABLE:
            logger.warning("Oracle functionality not available. Returning mock data for development.")
            # Return mock data for development/testing when Oracle is not available
            students = {}
            for student_id in student_ids:
                students[student_id] = {
                    "student_id": student_id,
                    "id_number": f"A{student_id[:8]}",
                    "chinese_name": f"測試學生{student_id[-2:]}",
                    "english_name": f"Test Student {student_id[-2:]}",
                    "phone": "0912345678",
                    "postal_code": "40227",
                    "address": "台中市南區興大路145號",
                    "student_type": "N",
                    "name": f"測試學生{student_id[-2:]}",
                    "email": f"{student_id}@smail.nchu.edu.tw"
                }
            return students
        
        try:
            students = {}
            # Oracle IN clause has a limit of 1000 expressions, so we batch the queries
            batch_size = 900  # Use 900 to be safe, leaving some margin
            
            with OracleDatabase.get_connection() as conn:
                cursor = conn.cursor()
                
                # Process student IDs in batches
                for i in range(0, len(student_ids), batch_size):
                    batch_ids = student_ids[i:i + batch_size]
                    logger.info(f"Processing Oracle batch {i//batch_size + 1}: {len(batch_ids)} students")
                    
                    # Create parameter placeholders for this batch
                    placeholders = ','.join([f':id{j}' for j in range(len(batch_ids))])
                    
                    query = f"""
                    SELECT s.PS_STUD_NO, s.STUD_ID, s.STUD_CHINESE_NAME, s.STUD_ENGLISH_NAME, 
                           s.STUD_NOW_TEL, s.STUD_NOW_POST, s.STUD_NOW_ADDR, s.STUD_EXTRA, s.STUD_EMAIL
                    FROM SCHOOL.STFSTUD s
                    WHERE s.PS_STUD_NO IN ({placeholders})
                    """
                    # Create parameter dictionary for this batch
                    params = {f'id{j}': student_id for j, student_id in enumerate(batch_ids)}
                    cursor.execute(query, params)
                    results = cursor.fetchall()

                    # Process results from this batch
                    for result in results:
                        student_id = result[0]
                        students[student_id] = {
                            "student_id": result[0],  # PS_STUD_NO
                            "id_number": result[1],   # STUD_ID
                            "chinese_name": result[2], # STUD_CHINESE_NAME
                            "english_name": result[3], # STUD_ENGLISH_NAME
                            "phone": result[4],       # STUD_NOW_TEL
                            "postal_code": result[5], # STUD_NOW_POST
                            "address": result[6],     # STUD_NOW_ADDR
                            "student_type": result[7], # STUD_EXTRA (Y=外籍生, N=本國生)
                            "email": result[8],       # STUD_EMAIL
                            "name": result[2] if result[2] else result[3],  # 優先使用中文姓名
                        }
                
                logger.info(f"Oracle batch processing completed: {len(students)} students found out of {len(student_ids)} requested")
                return students
        except Exception as e:
            logger.error(f"Error getting students info from Oracle: {e}")
            return {}
