document.addEventListener('DOMContentLoaded', () => {
    // Animate elements on scroll
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
            }
        });
    });

    document.querySelectorAll('.card, .stat-card').forEach((el) => {
        el.style.opacity = '0';
        observer.observe(el);
    });

    // Form validation and feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            const btn = form.querySelector('button[type="submit"]');
            if (btn) {
                const originalText = btn.innerText;
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner"></span> Processing...';
                
                // Simulate minimum loading time for UX
                setTimeout(() => {
                    // Allow form submission to proceed
                }, 500);
            }
        });
    });

    // Agentic Visualization Logic (if present)
    const agentChain = document.getElementById('agent-chain');
    if (agentChain) {
        // Simulate real-time updates for demo purposes
        // In production, this would be WebSocket driven
        const steps = agentChain.querySelectorAll('.agent-step');
        steps.forEach((step, index) => {
            step.style.opacity = '0';
            setTimeout(() => {
                step.classList.add('animate-fade-in');
            }, index * 800);
        });
    }
});
