# Email API 使用說明

本 API 提供完整的郵件發送功能，支援單一郵件、批量郵件和中獎通知郵件發送，並支援自定義模板變數替換。

## 功能特色

- ✅ 支援多種 SMTP 伺服器設定
- ✅ 單一郵件和批量郵件發送
- ✅ 中獎通知郵件自動發送
- ✅ **模板變數替換功能**
- ✅ HTML 和純文字郵件支援
- ✅ 郵件伺服器連接測試
- ✅ 中興大學郵件伺服器最佳化設定

## API 端點

### 1. 取得 SMTP 設定範例

```http
GET /email/smtp-settings-example
```

### 2. 取得模板變數列表 🆕

```http
GET /email/template-variables
```

返回所有可用的模板變數及其說明和使用範例。

### 3. 測試郵件伺服器連接

```http
POST /email/test-connection
```

### 4. 發送單一郵件

```http
POST /email/send
```

### 5. 批量發送郵件

```http
POST /email/send-bulk
```

### 6. 發送中獎通知郵件

```http
POST /email/send-winners/{event_id}
```

## 模板變數功能 🆕

### 可用變數

| 變數名稱      | 說明         | 範例值              | 使用方式          |
| ------------- | ------------ | ------------------- | ----------------- |
| `winner_name` | 中獎者姓名   | 王小明              | `{{winner_name}}` |
| `event_name`  | 抽獎活動名稱 | 期末學生活動抽獎    | `{{event_name}}`  |
| `event_date`  | 活動日期     | 2024-01-15          | `{{event_date}}`  |
| `prize_name`  | 獎項名稱     | 頭獎 - iPad Pro     | `{{prize_name}}`  |
| `sender_name` | 寄件者名稱   | 抽獎系統            | `{{sender_name}}` |
| `student_id`  | 學號         | s1234567            | `{{student_id}}`  |
| `department`  | 系所         | 資訊工程學系        | `{{department}}`  |
| `grade`       | 年級         | 大三                | `{{grade}}`       |
| `phone`       | 電話號碼     | 0912345678          | `{{phone}}`       |
| `email`       | 電子郵件     | student@example.com | `{{email}}`       |

### 使用說明

1. **變數格式**：使用雙大括號 `{{variable_name}}` 來標記變數
2. **區分大小寫**：變數名稱區分大小寫
3. **預設值**：如果中獎者資料中沒有某個欄位，會顯示 "未提供"
4. **適用範圍**：可以在主旨、文字內容和 HTML 內容中使用變數

### 模板範例

#### 簡單文字模板

```text
親愛的 {{winner_name}}，

恭喜您在「{{event_name}}」中獲得「{{prize_name}}」！

請聯絡我們領取獎品。

{{sender_name}}
```

#### 詳細文字模板

```text
親愛的 {{winner_name}} 同學，

🎉 恭喜您中獎了！🎉

您在「{{event_name}}」抽獎活動中獲得了「{{prize_name}}」！

📋 中獎者資訊：
• 姓名：{{winner_name}}
• 學號：{{student_id}}
• 系所：{{department}}
• 年級：{{grade}}

📅 活動資訊：
• 活動名稱：{{event_name}}
• 活動日期：{{event_date}}

請盡快聯絡我們領取您的獎品！

祝您學業進步！
{{sender_name}}
```

#### HTML 模板範例

```html
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>中獎通知</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        line-height: 1.6;
        color: #333;
      }
      .container {
        max-width: 600px;
        margin: 0 auto;
        padding: 20px;
      }
      .header {
        background-color: #f8f9fa;
        padding: 20px;
        text-align: center;
      }
      .prize-info {
        background-color: #e8f5e8;
        padding: 15px;
        margin: 15px 0;
      }
      .winner-info {
        background-color: #f0f8ff;
        padding: 15px;
        margin: 15px 0;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="header">
        <h1>🎉 恭喜中獎！🎉</h1>
        <p>{{event_name}}</p>
      </div>

      <p>親愛的 <strong>{{winner_name}}</strong>，</p>

      <div class="prize-info">
        <h3>🏆 獲得獎項</h3>
        <p><strong>{{prize_name}}</strong></p>
      </div>

      <div class="winner-info">
        <h3>👤 中獎者資訊</h3>
        <ul>
          <li><strong>姓名：</strong>{{winner_name}}</li>
          <li><strong>學號：</strong>{{student_id}}</li>
          <li><strong>系所：</strong>{{department}}</li>
          <li><strong>年級：</strong>{{grade}}</li>
        </ul>
      </div>

      <p>請依照相關規定領取您的獎品。</p>
      <p><strong>{{sender_name}}</strong></p>
    </div>
  </body>
</html>
```

## 中興大學郵件設定

### 建議設定（安全連線）

```json
{
  "smtp_server": "dragon.nchu.edu.tw",
  "smtp_port": 465,
  "username": "your-username@dragon.nchu.edu.tw",
  "password": "your-password",
  "use_tls": true
}
```

### 一般連線設定（不建議）

```json
{
  "smtp_server": "dragon.nchu.edu.tw",
  "smtp_port": 25,
  "username": "your-username@dragon.nchu.edu.tw",
  "password": "your-password",
  "use_tls": false
}
```

## 使用範例

### 發送中獎通知（使用自定義模板）

```bash
curl -X POST "http://localhost:8000/email/send-winners/event_001" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "event_001",
    "email_config": {
      "smtp_server": "dragon.nchu.edu.tw",
      "smtp_port": 465,
      "username": "your-username@dragon.nchu.edu.tw",
      "password": "your-password",
      "use_tls": true
    },
    "sender_name": "中興大學抽獎系統",
    "subject": "🎉 恭喜 {{winner_name}} 在「{{event_name}}」中獲得「{{prize_name}}」！",
    "email_template": "親愛的 {{winner_name}} 同學，\n\n🎉 恭喜您中獎了！🎉\n\n您在「{{event_name}}」抽獎活動中獲得了「{{prize_name}}」！\n\n中獎者資訊：\n• 姓名：{{winner_name}}\n• 學號：{{student_id}}\n• 系所：{{department}}\n• 年級：{{grade}}\n\n活動資訊：\n• 活動名稱：{{event_name}}\n• 活動日期：{{event_date}}\n\n請盡快聯絡我們領取您的獎品！\n\n祝您學業進步！\n{{sender_name}}",
    "html_template": "<!DOCTYPE html><html><head><meta charset=\"UTF-8\"><title>中獎通知</title></head><body><h1>🎉 恭喜中獎！🎉</h1><p>親愛的 <strong>{{winner_name}}</strong>，</p><p>恭喜您在「{{event_name}}」中獲得「{{prize_name}}」！</p><p><strong>{{sender_name}}</strong></p></body></html>"
  }'
```

### 取得模板變數列表

```bash
curl -X GET "http://localhost:8000/email/template-variables"
```

## 注意事項

1. **安全性**：建議使用 SMTPs (port 465) 安全連線
2. **帳號格式**：中興大學帳號格式為 `username@dragon.nchu.edu.tw`
3. **模板語法**：使用 `{{variable_name}}` 格式，注意大小寫
4. **HTML 模板**：確保 HTML 語法正確，建議先測試
5. **錯誤處理**：API 會返回發送成功和失敗的詳細資訊

## 測試建議

1. 先使用 `/email/test-connection` 測試連接
2. 使用 `/email/template-variables` 查看可用變數
3. 先發送單一測試郵件確認設定正確
4. 再進行批量或中獎通知郵件發送

## 故障排除

### 常見問題

1. **連接超時**：檢查網路連線和防火牆設定
2. **認證失敗**：確認帳號密碼正確
3. **模板變數未替換**：檢查變數名稱拼寫和大小寫
4. **HTML 顯示異常**：檢查 HTML 語法和編碼

### 支援的郵件服務商

- ✅ 中興大學 (dragon.nchu.edu.tw)
- ✅ Gmail (smtp.gmail.com)
- ✅ Outlook (smtp-mail.outlook.com)
- ✅ Yahoo (smtp.mail.yahoo.com)
- ✅ 其他標準 SMTP 伺服器

更多詳細資訊請參考 API 文檔或聯絡系統管理員。
