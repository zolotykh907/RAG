import { useState } from 'react';

const ExpandableBlock = ({ title, children }) => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleBlock = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div className='exp-block' >
      <div 
        className='exp-text'
        onClick={toggleBlock}
      >
        {isOpen ? '▲' : '▼'}
        <span>{title}</span>
      </div>

      {isOpen && (
        <div className='fade-in'>
          {children}
        </div>
      )}
    </div>
  );
};

export default ExpandableBlock;
