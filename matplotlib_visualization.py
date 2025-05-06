import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import rcParams

import plotly.express as px

# 设置中文字体
rcParams['font.sans-serif'] = ['SimHei']  # Windows系统常用字体
rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 准备数据
df = pd.read_csv('standardized_results.csv')

# 数据完整性检查
print("原始数据前几行:")
print(df.head())
print("\n原始数据信息:")
print(df.info())

# 更严格的数据清洗
# 修改数据清洗逻辑，确保层级关系完整
df = df.dropna(subset=['省', '市', '区县'], how='all')  # 保留至少有一个层级有值的记录

# 修改数据清洗逻辑，确保数据类型正确
# 将浮点数格式的代码转换为字符串格式，并去除后缀的 .0
df['省'] = df['省'].astype(str).str.split('.').str[0]
df['市'] = df['市'].astype(str).str.split('.').str[0]
df['区县'] = df['区县'].astype(str).str.split('.').str[0]

# 填充特定空值逻辑
mask = (df['区县'] != '未知区县') & (df['省'] == '未知省份')
df.loc[mask, '省'] = df.loc[mask, '区县'].str[:2] + '0000'

mask = (df['区县'] != '未知区县') & (df['市'] == '未知城市')
df.loc[mask, '市'] = df.loc[mask, '区县'].str[:4] + '00'

# 填充剩余空值
df = df.fillna({'省': '未知省份', '市': '未知城市', '区县': '未知区县'})  # 填充剩余空值

# 确保三级数据完整
if df[['省', '市', '区县']].isnull().any().any():
    raise ValueError("数据清洗后仍存在空值，请检查数据质量")

if df.empty:
    raise ValueError("过滤空值后数据为空，请检查数据质量")

# 确保数据不为空
if len(df) == 0:
    print("警告：数据为空，请检查数据源")
    exit()

# 数据完整性检查
print("\n清洗后的数据前几行:")
print(df.head())
print("\n清洗后的数据信息:")
print(df.info())

# 在数据预处理部分添加行政区划代码转换
province_map = {
    '110000': '北京市',
    '120000': '天津市',
    '130000': '河北省'
}

city_map = {
    '110000': '北京市',
    '110101': '东城区',
    '110102': '西城区',
    '110105': '朝阳区',
    '110106': '丰台区',
    '110107': '石景山区',
    '110108': '海淀区',
    '110109': '门头沟区',
    '110111': '房山区',
    '110112': '通州区',
    '110113': '顺义区',
    '110114': '昌平区',
    '110115': '大兴区',
    '110116': '怀柔区',
    '110117': '平谷区',
    '110118': '密云区',
    '110119': '延庆区',
    '120000': '天津市',
    '120101': '和平区',
    '120102': '河东区',
    '120103': '河西区',
    '120104': '南开区',
    '120105': '河北区',
    '120106': '红桥区',
    '120110': '东丽区',
    '120111': '西青区',
    '120112': '津南区',
    '120113': '北辰区',
    '120114': '武清区',
    '120115': '宝坻区',
    '120116': '滨海新区',
    '120117': '宁河区',
    '120118': '静海区',
    '120119': '蓟州区',
    '130000': '河北省',
    '130100': '石家庄市',
    '130200': '唐山市',
    '130300': '秦皇岛市',
    '130400': '邯郸市',
    '130500': '邢台市',
    '130600': '保定市',
    '130700': '张家口市',
    '130800': '承德市',
    '130900': '沧州市',
    '131000': '廊坊市',
    '131100': '衡水市'
}

# 转换行政区划代码为中文名称
df['省'] = df['省'].map(province_map).fillna(df['省'])  # 保留原始代码，未匹配则不转换
df['市'] = df['市'].map(city_map).fillna(df['市'])  # 保留原始代码，未匹配则不转换
df['区县'] = df['区县'].astype(str)

# 在转换行政区划代码后，添加数据完整性检查
# 确保如果区县有值，则省市必须有值
mask = (df['区县'] != '未知区县') & ((df['省'] == '未知省份') | (df['市'] == '未知城市'))
print("\n===== 数据完整性检查 =====")
print(f"总记录数: {len(df)}")
print(f"不完整记录数: {len(df[mask])}")

# 创建多级条形图
if not df.empty and len(df['省'].unique()) > 0:
    plt.figure(figsize=(15, 8))
    ax = sns.countplot(data=df, x='省', hue='市', dodge=True)
    plt.title('京津冀科技成果分布')
    plt.xticks(rotation=45)

    # 仅在有数据时添加图例
    if len(df['市'].unique()) > 0:
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()
    try:
        plt.show()  # 显示matplotlib图表
    except AttributeError:
        plt.savefig('output.png')
        print("Matplotlib图表已保存为output.png")
else:
    print("警告：数据为空，无法生成Matplotlib图表")

# 仅在有数据时创建分面网格
if not df.empty and len(df['省'].unique()) > 0:
    g = sns.FacetGrid(df, col='省', col_wrap=min(3, len(df['省'].unique())), height=4)
    g.map_dataframe(sns.countplot, x='市')
    g.set_titles("{col_name}")
    plt.tight_layout()
    try:
        plt.show()
    except AttributeError:
        plt.savefig('facet_output.png')
        print("分面网格图表已保存为facet_output.png")
else:
    print("警告：数据为空，无法生成分面网格图表")

# 修改plotly旭日图
if not df.empty:
    fig = px.sunburst(
        df,
        path=['省', '市', '区县'],
        title='京津冀科技成果三级分布(包含不完整数据)',
        width=1200,
        height=800
    )

    # 修改图表显示方式
    try:
        fig.show()  # 显示plotly图表
    except:
        fig.write_html("sunburst_chart.html")
        print("交互式图表已保存为sunburst_chart.html")
else:
    print("警告：数据为空，无法生成Plotly旭日图")

import os
print(os.path.exists('standardized_results.csv'))

# 在转换后添加以下代码检查
print("\n===== 行政区划转换检查 =====")
print("省级代码转换样例:", df[['省']].head())
print("市级代码转换样例:", df[['市']].head())

# 在读取数据后添加检查
# 在转换前添加原始数据检查
print("\n===== 原始行政区划代码检查 =====")
print("省级原始代码:", df['省'].head().unique())
print("市级原始代码:", df['市'].head().unique())
print("市级代码样例:", df['市'].head().unique())

# 在转换后添加详细检查
print("\n===== 详细转换检查 =====")
print("省级映射表:", province_map)
print("市级映射表样本:", dict(list(city_map.items())[:5]))
print("实际省级值:", df['省'].unique())
print("实际市级值:", df['市'].unique())

# 检查映射后的省和市的唯一值
print("\n===== 映射后唯一值检查 =====")
print("映射后的省级唯一值:", df['省'].unique())
print("映射后的市级唯一值:", df['市'].unique())