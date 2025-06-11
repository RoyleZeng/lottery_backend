from lottery_api.data_access_object.db import Database
import uuid
import json


class LotteryDAO:
    """Data Access Object for lottery-related operations"""

    @staticmethod
    def _parse_meta(meta_value):
        """Parse meta field from database"""
        if isinstance(meta_value, str):
            try:
                return json.loads(meta_value)
            except (json.JSONDecodeError, TypeError):
                return {}
        elif isinstance(meta_value, dict):
            return meta_value
        else:
            return {}

    @staticmethod
    async def create_lottery_event(conn, academic_year_term, name, description, event_date, type="general", status="pending"):
        """Create a new lottery event"""
        event_id = str(uuid.uuid4())
        query = """
        INSERT INTO lottery_events (id, academic_year_term, name, description, event_date, type, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id, academic_year_term, name, description, event_date, type, status, created_at
        """
        return await Database.fetchrow(conn, query, event_id, academic_year_term, name, description, event_date, type, status)

    @staticmethod
    async def update_event_status(conn, event_id, status):
        """Update event status"""
        query = """
        UPDATE lottery_events
        SET status = $2
        WHERE id = $1
        RETURNING id, academic_year_term, name, description, event_date, status, created_at
        """
        return await Database.fetchrow(conn, query, event_id, status)

    @staticmethod
    async def get_lottery_events(conn, limit=100, offset=0, event_type=None):
        """Get all lottery events with pagination"""
        if event_type:
            query = """
            SELECT id, academic_year_term, name, description, event_date, type, status, created_at
            FROM lottery_events
            WHERE type = $3
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            """
            return await Database.fetch(conn, query, limit, offset, event_type)
        else:
            query = """
            SELECT id, academic_year_term, name, description, event_date, type, status, created_at
            FROM lottery_events
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            """
            return await Database.fetch(conn, query, limit, offset)

    @staticmethod
    async def get_lottery_event_by_id(conn, event_id):
        """Get a lottery event by ID"""
        query = """
        SELECT id, academic_year_term, name, description, event_date, type, status, created_at
        FROM lottery_events
        WHERE id = $1
        """
        return await Database.fetchrow(conn, query, event_id)

    @staticmethod
    async def add_participant(conn, event_id, participant_data):
        """Add a participant to a lottery event with metadata"""
        # Prepare meta data
        meta = {
            "student_info": {
                "id": participant_data.get('id', ''),
                "department": participant_data.get('department', ''),
                "name": participant_data.get('name', ''),
                "grade": participant_data.get('grade', '')
            }
        }
        
        # Add teaching comments if available
        if any(key in participant_data for key in ['required_surveys', 'completed_surveys', 'surveys_completed', 'valid_surveys']):
            meta["teaching_comments"] = {
                "required_surveys": participant_data.get('required_surveys', 0),
                "completed_surveys": participant_data.get('completed_surveys', 0),
                "surveys_completed": participant_data.get('surveys_completed', False),
                "valid_surveys": participant_data.get('valid_surveys', False)
            }
        
        query = """
        INSERT INTO lottery_participants (event_id, meta)
        VALUES ($1, $2)
        RETURNING id, event_id, meta, created_at
        """
        result = await Database.fetchrow(conn, query, event_id, json.dumps(meta))
        if result:
            # Parse meta field
            result = dict(result)
            result['meta'] = LotteryDAO._parse_meta(result['meta'])
        return result

    @staticmethod
    async def get_participants(conn, event_id, limit=1000, offset=0):
        """Get participants for a lottery event"""
        query = """
        SELECT id, event_id, meta, created_at
        FROM lottery_participants
        WHERE event_id = $1
        ORDER BY id
        LIMIT $2 OFFSET $3
        """
        rows = await Database.fetch(conn, query, event_id, limit, offset)
        
        # Transform the data to flatten meta information
        participants = []
        for row in rows:
            meta = LotteryDAO._parse_meta(row['meta'])
            student_info = meta.get('student_info', {})
            teaching_comments = meta.get('teaching_comments', {})
            
            participant = {
                'id': row['id'],
                'event_id': row['event_id'],
                'created_at': row['created_at'],
                'student_id': student_info.get('id', ''),
                'department': student_info.get('department', ''),
                'name': student_info.get('name', ''),
                'grade': student_info.get('grade', ''),
                'required_surveys': teaching_comments.get('required_surveys'),
                'completed_surveys': teaching_comments.get('completed_surveys'),
                'surveys_completed': teaching_comments.get('surveys_completed'),
                'valid_surveys': teaching_comments.get('valid_surveys')
            }
            participants.append(participant)
        
        return participants

    @staticmethod
    async def count_participants(conn, event_id):
        """Count participants for a lottery event"""
        query = """
        SELECT COUNT(*) FROM lottery_participants
        WHERE event_id = $1
        """
        return await Database.fetchval(conn, query, event_id)

    @staticmethod
    async def create_prize(conn, event_id, name, quantity):
        """Create a prize for a lottery event"""
        query = """
        INSERT INTO lottery_prizes (event_id, name, quantity)
        VALUES ($1, $2, $3)
        RETURNING id, event_id, name, quantity, created_at
        """
        return await Database.fetchrow(conn, query, event_id, name, quantity)

    @staticmethod
    async def get_prizes(conn, event_id):
        """Get prizes for a lottery event"""
        query = """
        SELECT id, event_id, name, quantity, created_at
        FROM lottery_prizes
        WHERE event_id = $1
        ORDER BY id
        """
        return await Database.fetch(conn, query, event_id)

    @staticmethod
    async def update_prize(conn, prize_id, name, quantity):
        """Update a prize"""
        query = """
        UPDATE lottery_prizes
        SET name = $2, quantity = $3
        WHERE id = $1
        RETURNING id, event_id, name, quantity, created_at
        """
        return await Database.fetchrow(conn, query, prize_id, name, quantity)

    @staticmethod
    async def delete_prize(conn, prize_id):
        """Delete a prize"""
        query = """
        DELETE FROM lottery_prizes
        WHERE id = $1
        RETURNING id
        """
        return await Database.fetchval(conn, query, prize_id)

    @staticmethod
    async def save_winner(conn, event_id, prize_id, participant_id):
        """Save a winner"""
        query = """
        INSERT INTO lottery_winners (event_id, prize_id, participant_id)
        VALUES ($1, $2, $3)
        RETURNING id, event_id, prize_id, participant_id, created_at
        """
        return await Database.fetchrow(conn, query, event_id, prize_id, participant_id)

    @staticmethod
    async def has_winners(conn, event_id):
        """Check if an event already has winners"""
        query = """
        SELECT EXISTS (
            SELECT 1 FROM lottery_winners
            WHERE event_id = $1
        ) as has_winners
        """
        return await Database.fetchval(conn, query, event_id)

    @staticmethod
    async def get_winners(conn, event_id):
        """Get winners for a lottery event"""
        query = """
        SELECT w.id, w.event_id, w.prize_id, w.participant_id, w.created_at,
               pr.name as prize_name, p.meta
        FROM lottery_winners w
        JOIN lottery_prizes pr ON w.prize_id = pr.id
        JOIN lottery_participants p ON w.participant_id = p.id
        WHERE w.event_id = $1
        ORDER BY pr.id, w.id
        """
        rows = await Database.fetch(conn, query, event_id)
        
        # Transform the data to flatten meta information
        winners = []
        for row in rows:
            meta = LotteryDAO._parse_meta(row['meta'])
            student_info = meta.get('student_info', {})
            teaching_comments = meta.get('teaching_comments', {})
            
            winner = {
                'id': row['id'],
                'event_id': row['event_id'],
                'prize_id': row['prize_id'],
                'participant_id': row['participant_id'],
                'created_at': row['created_at'],
                'prize_name': row['prize_name'],
                'student_id': student_info.get('id', ''),
                'department': student_info.get('department', ''),
                'name': student_info.get('name', ''),
                'grade': student_info.get('grade', ''),
                'required_surveys': teaching_comments.get('required_surveys'),
                'completed_surveys': teaching_comments.get('completed_surveys'),
                'surveys_completed': teaching_comments.get('surveys_completed'),
                'valid_surveys': teaching_comments.get('valid_surveys')
            }
            winners.append(winner)
        
        return winners

    @staticmethod
    async def get_non_winners(conn, event_id):
        """Get participants who haven't won any prize yet"""
        query = """
        SELECT p.id as participant_id, p.event_id, p.meta, p.created_at
        FROM lottery_participants p
        LEFT JOIN lottery_winners w ON p.id = w.participant_id AND w.event_id = p.event_id
        WHERE p.event_id = $1 AND w.id IS NULL
        """
        rows = await Database.fetch(conn, query, event_id)
        
        # Transform the data to flatten meta information
        participants = []
        for row in rows:
            meta = LotteryDAO._parse_meta(row['meta'])
            student_info = meta.get('student_info', {})
            teaching_comments = meta.get('teaching_comments', {})
            
            participant = {
                'participant_id': row['participant_id'],
                'event_id': row['event_id'],
                'created_at': row['created_at'],
                'student_id': student_info.get('id', ''),
                'department': student_info.get('department', ''),
                'name': student_info.get('name', ''),
                'grade': student_info.get('grade', ''),
                'required_surveys': teaching_comments.get('required_surveys'),
                'completed_surveys': teaching_comments.get('completed_surveys'),
                'surveys_completed': teaching_comments.get('surveys_completed'),
                'valid_surveys': teaching_comments.get('valid_surveys')
            }
            participants.append(participant)
        
        return participants

    @staticmethod
    async def delete_winners(conn, event_id):
        """Delete all winners for an event"""
        query = """
        DELETE FROM lottery_winners
        WHERE event_id = $1
        RETURNING id
        """
        return await Database.fetch(conn, query, event_id)

    @staticmethod
    async def delete_participant(conn, participant_id):
        """Delete a specific participant"""
        query = """
        DELETE FROM lottery_participants
        WHERE id = $1
        RETURNING id, event_id
        """
        return await Database.fetchrow(conn, query, participant_id)

    @staticmethod
    async def delete_all_participants(conn, event_id):
        """Delete all participants for an event"""
        query = """
        DELETE FROM lottery_participants
        WHERE event_id = $1
        RETURNING id
        """
        return await Database.fetch(conn, query, event_id) 