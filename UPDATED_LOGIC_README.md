# 上傳參與者與抽獎邏輯更新說明

## 概述

根據用戶需求，系統進行了以下重要邏輯更新：

1. **General 參與者邏輯**：移除 Oracle 查不到就跳過的邏輯
2. **Final_teaching 參與者邏輯**：新增雙重條件檢查
3. **Schema 更新**：`surveys_completed` 改為 enum 類型
4. **回傳格式增強**：新增詳細統計資訊

## 主要變更

### 1. Schema 層變更

#### 新增 SurveysCompleted Enum

```python
class SurveysCompleted(str, Enum):
    """Enum for surveys completed status"""
    YES = "Y"  # 已完成問卷
    NO = "N"   # 未完成問卷
```

#### 更新的 Schema 類別

- `TeachingCommentBase.surveys_completed`: `Optional[SurveysCompleted]`
- `FinalParticipant.surveys_completed`: `Optional[SurveysCompleted]`
- `Winner.surveys_completed`: `Optional[SurveysCompleted]`

#### 增強的回傳格式

```python
class ImportStudentsResponse(BaseModel):
    imported: List[ImportedStudent]
    skipped: List[SkippedStudent]
    total_uploaded: int = 0      # 總共上傳的人數
    total_imported: int          # 匯入成功的人數
    total_eligible: int = 0      # 匯入成待抽名單中的人數
    total_skipped: int           # 跳過的人數
    inserted_count: int = 0      # 新增的參與者數量
    updated_count: int = 0       # 更新的參與者數量
```

### 2. General 參與者邏輯更新

#### 變更前的邏輯

```python
# 如果 Oracle 可用但查不到學生資料，跳過該學生
if oracle_available and not oracle_student_info:
    skipped_students.append({
        "student_id": student_id,
        "reason": "Student not found in Oracle database"
    })
    continue
```

#### 變更後的邏輯

```python
# 對於 general 活動：如果 Oracle 可用但查不到學生資料，
# 仍然匯入該學生但不補充 Oracle 資料
# （移除跳過邏輯）
```

#### 實際效果

- **變更前**：Oracle 查不到 → 跳過學生 → 不在待抽名單中
- **變更後**：Oracle 查不到 → 仍然匯入 → 在待抽名單中（但沒有 Oracle 補充資料）

### 3. Final_teaching 參與者邏輯更新

#### 變更前的邏輯

```python
# 只檢查 valid_surveys
if valid_surveys_value != ValidSurveys.YES.value:
    skipped_students.append({
        "student_id": student_data.get('id', ''),
        "reason": "valid_surveys is not Y"
    })
    continue
```

#### 變更後的邏輯

```python
# 同時檢查 surveys_completed 和 valid_surveys
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
```

#### 條件矩陣

| surveys_completed | valid_surveys | 結果    | 說明             |
| ----------------- | ------------- | ------- | ---------------- |
| Y                 | Y             | ✅ 匯入 | 完全符合條件     |
| Y                 | N             | ❌ 跳過 | 問卷無效         |
| N                 | Y             | ❌ 跳過 | 問卷未完成       |
| N                 | N             | ❌ 跳過 | 問卷未完成且無效 |

### 4. 抽獎邏輯更新

#### 新增資格篩選

```python
@staticmethod
async def get_non_winners(conn, event_id):
    """Get participants who haven't won any prize yet and are eligible for drawing"""
    # 獲取活動類型以決定資格條件
    event = await LotteryDAO.get_lottery_event_by_id(conn, event_id)

    # ... 查詢參與者 ...

    for row in rows:
        # 檢查抽獎資格
        is_eligible = True

        if event and event['type'] == 'final_teaching':
            # 對於 final_teaching 活動，surveys_completed 和 valid_surveys 都必須是 "Y"
            surveys_completed = teaching_comments.get('surveys_completed')
            valid_surveys = teaching_comments.get('valid_surveys')

            if surveys_completed != "Y" or valid_surveys != "Y":
                is_eligible = False

        # 只有符合資格的參與者才能進入抽獎池
        if not is_eligible:
            continue
```

### 5. 回傳格式增強

#### 新的統計資訊

```json
{
  "imported": [...],
  "skipped": [...],
  "total_uploaded": 10,     // 總共上傳的人數
  "total_imported": 7,      // 成功匯入的人數
  "total_eligible": 7,      // 匯入成待抽名單中的人數
  "total_skipped": 3,       // 跳過的人數
  "inserted_count": 5,      // 新增的參與者數量
  "updated_count": 2        // 更新的參與者數量
}
```

## 測試案例

### General 活動測試

```python
# 測試學生（包含不存在的學號）
students = [
    {"id": "S1234567", "name": "存在學生"},      # Oracle 可能找得到
    {"id": "S9999999", "name": "不存在學生1"},   # Oracle 肯定找不到
    {"id": "S0000000", "name": "不存在學生2"}    # Oracle 肯定找不到
]

# 預期結果：全部匯入（即使 Oracle 查不到）
expected_imported = 3
expected_skipped = 0
```

### Final_teaching 活動測試

```python
# 測試不同條件組合的學生
students = [
    {"surveys_completed": "Y", "valid_surveys": "Y"},  # ✅ 應該匯入
    {"surveys_completed": "N", "valid_surveys": "Y"},  # ❌ 應該跳過
    {"surveys_completed": "Y", "valid_surveys": "N"},  # ❌ 應該跳過
    {"surveys_completed": "N", "valid_surveys": "N"}   # ❌ 應該跳過
]

# 預期結果：只有第一個學生被匯入
expected_imported = 1
expected_skipped = 3
```

## 向後相容性

- **API 端點**：保持不變
- **請求格式**：保持不變，但支援新的 enum 值
- **回傳格式**：新增欄位，舊欄位保持不變
- **資料庫**：無結構變更，只有業務邏輯變更

## 使用方式

### General 活動匯入

```bash
curl -X POST "http://localhost:8000/lottery/events/{event_id}/participants" \
  -H "Content-Type: application/json" \
  -d '{
    "students": [
      {
        "id": "S1234567",
        "department": "資訊工程學系",
        "name": "王小明",
        "grade": "大四",
        "surveys_completed": "Y",
        "valid_surveys": "Y"
      }
    ]
  }'
```

### Final_teaching 活動匯入

```bash
curl -X POST "http://localhost:8000/lottery/events/{event_id}/participants" \
  -H "Content-Type: application/json" \
  -d '{
    "students": [
      {
        "id": "FT001",
        "department": "資訊工程學系",
        "name": "完全符合學生",
        "grade": "大四",
        "id_number": "A123456789",
        "address": "台中市南區興大路145號",
        "student_type": "N",
        "phone": "0912345678",
        "email": "ft001@smail.nchu.edu.tw",
        "surveys_completed": "Y",  // 必須是 Y
        "valid_surveys": "Y"       // 必須是 Y
      }
    ]
  }'
```

## 測試指令

```bash
# 執行完整測試
python test_updated_logic.py

# 測試涵蓋項目：
# 1. General 邏輯：Oracle 查不到不跳過
# 2. Final_teaching 邏輯：雙重條件檢查
# 3. 回傳格式：新統計欄位
# 4. 抽獎邏輯：只抽符合條件的參與者
```

## 注意事項

1. **資料一致性**：enum 值必須使用 "Y" 或 "N"
2. **條件檢查**：final_teaching 活動需要同時滿足兩個條件
3. **抽獎資格**：系統會自動篩選符合條件的參與者
4. **統計資訊**：新的回傳格式提供更詳細的處理統計

## 問題排查

### 常見問題

1. **Q**: General 活動的學生還是被跳過了？
   **A**: 檢查是否是 final_teaching 活動類型的條件檢查

2. **Q**: Final_teaching 活動沒有學生被匯入？
   **A**: 確認 surveys_completed 和 valid_surveys 都是 "Y"

3. **Q**: 抽獎時沒有可抽的參與者？
   **A**: 檢查參與者是否符合活動類型的資格條件

4. **Q**: 統計數字不正確？
   **A**: 確認是否使用了新的回傳格式欄位

## 影響範圍

- ✅ **上傳參與者功能**：邏輯更新
- ✅ **抽獎功能**：資格篩選更新
- ✅ **統計回傳**：格式增強
- ❌ **查看參與者**：無變更
- ❌ **匯出功能**：無變更
- ❌ **其他功能**：無變更
