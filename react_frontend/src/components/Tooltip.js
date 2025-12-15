import { useState } from 'react';
import './Tooltip.css';

function Tooltip({ children, text }) {
  const [visible, setVisible] = useState(false);

  if (!text) return children;

  return (
    <div className="tooltip-wrapper">
      <span
        onMouseEnter={() => setVisible(true)}
        onMouseLeave={() => setVisible(false)}
      >
        {children}
      </span>
      {visible && (
        <div className="tooltip-content">
          {text}
        </div>
      )}
    </div>
  );
}

export default Tooltip;
