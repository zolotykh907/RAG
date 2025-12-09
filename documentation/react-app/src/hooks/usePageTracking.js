import { useEffect, useRef } from 'react';
import { recordPageVisit, updatePageTime } from '../utils/api';

const usePageTracking = (pageId) => {
  const startTimeRef = useRef(null);
  const hasRecordedVisitRef = useRef(false);

  useEffect(() => {
    if (!pageId) return;

    if (!hasRecordedVisitRef.current) {
      recordPageVisit(pageId);
      hasRecordedVisitRef.current = true;
    }

    startTimeRef.current = Date.now();

    const handleBeforeUnload = () => {
      if (startTimeRef.current) {
        const timeSpent = Math.floor((Date.now() - startTimeRef.current) / 1000);
        if (timeSpent > 0) {
          const data = JSON.stringify({ time_seconds: timeSpent });
          navigator.sendBeacon(
            `http://localhost:8000/pages/${pageId}/time`,
            new Blob([data], { type: 'application/json' })
          );
        }
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);

      if (startTimeRef.current) {
        const timeSpent = Math.floor((Date.now() - startTimeRef.current) / 1000);
        if (timeSpent > 0) {
          updatePageTime(pageId, timeSpent);
        }
      }
    };
  }, [pageId]);
};

export default usePageTracking;
