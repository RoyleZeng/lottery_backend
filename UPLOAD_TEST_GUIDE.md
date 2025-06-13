# 📤 待抽名單上傳功能測試指南

本指南說明如何測試抽獎系統的參與者文件上傳功能。

## 🎯 功能概述

系統支援上傳 Excel (.xlsx) 和 CSV (.csv) 格式的參與者名單，自動解析並匯入到指定的抽獎活動中。

## 📁 測試文件

執行 `python generate_test_participants.py` 會自動生成以下測試文件：

### 📊 生成的測試文件

| 文件名稱                                | 說明               | 用途                       |
| --------------------------------------- | ------------------ | -------------------------- |
| `test_data/sample_upload.xlsx`          | 範例文件（3 人）   | 基本功能測試，包含說明文檔 |
| `test_data/basic_participants.xlsx`     | 基本測試（50 人）  | 一般情況測試               |
| `test_data/large_participants.xlsx`     | 大量測試（200 人） | 性能測試                   |
| `test_data/essential_participants.xlsx` | 必要欄位（50 人）  | 最小欄位測試               |
| `test_data/eligible_participants.xlsx`  | 中獎候選人         | 符合抽獎資格的參與者       |
| `test_data/participants.csv`            | CSV 格式（50 人）  | CSV 上傳測試               |

### 📋 支援的欄位

| 欄位名稱            | 說明             | 必填 | 範例                     |
| ------------------- | ---------------- | ---- | ------------------------ |
| `department`        | 系所名稱         | ✅   | 資訊工程學系             |
| `student_id`        | 學號             | ✅   | s1234567                 |
| `name`              | 姓名             | ✅   | 王小明                   |
| `grade`             | 年級             | ❌   | 大三                     |
| `required_surveys`  | 需要完成的問卷數 | ❌   | 5                        |
| `completed_surveys` | 已完成的問卷數   | ❌   | 5                        |
| `surveys_completed` | 是否完成所有問卷 | ❌   | True                     |
| `is_foreign`        | 是否為外籍學生   | ❌   | False                    |
| `valid_surveys`     | 問卷是否有效     | ❌   | True                     |
| `id_number`         | 身分證字號       | ❌   | A123456789               |
| `address`           | 地址             | ❌   | 台中市西區中山路 123 號  |
| `identity_type`     | 身分類型         | ❌   | 學生                     |
| `phone`             | 電話號碼         | ❌   | 0912345678               |
| `email`             | 電子郵件         | ❌   | student@mail.nchu.edu.tw |

## 🚀 快速開始

### 1. 生成測試文件

```bash
# 生成所有測試文件
python generate_test_participants.py
```

### 2. 啟動 API 服務器

```bash
# 啟動服務器
uvicorn lottery_api.main:app --reload

# 或使用 Python 模組方式
python -m lottery_api.main
```

### 3. 執行自動化測試

```bash
# 執行完整的上傳功能測試
python test_upload_functionality.py
```

### 4. 手動測試（使用 curl）

```bash
# 測試上傳 Excel 文件
curl -X POST "http://localhost:8000/lottery/events/event_001/participants/upload" \
     -F "file=@test_data/sample_upload.xlsx"

# 測試上傳 CSV 文件
curl -X POST "http://localhost:8000/lottery/events/event_001/participants/upload" \
     -F "file=@test_data/participants.csv"
```

## 📊 API 端點

### 上傳參與者文件

```http
POST /lottery/events/{event_id}/participants/upload
Content-Type: multipart/form-data
```

**參數：**

- `event_id`: 抽獎活動 ID
- `file`: 上傳的文件（Excel 或 CSV）

**回應範例：**

```json
{
  "status": "success",
  "result": {
    "success_count": 50,
    "error_count": 0,
    "total_processed": 50,
    "errors": []
  }
}
```

### 取得參與者列表

```http
GET /lottery/events/{event_id}/participants
```

**回應範例：**

```json
{
  "status": "success",
  "result": {
    "total_count": 50,
    "eligible_count": 45,
    "participants": [
      {
        "id": "participant_001",
        "student_id": "s1234567",
        "name": "王小明",
        "department": "資訊工程學系",
        "grade": "大三",
        "phone": "0912345678",
        "email": "s1234567@mail.nchu.edu.tw"
      }
    ]
  }
}
```

## 🧪 測試案例

### 1. 基本功能測試

**目標：** 驗證系統能正確解析和匯入參與者資料

**測試文件：** `test_data/sample_upload.xlsx`

**預期結果：** 成功匯入 3 位參與者

```bash
curl -X POST "http://localhost:8000/lottery/events/test_event/participants/upload" \
     -F "file=@test_data/sample_upload.xlsx"
```

### 2. 大量資料測試

**目標：** 驗證系統處理大量資料的能力

**測試文件：** `test_data/large_participants.xlsx`

**預期結果：** 成功匯入 200 位參與者

### 3. 最小欄位測試

**目標：** 驗證僅包含必要欄位的文件上傳

**測試文件：** `test_data/essential_participants.xlsx`

**預期結果：** 成功匯入，其他欄位為空值

### 4. CSV 格式測試

**目標：** 驗證 CSV 格式文件上傳

**測試文件：** `test_data/participants.csv`

**預期結果：** 成功匯入 CSV 格式資料

### 5. 錯誤處理測試

**目標：** 驗證錯誤檔案的處理

**測試方法：** 上傳格式錯誤或空白的文件

**預期結果：** 返回適當的錯誤信息

## 📈 性能指標

### 預期性能

- **小文件（<10 人）：** < 1 秒
- **中等文件（10-100 人）：** < 3 秒
- **大文件（100-500 人）：** < 10 秒
- **超大文件（500-1000 人）：** < 30 秒

### 支援格式

- ✅ Excel (.xlsx)
- ✅ CSV (.csv)
- ❌ 舊版 Excel (.xls)
- ❌ 其他格式

## 🛠️ 故障排除

### 常見問題

1. **上傳失敗 - 文件格式錯誤**

   ```
   解決方案：確保文件是 .xlsx 或 .csv 格式
   ```

2. **部分資料匯入失敗**

   ```
   解決方案：檢查必填欄位是否完整（department, student_id, name）
   ```

3. **服務器連接失敗**

   ```
   解決方案：確保 API 服務器正在運行
   uvicorn lottery_api.main:app --reload
   ```

4. **字元編碼問題**
   ```
   解決方案：CSV 文件使用 UTF-8 編碼保存
   ```

### 除錯技巧

1. **查看詳細錯誤信息**

   ```bash
   # 查看 API 回應
   curl -v -X POST "http://localhost:8000/lottery/events/test/participants/upload" \
        -F "file=@test_data/sample_upload.xlsx"
   ```

2. **檢查文件內容**

   ```python
   import pandas as pd
   df = pd.read_excel("test_data/sample_upload.xlsx")
   print(df.head())
   print(df.columns.tolist())
   ```

3. **驗證資料格式**
   ```python
   # 檢查必填欄位
   required_columns = ['department', 'student_id', 'name']
   missing = [col for col in required_columns if col not in df.columns]
   print(f"缺少的必填欄位：{missing}")
   ```

## 📝 最佳實踐

1. **文件準備**

   - 確保必填欄位完整
   - 使用標準的欄位名稱
   - 資料格式一致

2. **測試流程**

   - 先用小文件測試基本功能
   - 逐步增加資料量
   - 測試邊界情況

3. **錯誤處理**
   - 仔細閱讀錯誤信息
   - 逐行檢查問題資料
   - 修正後重新上傳

## 🎯 下一步

上傳成功後，您可以：

1. **查看參與者列表**

   ```bash
   curl "http://localhost:8000/lottery/events/{event_id}/participants"
   ```

2. **設定獎項**

   ```bash
   curl -X POST "http://localhost:8000/lottery/events/{event_id}/prizes" \
        -H "Content-Type: application/json" \
        -d '{"prizes": [{"name": "頭獎", "quantity": 1}]}'
   ```

3. **執行抽獎**

   ```bash
   curl -X POST "http://localhost:8000/lottery/draw" \
        -H "Content-Type: application/json" \
        -d '{"event_id": "{event_id}"}'
   ```

4. **發送中獎通知**
   ```bash
   curl -X POST "http://localhost:8000/email/send-winners/{event_id}" \
        -H "Content-Type: application/json" \
        -d '{"email_config": {...}, "sender_name": "抽獎系統"}'
   ```

---

**💡 提示：** 更多詳細的 API 文檔請查看：http://localhost:8000/spec/doc
