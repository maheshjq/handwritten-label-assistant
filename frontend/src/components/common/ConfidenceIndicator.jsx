import React from 'react';
import { Progress, Tag, Tooltip } from 'antd';
import { 
  CheckCircleOutlined, 
  WarningOutlined, 
  CloseCircleOutlined 
} from '@ant-design/icons';

const ConfidenceIndicator = ({ value, showText = true }) => {
  // Normalize value to be between 0 and 1
  const normalizedValue = value > 1 ? value / 100 : value;
  const percentage = Math.round(normalizedValue * 100);
  
  // Determine status and color based on confidence value
  let status, color, icon, text;
  
  if (percentage >= 90) {
    status = 'success';
    color = 'success';
    icon = <CheckCircleOutlined />;
    text = 'High';
  } else if (percentage >= 70) {
    status = 'normal';
    color = 'processing';
    icon = <CheckCircleOutlined />;
    text = 'Good';
  } else if (percentage >= 50) {
    status = 'active';
    color = 'warning';
    icon = <WarningOutlined />;
    text = 'Moderate';
  } else {
    status = 'exception';
    color = 'error';
    icon = <CloseCircleOutlined />;
    text = 'Low';
  }
  
  return (
    <div className="confidence-indicator">
      <Progress 
        percent={percentage} 
        status={status} 
        size="small"
        style={{ marginRight: 8 }}
      />
      {showText && (
        <Tooltip title={`${percentage}% confidence`}>
          <Tag color={color} icon={icon}>
            {text}
          </Tag>
        </Tooltip>
      )}
    </div>
  );
};

export default ConfidenceIndicator;
