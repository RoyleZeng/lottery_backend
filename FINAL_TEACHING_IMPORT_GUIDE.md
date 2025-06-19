# Final Teaching 匯入功能說明

## 概述

本系統現在支援兩種不同的學生匯入模式：

1. **General 類型**：需要從 Oracle 資料庫補充學生個資
2. **Final Teaching 類型**：前端提供完整學生資料，不需要查詢 Oracle

## 功能變更說明

### 背景

由於前端已解決 `final_teaching` 類型活動的資料收集問題，現在可以直接提供完整的學生資訊，包括：

- 序號
- 獎項
- 系所
- 年級
- 姓名
- 學號
- 身份證字號
- 戶籍地址
- 身份別
- 手機
- 電子郵件

因此，`final_teaching` 類型的活動不再需要查詢 Oracle 資料庫來補充資料。

### API 變更

#### 匯入端點

**端點**: `POST /lottery/events/{event_id}/participants`

**請求格式**:

系統會自動根據活動類型和請求內容判斷處理方式：

##### General 類型活動（原有功能）

```json
{
  "students": [
    {
      "id": "S1234567",
      "department": "資訊工程學系",
      "name": "王小明",
      "grade": "大四",
      "required_surveys": 5,
      "completed_surveys": 5,
      "surveys_completed": true,
      "valid_surveys": true
    }
  ]
}
```

- 系統會查詢 Oracle 資料庫補充個人資訊
- 如果 Oracle 中找不到學生，該學生會被跳過

##### Final Teaching 類型活動（新功能）

```json
{
  "students": [
    {
      "id": "S1234567",
      "department": "資訊工程學系",
      "name": "王小明",
      "grade": "大四",
      "id_number": "A123456789",
      "address": "台中市南區興大路145號",
      "student_type": "本國生",
      "phone": "0912345678",
      "email": "s1234567@smail.nchu.edu.tw",
      "required_surveys": 5,
      "completed_surveys": 5,
      "surveys_completed": true,
      "valid_surveys": "Y"
    }
  ]
}
```

- 系統不會查詢 Oracle 資料庫
- 直接使用前端提供的完整資料
- 只有 `valid_surveys` 為 "Y" 的學生會被匯入

#### 回應格式

兩種類型的回應格式相同：

```json
{
  "result": {
    "imported": [
      {
        "participant_id": 123,
        "student_id": "S1234567",
        "student_name": "王小明"
      }
    ],
    "skipped": [
      {
        "student_id": "S2345678",
        "reason": "valid_surveys is not Y"
      }
    ],
    "total_imported": 1,
    "total_skipped": 1
  }
}
```

### 參與者資料格式

#### API 回應（包含個資遮罩）

```json
{
  "result": {
    "total": 2,
    "participants": [
      {
        "id": 123,
        "event_id": "event-uuid",
        "student_id": "S1***567",
        "department": "資訊工程學系",
        "name": "王O明",
        "grade": "大四",
        "created_at": "2024-01-15T10:00:00Z",
        // Oracle 資料（General 類型，經過遮罩）
        "oracle_student_id": "S1***567",
        "chinese_name": "王O明",
        "english_name": "W*** M***",
        // Final Teaching 完整資料（經過遮罩）
        "id_number": "A1******89",
        "address": "台中市南區***",
        "student_type": "本國生",
        "phone": "091*****78",
        "email": "s***@smail.nchu.edu.tw",
        // 教學評量資料
        "required_surveys": 5,
        "completed_surveys": 5,
        "surveys_completed": true,
        "valid_surveys": "Y"
      }
    ]
  }
}
```

#### Excel 匯出（完整資料，無遮罩）

Excel 匯出包含完整的學生資訊，用於正式用途：

| 欄位       | General 類型來源 | Final Teaching 類型來源 |
| ---------- | ---------------- | ----------------------- |
| 序號       | 系統生成         | 系統生成                |
| 獎項       | 抽獎結果         | 抽獎結果                |
| 系所       | 匯入資料         | 匯入資料                |
| 年級       | 匯入資料         | 匯入資料                |
| 姓名       | Oracle 資料庫    | 前端提供                |
| 學號       | Oracle 資料庫    | 前端提供                |
| 身份證字號 | Oracle 資料庫    | 前端提供                |
| 戶籍地址   | Oracle 資料庫    | 前端提供                |
| 身份別     | Oracle 資料庫    | 前端提供                |
| 手機       | Oracle 資料庫    | 前端提供                |
| 電子郵件   | Oracle 資料庫    | 前端提供                |

### 驗證邏輯

#### General 類型

1. 檢查 Oracle 資料庫連接狀態
2. 查詢 Oracle 取得學生資料
3. 如果找不到學生，跳過該學生
4. 如果是 final_teaching 活動，額外檢查 `valid_surveys`

#### Final Teaching 類型

1. 跳過 Oracle 資料庫查詢
2. 檢查 `valid_surveys` 是否為 "Y"
3. 如果不是 "Y"，跳過該學生
4. 直接使用前端提供的完整資料

### 個資保護

系統會對 API 回應進行個資遮罩：

- **學號**: 保留前 2 後 3，中間改為 `*`
- **中文姓名**: 三個字中間改 `O`，兩個字最後改 `O`
- **英文姓名**: 每個單字保留第一個字母，其他改為 `*`
- **身份證字號**: 保留前 1 後 2，中間改為 `*`
- **地址**: 只顯示縣市區，詳細地址改為 `***`
- **手機**: 保留前 3 後 2，中間改為 `*`
- **Email**: 只顯示第一個字母和 `@` 後的網域，其他改為 `*`

Excel 匯出不進行遮罩，包含完整資訊。

## 使用範例

### 創建 Final Teaching 活動

```bash
curl -X POST "http://localhost:8000/lottery/events" \
  -H "Content-Type: application/json" \
  -d '{
    "academic_year_term": "113-1",
    "name": "期末教學評量抽獎",
    "description": "完成教學評量問卷的學生抽獎活動",
    "event_date": "2024-01-15T10:00:00",
    "type": "final_teaching"
  }'
```

### 匯入 Final Teaching 學生

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
        "id_number": "A123456789",
        "address": "台中市南區興大路145號",
        "student_type": "本國生",
        "phone": "0912345678",
        "email": "s1234567@smail.nchu.edu.tw",
        "required_surveys": 5,
        "completed_surveys": 5,
        "surveys_completed": true,
        "valid_surveys": "Y"
      }
    ]
  }'
```

## 注意事項

1. **活動類型**: 系統會根據活動的 `type` 欄位自動判斷處理方式
2. **資料完整性**: Final Teaching 類型請確保提供所有必要欄位
3. **驗證邏輯**: Final Teaching 只有 `valid_surveys` 為 "Y" 的學生會被匯入
4. **個資保護**: API 回應會自動進行個資遮罩，Excel 匯出包含完整資訊
5. **向後相容**: General 類型的匯入邏輯完全不變

## 測試

可以使用提供的測試腳本驗證功能：

```bash
python test_final_teaching_import.py
```

測試腳本會：

1. 創建 Final Teaching 活動
2. 匯入測試學生資料
3. 驗證匯入結果
4. 檢查個資遮罩
5. 清理測試資料
