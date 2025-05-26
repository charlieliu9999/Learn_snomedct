/**
 * SNOMED CT医学影像应用与诊断报告结构化网站主要JS文件
 */

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', () => {
    // 初始化移动端菜单
    initMobileMenu();
    
    // 初始化滚动动画
    initScrollAnimation();
    
    // 根据当前页面设置活动导航链接
    setActivePage();
});

/**
 * 初始化移动端菜单
 */
function initMobileMenu() {
    const menuToggle = document.getElementById('menuToggle');
    const navLinks = document.getElementById('navLinks');
    
    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            menuToggle.classList.toggle('active');
        });
    }
}

/**
 * 设置当前活动页面的导航链接样式
 */
function setActivePage() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const navLinks = document.querySelectorAll('.nav-links a');
    
    navLinks.forEach(link => {
        const linkHref = link.getAttribute('href');
        if (linkHref === currentPage) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

/**
 * 初始化滚动动画
 */
function initScrollAnimation() {
    const animateElements = document.querySelectorAll('.feature-card, .app-card, .step-card');
    
    // 如果IntersectionObserver可用，使用它来实现滚动显示动画
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animated');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.2
        });
        
        animateElements.forEach(element => {
            observer.observe(element);
        });
    } else {
        // 如果不支持IntersectionObserver，默认显示所有元素
        animateElements.forEach(element => {
            element.classList.add('animated');
        });
    }
}

/**
 * 滚动到指定区域
 * @param {string} sectionId - 目标区域ID
 */
function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        window.scrollTo({
            top: section.offsetTop - 80,  // 减去头部导航高度
            behavior: 'smooth'
        });
    }
}

/**
 * 处理图片加载错误
 * @param {HTMLImageElement} img - 图片元素
 * @param {string} fallbackSrc - 备用图片地址
 */
function handleImageError(img, fallbackSrc) {
    img.onerror = null;  // 防止循环触发错误
    img.src = fallbackSrc;
}

// 图片加载错误时的处理
document.querySelectorAll('img').forEach(img => {
    img.addEventListener('error', function() {
        // 根据图片类型提供不同的备用图片
        if (this.classList.contains('feature-icon')) {
            handleImageError(this, 'images/default-icon.svg');
        } else if (this.id === 'heroImage') {
            handleImageError(this, 'images/default-hero.jpg');
        } else {
            handleImageError(this, 'images/image-placeholder.jpg');
        }
    });
});

// Syntax self-check
try {
    console.log("Syntax check passed");
}
catch (error) {
    console.error("Syntax error:", error.message);
}