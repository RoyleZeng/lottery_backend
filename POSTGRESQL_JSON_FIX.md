# PostgreSQL JSON 查詢修復

## 問題

在實作重複參與者去重功能時，出現以下錯誤：

```
asyncpg.exceptions.UndefinedFunctionError: function json_extract_path_text(jsonb, unknown, unknown) does not exist
HINT: No function matches the given name and argument types. You might need to add explicit type casts.
```

## 原因

使用了 `JSON_EXTRACT_PATH_TEXT` 函數，這是 MySQL 的語法，在 PostgreSQL 中不存在。

## 修復

將查詢語法改為使用 PostgreSQL 標準的 JSON 操作符：

### 修復前（錯誤）

```sql
SELECT id, event_id, meta, created_at
FROM lottery_participants
WHERE event_id = $1
AND JSON_EXTRACT_PATH_TEXT(meta, 'student_info', 'id') IN ($2, $3, ...)
```

### 修復後（正確）

```sql
SELECT id, event_id, meta, created_at
FROM lottery_participants
WHERE event_id = $1
AND meta->'student_info'->>'id' IN ($2, $3, ...)
```

## PostgreSQL JSON 操作符

- `->` : 獲取 JSON 物件或陣列，返回 JSON 類型
- `->>` : 獲取 JSON 值，返回文字類型
- `#>` : 獲取指定路徑的 JSON 物件（使用陣列路徑）
- `#>>` : 獲取指定路徑的 JSON 值為文字（使用陣列路徑）

## 範例

```sql
-- 獲取巢狀 JSON 的值
SELECT meta->'student_info'->>'id' FROM lottery_participants;

-- 等同於（使用路徑陣列）
SELECT meta#>>'{student_info,id}' FROM lottery_participants;
```

## 修復的檔案

- `lottery_api/data_access_object/lottery_dao.py` - 第 208 行
- `DUPLICATE_PREVENTION_README.md` - 更新文檔

## 狀態

✅ 修復完成，功能應該可以正常運作
