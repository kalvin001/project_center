/**
 * 日期工具函数
 */

/**
 * 格式化日期显示
 * @param dateString 日期字符串或Date对象
 * @param defaultText 默认显示文本
 * @returns 格式化后的日期字符串
 */
export const formatDate = (dateString: string | Date | null | undefined, defaultText: string = '未设置'): string => {
  if (!dateString) {
    return defaultText;
  }
  
  // 检查是否是有效的日期字符串
  const date = new Date(dateString);
  
  // 检查日期是否有效
  if (
    isNaN(date.getTime()) || 
    date.getTime() <= 0 || 
    dateString === '0001-01-01T00:00:00' ||
    dateString === '0001-01-01T00:00:00Z'
  ) {
    return defaultText;
  }
  
  // 格式化日期 (年-月-日 时:分:秒)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });
};

/**
 * 获取友好的时间显示
 * @param dateString 日期字符串或Date对象
 * @param defaultText 默认显示文本
 * @returns 友好的时间显示
 */
export const getFriendlyTime = (dateString: string | Date | null | undefined, defaultText: string = '未设置'): string => {
  if (!dateString) {
    return defaultText;
  }
  
  // 检查是否是有效的日期字符串
  const date = new Date(dateString);
  
  // 检查日期是否有效
  if (
    isNaN(date.getTime()) || 
    date.getTime() <= 0 || 
    dateString === '0001-01-01T00:00:00' ||
    dateString === '0001-01-01T00:00:00Z'
  ) {
    return defaultText;
  }
  
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);
  
  if (diffSec < 60) {
    return '刚刚';
  } else if (diffMin < 60) {
    return `${diffMin}分钟前`;
  } else if (diffHour < 24) {
    return `${diffHour}小时前`;
  } else if (diffDay < 30) {
    return `${diffDay}天前`;
  } else {
    return formatDate(date);
  }
}; 