import React from 'react';
import ServiceSelector from './ServiceSelector';
import ConfigButtons from './ConfigButtons';

const ConfigSidebar = ({
  selectedService,
  onSelectService,
  onReset,
  onReload,
  isLoading,
  onSave
}) => {
  return (
    <div className="sidebar">
      <ServiceSelector
        selectedService={selectedService}
        onSelectService={onSelectService}
      />
      <ConfigButtons
        onReset={onReset}
        onReload={onReload}
        isLoading={isLoading}
        selectedService={selectedService}
        onSave={onSave}
      />
    </div>
  );
};

export default ConfigSidebar;
