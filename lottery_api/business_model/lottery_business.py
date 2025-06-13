import random
import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Any

from lottery_api.data_access_object.lottery_dao import LotteryDAO
from lottery_api.lib.base_exception import ResourceNotFoundException, ParameterViolationException


class LotteryBusiness:
    """Business logic for lottery operations"""

    @staticmethod
    async def create_lottery_event(conn, event_data):
        """Create a new lottery event"""
        result = await LotteryDAO.create_lottery_event(
            conn,
            academic_year_term=event_data.academic_year_term,
            name=event_data.name,
            description=event_data.description,
            event_date=event_data.event_date,
            type=event_data.type.value
        )
        return result

    @staticmethod
    async def get_lottery_events(conn, limit=100, offset=0, event_type=None):
        """Get all lottery events with pagination"""
        return await LotteryDAO.get_lottery_events(conn, limit, offset, event_type)

    @staticmethod
    async def get_lottery_event(conn, event_id):
        """Get a lottery event by ID"""
        event = await LotteryDAO.get_lottery_event_by_id(conn, event_id)
        if not event:
            raise ResourceNotFoundException(f"Lottery event with ID {event_id} not found")
        return event

    @staticmethod
    async def import_students_and_add_participants(conn, event_id, students_data: List[Dict[str, Any]]):
        """Import students and add them as participants with metadata"""
        results = []
        for student_data in students_data:
            # Add participant with student data as metadata
            participant = await LotteryDAO.add_participant(conn, event_id, student_data)
            
            results.append({
                "participant_id": participant['id'],
                "student_id": student_data.get('id', ''),
                "student_name": student_data.get('name', '')
            })
            
        return results

    @staticmethod
    async def get_participants(conn, event_id, limit=1000, offset=0):
        """Get participants for a lottery event"""
        # Check if event exists
        event = await LotteryBusiness.get_lottery_event(conn, event_id)
        
        participants = await LotteryDAO.get_participants(conn, event_id, limit, offset)
        total = await LotteryDAO.count_participants(conn, event_id)
        
        return {
            "total": total,
            "participants": participants
        }

    @staticmethod
    async def set_prizes(conn, event_id, prizes_data):
        """Set prizes for a lottery event"""
        # Check if event exists
        event = await LotteryBusiness.get_lottery_event(conn, event_id)
        
        # Get existing prizes
        existing_prizes = await LotteryDAO.get_prizes(conn, event_id)
        
        # Delete all existing prizes first
        for existing_prize in existing_prizes:
            await LotteryDAO.delete_prize(conn, existing_prize['id'])
        
        # Create new prizes
        results = []
        for prize_data in prizes_data:
            result = await LotteryDAO.create_prize(
                conn,
                event_id=event_id,
                name=prize_data.name,
                quantity=prize_data.quantity
            )
            results.append(result)
        
        return results

    @staticmethod
    async def get_prizes(conn, event_id):
        """Get prizes for a lottery event"""
        # Check if event exists
        event = await LotteryBusiness.get_lottery_event(conn, event_id)
        
        prizes = await LotteryDAO.get_prizes(conn, event_id)
        return {"prizes": prizes}

    @staticmethod
    async def update_prize(conn, prize_id, prize_data):
        """Update a prize"""
        name = prize_data.name if prize_data.name is not None else ""
        quantity = prize_data.quantity if prize_data.quantity is not None else 0
        
        result = await LotteryDAO.update_prize(conn, prize_id, name, quantity)
        if not result:
            raise ResourceNotFoundException(f"Prize with ID {prize_id} not found")
        return result

    @staticmethod
    async def delete_prize(conn, prize_id):
        """Delete a prize"""
        result = await LotteryDAO.delete_prize(conn, prize_id)
        if not result:
            raise ResourceNotFoundException(f"Prize with ID {prize_id} not found")
        return {"id": result}

    @staticmethod
    async def draw_winners(conn, event_id):
        """Draw winners for a lottery event"""
        # Check if event exists
        event = await LotteryBusiness.get_lottery_event(conn, event_id)
        
        # Check if the event is in pending status
        if event['status'] != 'pending':
            raise ParameterViolationException("This lottery event is not in pending status. Only pending events can be drawn.")
        
        # Check if the event already has winners
        has_winners = await LotteryDAO.has_winners(conn, event_id)
        if has_winners:
            raise ParameterViolationException("This lottery event has already been drawn. Cannot draw again.")
        
        # Get all prizes
        prizes = await LotteryDAO.get_prizes(conn, event_id)
        if not prizes:
            raise ParameterViolationException("No prizes defined for this lottery event")
        
        # Get participants who haven't won yet
        participants = await LotteryDAO.get_non_winners(conn, event_id)
        if not participants:
            raise ParameterViolationException("No participants available for drawing")
        
        # Draw winners for each prize
        winners_by_prize = []
        for prize in prizes:
            prize_winners = []
            quantity = min(prize['quantity'], len(participants))
            
            # Randomly select winners
            selected_winners = random.sample(participants, quantity)
            
            # Remove selected winners from participants pool to avoid duplicates
            participant_ids = [p['participant_id'] for p in selected_winners]
            participants = [p for p in participants if p['participant_id'] not in participant_ids]
            
            # Save winners to database
            for winner in selected_winners:
                result = await LotteryDAO.save_winner(conn, event_id, prize['id'], winner['participant_id'])
                prize_winners.append({**winner, 'winner_id': result['id']})
            
            winners_by_prize.append({
                "prize_name": prize['name'],
                "quantity": prize['quantity'],
                "winners": prize_winners
            })
        
        # Update event status to 'drawn'
        await LotteryDAO.update_event_status(conn, event_id, "drawn")
        
        return winners_by_prize

    @staticmethod
    async def reset_drawing(conn, event_id):
        """Reset a lottery drawing by deleting all winners and setting status back to pending"""
        # Check if event exists
        event = await LotteryBusiness.get_lottery_event(conn, event_id)
        
        # Check if the event has winners
        has_winners = await LotteryDAO.has_winners(conn, event_id)
        if not has_winners:
            raise ParameterViolationException("This lottery event has no winners to delete.")
        
        # Delete all winners for this event
        deleted_winners = await LotteryDAO.delete_winners(conn, event_id)
        
        # Update event status back to 'pending'
        await LotteryDAO.update_event_status(conn, event_id, "pending")
        
        # Convert to dict to avoid serialization issues with asyncpg.Record
        return {
            "event_id": event_id,
            "deleted_winners_count": len(deleted_winners),
            "status": "pending"
        }

    @staticmethod
    async def get_winners(conn, event_id):
        """Get winners for a lottery event"""
        # Check if event exists
        event = await LotteryBusiness.get_lottery_event(conn, event_id)
        
        # Get all winners
        all_winners = await LotteryDAO.get_winners(conn, event_id)
        
        # Group winners by prize
        prizes_map = {}
        for winner in all_winners:
            prize_id = winner['prize_id']
            prize_name = winner['prize_name']
            
            if prize_id not in prizes_map:
                prizes_map[prize_id] = {
                    "prize_name": prize_name,
                    "quantity": 0,
                    "winners": []
                }
            
            prizes_map[prize_id]["quantity"] += 1
            
            # Convert row to dict excluding some fields
            winner_dict = {k: v for k, v in winner.items() 
                          if k not in ('prize_id', 'prize_name', 'event_id')}
            prizes_map[prize_id]["winners"].append(winner_dict)
        
        return list(prizes_map.values())

    @staticmethod
    async def export_winners(conn, event_id):
        """Export winners for a lottery event to Excel"""
        # Check if event exists
        event = await LotteryBusiness.get_lottery_event(conn, event_id)
        
        # Get all winners
        all_winners = await LotteryDAO.get_winners(conn, event_id)
        
        if not all_winners:
            raise ParameterViolationException("No winners available for export")
        
        # Prepare data for Excel
        excel_data = []
        for i, winner in enumerate(all_winners, 1):
            excel_data.append({
                "序號": i,
                "獎項名稱": winner['prize_name'],
                "系所": winner.get('department', ''),
                "年級": winner.get('grade', ''),
                "姓名": winner.get('name', ''),
                "學號": winner.get('student_id', ''),
                "必修問卷數": winner.get('required_surveys', ''),
                "已完成問卷數": winner.get('completed_surveys', ''),
                "問卷完成狀態": "是" if winner.get('surveys_completed') else "否",
                "有效問卷狀態": "是" if winner.get('valid_surveys') else "否",
            })
        
        # Create DataFrame and export to Excel
        df = pd.DataFrame(excel_data)
        
        # Create directory if it doesn't exist
        os.makedirs("exports", exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"exports/lottery_winners_{event_id}_{timestamp}.xlsx"
        
        # Export to Excel
        df.to_excel(filename, index=False)
        
        return {"file_url": f"/api/lottery/export/{os.path.basename(filename)}"}

    @staticmethod
    async def delete_participant(conn, participant_id):
        """Delete a specific participant"""
        # First get the participant to check which event it belongs to
        participant = await conn.fetchrow("""
            SELECT id, event_id FROM lottery_participants WHERE id = $1
        """, participant_id)
        
        if not participant:
            raise ResourceNotFoundException(f"Participant with ID {participant_id} not found")
        
        event_id = participant['event_id']
        
        # Check if the event exists and get its status
        event = await LotteryBusiness.get_lottery_event(conn, event_id)
        
        # Check if the event has been drawn (has winners)
        has_winners = await LotteryDAO.has_winners(conn, event_id)
        if has_winners:
            raise ParameterViolationException("Cannot delete participants from an event that has already been drawn. Please reset the drawing first.")
        
        # Delete the participant
        result = await LotteryDAO.delete_participant(conn, participant_id)
        if not result:
            raise ResourceNotFoundException(f"Participant with ID {participant_id} not found")
        
        return {
            "participant_id": result['id'],
            "event_id": result['event_id'],
            "message": "Participant deleted successfully"
        }

    @staticmethod
    async def delete_all_participants(conn, event_id):
        """Delete all participants for an event"""
        # Check if event exists
        event = await LotteryBusiness.get_lottery_event(conn, event_id)
        
        # Check if the event has been drawn (has winners)
        has_winners = await LotteryDAO.has_winners(conn, event_id)
        if has_winners:
            raise ParameterViolationException("Cannot delete participants from an event that has already been drawn. Please reset the drawing first.")
        
        # Delete all participants
        deleted_participants = await LotteryDAO.delete_all_participants(conn, event_id)
        
        return {
            "event_id": event_id,
            "deleted_participants_count": len(deleted_participants),
            "message": f"Successfully deleted {len(deleted_participants)} participants"
        } 