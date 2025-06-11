# 抽獎系統資料結構遷移總結

## 概述

本次遷移成功將抽獎系統的資料結構從使用獨立的 `student` 和 `final_teaching_comments` 表格，改為使用 `lottery_participants` 表格的 `meta` JSONB 欄位來存儲所有相關資訊。

## 主要變更

### 1. 資料庫結構變更

#### 移除的表格
- `student` - 學生基本資料表
- `final_teaching_comments` - 期末教學評鑑表

#### 修改的表格
- `lottery_participants` - 新增 `meta` JSONB 欄位，移除 `student_id` 欄位

#### 新的 meta 欄位結構
```json
{
  "student_info": {
    "id": "學號",
    "name": "姓名", 
    "department": "系所",
    "grade": "年級"
  },
  "teaching_comments": {  // 僅教學評鑑抽獎需要
    "required_surveys": 3,
    "completed_surveys": 3,
    "surveys_completed": true,
    "valid_surveys": true
  }
}
```

### 2. 移除的個人資訊欄位
為了保護隱私，以下欄位已被移除：
- `id_number` - 身份證字號
- `address` - 戶籍地址  
- `identity_type` - 身份別
- `phone` - 手機號碼
- `email` - 電子郵件

### 3. 程式碼變更

#### DAO 層 (`lottery_dao.py`)
- 新增 `_parse_meta()` 方法處理 JSONB 欄位解析
- 重寫 `add_participant()` 方法，直接存儲學生資訊到 meta 欄位
- 重寫 `get_participants()`, `get_winners()`, `get_non_winners()` 方法，自動展開 meta 資訊
- 移除 `get_or_create_student()` 方法

#### 業務邏輯層 (`lottery_business.py`)
- 簡化 `import_students_and_add_participants()` 方法
- 更新 Excel 匯出功能，移除個人敏感資訊欄位

#### Schema 定義 (`lottery.py`)
- 更新 `StudentBase` 模型，移除個人資訊欄位
- 更新 `Winner` 模型，移除個人資訊欄位
- 保持 API 回應格式的向後相容性

#### API 端點 (`lottery.py`)
- 新增學生導入端點 `POST /events/{event_id}/participants`
- 保持現有端點的功能不變

### 4. 腳本更新

#### 遷移腳本
- `db_migrations/remove_old_tables.sql` - 移除舊表格並確保新結構
- `scripts/run_migrations.sh` - 支援多個遷移文件執行

#### 資料生成腳本
- `scripts/create_lottery_events.py` - 重寫以使用新的 meta 結構
- `scripts/test_new_api.py` - 新增測試腳本驗證新結構

## 執行的遷移步驟

1. **執行資料庫遷移**
   ```bash
   ./scripts/run_migrations.sh
   ```

2. **生成測試資料**
   ```bash
   python scripts/create_lottery_events.py
   ```

3. **驗證新結構**
   ```bash
   python scripts/test_new_api.py
   ```

## 測試結果

✅ 所有測試通過：
- 資料庫結構正確建立
- 舊表格成功移除
- 新的 meta 欄位正常工作
- 參與者資料正確存儲和讀取
- 教學評鑑資料正確處理
- 統計功能正常運作

## 優勢

1. **簡化資料結構** - 減少表格數量和 JOIN 查詢
2. **保護隱私** - 移除敏感個人資訊
3. **靈活性** - JSONB 欄位可輕鬆擴展
4. **效能提升** - 減少複雜查詢
5. **維護性** - 更簡潔的資料模型

## 向後相容性

- API 回應格式保持不變
- 現有的前端程式碼無需修改
- 所有功能正常運作

## 注意事項

1. 現有資料在遷移時會被清除
2. 新結構不支援學生資料的獨立管理
3. 所有學生資訊都與特定抽獎活動綁定
4. 如需持久化學生資料，需考慮其他解決方案

## 檔案清單

### 修改的檔案
- `db_migrations/lottery_tables.sql`
- `db_migrations/remove_old_tables.sql`
- `lottery_api/data_access_object/lottery_dao.py`
- `lottery_api/business_model/lottery_business.py`
- `lottery_api/schema/lottery.py`
- `lottery_api/endpoints/lottery.py`
- `scripts/create_lottery_events.py`
- `scripts/run_migrations.sh`

### 新增的檔案
- `scripts/test_new_api.py`
- `scripts/README_new_structure.md`
- `MIGRATION_SUMMARY.md`

遷移已成功完成，系統現在使用新的簡化資料結構運行。 