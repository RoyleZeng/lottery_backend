# Oracle 數據庫集成功能說明

## 概述

本次更新將抽獎系統與 Oracle 數據庫集成，實現以下功能：

1. **從 Oracle 數據庫獲取學生詳細資料**
2. **驗證學生身份** - 只有在 Oracle 中存在的學生才能參與抽獎
3. **自動生成郵件地址** - 使用 Oracle 中的學生資料
4. **支援 final_teaching 類型活動** - 根據 valid_surveys 狀態篩選參與者
5. **更新 Excel 匯出格式** - 包含更多學生詳細資訊

## Oracle 數據庫配置

### 依賴項說明

- **cx_Oracle**: Oracle 數據庫客戶端（可選）
- 如果未安裝 cx_Oracle，系統會自動使用模擬數據進行開發和測試
- 生產環境中需要安裝 cx_Oracle 以連接真實的 Oracle 數據庫

### 安裝 Oracle 客戶端（可選）

```bash
# 如果需要連接真實Oracle數據庫，請安裝cx_Oracle
poetry add cx_Oracle

# 或使用pip
pip install cx_Oracle
```

### 連接資訊

- **IP**: 140.120.3.90
- **Port**: 1521
- **Database**: nchu
- **Username**: studlottery
- **Password**: Lottery2025

### 查詢的學生資料欄位

從 `SCHOOL.STFSTUD` 表查詢以下欄位：

| 欄位名稱          | 說明       | 用途               |
| ----------------- | ---------- | ------------------ |
| PS_STUD_NO        | 學號       | 主要識別碼         |
| STUD_ID           | 身分證字號 | 身份驗證           |
| STUD_CHINESE_NAME | 中文姓名   | 優先顯示名稱       |
| STUD_ENGLISH_NAME | 英文姓名   | 備用顯示名稱       |
| STUD_NOW_TEL      | 電話       | 聯絡資訊           |
| STUD_NOW_POST     | 郵遞區號   | 地址資訊           |
| STUD_NOW_ADDR     | 地址       | 戶籍地址           |
| STUD_EXTRA        | 身份別     | Y=外籍生, N=本國生 |

## 功能更新

### 1. 學生資料驗證

- 匯入參與者時會自動查詢 Oracle 數據庫
- 只有在 Oracle 中找到的學生才會被加入抽獎名單
- 找不到的學生會被記錄在跳過名單中
- **批次處理**: 自動將大量學生 ID 分批查詢（每批最多 900 筆），避免 Oracle ORA-01795 錯誤

### 2. Final Teaching 活動類型

- 新增 `final_teaching` 活動類型
- 只有 `valid_surveys` 為 `Y` 的學生才能參與
- 其他學生會被自動跳過

### 3. 郵件地址生成

- 使用 Oracle 中的學生資料自動生成郵件地址
- 格式：`{學號}@smail.nchu.edu.tw`
- 發送中獎通知時優先使用 Oracle 中的郵件地址

### 4. Excel 匯出格式更新

新的匯出欄位：

| 欄位名稱   | 來源     | 說明                       |
| ---------- | -------- | -------------------------- |
| 序號       | 系統生成 | 流水號                     |
| 獎項       | 抽獎結果 | 獲得的獎項名稱             |
| 系所       | 匯入資料 | 學生所屬系所               |
| 年級       | 匯入資料 | 學生年級                   |
| 姓名       | Oracle   | 優先中文姓名，無則英文姓名 |
| 學號       | Oracle   | PS_STUD_NO                 |
| 身份證字號 | Oracle   | STUD_ID                    |
| 戶籍地址   | Oracle   | STUD_NOW_ADDR              |
| 身份別     | Oracle   | 外籍生/本國生              |
| 手機       | Oracle   | STUD_NOW_TEL               |
| 電子郵件   | Oracle   | 自動生成的郵件地址         |

## API 更新

### 匯入參與者 API 回應格式更新

```json
{
  "imported": [
    {
      "participant_id": 123,
      "student_id": "1234567",
      "student_name": "王小明"
    }
  ],
  "skipped": [
    {
      "student_id": "9999999",
      "reason": "Student not found in Oracle database"
    },
    {
      "student_id": "1234568",
      "reason": "valid_surveys is not Y"
    }
  ],
  "total_imported": 1,
  "total_skipped": 2
}
```

### 參與者資料包含 Oracle 資訊

```json
{
  "id": 123,
  "student_id": "1234567",
  "name": "王小明",
  "department": "資訊工程學系",
  "grade": "大四",
  "oracle_student_id": "1234567",
  "id_number": "A123456789",
  "chinese_name": "王小明",
  "english_name": "Wang Xiao Ming",
  "phone": "0912345678",
  "address": "台中市南區興大路145號",
  "student_type": "N",
  "email": "1234567@smail.nchu.edu.tw"
}
```

## 使用方式

### 1. 一般抽獎活動

```python
# 創建一般抽獎活動
event_data = LotteryEventCreate(
    academic_year_term="113-1",
    name="期末抽獎活動",
    description="一般學生抽獎活動",
    event_date=datetime.now(),
    type=LotteryEventType.general
)

# 匯入學生資料（會自動查詢Oracle）
students_data = [
    {
        "id": "1234567",
        "department": "資訊工程學系",
        "name": "王小明",
        "grade": "大四"
    }
]
```

### 2. 教學評量抽獎活動

```python
# 創建教學評量抽獎活動
event_data = LotteryEventCreate(
    academic_year_term="113-1",
    name="教學評量抽獎",
    description="完成教學評量問卷的學生抽獎",
    event_date=datetime.now(),
    type=LotteryEventType.final_teaching
)

# 匯入學生資料（只有valid_surveys='Y'的會被匯入）
students_data = [
    {
        "id": "1234567",
        "department": "資訊工程學系",
        "name": "王小明",
        "grade": "大四",
        "valid_surveys": "Y"  # 必須為Y才會被匯入
    }
]
```

## 技術細節

### Oracle 批次處理

由於 Oracle 數據庫的 IN 子句最多只能包含 1000 個表達式，系統實現了自動批次處理：

- **批次大小**: 每批最多 900 個學生 ID（留有安全邊際）
- **自動分批**: 當學生 ID 數量超過 900 時，自動分批查詢
- **日誌記錄**: 每批查詢都會記錄處理進度
- **結果合併**: 自動合併所有批次的查詢結果

### 性能優化

- 使用批次查詢減少數據庫連接次數
- 單次查詢最多處理 900 個學生 ID
- 支援處理超過 10,000 個學生的大型活動

## 測試

### 測試 Oracle 連接

```bash
python test_oracle_connection.py
```

### 測試完整集成功能

```bash
python test_oracle_integration.py
```

### 測試大批量處理

系統已通過 1500 個學生 ID 的批次處理測試，確保不會出現 ORA-01795 錯誤。

## 注意事項

1. **Oracle 客戶端**: 確保系統已安裝 Oracle 客戶端程式庫
2. **網路連接**: 確保能夠連接到 Oracle 數據庫伺服器
3. **學號格式**: 確保匯入的學號格式與 Oracle 中的 PS_STUD_NO 一致
4. **效能考量**: 使用批量查詢來提高大量學生資料的處理效能
5. **錯誤處理**: 系統會自動處理 Oracle 連接失敗的情況，並記錄錯誤訊息

## 故障排除

### 常見問題

1. **Oracle 連接失敗**

   - 檢查網路連接
   - 確認數據庫連接資訊是否正確
   - 檢查 Oracle 客戶端是否正確安裝

2. **學生資料找不到**

   - 確認學號格式是否正確
   - 檢查 Oracle 數據庫中是否存在該學生資料

3. **final_teaching 活動沒有參與者**
   - 確認學生資料中的 valid_surveys 欄位是否設為'Y'
   - 檢查 Oracle 中是否存在對應的學生資料

### 日誌查看

系統會記錄詳細的 Oracle 查詢和錯誤日誌，可以通過日誌文件查看具體的錯誤信息。
