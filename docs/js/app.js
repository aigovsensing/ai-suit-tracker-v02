document.addEventListener('DOMContentLoaded', () => {
    // Smooth scrolling for navigation
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Nav background change on scroll
    const nav = document.querySelector('.main-nav');
    if (nav) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                nav.style.padding = '1rem 0';
                nav.style.background = 'rgba(11, 14, 20, 0.9)';
                nav.style.boxShadow = '0 10px 30px -10px rgba(0,0,0,0.5)';
            } else {
                nav.style.padding = '1.5rem 0';
                nav.style.background = 'rgba(11, 14, 20, 0.7)';
                nav.style.boxShadow = 'none';
            }
        });
    }

    // Reveal animations on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Initial styles for animations
    const animatedElements = document.querySelectorAll('.feature-card, .level-card, .flow-step');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'all 0.6s cubic-bezier(0.22, 1, 0.36, 1)';
        observer.observe(el);
    });

    // Code typing effect (simple)
    const codeBlock = document.querySelector('pre code');
    if (codeBlock) {
        const text = codeBlock.textContent;
        // codeBlock.textContent = '';
        // let i = 0;
        // function type() {
        //     if (i < text.length) {
        //         codeBlock.textContent += text.charAt(i);
        //         i++;
        //         setTimeout(type, 10);
        //     }
        // }
        // type();
    }
});
