// 全局变量
let currentPage = 'home';
let currentReportId = null;

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 导航链接事件监听
    document.getElementById('history-link').addEventListener('click', function(e) {
        e.preventDefault();
        showPage('history');
        loadHistoryData();
    });

    document.getElementById('about-link').addEventListener('click', function(e) {
        e.preventDefault();
        showPage('about');
    });

    // 表单提交事件监听
    document.getElementById('report-form').addEventListener('submit', function(e) {
        e.preventDefault();
        analyzeReport();
    });

    // 初始化页面
    showPage('home');
});

// 显示指定页面
function showPage(pageName) {
    // 隐藏所有页面
    document.getElementById('home-page').classList.add('d-none');
    document.getElementById('history-page').classList.add('d-none');
    document.getElementById('about-page').classList.add('d-none');
    
    // 显示指定页面
    document.getElementById(pageName + '-page').classList.remove('d-none');
    
    // 更新当前页面
    currentPage = pageName;
    
    // 更新导航栏活动项
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.classList.remove('active');
    });
    
    if (pageName === 'home') {
        document.querySelector('.nav-link[href="/"]').classList.add('active');
    } else {
        document.querySelector(`#${pageName}-link`).classList.add('active');
    }
}

// 分析报告
function analyzeReport() {
    // 显示加载状态
    document.getElementById('loading').classList.remove('d-none');
    document.getElementById('empty-result').classList.add('d-none');
    document.getElementById('result-container').classList.add('d-none');
    
    // 获取表单数据
    const formData = {
        age: document.getElementById('age').value,
        gender: document.getElementById('gender').value,
        examination_type: document.getElementById('examination_type').value,
        findings: document.getElementById('findings').value,
        impression: document.getElementById('impression').value
    };
    
    // 发送API请求
    fetch('/api/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('网络响应异常');
        }
        return response.json();
    })
    .then(data => {
        // 隐藏加载状态
        document.getElementById('loading').classList.add('d-none');
        document.getElementById('result-container').classList.remove('d-none');
        
        // 保存当前报告ID
        currentReportId = data.report_id;
        
        // 显示分析结果
        displayResults(data);
    })
    .catch(error => {
        // 隐藏加载状态
        document.getElementById('loading').classList.add('d-none');
        document.getElementById('empty-result').classList.remove('d-none');
        
        // 显示错误信息
        alert('分析报告时出错: ' + error.message);
    });
}

// 显示分析结果
function displayResults(data) {
    // 显示影像所见分析结果
    displayEntities(data.findings.entities, 'findings-entities-table');
    displayRelationships(data.findings.entities, data.findings.relationships, 'findings-relationships-table');
    
    // 显示诊断意见分析结果
    displayEntities(data.impression.entities, 'impression-entities-table');
    displayRelationships(data.impression.entities, data.impression.relationships, 'impression-relationships-table');
    
    // 显示关系可视化
    setTimeout(() => {
        renderGraph(data.findings.entities, data.findings.relationships, 'visualization');
    }, 100);
}

// 显示实体表格
function displayEntities(entities, tableId) {
    const tableBody = document.querySelector(`#${tableId} tbody`);
    tableBody.innerHTML = '';
    
    if (entities && entities.length > 0) {
        entities.forEach(entity => {
            const row = document.createElement('tr');
            
            // 创建单元格
            const textCell = document.createElement('td');
            textCell.textContent = entity.text;
            
            const typeCell = document.createElement('td');
            typeCell.textContent = entity.entity_type;
            
            const codeCell = document.createElement('td');
            codeCell.textContent = entity.snomed_code || '-';
            
            const termCell = document.createElement('td');
            termCell.textContent = entity.snomed_term || '-';
            
            // 添加单元格到行
            row.appendChild(textCell);
            row.appendChild(typeCell);
            row.appendChild(codeCell);
            row.appendChild(termCell);
            
            // 添加行到表格
            tableBody.appendChild(row);
        });
    } else {
        // 如果没有实体，显示空行
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 4;
        cell.textContent = '未识别到实体';
        cell.className = 'text-center';
        row.appendChild(cell);
        tableBody.appendChild(row);
    }
}

// 显示关系表格
function displayRelationships(entities, relationships, tableId) {
    const tableBody = document.querySelector(`#${tableId} tbody`);
    tableBody.innerHTML = '';
    
    if (relationships && relationships.length > 0) {
        // 创建实体ID到实体的映射
        const entityMap = {};
        entities.forEach(entity => {
            entityMap[entity.id] = entity;
        });
        
        relationships.forEach(rel => {
            const row = document.createElement('tr');
            
            // 获取源实体和目标实体
            const sourceEntity = entityMap[rel.source_id];
            const targetEntity = entityMap[rel.target_id];
            
            // 创建单元格
            const sourceCell = document.createElement('td');
            sourceCell.textContent = sourceEntity ? sourceEntity.text : '-';
            
            const relationCell = document.createElement('td');
            relationCell.textContent = rel.relation_type;
            
            const targetCell = document.createElement('td');
            targetCell.textContent = targetEntity ? targetEntity.text : '-';
            
            const codeCell = document.createElement('td');
            codeCell.textContent = rel.snomed_relation_code || '-';
            
            // 添加单元格到行
            row.appendChild(sourceCell);
            row.appendChild(relationCell);
            row.appendChild(targetCell);
            row.appendChild(codeCell);
            
            // 添加行到表格
            tableBody.appendChild(row);
        });
    } else {
        // 如果没有关系，显示空行
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 4;
        cell.textContent = '未识别到关系';
        cell.className = 'text-center';
        row.appendChild(cell);
        tableBody.appendChild(row);
    }
}

// 渲染关系图
function renderGraph(entities, relationships, containerId) {
    // 获取容器
    const container = document.getElementById('graph-container');
    container.innerHTML = '';
    
    // 如果没有实体或关系，显示提示信息
    if (!entities || entities.length === 0 || !relationships || relationships.length === 0) {
        container.innerHTML = '<div class="text-center p-5"><p class="text-muted">没有足够的数据来生成关系图</p></div>';
        return;
    }
    
    // 设置图表尺寸
    const width = container.clientWidth;
    const height = 400;
    
    // 创建SVG元素
    const svg = d3.select(container)
        .append('svg')
        .attr('width', width)
        .attr('height', height);
    
    // 创建实体ID到实体的映射
    const entityMap = {};
    entities.forEach(entity => {
        entityMap[entity.id] = entity;
    });
    
    // 准备节点数据
    const nodes = entities.map(entity => ({
        id: entity.id,
        name: entity.text,
        type: entity.entity_type,
        code: entity.snomed_code
    }));
    
    // 准备连接数据
    const links = relationships.map(rel => ({
        source: rel.source_id,
        target: rel.target_id,
        type: rel.relation_type
    }));
    
    // 创建力导向图
    const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2));
    
    // 绘制连接线
    const link = svg.append('g')
        .selectAll('line')
        .data(links)
        .enter()
        .append('line')
        .attr('class', 'link');
    
    // 绘制连接标签
    const linkLabel = svg.append('g')
        .selectAll('text')
        .data(links)
        .enter()
        .append('text')
        .attr('class', 'link-label')
        .text(d => d.type);
    
    // 绘制节点
    const node = svg.append('g')
        .selectAll('.node')
        .data(nodes)
        .enter()
        .append('g')
        .attr('class', 'node')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    // 添加节点圆圈
    node.append('circle')
        .attr('r', 8)
        .style('fill', d => getColorByType(d.type));
    
    // 添加节点标签
    node.append('text')
        .attr('dy', -12)
        .style('text-anchor', 'middle')
        .text(d => d.name);
    
    // 更新力导向图
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        linkLabel
            .attr('x', d => (d.source.x + d.target.x) / 2)
            .attr('y', d => (d.source.y + d.target.y) / 2);
        
        node
            .attr('transform', d => `translate(${d.x},${d.y})`);
    });
    
    // 拖拽开始
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    // 拖拽中
    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    // 拖拽结束
    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
    
    // 根据实体类型获取颜色
    function getColorByType(type) {
        const colorMap = {
            '解剖部位': '#3f51b5',
            '病理发现': '#f44336',
            '疾病': '#4caf50',
            '严重程度': '#ff9800',
            '影像学表现': '#9c27b0'
        };
        
        return colorMap[type] || '#999';
    }
}

// 加载历史记录数据
function loadHistoryData() {
    // 显示加载状态
    document.getElementById('history-loading').classList.remove('d-none');
    document.getElementById('history-empty').classList.add('d-none');
    
    // 发送API请求
    fetch('/api/reports')
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应异常');
            }
            return response.json();
        })
        .then(data => {
            // 隐藏加载状态
            document.getElementById('history-loading').classList.add('d-none');
            
            // 显示历史记录
            displayHistoryData(data);
        })
        .catch(error => {
            // 隐藏加载状态
            document.getElementById('history-loading').classList.add('d-none');
            document.getElementById('history-empty').classList.remove('d-none');
            
            // 显示错误信息
            console.error('加载历史记录时出错:', error);
        });
}

// 显示历史记录数据
function displayHistoryData(reports) {
    const tableBody = document.querySelector('#history-table tbody');
    tableBody.innerHTML = '';
    
    if (reports && reports.length > 0) {
        reports.forEach(report => {
            const row = document.createElement('tr');
            
            // 创建单元格
            const idCell = document.createElement('td');
            idCell.textContent = report.id;
            
            const patientCell = document.createElement('td');
            if (report.patient) {
                patientCell.textContent = `${report.patient.age}岁 ${report.patient.gender}`;
            } else {
                patientCell.textContent = '未知';
            }
            
            const examinationCell = document.createElement('td');
            examinationCell.textContent = report.examination_type;
            
            const timeCell = document.createElement('td');
            if (report.created_at) {
                const date = new Date(report.created_at);
                timeCell.textContent = date.toLocaleString('zh-CN');
            } else {
                timeCell.textContent = '未知';
            }
            
            const actionCell = document.createElement('td');
            const viewButton = document.createElement('button');
            viewButton.className = 'btn btn-sm btn-view';
            viewButton.innerHTML = '<i class="bi bi-eye me-1"></i>查看';
            viewButton.addEventListener('click', () => {
                viewReportDetail(report.id);
            });
            actionCell.appendChild(viewButton);
            
            // 添加单元格到行
            row.appendChild(idCell);
            row.appendChild(patientCell);
            row.appendChild(examinationCell);
            row.appendChild(timeCell);
            row.appendChild(actionCell);
            
            // 添加行到表格
            tableBody.appendChild(row);
        });
    } else {
        // 如果没有历史记录，显示空行
        document.getElementById('history-empty').classList.remove('d-none');
    }
}

// 查看报告详情
function viewReportDetail(reportId) {
    // 发送API请求
    fetch(`/api/reports/${reportId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应异常');
            }
            return response.json();
        })
        .then(data => {
            // 切换到首页
            showPage('home');
            
            // 填充表单数据
            document.getElementById('age').value = data.patient ? data.patient.age : '';
            document.getElementById('gender').value = data.patient ? data.patient.gender : '';
            document.getElementById('examination_type').value = data.examination_type;
            document.getElementById('findings').value = data.findings;
            document.getElementById('impression').value = data.impression;
            
            // 显示结构化结果
            if (data.structured_results) {
                // 隐藏加载状态和空结果
                document.getElementById('loading').classList.add('d-none');
                document.getElementById('empty-result').classList.add('d-none');
                document.getElementById('result-container').classList.remove('d-none');
                
                // 准备数据
                const findingsResult = data.structured_results.findings || { entities: [], relationships: [] };
                const impressionResult = data.structured_results.impression || { entities: [], relationships: [] };
                
                // 显示结果
                displayEntities(findingsResult.entities, 'findings-entities-table');
                displayRelationships(findingsResult.entities, findingsResult.relationships, 'findings-relationships-table');
                displayEntities(impressionResult.entities, 'impression-entities-table');
                displayRelationships(impressionResult.entities, impressionResult.relationships, 'impression-relationships-table');
                
                // 显示关系可视化
                setTimeout(() => {
                    renderGraph(findingsResult.entities, findingsResult.relationships, 'visualization');
                }, 100);
            }
        })
        .catch(error => {
            // 显示错误信息
            alert('获取报告详情时出错: ' + error.message);
        });
}
