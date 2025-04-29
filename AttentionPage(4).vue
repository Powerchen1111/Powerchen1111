<template>
    <div>
        <!-- 表格 -->
        <el-table
            :data="pagedData"
            stripe  style="width: 100%"
            row-key="id"
            border
            :tree-props="{ children: 'children' }"
            :height="tableHeight"
            :row-class-name="tableRowClassName"
            :virtual-scroll="true"
        >
            <el-table-column prop="id" label="id"></el-table-column>
            <el-table-column prop="text" label="订单描述" min-width="250"></el-table-column>s
            <el-table-column prop="start_date" label="开始时间"></el-table-column>
            <el-table-column prop="duration_m" label="持续时间"></el-table-column>
            <el-table-column label="理想结束时间" prop="end_date"></el-table-column>
            <!-- 实际汇报时间列 -->
            <el-table-column label="实际汇报时间" prop="actualCompletionTime">
                <template #default="{ row }">
                    <span>{{ isValidDate(row.actualCompletionTime) ? row.actualCompletionTime : '暂无' }}</span>
                </template>
            </el-table-column>

            <el-table-column label="状态" prop="progress"></el-table-column>
            <el-table-column label="延期时间">
                <template #default="{ row }">
                    <span v-if="row.delay > 0" style="color: red;">延期 {{ row.delay }} 天</span>
                    <span v-else-if="row.delay < 0" style="color: green;">提前 {{ Math.abs(row.delay) }} 天</span>
                    <span v-else>无延期</span>
                </template>
            </el-table-column>
        </el-table>

        <!-- 分页 -->
        <el-pagination
            v-if="totalRecords > pageSize"
            :current-page="currentPage"
            :page-size="pageSize"
            :total="totalRecords"
            @current-change="handlePageChange"
            layout="prev, pager, next, sizes, total"
        />
    </div>
</template>

<script>
export default {
    methods: {
        isValidDate(date) {
            const parsedDate = Date.parse(date);
            return !isNaN(parsedDate); // 如果是有效日期，返回 true
        }
    }
}
</script>

<script setup>
import { reactive, onMounted, ref } from 'vue';
import axios from 'axios';
import dayjs from 'dayjs';
import 'element-plus/dist/index.css';
import { ElTable, ElTableColumn, ElPagination } from 'element-plus';

// 定义常量
const tableData = reactive([]); // 全量数据
const pagedData = ref([]); // 当前页数据
const currentPage = ref(1); // 当前页
const pageSize = ref(10); // 每页显示数量
const totalRecords = ref(0); // 数据总条数
const tableHeight = ref(700); // 表格高度，用于虚拟滚动



// 获取数据并处理
const fetchTableData = async () => {
    try {
        const response = await axios.post('http://192.168.159.177:9090/make/plan/lookAnyDayPlan');

        const responseData = response.data;

        if (responseData && responseData.tasks && Array.isArray(responseData.tasks)) {
            // 处理任务数据：去重和清理
            const uniqueTasks = removeDuplicates(responseData.tasks);

            // 将去重后的数据传递给 processTasks 函数
            const processedData = processTasks(uniqueTasks);

            // 更新表格数据
            tableData.length = 0;
            tableData.push(...processedData); // 将处理后的数据赋值给全量数据

            // 更新总记录数
            totalRecords.value = tableData.length;

            // 更新当前页数据
            handlePageChange(currentPage.value);
        } else {
            console.error('返回的数据格式不正确');
        }
    } catch (error) {
        console.error('请求失败:', error);
    }
};

// 去重函数：根据任务的 id 字段去重
const removeDuplicates = (tasks) => {
    const uniqueTasksMap = new Map();

    tasks.forEach(task => {
        if (task.id && !uniqueTasksMap.has(task.id)) {
            uniqueTasksMap.set(task.id, task);
        }
    });

    return Array.from(uniqueTasksMap.values());
};

// 计算延期时间（根据实际汇报时间计算延期）
const calculateDelay = (endDate, actualCompletionTime) => {
    const expectedEnd = dayjs(endDate, 'DD-MM-YYYY HH-mm');
    const actualEnd = actualCompletionTime ? dayjs(actualCompletionTime, 'DD-MM-YYYY HH-mm', true) : null;

    if (!actualEnd) return 0; // 无实际结束时间，默认无延期

    return actualEnd.isAfter(expectedEnd)
        ? actualEnd.diff(expectedEnd, 'day')
        : -expectedEnd.diff(actualEnd, 'day');
};

// 处理任务数据并构建树形结构
// 处理任务数据并构建树形结构
const processTasks = (tasks) => {
    if (!Array.isArray(tasks)) {
        console.error('buildTreeData函数的参数不是一个数组:', tasks);
        return [];
    }

    const taskMap = new Map();
    const result = [];

    tasks.forEach(task => {


        const start = dayjs(task.start_date, 'DD-MM-YYYY HH-mm');
        const duration = task.duration_m;
        const actualCompletionTime = task.actualCompletionTime

        const end = start.clone().add(duration, 'minute').format('YYYY-MM-DD HH:mm');

        const processedTask = {
            ...task,
            start_date: start.format('YYYY-MM-DD HH:mm'),
            end_date: end,
            duration_m: duration,
            progress: task.progress=== 1? '已完成' : '未完成',
            children: [],
            actualCompletionTime: actualCompletionTime ? (dayjs(actualCompletionTime, 'DD-MM-YYYY HH-mm').isValid() ? dayjs(actualCompletionTime, 'DD-MM-YYYY HH-mm').format('YYYY-MM-DD HH:mm') : '暂无') : '暂无',
            delay: calculateDelay(start.format('DD-MM-YYYY HH-mm'), actualCompletionTime) // 使用实际报告时间计算延期
        };

        taskMap.set(task.id, processedTask);

        const parentId = task.parent || task['$rendered_parent'];
        if (parentId) {
            const parentTask = taskMap.get(parentId);
            if (parentTask) {
                parentTask.children.push(processedTask);
            }
        } else {
            result.push(processedTask);
        }
    });

    // 递归函数，计算父节点的开始时间、结束时间、持续时间和延期时间
    const calculateParentTimes = (task) => {
        if (task.children.length === 0) return;

        let totalDuration = 0;
        let earliestStartDate = null;
        let latestEndDate = null;
        let latestActualCompletionTime=null;
        let totalDelay = 0;


        task.children.forEach(childTask => {
            calculateParentTimes(childTask);

            // 更新父节点的时间数据
            totalDuration += childTask.duration_m;
            const childStart = dayjs(childTask.start_date, 'YYYY-MM-DD HH:mm');
            const childEnd = dayjs(childTask.end_date, 'YYYY-MM-DD HH:mm');
            const childactualCompletionTime=dayjs(childTask.actualCompletionTime, 'YYYY-MM-DD HH:mm');

            if (!earliestStartDate || childStart.isBefore(earliestStartDate)) {
                earliestStartDate = childStart;
            }
            if (!latestEndDate || childEnd.isAfter(latestEndDate)) {
                latestEndDate = childEnd;
            }
            if (!latestActualCompletionTime||childactualCompletionTime.isAfter(latestActualCompletionTime)){
                latestActualCompletionTime=childactualCompletionTime;
            }

            totalDelay += childTask.delay;


        });

        task.start_date = earliestStartDate ? earliestStartDate.format('YYYY-MM-DD HH:mm') : null;
        task.end_date = latestEndDate ? latestEndDate.format('YYYY-MM-DD HH:mm') : null;
        task.duration_m = totalDuration;
        task.delay = totalDelay;
        task.actualCompletionTime = latestActualCompletionTime ? latestActualCompletionTime.format('YYYY-MM-DD HH:mm') : '暂无';


        console.log('处理任务:', task.id, {
            start_date: task.start_date,
            end_date: task.end_date,
            ac:task.actualCompletionTime,
            progress: task.progress
        });
    };


    result.forEach(rootTask => {
        calculateParentTimes(rootTask);
    });

    return result;
};


// 处理分页
const handlePageChange = (page) => {
    const start = (page - 1) * pageSize.value;
    const end = start + pageSize.value;
    pagedData.value = tableData.slice(start, end);
};

// 在组件挂载后获取数据
onMounted(() => {
    fetchTableData();
});

// 表格行颜色处理
const tableRowClassName = ({ row }) => {
    if (row.delay < 0) {
        return 'early-row'; // 提前，绿色
    } else if (row.delay > 7) {
        return 'late-row'; // 延期超过七天，红色
    } else if (row.delay > 3) {
        return 'warning-row'; // 延期超过三天，黄色
    }
    return '';
};
</script>

<style lang="scss">
/* 样式 */
.el-table .el-table__body tr:nth-child(odd) td {
    background-color: #ffffff !important; /* 奇数行颜色 */
}

.el-table .el-table__body tr:nth-child(even) td {
    background-color: #e9e9e9 !important; /* 偶数行颜色 */
}

/* 自定义行背景颜色 */
.el-table .early-row td {
    background-color: #d4f9d6 !important;
}
.el-table .late-row td {
    background-color: #f73747 !important;
}
.el-table .warning-row td {
    background-color: #d4b962 !important;
}

/* 平滑过渡效果 */
.el-table td {
    transition: background-color 0.3s ease;
}
.el-table__row {
    border-bottom: 2px solid #ddd !important; /* 更显眼的行分隔线 */
}
</style>
