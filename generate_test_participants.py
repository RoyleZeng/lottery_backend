#!/usr/bin/env python3
"""
生成測試用的參與者 Excel 文件
用於測試待抽名單上傳功能
"""

import pandas as pd
import random
from datetime import datetime
import os

def generate_test_participants(num_participants=50):
    """生成測試參與者資料"""
    
    # 中興大學系所列表
    departments = [
        "資訊工程學系", "電機工程學系", "機械工程學系", "化學工程學系",
        "材料科學與工程學系", "環境工程學系", "土木工程學系", "生物醫學工程學系",
        "企業管理學系", "財務金融學系", "會計學系", "行銷學系",
        "國際貿易學系", "資訊管理學系", "應用經濟學系", "科技管理學系",
        "中國文學系", "外國語文學系", "歷史學系", "台灣文學與跨國文化學系",
        "生命科學系", "食品暨應用生物科技學系", "植物病理學系", "昆蟲學系",
        "園藝學系", "森林學系", "動物科學系", "獸醫學系",
        "應用數學系", "物理學系", "化學系", "地球科學系"
    ]
    
    # 年級列表
    grades = ["大一", "大二", "大三", "大四", "碩一", "碩二", "博一", "博二", "博三", "博四"]
    
    # 身分類型
    identity_types = ["學生", "在職專班", "研究生", "博士生", "交換學生"]
    
    # 台灣常見姓氏
    surnames = [
        "陳", "林", "李", "張", "王", "吳", "劉", "蔡", "楊", "許", 
        "鄭", "謝", "郭", "洪", "曾", "廖", "賴", "徐", "周", "葉",
        "蘇", "莊", "呂", "江", "何", "羅", "高", "潘", "簡", "朱"
    ]
    
    # 台灣常見名字
    given_names = [
        "志明", "美麗", "家豪", "怡君", "建宏", "雅婷", "宗翰", "佩君",
        "冠宇", "雨潔", "承翰", "心怡", "彥廷", "思妤", "柏翰", "欣怡",
        "哲瑋", "筱涵", "俊傑", "婉婷", "睿哲", "淑芬", "明哲", "麗華",
        "文龍", "秀英", "國輝", "淑娟", "志偉", "麗娟", "世豪", "美惠"
    ]
    
    participants = []
    
    for i in range(num_participants):
        # 生成學號（格式：s + 7位數字）
        student_id = f"s{random.randint(1000000, 9999999)}"
        
        # 隨機選擇姓名
        name = random.choice(surnames) + random.choice(given_names)
        
        # 隨機選擇系所和年級
        department = random.choice(departments)
        grade = random.choice(grades)
        
        # 問卷相關資料
        required_surveys = random.randint(3, 8)
        completed_surveys = random.randint(0, required_surveys)
        surveys_completed = completed_surveys >= required_surveys
        
        # 其他資料
        is_foreign = random.choice([True, False]) if random.random() < 0.1 else False
        valid_surveys = surveys_completed and random.choice([True, False]) if random.random() < 0.95 else True
        
        # 生成身分證字號（假的，僅供測試）
        id_number = f"{random.choice(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'])}{random.randint(100000000, 299999999)}"
        
        # 生成地址
        cities = ["台中市", "台北市", "新北市", "桃園市", "台南市", "高雄市", "彰化縣", "南投縣"]
        districts = ["西區", "北區", "東區", "南區", "中區", "西屯區", "北屯區", "南屯區"]
        address = f"{random.choice(cities)}{random.choice(districts)}{random.choice(['中山路', '民權路', '建國路', '忠孝路', '仁愛路'])}{random.randint(1, 999)}號"
        
        # 生成電話
        phone = f"09{random.randint(10000000, 99999999)}"
        
        # 生成 email
        email_domains = ["@mail.nchu.edu.tw", "@dragon.nchu.edu.tw", "@gmail.com", "@yahoo.com.tw"]
        email = f"{student_id}{random.choice(email_domains)}"
        
        participant = {
            "department": department,
            "student_id": student_id,
            "name": name,
            "grade": grade,
            "required_surveys": required_surveys,
            "completed_surveys": completed_surveys,
            "surveys_completed": surveys_completed,
            "is_foreign": is_foreign,
            "valid_surveys": valid_surveys,
            "id_number": id_number,
            "address": address,
            "identity_type": random.choice(identity_types),
            "phone": phone,
            "email": email
        }
        
        participants.append(participant)
    
    return participants

def create_excel_files():
    """創建多個測試 Excel 文件"""
    
    # 創建輸出目錄
    os.makedirs("test_data", exist_ok=True)
    
    # 1. 基本參與者名單（50人）
    print("生成基本參與者名單...")
    participants = generate_test_participants(50)
    df_basic = pd.DataFrame(participants)
    df_basic.to_excel("test_data/basic_participants.xlsx", index=False, engine='openpyxl')
    print(f"✅ 已生成：test_data/basic_participants.xlsx ({len(participants)} 人)")
    
    # 2. 大型參與者名單（200人）
    print("生成大型參與者名單...")
    participants_large = generate_test_participants(200)
    df_large = pd.DataFrame(participants_large)
    df_large.to_excel("test_data/large_participants.xlsx", index=False, engine='openpyxl')
    print(f"✅ 已生成：test_data/large_participants.xlsx ({len(participants_large)} 人)")
    
    # 3. 僅必要欄位的精簡版本
    print("生成精簡版參與者名單...")
    essential_columns = ["department", "student_id", "name", "grade", "phone", "email"]
    df_essential = df_basic[essential_columns]
    df_essential.to_excel("test_data/essential_participants.xlsx", index=False, engine='openpyxl')
    print(f"✅ 已生成：test_data/essential_participants.xlsx（僅包含必要欄位）")
    
    # 4. 中獎候選人（已完成所有問卷的參與者）
    print("生成中獎候選人名單...")
    eligible_participants = [p for p in participants if p['surveys_completed'] and p['valid_surveys']]
    if eligible_participants:
        df_eligible = pd.DataFrame(eligible_participants)
        df_eligible.to_excel("test_data/eligible_participants.xlsx", index=False, engine='openpyxl')
        print(f"✅ 已生成：test_data/eligible_participants.xlsx ({len(eligible_participants)} 人符合抽獎資格)")
    
    # 5. CSV 格式（測試 CSV 上傳）
    print("生成 CSV 格式檔案...")
    df_basic.to_csv("test_data/participants.csv", index=False, encoding='utf-8-sig')
    print("✅ 已生成：test_data/participants.csv")
    
    # 顯示範例資料
    print("\n📊 範例資料預覽：")
    print("="*80)
    print(df_basic.head(3).to_string(index=False))
    print("="*80)
    
    # 統計資訊
    print(f"\n📈 統計資訊：")
    print(f"   總參與者數量：{len(participants)}")
    print(f"   符合抽獎資格：{len(eligible_participants)}")
    print(f"   完成問卷比例：{len(eligible_participants)/len(participants)*100:.1f}%")
    print(f"   外籍學生數量：{sum(1 for p in participants if p['is_foreign'])}")
    print(f"   包含的系所數量：{len(set(p['department'] for p in participants))}")

def create_sample_upload_file():
    """創建一個小的範例上傳文件，包含詳細說明"""
    
    sample_data = [
        {
            "department": "資訊工程學系",
            "student_id": "s1234567",
            "name": "王小明",
            "grade": "大三",
            "required_surveys": 5,
            "completed_surveys": 5,
            "surveys_completed": True,
            "is_foreign": False,
            "valid_surveys": True,
            "id_number": "A123456789",
            "address": "台中市西區中山路123號",
            "identity_type": "學生",
            "phone": "0912345678",
            "email": "s1234567@mail.nchu.edu.tw"
        },
        {
            "department": "電機工程學系", 
            "student_id": "s2345678",
            "name": "李小華",
            "grade": "大二",
            "required_surveys": 4,
            "completed_surveys": 4,
            "surveys_completed": True,
            "is_foreign": False,
            "valid_surveys": True,
            "id_number": "B234567890",
            "address": "台中市北區建國路456號",
            "identity_type": "學生",
            "phone": "0923456789",
            "email": "s2345678@dragon.nchu.edu.tw"
        },
        {
            "department": "企業管理學系",
            "student_id": "s3456789", 
            "name": "張美麗",
            "grade": "碩一",
            "required_surveys": 6,
            "completed_surveys": 3,
            "surveys_completed": False,
            "is_foreign": False,
            "valid_surveys": False,
            "id_number": "C345678901",
            "address": "台中市南區民權路789號",
            "identity_type": "研究生",
            "phone": "0934567890",
            "email": "s3456789@gmail.com"
        }
    ]
    
    df_sample = pd.DataFrame(sample_data)
    
    # 創建帶有說明的 Excel 文件
    with pd.ExcelWriter("test_data/sample_upload.xlsx", engine='openpyxl') as writer:
        # 資料工作表
        df_sample.to_excel(writer, sheet_name='參與者資料', index=False)
        
        # 說明工作表
        instructions = pd.DataFrame({
            "欄位名稱": [
                "department", "student_id", "name", "grade", "required_surveys",
                "completed_surveys", "surveys_completed", "is_foreign", "valid_surveys",
                "id_number", "address", "identity_type", "phone", "email"
            ],
            "說明": [
                "系所名稱", "學號", "姓名", "年級", "需要完成的問卷數",
                "已完成的問卷數", "是否完成所有問卷", "是否為外籍學生", "問卷是否有效",
                "身分證字號", "地址", "身分類型", "電話號碼", "電子郵件"
            ],
            "範例": [
                "資訊工程學系", "s1234567", "王小明", "大三", "5",
                "5", "True", "False", "True",
                "A123456789", "台中市西區中山路123號", "學生", "0912345678", "student@mail.nchu.edu.tw"
            ],
            "必填": [
                "是", "是", "是", "否", "否",
                "否", "否", "否", "否",
                "否", "否", "否", "否", "否"
            ]
        })
        instructions.to_excel(writer, sheet_name='欄位說明', index=False)
    
    print("✅ 已生成：test_data/sample_upload.xlsx（包含範例和說明）")

if __name__ == "__main__":
    print("🎯 生成抽獎系統測試資料")
    print("="*50)
    
    try:
        # 創建各種測試文件
        create_excel_files()
        
        # 創建範例上傳文件
        create_sample_upload_file()
        
        print(f"\n🎉 所有測試文件已生成完成！")
        print(f"\n📁 文件位置：")
        print(f"   - test_data/basic_participants.xlsx      (基本測試，50人)")
        print(f"   - test_data/large_participants.xlsx      (大量測試，200人)")
        print(f"   - test_data/essential_participants.xlsx  (必要欄位)")
        print(f"   - test_data/eligible_participants.xlsx   (符合抽獎資格)")
        print(f"   - test_data/participants.csv             (CSV格式)")
        print(f"   - test_data/sample_upload.xlsx           (範例和說明)")
        
        print(f"\n🚀 測試建議：")
        print(f"   1. 先用 sample_upload.xlsx 測試基本上傳功能")
        print(f"   2. 用 basic_participants.xlsx 測試一般情況")
        print(f"   3. 用 large_participants.xlsx 測試大量資料")
        print(f"   4. 用 participants.csv 測試 CSV 上傳")
        print(f"   5. 用 eligible_participants.xlsx 測試抽獎功能")
        
    except Exception as e:
        print(f"❌ 生成測試資料時發生錯誤：{e}")
        print("請確保已安裝必要的套件：pip install pandas openpyxl") 