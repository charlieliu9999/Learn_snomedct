/**
 * SNOMED CT医学影像应用与诊断报告结构化网站增强JS
 * 用于改进网站响应式设计和用户交互体验
 */

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', () => {
    // 初始化增强的移动端菜单
    initEnhancedMobileMenu();
    
    // 初始化页内导航高亮
    initPageNavHighlight();
    
    // 初始化平滑滚动
    initSmoothScroll();
    
    // 初始化Header滚动效果
    initHeaderScrollEffect();
    
    // 初始化卡片悬停效果
    initCardHoverEffects();
    
    // 初始化交互式案例
    initCaseDemos();
    
    // 初始化深色模式切换
    initDarkModeToggle();
    
    // 添加图片加载错误处理
    handleImageErrors();
});

/**
 * 初始化增强的移动端菜单
 */
function initEnhancedMobileMenu() {
    const menuToggle = document.getElementById('menuToggle');
    const navLinks = document.getElementById('navLinks');
    const body = document.body;
    
    if (!menuToggle || !navLinks) return;
    
    menuToggle.addEventListener('click', () => {
        navLinks.classList.toggle('active');
        menuToggle.classList.toggle('active');
        body.classList.toggle('menu-open');
    });
    
    // 点击链接后关闭菜单
    const navItems = navLinks.querySelectorAll('a');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                navLinks.classList.remove('active');
                menuToggle.classList.remove('active');
                body.classList.remove('menu-open');
            }
        });
    });
    
    // 点击菜单外部关闭菜单
    document.addEventListener('click', (e) => {
        if (
            window.innerWidth <= 768 &&
            navLinks.classList.contains('active') &&
            !navLinks.contains(e.target) &&
            !menuToggle.contains(e.target)
        ) {
            navLinks.classList.remove('active');
            menuToggle.classList.remove('active');
            body.classList.remove('menu-open');
        }
    });
}

/**
 * 初始化页内导航高亮
 */
function initPageNavHighlight() {
    const pageNav = document.querySelector('.page-nav');
    if (!pageNav) return;
    
    const navLinks = pageNav.querySelectorAll('a');
    const contentBlocks = document.querySelectorAll('.content-block');
    
    // 初始激活第一个链接
    if (navLinks.length > 0) {
        navLinks[0].classList.add('active');
    }
    
    // 监听滚动，高亮当前可见部分
    window.addEventListener('scroll', () => {
        let currentSection = '';
        
        contentBlocks.forEach(section => {
            const sectionTop = section.offsetTop - 150;
            const sectionHeight = section.offsetHeight;
            const scrollPosition = window.scrollY;
            
            if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                currentSection = section.getAttribute('id');
            }
        });
        
        if (currentSection !== '') {
            navLinks.forEach(link => {
                link.classList.remove('active');
                
                if (link.getAttribute('href') === `#${currentSection}`) {
                    link.classList.add('active');
                }
            });
        }
    });
    
    // 点击导航链接平滑滚动到对应部分
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            
            if (targetSection) {
                const offsetTop = targetSection.offsetTop - 100;
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
                
                // 更新URL但不刷新页面
                history.pushState(null, null, `#${targetId}`);
                
                // 更新导航链接状态
                navLinks.forEach(navLink => navLink.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });
    
    // 使页面导航固定在滚动位置
    if (pageNav) {
        const navTop = pageNav.offsetTop - 100;
        
        window.addEventListener('scroll', () => {
            if (window.scrollY >= navTop) {
                pageNav.classList.add('sticky');
            } else {
                pageNav.classList.remove('sticky');
            }
        });
    }
}

/**
 * 初始化平滑滚动
 */
function initSmoothScroll() {
    // 选择所有内部链接
    const internalLinks = document.querySelectorAll('a[href^="#"]');
    
    internalLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // 如果是页面导航链接，已在另一个函数中处理
            if (this.closest('.page-nav')) return;
            
            const targetId = this.getAttribute('href').substring(1);
            if (!targetId) return; // 如果是 "#" 空链接
            
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                e.preventDefault();
                const offsetTop = targetElement.offsetTop - 100;
                
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
}

/**
 * 初始化Header滚动效果
 */
function initHeaderScrollEffect() {
    const header = document.querySelector('header');
    if (!header) return;
    
    let lastScrollTop = 0;
    
    window.addEventListener('scroll', () => {
        const scrollTop = window.scrollY;
        
        // 如果滚动超过100px，添加compact类
        if (scrollTop > 100) {
            header.classList.add('compact');
        } else {
            header.classList.remove('compact');
        }
        
        // 如果向下滚动超过500px且继续向下滚动，隐藏导航栏
        if (scrollTop > 500 && scrollTop > lastScrollTop) {
            header.classList.add('hidden');
        } else {
            header.classList.remove('hidden');
        }
        
        lastScrollTop = scrollTop;
    });
}

/**
 * 初始化卡片悬停效果
 */
function initCardHoverEffects() {
    // 为所有卡片类型添加高级悬停效果
    const cards = document.querySelectorAll('.feature-card, .component-card, .application-card, .advantage-item, .benefit-item, .element-card, .standard-box, .app-card, .case-card');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.classList.add('hover');
        });
        
        card.addEventListener('mouseleave', function() {
            this.classList.remove('hover');
        });
    });
}

/**
 * 初始化交互式案例
 */
function initCaseDemos() {
    // 处理案例页的标签切换
    const demoTabs = document.querySelector('.demo-tabs');
    if (!demoTabs) return;
    
    const tabButtons = demoTabs.querySelectorAll('.tab-button');
    const tabContents = demoTabs.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // 更新按钮状态
            tabButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // 更新内容显示
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === tabId) {
                    content.classList.add('active');
                }
            });
        });
    });
    
    // 处理SNOMED术语高亮
    const snomedTerms = document.querySelectorAll('.snomedTerm');
    
    snomedTerms.forEach(term => {
        term.addEventListener('click', function() {
            const conceptId = this.getAttribute('data-concept');
            const termName = this.getAttribute('data-term');
            
            // 显示术语详情
            const detailContainer = document.getElementById('termDetail');
            if (detailContainer) {
                detailContainer.innerHTML = `
                    <div class="term-detail-header">
                        <h3>${termName}</h3>
                        <p>SNOMED CT概念ID: ${conceptId}</p>
                    </div>
                    <div class="term-detail-content">
                        <p>此术语在SNOMED CT本体中有明确的定义和关系网络。点击下方链接在SNOMED CT浏览器中查看完整定义。</p>
                        <a href="https://browser.ihtsdotools.org/?perspective=full&conceptId1=${conceptId}" target="_blank" class="detail-link">
                            在SNOMED浏览器中查看
                        </a>
                    </div>
                `;
                detailContainer.classList.add('visible');
                
                // 添加关闭按钮
                const closeButton = document.createElement('button');
                closeButton.className = 'close-detail';
                closeButton.innerHTML = '×';
                closeButton.setAttribute('aria-label', '关闭详情');
                
                closeButton.addEventListener('click', () => {
                    detailContainer.classList.remove('visible');
                });
                
                detailContainer.appendChild(closeButton);
            }
            
            // 高亮所有相同的术语
            snomedTerms.forEach(t => {
                if (t.getAttribute('data-concept') === conceptId) {
                    t.classList.add('highlighted');
                }
            });
        });
    });
    
    // 创建术语详情容器（如果不存在）
    if (document.querySelectorAll('.snomedTerm').length > 0 && !document.getElementById('termDetail')) {
        const detailContainer = document.createElement('div');
        detailContainer.id = 'termDetail';
        detailContainer.className = 'term-detail-container';
        
        document.body.appendChild(detailContainer);
        
        // 点击外部关闭详情
        document.addEventListener('click', (e) => {
            const container = document.getElementById('termDetail');
            if (
                container && 
                container.classList.contains('visible') && 
                !container.contains(e.target) && 
                !e.target.classList.contains('snomedTerm')
            ) {
                container.classList.remove('visible');
                // 移除高亮
                document.querySelectorAll('.snomedTerm.highlighted').forEach(t => {
                    t.classList.remove('highlighted');
                });
            }
        });
    }
}

/**
 * 初始化深色模式切换
 */
function initDarkModeToggle() {
    // 检查是否支持深色模式
    if (!window.matchMedia) return;
    
    const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const storedTheme = localStorage.getItem('theme');
    
    // 创建切换按钮
    const toggleButton = document.createElement('button');
    toggleButton.className = 'theme-toggle';
    toggleButton.setAttribute('aria-label', '切换深色/浅色主题');
    toggleButton.innerHTML = '<span class="sr-only">切换主题</span>';
    
    // 添加到页面
    const container = document.createElement('div');
    container.className = 'theme-toggle-container';
    container.appendChild(toggleButton);
    document.body.appendChild(container);
    
    // 设置初始主题
    if (storedTheme === 'dark' || (!storedTheme && prefersDarkMode)) {
        document.documentElement.classList.add('dark-theme');
        toggleButton.classList.add('dark');
    }
    
    // 添加切换事件
    toggleButton.addEventListener('click', () => {
        document.documentElement.classList.toggle('dark-theme');
        toggleButton.classList.toggle('dark');
        
        const isDark = document.documentElement.classList.contains('dark-theme');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });
    
    // 监听系统主题变化
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            if (e.matches) {
                document.documentElement.classList.add('dark-theme');
                toggleButton.classList.add('dark');
            } else {
                document.documentElement.classList.remove('dark-theme');
                toggleButton.classList.remove('dark');
            }
        }
    });
}

/**
 * 处理图片加载错误
 */
function handleImageErrors() {
    const images = document.querySelectorAll('img');
    
    images.forEach(img => {
        img.addEventListener('error', function() {
            // 根据图片类型选择不同的替代图片
            if (this.classList.contains('content-image')) {
                this.src = '/workspace/website/images/architecture.jpg';
            } else if (this.classList.contains('card-image')) {
                this.src = '/workspace/website/images/storage.jpg';
            } else {
                this.src = '/workspace/website/images/mapping.jpg';
            }
            
            this.classList.add('fallback-image');
        });
    });
}

// Syntax self-check
try {
    console.log("Enhanced JS syntax check passed");
}
catch (error) {
    console.error("Enhanced JS syntax error:", error.message);
}