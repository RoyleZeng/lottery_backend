import random
import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Any

from lottery_api.data_access_object.lottery_dao import LotteryDAO
from lottery_api.lib.base_exception import ResourceNotFoundException, ParameterViolationException
from lottery_api.schema.lottery import ValidSurveys, SurveysCompleted, StudentType


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
    async def update_lottery_event(conn, event_id, event_data):
        """Update a lottery event"""
        # First check if event exists
        existing_event = await LotteryBusiness.get_lottery_event(conn, event_id)
        
        # Check if event has been drawn (prevent modification of drawn events)
        if existing_event['status'] == 'drawn':
            raise ParameterViolationException("Cannot update a lottery event that has already been drawn")
        
        # Prepare update data, converting enum to value if needed
        update_data = {}
        if event_data.academic_year_term is not None:
            update_data['academic_year_term'] = event_data.academic_year_term
        if event_data.name is not None:
            update_data['name'] = event_data.name
        if event_data.description is not None:
            update_data['description'] = event_data.description
        if event_data.event_date is not None:
            update_data['event_date'] = event_data.event_date
        if event_data.type is not None:
            update_data['type'] = event_data.type.value
        
        # Perform update
        result = await LotteryDAO.update_lottery_event(conn, event_id, **update_data)
        if not result:
            raise ResourceNotFoundException(f"Lottery event with ID {event_id} not found or no changes made")
        
        return result

    @staticmethod
    async def import_students_and_add_participants(conn, event_id, students_data: List[Dict[str, Any]]):
        """Import students and add them as participants with metadata from Oracle"""
        # Get event info to check type
        event = await LotteryBusiness.get_lottery_event(conn, event_id)
        
        # Pre-filter students for final_teaching events
        filtered_students = []
        skipped_students = []
        total_uploaded = len(students_data)
        
        for student_data in students_data:
            # For final_teaching events, check both surveys_completed and valid_surveys
            if event['type'] == 'final_teaching':
                # Check surveys_completed
                surveys_completed = student_data.get('surveys_completed')
                if isinstance(surveys_completed, SurveysCompleted):
                    surveys_completed_value = surveys_completed.value
                else:
                    surveys_completed_value = surveys_completed
                
                # Check valid_surveys
                valid_surveys = student_data.get('valid_surveys')
                if isinstance(valid_surveys, ValidSurveys):
                    valid_surveys_value = valid_surveys.value
                else:
                    valid_surveys_value = valid_surveys
                
                # Both must be "Y" to be eligible for drawing
                if surveys_completed_value != SurveysCompleted.YES.value or valid_surveys_value != ValidSurveys.YES.value:
                    skip_reason = []
                    if surveys_completed_value != SurveysCompleted.YES.value:
                        skip_reason.append("surveys_completed is not Y")
                    if valid_surveys_value != ValidSurveys.YES.value:
                        skip_reason.append("valid_surveys is not Y")
                    
                    skipped_students.append({
                        "student_id": student_data.get('id', ''),
                        "reason": " and ".join(skip_reason)
                    })
                    continue
            
            filtered_students.append(student_data)
        
        # Use batch processing for better performance
        if filtered_students:
            result = await LotteryDAO.add_participants_batch(conn, event_id, filtered_students, event['type'])
            
            # Combine results
            all_imported = []
            for participant in result["imported"]:
                # Find corresponding student data for name
                student_data = next((s for s in filtered_students if s.get('id') == participant['meta']['student_info']['id']), {})
                all_imported.append({
                    "participant_id": participant['id'],
                    "student_id": participant['meta']['student_info']['id'],
                    "student_name": student_data.get('name', '')
                })
            
            # Combine skipped students
            all_skipped = skipped_students + result["skipped"]
            
            # Calculate eligible count (imported students who can participate in drawing)
            total_eligible = len(all_imported)
            
            return {
                "imported": all_imported,
                "skipped": all_skipped,
                "total_uploaded": total_uploaded,
                "total_imported": len(all_imported),
                "total_eligible": total_eligible,
                "total_skipped": len(all_skipped),
                "inserted_count": result.get("inserted_count", 0),
                "updated_count": result.get("updated_count", 0)
            }
        else:
            return {
                "imported": [],
                "skipped": skipped_students,
                "total_uploaded": total_uploaded,
                "total_imported": 0,
                "total_eligible": 0,
                "total_skipped": len(skipped_students),
                "inserted_count": 0,
                "updated_count": 0
            }

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
        
        # Get all winners (without privacy masking for export)
        all_winners = await LotteryDAO.get_winners_for_export(conn, event_id)
        
        if not all_winners:
            raise ParameterViolationException("No winners available for export")
        
        # Prepare data for Excel with new format
        excel_data = []
        for i, winner in enumerate(all_winners, 1):
            # Use Oracle name (Chinese name if available, otherwise English name)
            display_name = winner.get('chinese_name', '') or winner.get('english_name', '') or winner.get('name', '')
            # Convert student type to Chinese
            student_type_value = winner.get('student_type')
            if student_type_value == StudentType.FOREIGN.value or student_type_value == 'Y':
                student_type_text = "外籍生"
            elif student_type_value == StudentType.DOMESTIC.value or student_type_value == 'N':
                student_type_text = "本國生"
            else:
                student_type_text = ""
            
            excel_data.append({
                "序號": i,
                "獎項": winner['prize_name'],
                "系所": winner.get('department', ''),
                "年級": winner.get('grade', ''),
                "姓名": display_name,
                "學號": winner.get('oracle_student_id', '') or winner.get('student_id', ''),
                "身份證字號": winner.get('id_number', ''),
                "戶籍地址": winner.get('address', ''),
                "身份別": student_type_text,
                "手機": winner.get('phone', ''),
                "電子郵件": winner.get('email', '')
            })
        
        # Create DataFrame and export to Excel
        df = pd.DataFrame(excel_data)
        
        # Create directory if it doesn't exist
        os.makedirs("exports", exist_ok=True)
        
        # Generate filename - use a consistent format for easy access
        filename = f"exports/中獎名單_{event_id}.xlsx"
        
        # Export to Excel with proper encoding
        df.to_excel(filename, index=False, engine='openpyxl')
        
        return {"file_url": f"/api/lottery/export/中獎名單_{event_id}.xlsx"}

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

    @staticmethod
    async def soft_delete_event(conn, event_id):
        """Soft delete a lottery event"""
        # Check if event exists and is not already deleted
        event = await LotteryDAO.get_lottery_event_by_id(conn, event_id)
        if not event:
            raise ResourceNotFoundException(f"Lottery event with ID {event_id} not found or already deleted")
        
        # Perform soft delete
        result = await LotteryDAO.soft_delete_event(conn, event_id)
        if not result:
            raise ResourceNotFoundException(f"Failed to delete lottery event with ID {event_id}")
        
        return result

    @staticmethod
    async def restore_event(conn, event_id):
        """Restore a soft deleted lottery event"""
        # Check if event exists in deleted state
        result = await LotteryDAO.restore_event(conn, event_id)
        if not result:
            raise ResourceNotFoundException(f"Deleted lottery event with ID {event_id} not found")
        
        return result

    @staticmethod
    async def get_deleted_events(conn, limit=100, offset=0):
        """Get all soft deleted lottery events with pagination"""
        return await LotteryDAO.get_deleted_events(conn, limit, offset) 