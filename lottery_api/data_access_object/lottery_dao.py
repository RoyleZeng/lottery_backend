from lottery_api.data_access_object.db import Database, OracleDatabase
from lottery_api.utils.privacy_protection import apply_privacy_mask
import uuid
import json


class LotteryDAO:
    """Data Access Object for lottery-related operations"""

    @staticmethod
    def _parse_meta(meta_value):
        """Parse meta field from JSON string to dict"""
        if isinstance(meta_value, str):
            try:
                return json.loads(meta_value)
            except json.JSONDecodeError:
                return {}
        elif isinstance(meta_value, dict):
            return meta_value
        else:
            return {}

    @staticmethod
    def _is_oracle_available():
        """Check if Oracle database is available for connections"""
        try:
            # Try to get a connection to test availability
            conn = OracleDatabase.get_connection()
            conn.close()
            return True
        except Exception:
            # Oracle is not available (connection error, timeout, etc.)
            return False

    @staticmethod
    async def create_lottery_event(conn, academic_year_term, name, description, event_date, type="general", status="pending"):
        """Create a new lottery event"""
        event_id = str(uuid.uuid4())
        query = """
        INSERT INTO lottery_events (id, academic_year_term, name, description, event_date, type, status, is_deleted)
        VALUES ($1, $2, $3, $4, $5, $6, $7, FALSE)
        RETURNING id, academic_year_term, name, description, event_date, type, status, is_deleted, created_at
        """
        return await Database.fetchrow(conn, query, event_id, academic_year_term, name, description, event_date, type, status)

    @staticmethod
    async def update_event_status(conn, event_id, status):
        """Update event status"""
        query = """
        UPDATE lottery_events
        SET status = $2
        WHERE id = $1 AND is_deleted = FALSE
        RETURNING id, academic_year_term, name, description, event_date, type, status, is_deleted, created_at
        """
        return await Database.fetchrow(conn, query, event_id, status)

    @staticmethod
    async def update_lottery_event(conn, event_id, **kwargs):
        """Update lottery event with provided fields"""
        # Build dynamic query based on provided fields
        set_clauses = []
        params = []
        param_count = 1
        
        # Add event_id as first parameter
        params.append(event_id)
        param_count += 1
        
        # Build SET clauses for provided fields
        if 'academic_year_term' in kwargs and kwargs['academic_year_term'] is not None:
            set_clauses.append(f"academic_year_term = ${param_count}")
            params.append(kwargs['academic_year_term'])
            param_count += 1
            
        if 'name' in kwargs and kwargs['name'] is not None:
            set_clauses.append(f"name = ${param_count}")
            params.append(kwargs['name'])
            param_count += 1
            
        if 'description' in kwargs and kwargs['description'] is not None:
            set_clauses.append(f"description = ${param_count}")
            params.append(kwargs['description'])
            param_count += 1
            
        if 'event_date' in kwargs and kwargs['event_date'] is not None:
            set_clauses.append(f"event_date = ${param_count}")
            params.append(kwargs['event_date'])
            param_count += 1
            
        if 'type' in kwargs and kwargs['type'] is not None:
            set_clauses.append(f"type = ${param_count}")
            params.append(kwargs['type'])
            param_count += 1
        
        # If no fields to update, return None
        if not set_clauses:
            return None
        
        # Build complete query
        query = f"""
        UPDATE lottery_events
        SET {', '.join(set_clauses)}
        WHERE id = $1 AND is_deleted = FALSE
        RETURNING id, academic_year_term, name, description, event_date, type, status, is_deleted, created_at
        """
        
        return await Database.fetchrow(conn, query, *params)

    @staticmethod
    async def get_lottery_events(conn, limit=100, offset=0, event_type=None):
        """Get all lottery events with pagination (excluding soft deleted)"""
        if event_type:
            query = """
            SELECT id, academic_year_term, name, description, event_date, type, status, is_deleted, created_at
            FROM lottery_events
            WHERE type = $3 AND is_deleted = FALSE
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            """
            return await Database.fetch(conn, query, limit, offset, event_type)
        else:
            query = """
            SELECT id, academic_year_term, name, description, event_date, type, status, is_deleted, created_at
            FROM lottery_events
            WHERE is_deleted = FALSE
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            """
            return await Database.fetch(conn, query, limit, offset)

    @staticmethod
    async def get_lottery_event_by_id(conn, event_id):
        """Get a lottery event by ID (excluding soft deleted)"""
        query = """
        SELECT id, academic_year_term, name, description, event_date, type, status, is_deleted, created_at
        FROM lottery_events
        WHERE id = $1 AND is_deleted = FALSE
        """
        return await Database.fetchrow(conn, query, event_id)

    @staticmethod
    async def add_participant(conn, event_id, participant_data):
        """Add a participant to a lottery event with metadata from Oracle"""
        student_id = participant_data.get('id', '')
        
        # Check if Oracle is available
        oracle_available = LotteryDAO._is_oracle_available()
        oracle_student_info = None
        
        if oracle_available:
            # Get student info from Oracle database
            oracle_student_info = OracleDatabase.get_student_info(student_id)
            
            if not oracle_student_info:
                # If student not found in Oracle, skip this participant
                return None
        
        # Prepare meta data (with or without Oracle info)
        meta = {
            "student_info": {
                "id": participant_data.get('id', ''),
                "department": participant_data.get('department', ''),
                "name": participant_data.get('name', ''),
                "grade": participant_data.get('grade', '')
            }
        }
        
        # Add Oracle info if available
        if oracle_student_info:
            meta["oracle_info"] = oracle_student_info
        
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
            result['meta'] = LotteryDAO._parse_meta(result['meta'])
        return result

    @staticmethod
    async def get_existing_participants_by_student_ids(conn, event_id, student_ids):
        """Get existing participants by student IDs for a specific event"""
        if not student_ids:
            return {}
        
        # Build query with IN clause
        placeholders = ','.join([f'${i+2}' for i in range(len(student_ids))])
        query = f"""
        SELECT id, event_id, meta, created_at
        FROM lottery_participants
        WHERE event_id = $1 
        AND meta->'student_info'->>'id' IN ({placeholders})
        """
        
        params = [event_id] + student_ids
        rows = await Database.fetch(conn, query, *params)
        
        # Create a mapping of student_id -> participant record
        existing_participants = {}
        for row in rows:
            meta = LotteryDAO._parse_meta(row['meta'])
            student_info = meta.get('student_info', {})
            student_id = student_info.get('id', '')
            if student_id:
                existing_participants[student_id] = {
                    'id': row['id'],
                    'event_id': row['event_id'],
                    'meta': meta,
                    'created_at': row['created_at']
                }
        
        return existing_participants

    @staticmethod
    async def update_participant(conn, participant_id, meta_data):
        """Update an existing participant's meta data"""
        query = """
        UPDATE lottery_participants
        SET meta = $2
        WHERE id = $1
        RETURNING id, event_id, meta, created_at
        """
        result = await Database.fetchrow(conn, query, participant_id, json.dumps(meta_data))
        if result:
            result['meta'] = LotteryDAO._parse_meta(result['meta'])
        return result

    @staticmethod
    async def add_participants_batch(conn, event_id, participants_data, event_type="general"):
        """Batch add participants to a lottery event with Oracle metadata lookup and duplicate prevention"""
        # Check if Oracle is available and needed
        # For final_teaching events, skip Oracle lookup as frontend provides complete data
        oracle_available = LotteryDAO._is_oracle_available() and event_type != "final_teaching"
        oracle_students = {}
        
        # Extract all student IDs for batch Oracle lookup
        student_ids = [p.get('id', '') for p in participants_data if p.get('id')]
        
        if oracle_available:
            # Get all student info from Oracle in one batch
            oracle_students = OracleDatabase.get_students_batch(student_ids)
        
        # Get existing participants to check for duplicates
        existing_participants = await LotteryDAO.get_existing_participants_by_student_ids(conn, event_id, student_ids)
        
        # Separate data for insert vs update
        insert_data = []
        update_data = []
        skipped_students = []
        
        for participant_data in participants_data:
            student_id = participant_data.get('id', '')
            oracle_student_info = oracle_students.get(student_id) if oracle_available else None
            
            # If Oracle is available but student not found, skip this participant
            # This only applies to general events, not final_teaching
            if oracle_available and not oracle_student_info:
                skipped_students.append({
                    "student_id": student_id,
                    "reason": "Student not found in Oracle database"
                })
                continue
            
            # Prepare meta data (with or without Oracle info)
            meta = {
                "student_info": {
                    "id": participant_data.get('id', ''),
                    "department": participant_data.get('department', ''),
                    "name": participant_data.get('name', ''),
                    "grade": participant_data.get('grade', '')
                }
            }
            
            # Add Oracle info if available (for general events)
            if oracle_student_info:
                meta["oracle_info"] = oracle_student_info
            
            # For final_teaching events, add frontend-provided complete data
            if event_type == "final_teaching":
                # Handle enum values for student_type
                student_type_value = participant_data.get('student_type')
                if hasattr(student_type_value, 'value'):  # It's an enum
                    student_type_stored = student_type_value.value
                else:
                    student_type_stored = student_type_value
                
                meta["final_teaching_info"] = {
                    "id_number": participant_data.get('id_number', ''),
                    "address": participant_data.get('address', ''),
                    "student_type": student_type_stored,
                    "phone": participant_data.get('phone', ''),
                    "email": participant_data.get('email', '')
                }
            
            # Add teaching comments if available
            if any(key in participant_data for key in ['required_surveys', 'completed_surveys', 'surveys_completed', 'valid_surveys']):
                # Handle enum values for valid_surveys
                valid_surveys_value = participant_data.get('valid_surveys')
                if hasattr(valid_surveys_value, 'value'):  # It's an enum
                    valid_surveys_stored = valid_surveys_value.value
                else:
                    valid_surveys_stored = valid_surveys_value
                
                meta["teaching_comments"] = {
                    "required_surveys": participant_data.get('required_surveys', 0),
                    "completed_surveys": participant_data.get('completed_surveys', 0),
                    "surveys_completed": participant_data.get('surveys_completed', False),
                    "valid_surveys": valid_surveys_stored
                }
            
            # Check if student already exists - if yes, prepare for update; if no, prepare for insert
            if student_id in existing_participants:
                existing_participant = existing_participants[student_id]
                update_data.append((existing_participant['id'], meta))
            else:
                insert_data.append((event_id, json.dumps(meta)))
        
        # Process updates and inserts
        results = []
        updated_count = 0
        inserted_count = 0
        
        # Update existing participants
        if update_data:
            for participant_id, meta_data in update_data:
                result = await LotteryDAO.update_participant(conn, participant_id, meta_data)
                if result:
                    results.append(result)
                    updated_count += 1
        
        # Insert new participants
        if insert_data:
            query = """
            INSERT INTO lottery_participants (event_id, meta)
            VALUES ($1, $2)
            RETURNING id, event_id, meta, created_at
            """
            for event_id_val, meta_json in insert_data:
                result = await Database.fetchrow(conn, query, event_id_val, meta_json)
                if result:
                    result['meta'] = LotteryDAO._parse_meta(result['meta'])
                    results.append(result)
                    inserted_count += 1
        
        return {
            "imported": results,
            "skipped": skipped_students,
            "total_imported": len(results),
            "total_skipped": len(skipped_students),
            "inserted_count": inserted_count,
            "updated_count": updated_count
        }

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
            oracle_info = meta.get('oracle_info', {})
            final_teaching_info = meta.get('final_teaching_info', {})
            
            # Prioritize Oracle name data over student_info name
            display_name = (
                oracle_info.get('name') or 
                oracle_info.get('chinese_name') or 
                oracle_info.get('english_name') or 
                student_info.get('name', '')
            )
            
            participant = {
                'id': row['id'],
                'event_id': row['event_id'],
                'created_at': row['created_at'],
                'student_id': student_info.get('id', ''),
                'department': student_info.get('department', ''),
                'name': display_name,
                'grade': student_info.get('grade', ''),
                'required_surveys': teaching_comments.get('required_surveys'),
                'completed_surveys': teaching_comments.get('completed_surveys'),
                'surveys_completed': teaching_comments.get('surveys_completed'),
                'valid_surveys': teaching_comments.get('valid_surveys'),
                # Oracle data - only include necessary fields for frontend (with privacy masking)
                'oracle_student_id': oracle_info.get('student_id', ''),
                'chinese_name': oracle_info.get('chinese_name', ''),
                'english_name': oracle_info.get('english_name', ''),
                # Final teaching complete data - only for final_teaching events
                'id_number': final_teaching_info.get('id_number', ''),
                'address': final_teaching_info.get('address', ''),
                'student_type': final_teaching_info.get('student_type', ''),
                'phone': final_teaching_info.get('phone', ''),
                'email': final_teaching_info.get('email', ''),
            }
            # 應用個資遮罩
            participant = apply_privacy_mask(participant)
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
            oracle_info = meta.get('oracle_info', {})
            
            # Prioritize Oracle name data over student_info name
            display_name = (
                oracle_info.get('name') or 
                oracle_info.get('chinese_name') or 
                oracle_info.get('english_name') or 
                student_info.get('name', '')
            )
            
            winner = {
                'id': row['id'],
                'event_id': row['event_id'],
                'prize_id': row['prize_id'],
                'participant_id': row['participant_id'],
                'created_at': row['created_at'],
                'prize_name': row['prize_name'],
                'student_id': student_info.get('id', ''),
                'department': student_info.get('department', ''),
                'name': display_name,
                'grade': student_info.get('grade', ''),
                'required_surveys': teaching_comments.get('required_surveys'),
                'completed_surveys': teaching_comments.get('completed_surveys'),
                'surveys_completed': teaching_comments.get('surveys_completed'),
                'valid_surveys': teaching_comments.get('valid_surveys'),
                # Oracle data - only include necessary fields for frontend
                'oracle_student_id': oracle_info.get('student_id', ''),
                'chinese_name': oracle_info.get('chinese_name', ''),
                'english_name': oracle_info.get('english_name', ''),
            }
            # 應用個資遮罩
            winner = apply_privacy_mask(winner)
            winners.append(winner)
        
        return winners

    @staticmethod
    async def get_winners_for_export(conn, event_id):
        """Get winners for export (without privacy masking)"""
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
        
        # Transform the data to flatten meta information (without privacy masking)
        winners = []
        for row in rows:
            meta = LotteryDAO._parse_meta(row['meta'])
            student_info = meta.get('student_info', {})
            teaching_comments = meta.get('teaching_comments', {})
            oracle_info = meta.get('oracle_info', {})
            final_teaching_info = meta.get('final_teaching_info', {})
            
            # Prioritize Oracle name data over student_info name
            display_name = (
                oracle_info.get('name') or 
                oracle_info.get('chinese_name') or 
                oracle_info.get('english_name') or 
                student_info.get('name', '')
            )
            
            winner = {
                'id': row['id'],
                'event_id': row['event_id'],
                'prize_id': row['prize_id'],
                'participant_id': row['participant_id'],
                'created_at': row['created_at'],
                'prize_name': row['prize_name'],
                'student_id': student_info.get('id', ''),
                'department': student_info.get('department', ''),
                'name': display_name,
                'grade': student_info.get('grade', ''),
                'required_surveys': teaching_comments.get('required_surveys'),
                'completed_surveys': teaching_comments.get('completed_surveys'),
                'surveys_completed': teaching_comments.get('surveys_completed'),
                'valid_surveys': teaching_comments.get('valid_surveys'),
                # Oracle data (for general events)
                'oracle_student_id': oracle_info.get('student_id', ''),
                'id_number': oracle_info.get('id_number', '') or final_teaching_info.get('id_number', ''),
                'chinese_name': oracle_info.get('chinese_name', ''),
                'english_name': oracle_info.get('english_name', ''),
                'phone': oracle_info.get('phone', '') or final_teaching_info.get('phone', ''),
                'postal_code': oracle_info.get('postal_code', ''),
                'address': oracle_info.get('address', '') or final_teaching_info.get('address', ''),
                'student_type': oracle_info.get('student_type', '') or final_teaching_info.get('student_type', ''),
                'email': oracle_info.get('email', '') or final_teaching_info.get('email', '')
            }
            # 不應用個資遮罩 - 用於 Excel 匯出
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
            oracle_info = meta.get('oracle_info', {})
            
            # Prioritize Oracle name data over student_info name
            display_name = (
                oracle_info.get('name') or 
                oracle_info.get('chinese_name') or 
                oracle_info.get('english_name') or 
                student_info.get('name', '')
            )
            
            participant = {
                'participant_id': row['participant_id'],
                'event_id': row['event_id'],
                'created_at': row['created_at'],
                'student_id': student_info.get('id', ''),
                'department': student_info.get('department', ''),
                'name': display_name,
                'grade': student_info.get('grade', ''),
                'required_surveys': teaching_comments.get('required_surveys'),
                'completed_surveys': teaching_comments.get('completed_surveys'),
                'surveys_completed': teaching_comments.get('surveys_completed'),
                'valid_surveys': teaching_comments.get('valid_surveys'),
                # Oracle data - only include necessary fields for frontend
                'oracle_student_id': oracle_info.get('student_id', ''),
                'chinese_name': oracle_info.get('chinese_name', ''),
                'english_name': oracle_info.get('english_name', ''),
            }
            # 應用個資遮罩
            participant = apply_privacy_mask(participant)
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

    @staticmethod
    async def soft_delete_event(conn, event_id):
        """Soft delete a lottery event by setting is_deleted to TRUE"""
        query = """
        UPDATE lottery_events
        SET is_deleted = TRUE
        WHERE id = $1 AND is_deleted = FALSE
        RETURNING id, academic_year_term, name, description, event_date, type, status, is_deleted, created_at
        """
        return await Database.fetchrow(conn, query, event_id)

    @staticmethod
    async def restore_event(conn, event_id):
        """Restore a soft deleted lottery event by setting is_deleted to FALSE"""
        query = """
        UPDATE lottery_events
        SET is_deleted = FALSE
        WHERE id = $1 AND is_deleted = TRUE
        RETURNING id, academic_year_term, name, description, event_date, type, status, is_deleted, created_at
        """
        return await Database.fetchrow(conn, query, event_id)

    @staticmethod
    async def get_deleted_events(conn, limit=100, offset=0):
        """Get all soft deleted lottery events with pagination"""
        query = """
        SELECT id, academic_year_term, name, description, event_date, type, status, is_deleted, created_at
        FROM lottery_events
        WHERE is_deleted = TRUE
        ORDER BY created_at DESC
        LIMIT $1 OFFSET $2
        """
        return await Database.fetch(conn, query, limit, offset) 