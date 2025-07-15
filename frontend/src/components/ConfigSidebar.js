import React from 'react';
import ServiceSelector from './ServiceSelector';
import ConfigButtons from './ConfigButtons'

const ConfigSidebar = ({ selectedService, onSelectService }) => {
  return (
    <div className="sidebar">
      <ServiceSelector
        selectedService={selectedService}
        onSelectService={onSelectService}
      />
      <ConfigButtons
        selectedService={selectedService}
      />
    </div>
  );
};

export default ConfigSidebar;
