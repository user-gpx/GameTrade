// 主JavaScript文件

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('GameTrade 平台已加载');
    
    // 自动消失的提示消息
    setTimeout(function() {
        let alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.remove();
            }, 500);
        });
    }, 3000);
});

// 确认对话框
function confirmAction(message) {
    return confirm(message || '确定执行此操作吗？');
}