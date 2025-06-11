# Lottery Backend API

A FastAPI backend for managing lottery events, participants, prizes, drawing winners, exporting winner lists, and sending email notifications.

## Setup

1. Make sure you have PostgreSQL installed and running
2. Create a database and user as per the configuration in `lottery_api/data_access_object/db.py`
3. Run the database migration script: `psql -U <username> -d <database> -f db_migrations/lottery_tables.sql`
4. Install dependencies: `pip install -r requirements.txt` or `poetry install`
5. Start the server: `uvicorn lottery_api.main:app --reload`

## API Documentation

Once the server is running, you can access the API documentation at: `http://localhost:8000/spec/doc`

## Lottery API Endpoints

### Lottery Events

- `POST /lottery/events` - Create a new lottery event
- `GET /lottery/events` - List all lottery events
- `GET /lottery/events/{event_id}` - Get a specific lottery event

### Participants

- `POST /lottery/events/{event_id}/participants/upload` - Upload participants from Excel or CSV
- `GET /lottery/events/{event_id}/participants` - Get participants for an event

### Prizes

- `POST /lottery/events/{event_id}/prizes` - Set prizes for an event
- `GET /lottery/events/{event_id}/prizes` - Get prizes for an event
- `PUT /lottery/prizes/{prize_id}` - Update a specific prize
- `DELETE /lottery/prizes/{prize_id}` - Delete a specific prize

### Drawing and Winners

- `POST /lottery/draw` - Draw winners for an event
- `GET /lottery/events/{event_id}/winners` - Get winners for an event
- `GET /lottery/events/{event_id}/export` - Export winners to Excel
- `GET /lottery/export/{filename}` - Download exported winners file

## Email API Endpoints

### Email Sending with Template Variables 🆕

- `POST /email/send` - Send email to specific recipients
- `POST /email/send-bulk` - Send bulk email to multiple recipients
- `POST /email/send-winners/{event_id}` - Send winner notification emails with template support
- `POST /email/test-connection` - Test email server connection
- `GET /email/smtp-settings-example` - Get SMTP settings examples
- `GET /email/template-variables` - Get available template variables 🆕

### Template Variables Feature

The email system now supports template variables for personalized winner notifications:

```text
親愛的 {{winner_name}} 同學，

恭喜您在「{{event_name}}」中獲得「{{prize_name}}」！

中獎者資訊：
• 姓名：{{winner_name}}
• 學號：{{student_id}}
• 系所：{{department}}
• 年級：{{grade}}

{{sender_name}}
```

Available variables: `winner_name`, `event_name`, `prize_name`, `student_id`, `department`, `grade`, `phone`, `email`, `event_date`, `sender_name`

For detailed email API usage, see [EMAIL_API_README.md](EMAIL_API_README.md).

## Usage Examples

### 1. Create a Lottery Event

```bash
curl -X POST "http://localhost:8000/lottery/events" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "End of Semester Survey Lottery",
    "description": "Lottery for students who completed end of semester surveys",
    "event_date": "2023-12-20T14:00:00"
  }'
```

### 2. Upload Participants

Use a multipart form to upload an Excel file containing participant data:

```bash
curl -X POST "http://localhost:8000/lottery/events/1/participants/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@participants.xlsx"
```

### 3. Set Prizes

```bash
curl -X POST "http://localhost:8000/lottery/events/1/prizes" \
  -H "Content-Type: application/json" \
  -d '{
    "prizes": [
      {"name": "First Prize - iPad", "quantity": 1},
      {"name": "Second Prize - AirPods", "quantity": 3},
      {"name": "Third Prize - Gift Card", "quantity": 10}
    ]
  }'
```

### 4. Draw Winners

```bash
curl -X POST "http://localhost:8000/lottery/draw" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1
  }'
```

### 5. Export Winners

```bash
curl -X GET "http://localhost:8000/lottery/events/1/export"
```

### 6. Send Winner Notification Emails (NCHU Configuration)

```bash
curl -X POST "http://localhost:8000/email/send-winners/your-event-id" \
  -H "Content-Type: application/json" \
  -d '{
    "email_config": {
      "smtp_server": "dragon.nchu.edu.tw",
      "smtp_port": 465,
      "username": "your-username@dragon.nchu.edu.tw",
      "password": "your-password",
      "use_tls": true
    },
    "sender_name": "抽獎系統",
    "subject": "恭喜您中獎了！"
  }'
```

## Data Format for Participants Upload

The system supports uploading participants via Excel or CSV files. The file should contain columns that match the fields in the `lottery_participants` table. Common fields include:

- department - Department/Faculty name
- student_id - Student ID number
- name - Student name
- grade - Student grade/year
- required_surveys - Number of surveys required
- completed_surveys - Number of surveys completed
- surveys_completed - Whether all surveys are completed (boolean)
- is_foreign - Whether the student is a foreign student (boolean)
- valid_surveys - Whether the surveys are valid (boolean)
- id_number - ID card number
- address - Home address
- identity_type - Type of identity
- phone - Contact phone number
- email - Email address

The actual fields used will depend on what data you include in your upload file.

## Email Configuration

The system supports sending emails through external SMTP servers with optimized support for NCHU (National Chung Hsing University) mail servers.

### NCHU (National Chung Hsing University) Configuration

**Recommended (Secure Connection)**:

```json
{
  "smtp_server": "dragon.nchu.edu.tw",
  "smtp_port": 465,
  "username": "your-username@dragon.nchu.edu.tw",
  "password": "your-password",
  "use_tls": true
}
```

**Alternative (Plain Connection - Not Recommended)**:

```json
{
  "smtp_server": "dragon.nchu.edu.tw",
  "smtp_port": 25,
  "username": "your-username@dragon.nchu.edu.tw",
  "password": "your-password",
  "use_tls": false
}
```

### Other Supported Email Providers

- Gmail (smtp.gmail.com:587) - Requires app passwords
- Outlook/Hotmail (smtp-mail.outlook.com:587)
- Yahoo Mail (smtp.mail.yahoo.com:587) - Requires app passwords
- Custom SMTP servers

### Timeout Solutions

The system includes several optimizations to prevent timeout issues:

- 30-second connection timeout
- Automatic connection type detection (SSL/TLS/Plain)
- Detailed error logging and handling
- Support for different SMTP ports (25, 587, 465)

For detailed email setup instructions, see [EMAIL_API_README.md](EMAIL_API_README.md).

## Testing

- Use `test_email_api.py` to test email functionality
- Use `email_api_examples.sh` for curl command examples
- Access API documentation at `http://localhost:8000/spec/doc` for interactive testing
