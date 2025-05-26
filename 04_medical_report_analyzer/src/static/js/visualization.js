// 修复和优化关系可视化功能
document.addEventListener('DOMContentLoaded', function() {
    // 其他初始化代码保持不变...

    // 修改渲染关系图的函数
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
            .attr('height', height)
            .append('g')
            .attr('transform', 'translate(0,0)');
        
        // 添加箭头定义
        svg.append('defs').append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '-0 -5 10 10')
            .attr('refX', 18)
            .attr('refY', 0)
            .attr('orient', 'auto')
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('xoverflow', 'visible')
            .append('svg:path')
            .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
            .attr('fill', '#999')
            .style('stroke', 'none');
        
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
            type: rel.relation_type,
            code: rel.snomed_relation_code
        }));
        
        // 创建力导向图
        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(150))
            .force('charge', d3.forceManyBody().strength(-500))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(50));
        
        // 创建连接容器
        const link = svg.append('g')
            .attr('class', 'links')
            .selectAll('path')
            .data(links)
            .enter()
            .append('path')
            .attr('class', 'link')
            .attr('stroke', '#999')
            .attr('stroke-width', 1.5)
            .attr('fill', 'none')
            .attr('marker-end', 'url(#arrowhead)');
        
        // 创建连接标签容器
        const edgepaths = svg.selectAll(".edgepath")
            .data(links)
            .enter()
            .append('path')
            .attr('class', 'edgepath')
            .attr('fill-opacity', 0)
            .attr('stroke-opacity', 0)
            .attr('id', (d, i) => 'edgepath' + i)
            .style("pointer-events", "none");
        
        // 创建连接标签文本
        const edgelabels = svg.selectAll(".edgelabel")
            .data(links)
            .enter()
            .append('text')
            .attr('class', 'edgelabel')
            .attr('id', (d, i) => 'edgelabel' + i)
            .attr('font-size', 10)
            .attr('fill', '#666')
            .style("pointer-events", "none");
        
        edgelabels.append('textPath')
            .attr('xlink:href', (d, i) => '#edgepath' + i)
            .attr('startOffset', '50%')
            .text(d => d.type);
        
        // 创建节点容器
        const node = svg.append('g')
            .attr('class', 'nodes')
            .selectAll('g')
            .data(nodes)
            .enter()
            .append('g')
            .call(d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended));
        
        // 添加节点圆圈
        node.append('circle')
            .attr('r', 10)
            .attr('fill', d => getColorByType(d.type))
            .attr('stroke', '#fff')
            .attr('stroke-width', 2);
        
        // 添加节点标签
        node.append('text')
            .attr('dy', -15)
            .attr('text-anchor', 'middle')
            .text(d => d.name)
            .attr('font-size', '12px')
            .attr('fill', '#333');
        
        // 添加节点类型标签
        node.append('text')
            .attr('dy', 25)
            .attr('text-anchor', 'middle')
            .text(d => d.type)
            .attr('font-size', '10px')
            .attr('fill', '#666');
        
        // 添加节点悬停提示
        node.append('title')
            .text(d => `${d.name}\n类型: ${d.type}\nSNOMED编码: ${d.code || '未知'}`);
        
        // 更新力导向图
        simulation.on('tick', () => {
            // 更新连接路径
            link.attr('d', d => {
                const dx = d.target.x - d.source.x,
                      dy = d.target.y - d.source.y,
                      dr = Math.sqrt(dx * dx + dy * dy);
                return `M${d.source.x},${d.source.y}A${dr},${dr} 0 0,1 ${d.target.x},${d.target.y}`;
            });
            
            // 更新连接标签路径
            edgepaths.attr('d', d => {
                const dx = d.target.x - d.source.x,
                      dy = d.target.y - d.source.y,
                      dr = Math.sqrt(dx * dx + dy * dy);
                return `M${d.source.x},${d.source.y}A${dr},${dr} 0 0,1 ${d.target.x},${d.target.y}`;
            });
            
            // 更新连接标签位置
            edgelabels.attr('transform', d => {
                if (d.target.x < d.source.x) {
                    const bbox = this.getBBox();
                    const rx = bbox.x + bbox.width / 2;
                    const ry = bbox.y + bbox.height / 2;
                    return `rotate(180 ${rx} ${ry})`;
                }
                return 'rotate(0)';
            });
            
            // 更新节点位置
            node.attr('transform', d => `translate(${d.x},${d.y})`);
        });
        
        // 添加缩放功能
        const zoom = d3.zoom()
            .scaleExtent([0.5, 3])
            .on('zoom', (event) => {
                svg.attr('transform', event.transform);
            });
        
        d3.select(container).select('svg')
            .call(zoom);
        
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
                '影像学表现': '#9c27b0',
                '测量值': '#2196f3',
                '时间变化': '#795548'
            };
            
            return colorMap[type] || '#999';
        }
    }

    // 其他函数保持不变...

    // 替换原有的renderGraph函数
    window.renderGraph = renderGraph;
});
