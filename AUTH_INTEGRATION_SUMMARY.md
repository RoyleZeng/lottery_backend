# Auth 驗證集成總結

## 概述

已成功為所有需要認證的 API endpoints 加入 JWT auth 驗證功能，實現 20 分鐘 token 過期時間。

## 修改的文件

### 1. 配置文件修改

- **lottery_api/config.py**: 添加了 JWT 配置字段
  - `jwt_public_key: str` - JWT 公鑰
  - `jwt_private_key: Optional[str]` - JWT 私鑰

### 2. Auth Business Logic 修改

- **lottery_api/business_model/auth_business.py**: 加入 token 過期時間
  - `TOKEN_EXPIRY_TIME = 20 * 60` (1200 秒，20 分鐘)
  - 修改`login_user`方法，在生成 token 時設置過期時間

### 3. Auth Permission 修改

- **lottery_api/lib/auth_library/permission.py**: 修正 token 驗證方法
  - 使用正確的`get_claims_and_verify_token`方法進行 token 驗證

## 受保護的 API Endpoints

### Lottery APIs (lottery_api/endpoints/lottery.py)

✅ **所有 endpoints 都已加入 auth 驗證**

- `POST /lottery/events` - 創建抽獎活動
- `GET /lottery/events` - 獲取抽獎活動列表
- `GET /lottery/events/{event_id}` - 獲取特定抽獎活動
- `PUT /lottery/events/{event_id}` - 更新抽獎活動
- `DELETE /lottery/events/{event_id}` - 軟刪除抽獎活動
- `PUT /lottery/events/{event_id}/restore` - 恢復被刪除的活動
- `GET /lottery/deleted-events` - 獲取已刪除的活動
- `POST /lottery/events/{event_id}/participants` - 導入參與者
- `GET /lottery/events/{event_id}/participants` - 獲取參與者列表
- `DELETE /lottery/participants/{participant_id}` - 刪除特定參與者
- `DELETE /lottery/events/{event_id}/participants` - 刪除所有參與者
- `POST /lottery/events/{event_id}/prizes` - 設置獎項
- `GET /lottery/events/{event_id}/prizes` - 獲取獎項列表
- `PUT /lottery/prizes/{prize_id}` - 更新獎項
- `DELETE /lottery/prizes/{prize_id}` - 刪除獎項
- `POST /lottery/events/{event_id}/draw` - 抽獎
- `GET /lottery/events/{event_id}/winners` - 獲取中獎者
- `DELETE /lottery/events/{event_id}/winners` - 重置抽獎
- `GET /lottery/events/{event_id}/winners/export` - 導出中獎者 Excel
- `GET /lottery/export/{filename}` - 下載導出文件

### Email APIs (lottery_api/endpoints/email.py)

✅ **需要認證的 endpoints 都已加入 auth 驗證**

**受保護的 endpoints:**

- `POST /email/send` - 發送郵件
- `POST /email/send-bulk` - 批量發送郵件
- `POST /email/send-winners/{event_id}` - 發送中獎通知
- `POST /email/test-connection` - 測試郵件連接
- `POST /email/test-winners/{event_id}` - 測試中獎通知

**公開 endpoints (不需要認證):**

- `GET /email/template-variables` - 獲取郵件模板變數
- `GET /email/smtp-settings-example` - 獲取 SMTP 設定範例

### Auth APIs (lottery_api/endpoints/auth.py)

**公開 endpoints (不需要認證):**

- `POST /auth/register` - 用戶註冊
- `POST /auth/login` - 用戶登入

**受保護 endpoints:**

- `GET /auth/me` - 獲取當前用戶信息 (已有 auth 驗證)

## Auth 驗證機制

### JWT Token 配置

- **過期時間**: 20 分鐘 (1200 秒)
- **算法**: ES256 (ECDSA with P-256 and SHA-256)
- **發行者**: wild_force.io

### Token Claims 結構

```json
{
  "user_id": "用戶ID",
  "username": "用戶名",
  "roles": "用戶角色",
  "attributes": [],
  "iss": "wild_force.io",
  "iat": "發行時間戳",
  "exp": "過期時間戳"
}
```

### 使用方式

1. 用戶先調用 `POST /auth/login` 獲取 JWT token
2. 在後續 API 請求中，在 Header 加入: `Authorization: Bearer <token>`
3. Token 會在 20 分鐘後自動過期，需要重新登入

### 錯誤處理

- **401 Unauthorized**: Token 無效、過期或缺失
- **403 Forbidden**: Token 有效但權限不足
- **422 Unprocessable Entity**: 請求參數驗證失敗

## 測試驗證

### 測試文件

- `test_auth_apis.py` - 完整的 API auth 驗證測試

### 測試覆蓋

✅ 測試沒有 token 的受保護 API 返回 401  
✅ 測試有效 token 的受保護 API 正常訪問  
✅ 測試公開 API 不需要 token 即可訪問  
✅ 測試 token 過期機制

## 安全特性

1. **Token 過期**: 20 分鐘自動過期，減少 token 被盜用風險
2. **簽名驗證**: 使用 ES256 算法確保 token 完整性
3. **權限控制**: 每個受保護 endpoint 都需要有效 token
4. **錯誤隱藏**: 不洩露敏感的系統信息

## 部署注意事項

1. 確保環境變數文件 `config.local.env` 包含正確的 JWT 密鑰
2. JWT 密鑰應使用強隨機生成，不可泄露
3. 生產環境建議使用更短的 token 過期時間
4. 建議實施 token 刷新機制避免用戶頻繁重新登入

## 後續改進建議

1. **Token 刷新機制**: 實施 refresh token 避免頻繁登入
2. **角色權限**: 基於用戶角色實施更細粒度的權限控制
3. **API 限流**: 實施 rate limiting 防止 API 濫用
4. **審計日誌**: 記錄所有 API 訪問日誌用於安全審計
