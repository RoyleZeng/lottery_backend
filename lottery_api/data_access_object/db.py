import asyncpg


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
    """Database utility class with common operations"""

    @staticmethod
    async def execute(conn, query: str, *args):
        """Execute a query and return affected rows"""
        return await conn.execute(query, *args)

    @staticmethod
    async def fetch(conn, query: str, *args):
        """Execute a query and return all results"""
        rows = await conn.fetch(query, *args)
        return [dict(row) for row in rows]

    @staticmethod
    async def fetchrow(conn, query: str, *args):
        """Execute a query and return first result"""
        row = await conn.fetchrow(query, *args)
        return dict(row) if row else None

    @staticmethod
    async def fetchval(conn, query: str, *args):
        """Execute a query and return first value of first result"""
        return await conn.fetchval(query, *args)
