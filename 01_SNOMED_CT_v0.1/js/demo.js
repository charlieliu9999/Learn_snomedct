/**
 * SNOMED CT交互式案例演示功能
 */

document.addEventListener('DOMContentLoaded', () => {
    // 初始化标签页切换
    initTabSystem();
    
    // 初始化SNOMED CT术语点击事件
    initSnomedTermClicks();
    
    // 初始化工作流演示
    initWorkflowDemo();
    
    // 语义类型映射
    window.semanticTypes = {
        '71388002': '操作',
        '404684003': '临床发现',
        '123037004': '身体结构',
        '260787004': '物理对象',
        '362981000': '限定值',
        '410668003': '属性',
        '272379006': '事件',
        '105590001': '物质',
        '900000000000441003': '产后概念'
    };
});

/**
 * 初始化标签页系统
 */
function initTabSystem() {
    // 获取所有标签按钮和内容区域
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // 为每个标签按钮添加点击事件
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // 获取要激活的标签内容ID
            const tabId = button.getAttribute('data-tab');
            
            // 移除所有标签按钮和内容的活动状态
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // 激活当前点击的标签
            button.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });
}

/**
 * 初始化SNOMED CT术语点击事件
 */
function initSnomedTermClicks() {
    // 获取所有SNOMED CT术语元素
    const snomedTerms = document.querySelectorAll('.snomedTerm');
    
    // 获取概念详情显示区域的元素
    const conceptId = document.getElementById('conceptId');
    const conceptTerm = document.getElementById('conceptTerm');
    const conceptType = document.getElementById('conceptType');
    const conceptExpression = document.getElementById('conceptExpression');
    
    // 为每个术语添加点击事件
    snomedTerms.forEach(term => {
        term.addEventListener('click', () => {
            // 移除所有术语的活动状态
            snomedTerms.forEach(t => t.classList.remove('active'));
            
            // 激活当前点击的术语
            term.classList.add('active');
            
            // 获取术语的SNOMED CT概念ID和名称
            const id = term.getAttribute('data-concept');
            const termText = term.getAttribute('data-term');
            
            // 更新概念详情显示
            conceptId.textContent = id;
            conceptTerm.textContent = termText;
            
            // 根据概念ID确定语义类型（简化版，实际应通过API获取）
            // 从ID的前几位或概念特征推断语义类型
            const rootConceptId = determineRootConcept(id);
            conceptType.textContent = window.semanticTypes[rootConceptId] || '临床发现';
            
            // 生成简单的表达式示例（实际应通过API获取）
            generateExpressionExample(id, termText);
        });
    });
    
    /**
     * 根据概念ID确定语义类型（简化版）
     */
    function determineRootConcept(conceptId) {
        // 简化的映射逻辑，实际应查询SNOMED CT
        if (conceptId.startsWith('71')) return '71388002'; // 操作
        if (conceptId.startsWith('40')) return '404684003'; // 临床发现
        if (conceptId.startsWith('12')) return '123037004'; // 身体结构
        if (conceptId.startsWith('26')) return '260787004'; // 物理对象
        if (conceptId.startsWith('36')) return '362981000'; // 限定值
        if (conceptId.startsWith('41')) return '410668003'; // 属性
        return '404684003'; // 默认为临床发现
    }
    
    /**
     * 生成SNOMED CT表达式示例
     */
    function generateExpressionExample(conceptId, termText) {
        // 生成不同类型的表达式示例
        let expression;
        
        if (conceptId === '48387007') {
            // 右上肺
            expression = `48387007 |右上肺| = 
            45653009 |上肺| : 
                272741003 |侧向性| = 24028007 |右|`;
        } else if (conceptId === '41224006') {
            // 右下肺
            expression = `41224006 |右下肺| = 
            82998004 |下肺| : 
                272741003 |侧向性| = 24028007 |右|`;
        } else if (conceptId === '16404004') {
            // 随访胸部CT
            expression = `16404004 |胸部CT检查| : 
                408731000 |时间接近值| = 258705008 |三个月|`;
        } else if (conceptId === '372124000') {
            // 恶性肺结节
            expression = `372124000 |恶性肺结节| = 
            309529002 |肺结节| : 
                263502005 |临床过程| = 363346000 |恶性肿瘤过程|`;
        } else if (conceptId === '26241001') {
            // 毛刺状
            expression = `26241001 |毛刺状| : 
                246090004 |相关病变| = 309529002 |肺结节|`;
        } else if (conceptId === '393564001') {
            // 胶质母细胞瘤
            expression = `393564001 |胶质母细胞瘤| : 
                363698007 |发病部位| = 78277001 |右侧颞叶结构|`;
        } else if (conceptId === '235571004') {
            // 胆囊结石
            expression = `235571004 |胆囊结石| = 
            56381008 |结石| : 
                363698007 |发病部位| = 28231008 |胆囊结构|`;
        } else {
            // 默认简单表达式
            expression = `${conceptId} |${termText}|`;
        }
        
        conceptExpression.textContent = expression;
    }
}

/**
 * 初始化工作流演示
 */
function initWorkflowDemo() {
    // 获取工作流框架和控制按钮
    const frames = document.querySelectorAll('.animation-frame');
    const prevButton = document.getElementById('prevFrame');
    const nextButton = document.getElementById('nextFrame');
    
    // 初始显示第一个框架
    let currentFrame = 0;
    updateFrameDisplay();
    
    // 上一步按钮点击事件
    prevButton.addEventListener('click', () => {
        if (currentFrame > 0) {
            currentFrame--;
            updateFrameDisplay();
        }
    });
    
    // 下一步按钮点击事件
    nextButton.addEventListener('click', () => {
        if (currentFrame < frames.length - 1) {
            currentFrame++;
            updateFrameDisplay();
        }
    });
    
    /**
     * 更新框架显示
     */
    function updateFrameDisplay() {
        // 隐藏所有框架
        frames.forEach(frame => {
            frame.style.display = 'none';
        });
        
        // 显示当前框架
        frames[currentFrame].style.display = 'block';
        
        // 更新按钮状态
        prevButton.disabled = (currentFrame === 0);
        nextButton.disabled = (currentFrame === frames.length - 1);
    }
}

// Syntax self-check
try {
    console.log("Demo.js syntax check passed");
}
catch (error) {
    console.error("Syntax error in demo.js:", error.message);
}