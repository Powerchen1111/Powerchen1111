import pandas as pd
from sqlalchemy import create_engine, text

# 1. 读取四个Excel文件
df_tj = pd.read_excel('tianjin.xlsx')
df_hb = pd.read_excel('hebei.xlsx')
df_jjj = pd.read_excel('jjj.xlsx')
df_bj = pd.read_excel('beijing.xlsx')

# 2. 统一列名（合并同义列）
# 天津数据列名标准化
df_tj = df_tj.rename(columns={
    '序号': 'id_tj',
    '单位': 'organization',
    '成果名称': 'project_name',
    '技术水平': 'tech_level',
    '负责人': 'principal',
    '所属技术领域': 'tech_field',
    '合作单位': 'coop_org',
    '项目总规模或评估价值（万元）': 'project_value',
    '目前所处阶段': 'project_stage',
    '知识产权情况': 'ip_status',
    '项目简介': 'project_desc'
})

# 河北数据列名标准化
df_hb = df_hb.rename(columns={
    '序号': 'id_hb',
    '成果名称': 'project_name',
    '单位名称': 'organization',
    '主要人员': 'principal',
    '成果简介': 'project_desc',
    '年度': 'year',
    '批准登记号': 'reg_num',
    '课题来源': 'project_source',
    '评价单位名称': 'eval_org'
})

# 京津冀数据列名标准化
df_jjj = df_jjj.rename(columns={
    'ID': 'id_jjj',
    '成果名称': 'project_name',
    '完成单位': 'organization',
    '完成人': 'principal',
    '成果简介': 'project_desc',
    '省市': 'province',
    '成果分布年份': 'year',
    '登记号': 'reg_num',
    '鉴定部门': 'eval_org',
    '应用行业名称': 'application_field'
})

# 北京数据列名标准化
df_bj = df_bj.rename(columns={
    '编号': 'id_bj',
    '项目名称': 'project_name',
    '承担单位': 'organization',
    '负责人': 'principal',
    '项目简介': 'project_desc',
    '年度': 'year',
    '项目类别': 'project_type',
    '资助金额(万元)': 'funding_amount'
})

# 3. 合并四个DataFrame（保留所有列）
merged_df = pd.concat([df_tj, df_hb, df_jjj, df_bj], ignore_index=True, sort=False)

# 4. 处理缺失值
merged_df = merged_df.where(pd.notnull(merged_df), None)

# 5. 连接到MySQL数据库
engine = create_engine('mysql+mysqlconnector://root:wcy1111@localhost/techresult')

# 6. 彻底删除表（如果存在）
with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS tech_results"))
    # 确保表被完全删除
    conn.execute(text("COMMIT"))

# 7. 将合并后的数据写入MySQL
merged_df.to_sql('tech_results', con=engine, if_exists='append', index=False)

print("数据合并和同步完成！")