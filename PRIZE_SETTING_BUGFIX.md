# 🔧 獎項設定 Bug 修復說明

## 🐛 問題描述

在使用 `POST /lottery/events/{event_id}/prizes` API 設定獎項時，會發生以下問題：

- 每次呼叫都會新增獎項，而不是替換現有的獎項
- 導致獎項數量一直累加，無法正確更新獎項設定
- 重複設定會造成資料庫中出現重複的獎項記錄

## ⚠️ 影響範圍

- **API 端點**：`POST /lottery/events/{event_id}/prizes`
- **業務邏輯**：`LotteryBusiness.set_prizes()` 方法
- **症狀**：獎項數量異常增長，無法正確替換獎項設定

## 🔍 根本原因

在 `lottery_api/business_model/lottery_business.py` 的 `set_prizes` 方法中：

```python
# 問題代碼（修復前）
@staticmethod
async def set_prizes(conn, event_id, prizes_data):
    # 獲取現有獎項
    existing_prizes = await LotteryDAO.get_prizes(conn, event_id)

    # 這裡有獲取現有獎項，但沒有刪除它們！
    existing_prize_ids = set(prize['id'] for prize in existing_prizes)

    # 直接創建新獎項，導致累加
    results = []
    for prize_data in prizes_data:
        result = await LotteryDAO.create_prize(...)  # 只創建，不刪除舊的
        results.append(result)

    return results
```

**問題**：程式碼獲取了現有獎項但沒有刪除它們，只是繼續創建新的獎項。

## ✅ 修復方案

修改 `set_prizes` 方法，確保在創建新獎項前先刪除所有現有獎項：

```python
# 修復後的代碼
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
```

## 🚀 驗證修復

使用提供的測試腳本驗證修復效果：

```bash
# 執行獎項設定測試
python test_prize_setting.py
```

### 測試案例

1. **第一次設定獎項**：創建 2 個獎項
2. **第二次設定獎項**：創建 3 個不同獎項（應該替換前面的 2 個）
3. **第三次設定獎項**：創建 1 個獎項（應該替換前面的 3 個）
4. **第四次設定獎項**：設定空列表（應該清空所有獎項）

### 預期結果

```
📍 第一次設定獎項
✅ 獎項設定成功，共 2 個獎項
📋 當前獎項列表（共 2 個）

📍 第二次設定獎項（應該替換，不是累加）
✅ 獎項設定成功，共 3 個獎項
📋 當前獎項列表（共 3 個）  # 不是 5 個！

📍 第三次設定獎項（更少的獎項）
✅ 獎項設定成功，共 1 個獎項
📋 當前獎項列表（共 1 個）  # 不是 6 個！

📍 第四次設定獎項（空獎項列表）
✅ 獎項設定成功，共 0 個獎項
📋 當前獎項列表（共 0 個）  # 完全清空
```

## 📝 手動測試指令

### 1. 創建測試活動

```bash
curl -X POST "http://localhost:8000/lottery/events" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "獎項測試活動",
       "description": "測試獎項設定功能",
       "event_date": "2024-12-31T23:59:59"
     }'
```

### 2. 第一次設定獎項

```bash
curl -X POST "http://localhost:8000/lottery/events/{event_id}/prizes" \
     -H "Content-Type: application/json" \
     -d '{
       "prizes": [
         {"name": "頭獎", "quantity": 1},
         {"name": "二獎", "quantity": 2}
       ]
     }'
```

### 3. 查看當前獎項

```bash
curl "http://localhost:8000/lottery/events/{event_id}/prizes"
```

### 4. 第二次設定獎項（測試替換）

```bash
curl -X POST "http://localhost:8000/lottery/events/{event_id}/prizes" \
     -H "Content-Type: application/json" \
     -d '{
       "prizes": [
         {"name": "特等獎", "quantity": 1},
         {"name": "優等獎", "quantity": 3},
         {"name": "佳作", "quantity": 5}
       ]
     }'
```

### 5. 再次查看獎項（應該只有 3 個，不是 5 個）

```bash
curl "http://localhost:8000/lottery/events/{event_id}/prizes"
```

## 💡 最佳實踐

1. **完整替換**：`set_prizes` 現在會完全替換獎項設定，不會累加
2. **清空功能**：傳入空陣列 `[]` 可以清空所有獎項
3. **原子操作**：整個操作是原子性的，要麼全部成功，要麼全部失敗
4. **狀態檢查**：只能在活動處於 `pending` 狀態時修改獎項

## 🔄 其他相關 API

如果需要單獨管理獎項，可以使用：

- `PUT /prizes/{prize_id}` - 更新單個獎項
- `DELETE /prizes/{prize_id}` - 刪除單個獎項
- `GET /lottery/events/{event_id}/prizes` - 查看獎項列表

## ⚡ 性能考量

修復後的實現：

- 先刪除所有現有獎項（可能多個 DELETE 操作）
- 再創建所有新獎項（可能多個 INSERT 操作）
- 對於大量獎項的情況，建議考慮使用批次操作來優化性能

## 🎯 總結

- ✅ **問題**：獎項累加而不是替換
- ✅ **原因**：只創建不刪除現有獎項
- ✅ **修復**：先刪除後創建，確保完全替換
- ✅ **驗證**：透過測試腳本確認修復效果
- ✅ **影響**：現在 `set_prizes` 行為符合預期

---

**修復版本**：已在 `lottery_api/business_model/lottery_business.py` 中修復
**測試工具**：`test_prize_setting.py`
**修復日期**：2024-06-11
