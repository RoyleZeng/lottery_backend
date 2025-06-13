# Email 自動生成功能說明

## 概述

抽獎系統現在支援根據學號自動生成對應的 email 地址，解決了中獎者通知時缺少 email 資訊的問題。

## 功能特色

✅ **自動 Email 生成**: 根據學號規則自動生成對應的 email 地址  
✅ **多種學號格式支援**: 支援各種學號開頭數字和前綴格式  
✅ **智能前綴處理**: 自動處理已有前綴字母的學號  
✅ **類型識別**: 根據學號判斷學生類型（大學部、研究所等）  
✅ **批量處理**: 支援批量生成多個學號的 email 地址  
✅ **驗證功能**: 提供 email 格式驗證功能

## Email 生成規則

根據您提供的學號轉換規則，系統會按照以下對應關係生成 email 地址：

| 學號開頭      | Email 前綴 | 學生類型                  | 範例                                          |
| ------------- | ---------- | ------------------------- | --------------------------------------------- |
| 4             | s          | 大學部 Undergraduate      | `4101027415` → `s4101027415@mail.nchu.edu.tw` |
| 7             | g          | 研究所 Graduate           | `7101027415` → `g7101027415@mail.nchu.edu.tw` |
| 8             | d          | 博士班 PHD                | `8101027415` → `d8101027415@mail.nchu.edu.tw` |
| 5             | w          | 在職專班 Executive Master | `5101027415` → `w5101027415@mail.nchu.edu.tw` |
| 3             | n          | 進修部 Night Division     | `3101027415` → `n3101027415@mail.nchu.edu.tw` |
| 6, 9, 1, 2, 0 | s          | 大學部 Undergraduate      | `6920938` → `s6920938@mail.nchu.edu.tw`       |

## 使用方式

### 1. 在中獎通知中自動使用

當發送中獎通知時，系統會自動：

1. 檢查中獎者是否已有 email 地址
2. 如果沒有，則根據學號自動生成 email 地址
3. 將生成的 email 地址用於發送通知

```python
# 系統會自動處理，無需手動操作
POST /email/send-winners/{event_id}
```

### 2. 程式化使用

```python
from lottery_api.utils.email_generator import EmailGenerator

# 單個學號生成
email = EmailGenerator.generate_email_from_student_id("4101027415")
print(email)  # s4101027415@mail.nchu.edu.tw

# 獲取學生類型
student_type = EmailGenerator.get_student_type_from_id("4101027415")
print(student_type)  # 大學部 Undergraduate

# 批量生成
student_ids = ["4101027415", "7101027416", "8101027417"]
emails = EmailGenerator.batch_generate_emails(student_ids)
print(emails)  # {'4101027415': 's4101027415@mail.nchu.edu.tw', ...}

# 驗證 email 格式
is_valid = EmailGenerator.validate_generated_email("s4101027415@mail.nchu.edu.tw")
print(is_valid)  # True
```

## 學號格式處理

### 支援的學號格式

- **純數字**: `4101027415`
- **小寫前綴**: `s4101027415`
- **大寫前綴**: `S4101027415`
- **混合格式**: `G7101027415`

### 處理邏輯

1. **前綴移除**: 自動移除已存在的前綴字母（如 s, S, g, G 等）
2. **數字驗證**: 確保去除前綴後為純數字且長度至少 6 位
3. **規則匹配**: 根據第一位數字匹配對應的 email 前綴
4. **格式生成**: 生成標準格式的 email 地址

## 錯誤處理

系統會在以下情況下無法生成 email：

- 學號為空或 null
- 學號格式不正確（非數字）
- 學號長度不足（少於 6 位數字）
- 學號開頭數字不在支援範圍內

在這些情況下，系統會：

- 記錄警告日誌
- 跳過該中獎者的 email 發送
- 在最終報告中標註失敗原因

## 測試功能

### 運行基本測試

```bash
# 測試 email 生成規則
python lottery_api/utils/email_generator.py

# 測試完整功能（包括數據庫中的實際數據）
python test_email_generation.py
```

### 測試結果範例

```
=== Email Generator 測試 ===
✅ 學號: 4101027415 -> Email: s4101027415@mail.nchu.edu.tw
✅ 學號: 7101027415 -> Email: g7101027415@mail.nchu.edu.tw
✅ 學號: s6920938 -> Email: s6920938@mail.nchu.edu.tw
```

## 日誌記錄

系統會記錄以下資訊：

```python
# 成功生成 email
logger.info(f"Generated email for student {student_id}: {email}")

# 無法生成 email
logger.warning(f"無法為學號 {student_id} 生成有效的 email 地址")

# 發送成功
logger.info(f"Winner notification sent to {email}")
```

## 配置說明

### Email 伺服器設定

系統使用中興大學的郵件伺服器：

```json
{
  "smtp_server": "dragon.nchu.edu.tw",
  "smtp_port": 465,
  "use_tls": true
}
```

### 生成的 Email 格式

所有生成的 email 都使用 `@mail.nchu.edu.tw` 域名，格式為：

- `{前綴}{學號}@mail.nchu.edu.tw`

## 安全考量

1. **隱私保護**: 系統不儲存實際的個人 email 地址
2. **動態生成**: Email 地址在需要時才生成，不會永久儲存
3. **格式驗證**: 確保生成的 email 格式符合規範
4. **錯誤處理**: 優雅處理無效學號，不會導致系統崩潰

## 維護說明

### 新增學號規則

如需支援新的學號開頭數字，請修改 `lottery_api/utils/email_generator.py` 中的：

```python
prefix_mapping = {
    '4': 's',  # 大學部 Undergraduate
    '7': 'g',  # 研究所 Graduate
    # 在此新增新規則
}

type_mapping = {
    '4': '大學部 Undergraduate',
    '7': '研究所 Graduate',
    # 在此新增對應的類型描述
}
```

### 修改 Email 域名

如需修改 email 域名，請在 `generate_email_from_student_id` 方法中修改：

```python
email = f"{prefix}{clean_id}@mail.nchu.edu.tw"  # 修改此行
```

## 常見問題

### Q: 為什麼某些學號無法生成 email？

A: 請檢查學號格式是否正確，確保：

- 學號為純數字（去除前綴後）
- 學號長度至少 6 位
- 學號開頭數字在支援範圍內

### Q: 如何新增支援的學號格式？

A: 修改 `EmailGenerator` 類中的 `prefix_mapping` 和 `type_mapping` 字典。

### Q: 生成的 email 是否真實存在？

A: 生成的 email 地址遵循中興大學的命名規則，但實際是否存在需要由郵件系統驗證。

### Q: 如何測試 email 發送功能？

A: 使用測試腳本 `test_email_generation.py` 進行完整測試，或使用 API 端點進行實際發送測試。

## 更新日誌

- **v1.0.0**: 初始版本，支援基本的學號轉 email 功能
- **v1.1.0**: 新增對多種學號開頭數字的支援
- **v1.2.0**: 改進前綴處理邏輯，支援大小寫混合格式
- **v1.3.0**: 降低最小學號長度要求至 6 位，提高相容性
