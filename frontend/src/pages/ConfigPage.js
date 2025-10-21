import React, { useState, useCallback, useEffect } from 'react';
import Config from '../components/Config';
import ConfigSidebar from '../components/ConfigSidebar';
import LoadingOverlay from '../components/LoadingOverlay';
import Toast from '../components/Toast';

const ConfigPage = () => {
  const [config, setConfig] = useState({});
  const [initialConfig, setInitialConfig] = useState({});
  const [status, setStatus] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedService, setSelectedService] = useState('query');
  const [toast, setToast] = useState({ message: '', type: 'success', visible: false });

  const showToast = (message, type = 'success') => {
    setToast({ visible: true, message, type });
  };

  const fetchConfig = useCallback(async (service) => {
    try {
      setIsLoading(true);
      const endpoint = `http://localhost:8000/config?service=${service}`;
      const res = await fetch(endpoint);
      if (!res.ok) throw new Error('Ошибка сети');
      const data = await res.json();
      setConfig(data || {});
      setInitialConfig(prev => (Object.keys(prev).length === 0 ? (data || {}) : prev));
      setStatus('✅ Конфигурация загружена');
    } catch (err) {
      setStatus('❌ Ошибка загрузки');
      showToast('Ошибка загрузки конфигурации', 'error');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConfig(selectedService);
  }, [selectedService, fetchConfig]);

  const handleChange = (path, value) => {
    setConfig((prevConfig) => {
      const newConfig = structuredClone(prevConfig || {});
      let obj = newConfig;
      for (let i = 0; i < path.length - 1; i++) {
        obj = obj[path[i]] = obj[path[i]] || {};
      }
      const lastKey = path[path.length - 1];
      const original = obj[lastKey];
      if (Array.isArray(original)) {
        obj[lastKey] = value.split(',').map((v) => v.trim());
      } else {
        const numValue = Number(value);
        obj[lastKey] = !isNaN(numValue) && value.trim() !== '' ? numValue : value;
      }
      return newConfig;
    });
  };

  const handleSubmit = (e) => {
    if (e && e.preventDefault) e.preventDefault();
    setIsLoading(true);
    const endpoint = `http://localhost:8000/config?service=${selectedService}`;
    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    })
      .then((res) => {
        if (!res.ok) throw new Error('Ошибка сохранения');
        return res.json();
      })
      .then(() => {
        setStatus('✅ Конфигурация сохранена!');
        showToast('✅ Конфигурация сохранена!', 'success');
      })
      .catch(() => {
        setStatus('❌ Ошибка сохранения');
        showToast('❌ Ошибка сохранения', 'error');
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  const handleReset = () => {
    setConfig(initialConfig);
    setStatus('');
  };

  const handleReload = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/reload?service=${selectedService}`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('Ошибка перезагрузки');
      setStatus('✅ Сервис перезапущен');
      showToast('✅ Сервис перезапущен', 'success');
    } catch (e) {
      setStatus('❌ Ошибка при перезапуске сервиса');
      showToast('❌ Ошибка при перезапуске сервиса', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Config
        config={config}
        setConfig={setConfig}
        status={status}
        setStatus={setStatus}
        isLoading={isLoading}
        onChange={handleChange}
        onSubmit={handleSubmit}
        selectedService={selectedService}
      />
      <ConfigSidebar
        selectedService={selectedService}
        onSelectService={setSelectedService}
        onReset={handleReset}
        onReload={handleReload}
        isLoading={isLoading}
        onSave={handleSubmit}
      />
      {isLoading && <LoadingOverlay />}
      <Toast
        message={toast.message}
        type={toast.type}
        visible={toast.visible}
        onClose={() => setToast({ ...toast, visible: false })}
      />
    </>
  );
};

export default ConfigPage;
