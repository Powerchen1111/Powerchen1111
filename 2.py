import re
import requests
import pandas as pd

# 从CSV文件加载行政区划数据
districts_df = pd.read_csv('data.csv', encoding='utf-8')

# 创建映射表
# 修改映射表创建方式，确保值为字符串
location_map = dict(zip(districts_df['name'], districts_df['code'].astype(str)))

# 修改预处理映射表创建方式
province_map = {k:v for k,v in location_map.items() if str(v).endswith('0000')}  # 省级代码以0000结尾
city_map = {k:v for k,v in location_map.items() if str(v).endswith('00') and not str(v).endswith('0000')}  # 市级代码以00结尾但不以0000结尾
district_map = {k:v for k,v in location_map.items() if not str(v).endswith('00')}  # 区县级代码不以00结尾
beijing_districts = {k:v for k,v in location_map.items() if k.startswith('北京市') and k.endswith('区')}

# 验证映射字典
print("\n===== 映射字典验证 =====")
print(f"映射字典大小: {len(location_map)}")
print("映射字典样例:")
for name, code in list(location_map.items())[:5]:
    print(f"{code}: {name}")

# Move these preprocessing mappings to the top after location_map is created
province_map = {k:v for k,v in location_map.items() if v.endswith('省')}
city_map = {k:v for k,v in location_map.items() if v.endswith('市')}
district_map = {k:v for k,v in location_map.items() if v.endswith(('区','县'))}
beijing_districts = {k:v for k,v in location_map.items() if v.startswith('北京市') and v.endswith('区')}
# 定义匹配函数
def extract_location(unit_name, address, province=None, unit=None, organization=None, coop_org=None):
    # 构造搜索文本（使用所有字段）
    search_fields = [
        str(field).strip() for field in 
        [unit_name, address, province, unit, organization, coop_org]
        if pd.notna(field)
    ]
    search_text = " ".join(search_fields).lower()
    org_search_text = search_text  # 添加这行定义

    if not search_text or not location_map:
        print(f"匹配失败（无数据）: {search_text[:50]}...")
        return None, None

    # 新增模糊匹配逻辑
    def fuzzy_match(name, text):
        clean_name = re.sub(r'(省|市|区|县)$', '', name)
        from difflib import SequenceMatcher
        return SequenceMatcher(None, clean_name, text).ratio() > 0.6
    
    # 优化后的匹配逻辑
    # 1. 优先匹配北京区县
    if '北京市' in ' '.join(search_fields):
        for name, code in beijing_districts.items():
            district_part = name[3:]
            if district_part in search_text:
                return code, name
    
    # 2. 匹配区县
    for name, code in district_map.items():
        if name in search_text:
            return code, name
    
    # 3. 匹配市级
    for name, code in city_map.items():
        if name in search_text or name[:-1] in search_text:
            return code, name
    
    # 4. 匹配省级
    for name, code in province_map.items():
        if name in search_text or name[:-1] in search_text:
            return code, name

    # 修改后的匹配优先级：区县 > 市 > 省
    # 1. 优先匹配区县级
    for name, code in location_map.items():
        if name.endswith(('区','县')):
            # 处理北京市的特殊情况
            if name.startswith('北京市'):
                district_part = name[3:]  # 去掉"北京市"前缀
                if district_part in search_text:
                    print(f"匹配成功（北京区县）: {search_text[:50]}... -> {code} {name}")
                    return code, name
            # 处理普通区县
            elif name in search_text:
                print(f"匹配成功（区县）: {search_text[:50]}... -> {code} {name}")
                return code, name

    # 2. 匹配市级（包含直辖市）
    for name, code in location_map.items():
        if name.endswith('市'):
            city_short = name[:-1]  # 去掉"市"字
            if (name in search_text or 
                city_short in search_text or
                any(re.search(rf'\b{part}\b', search_text) for part in name.split())):
                print(f"匹配成功（市级）: {search_text[:50]}... -> {code} {name}")
                return code, name

    # 3. 最后匹配省级
    for name, code in location_map.items():
        if name.endswith('省'):
            short_name = name[:-1]
            if (re.search(rf'(^|\s){name}($|\s)', ' '.join(search_fields)) or
                re.search(rf'(^|\s){short_name}($|\s)', ' '.join(search_fields))):
                print(f"匹配成功（省级）: {search_text[:50]}... -> {code} {name}")
                return code, name
            clean_name = name.replace('省','').lower()
            match_condition = (
                    name.lower() in search_text or
                    clean_name in search_text or
                    any(part.lower() in search_text for part in name.split())
            )
            if match_condition:
                print(f"匹配成功（省级）: {search_text[:50]}... -> {code} {name} (匹配条件: {match_condition})")
                return code, name

    if not org_search_text or not location_map:
        print(f"匹配失败（无数据）: {org_search_text[:50]}...")
        return None, None

    # 如果精确匹配失败，尝试模糊匹配
    best_match = None
    best_score = 0
    for name, code in location_map.items():
        score = fuzzy_match(name, search_text)
        if score > best_score:
            best_score = score
            best_match = (code, name)
    
    if best_match and best_score > 0.6:
        print(f"模糊匹配成功: {search_text[:50]}... -> {best_match[0]} {best_match[1]} (相似度: {best_score:.2f})")
        return best_match

    print(f"匹配失败: {search_text[:50]}...")
    return None, None

# 测试匹配结果
print("\n===== 测试匹配结果 =====")
test_cases = [
    ("北京市海淀区某单位", "北京市海淀区中关村", "北京市", "某单位"),  # 区县级
    ("上海浦东新区开发公司", "", "上海市", ""),  # 区县级（含新区）
    ("广东省广州市天河区科技公司", "", "", ""),  # 区县级
    ("湖北省武汉市", "", "", ""),  # 市级
    ("四川省", "", "", ""),  # 省级
    ("未知地址的单位", "无明确地区信息", "", "")  # 匹配失败
]

for case in test_cases:
    code, loc = extract_location(*case)
    print(f"输入: {case} -> 匹配结果: {code}, {loc}")

# 读取合并后的数据框
merged_df = pd.read_excel('tech_results.xlsx')

# 增加调试信息
print("\n===== 实际数据匹配 =====")
# 应用地域信息提取
merged_df['district_code'], merged_df['location'] = zip(
    *merged_df.apply(lambda row: extract_location(
        row.get('单位名称', ''),
        row.get('联系单位地址', ''),
        row.get('省市', ''),
        row.get('单位', ''),
        row.get('organization', ''),
        row.get('coop_org', '')
    ), axis=1)
)

# 验证输出数据
print("\n===== 输出数据验证 =====")
print(f"总记录数: {len(merged_df)}")
print(f"成功匹配记录数: {merged_df['district_code'].notna().sum()}")
print(f"匹配率: {merged_df['district_code'].notna().mean()*100:.2f}%")

# 在保存结果前添加行政区划字段
# 在保存结果前添加行政区划字段
def get_admin_code(code, level):
    if pd.isna(code):
        return None
    code_str = str(int(float(code)))  # 处理浮点数格式的代码
    if level == 'province':
        return code_str[:2] + '0000'
    elif level == 'city':
        return code_str[:4] + '00'
    elif level == 'district':
        return code_str
    return None

# 修改后的行政区划字段生成逻辑
# 替换apply操作
merged_df['省'] = merged_df['district_code'].str[:2] + '0000'
merged_df['市'] = merged_df['district_code'].str[:4] + '00'
merged_df['区县'] = merged_df['district_code']

# 保存结果
merged_df.to_csv('standardized_results.csv', index=False)



