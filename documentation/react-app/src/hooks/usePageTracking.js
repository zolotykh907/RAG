import { useEffect, useRef } from 'react';
import { recordPageVisit, updatePageTime } from '../utils/api';

const usePageTracking = (pageId) => {
  const startTimeRef = useRef(null);
  const hasRecordedVisitRef = useRef(false);

  useEffect(() => {
    if (!pageId) return;

    // Record visit when component mounts
    if (!hasRecordedVisitRef.current) {
      recordPageVisit(pageId);
      hasRecordedVisitRef.current = true;
    }

    // Start tracking time
    startTimeRef.current = Date.now();

    // Handle page unload (user closes tab or navigates away)
    const handleBeforeUnload = () => {
      if (startTimeRef.current) {
        const timeSpent = Math.floor((Date.now() - startTimeRef.current) / 1000);
        if (timeSpent > 0) {
          // Use sendBeacon for reliable delivery on page unload
          const data = JSON.stringify({ time_seconds: timeSpent });
          navigator.sendBeacon(
            `http://localhost:8000/pages/${pageId}/time`,
            new Blob([data], { type: 'application/json' })
          );
        }
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    // Cleanup when component unmounts (user navigates to another page)
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
