import React from 'react';

const ServiceSelector = ({ selectedService, onSelectService }) => {
  const services = ['query', 'indexing'];

  return (
    <div className="sidebar-section">
      <h3><i className="fas fa-cogs"></i> Выбор сервиса</h3>
      <div className="service-buttons">
        {services.map((service) => (
          <button
            key={service}
            className={`service-button ${selectedService === service ? 'active' : ''}`}
            onClick={() => onSelectService(service)}
          >
            {service.toUpperCase()}
          </button>
        ))}
      </div>
    </div>
  );
};

export default ServiceSelector;