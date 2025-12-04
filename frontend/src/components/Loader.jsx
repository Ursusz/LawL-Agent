import { useEffect, useState } from 'react';
import { CheckCircle, Loader2, AlertCircle, Database, Globe, Sparkles } from 'lucide-react';

function Loader({ sessionId }) {
  const [explicitRefs, setExplicitRefs] = useState([]);
  const [implicitRefs, setImplicitRefs] = useState([]);
  const [referenceStatus, setReferenceStatus] = useState({});
  const [stageHistory, setStageHistory] = useState(['Initializing...']);

  const addStage = (stage, replaceLastIfMatches = null) => {
    setStageHistory(prev => {
      // Avoid duplicate consecutive messages
      if (prev[prev.length - 1] === stage) return prev;

      // If replaceLastIfMatches is provided and the last message matches, replace it
      if (replaceLastIfMatches && prev[prev.length - 1]?.includes(replaceLastIfMatches)) {
        return [...prev.slice(0, -1), stage];
      }

      return [...prev, stage];
    });
  };

  useEffect(() => {
    console.log('[Loader] Session ID:', sessionId);
    if (!sessionId) return;

    console.log('[Loader] Connecting to SSE...');
    const eventSource = new EventSource(`http://localhost:8000/progress/${sessionId}`);

    eventSource.onopen = () => {
      console.log('[Loader] SSE connection opened');
    };

    eventSource.onmessage = (event) => {
      console.log('[Loader] Received event:', event.data);
      try {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case 'reference_extraction_start':
            addStage(`Extracting ${data.data.extraction_type} references...`);
            break;

          case 'reference_extraction_complete':
            const completionMsg = `Found ${data.data.count} ${data.data.extraction_type} reference${data.data.count !== 1 ? 's' : ''}.`;
            // Replace the "Extracting..." message with "Found..." message
            addStage(completionMsg, `Extracting ${data.data.extraction_type}`);

            if (data.data.extraction_type === 'explicit') {
              setExplicitRefs(data.data.references);
            } else if (data.data.extraction_type === 'implicit') {
              setImplicitRefs(data.data.references);
            }
            break;

          case 'reference_processing_start':
            // Add to global stage history
            addStage(`Processing ${data.data.reference}...`);

            setReferenceStatus(prev => ({
              ...prev,
              [data.data.reference]: {
                stage: 'starting',
                status: 'processing',
                cached: {}
              }
            }));
            break;

          case 'reference_stage_update':
            setReferenceStatus(prev => ({
              ...prev,
              [data.data.reference]: {
                ...prev[data.data.reference],
                stage: data.data.stage,
                status: 'processing',
                cached: {
                  ...prev[data.data.reference]?.cached,
                  [data.data.stage]: data.data.cached
                }
              }
            }));
            break;

          case 'reference_complete':
            // Replace "Processing X..." with completion status
            if (data.data.success) {
              addStage(`Completed ${data.data.reference}.`, `Processing ${data.data.reference}`);
            } else {
              addStage(`Failed to process ${data.data.reference}.`, `Processing ${data.data.reference}`);
            }

            setReferenceStatus(prev => ({
              ...prev,
              [data.data.reference]: {
                ...prev[data.data.reference],
                status: data.data.success ? 'complete' : 'error',
                error: data.data.error
              }
            }));
            break;

          case 'processing_complete':
            addStage('All processing complete!');
            eventSource.close();
            break;

          case 'keepalive':
            // Just keep connection alive
            break;

          default:
            console.log('Unknown event type:', data.type);
        }
      } catch (error) {
        console.error('Error parsing SSE data:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [sessionId]);

  const getStageIcon = (stage, cached) => {
    if (cached) {
      return <Database className="w-4 h-4 text-green-400" />;
    }

    switch (stage) {
      case 'checking_cloud':
      case 'checking_cache':
        return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />;
      case 'fetching_online':
        return <Globe className="w-4 h-4 text-cyan-400 animate-pulse" />;
      case 'generating_law_summary':
      case 'generating_article_summary':
        return <Sparkles className="w-4 h-4 text-purple-400 animate-pulse" />;
      default:
        return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />;
    }
  };

  const getStageLabel = (stage) => {
    const labels = {
      'starting': 'Starting...',
      'checking_cloud': 'Checking cloud storage',
      'checking_cache': 'Checking cache',
      'fetching_online': 'Fetching law text online',
      'generating_law_summary': 'Generating law summary',
      'law_summary': 'Law summary ready',
      'generating_article_summary': 'Generating article summary'
    };
    return labels[stage] || stage;
  };

  return (
    <div
      className="fixed inset-0 flex items-center justify-center z-50"
      style={{
        backgroundImage: 'url("/background.jpg")',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
    >
      {/* Dark overlay */}
      <div className="absolute inset-0 bg-black/20"></div>

      {/* Progress card */}
      <div
        className="relative z-10 rounded-3xl p-8 w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col"
        style={{
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '2px solid rgba(255, 255, 255, 0.3)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
        }}
      >
        {/* Header */}
        <div className="flex flex-col items-center gap-4 mb-6 w-full">
          <div
            className="loader ease-linear rounded-full border-8 h-16 w-16"
            style={{
              borderColor: 'rgba(255, 255, 255, 0.3)',
              borderTopColor: 'rgba(255, 255, 255, 0.9)',
              boxShadow: '0 0 20px rgba(255, 255, 255, 0.2)'
            }}
          ></div>

          {/* Stage History */}
          <div className="w-full flex flex-col items-center space-y-1">
            {stageHistory.slice(-3).map((msg, idx) => {
              const isLast = idx === 2; // stageHistory.length - 1;
              return (
                <p
                  key={idx}
                  className={`text-center transition-all duration-300 ${isLast
                    ? 'text-xl font-semibold text-white drop-shadow-lg scale-105'
                    : 'text-sm text-white/60'
                    }`}
                >
                  {msg}
                </p>
              );
            })}
          </div>
        </div>

        {/* References sections */}
        <div className="flex-1 overflow-y-auto space-y-6 custom-scrollbar">
          {/* Explicit References */}
          {explicitRefs.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-cyan-300 uppercase tracking-wider flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                Explicit References ({explicitRefs.length})
              </h3>
              <div className="space-y-2">
                {explicitRefs.map((ref, idx) => (
                  <ReferenceItem
                    key={`explicit-${idx}`}
                    reference={ref}
                    status={referenceStatus[ref]}
                    getStageIcon={getStageIcon}
                    getStageLabel={getStageLabel}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Implicit References */}
          {implicitRefs.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-purple-300 uppercase tracking-wider flex items-center gap-2">
                <Sparkles className="w-4 h-4" />
                Implicit References ({implicitRefs.length})
              </h3>
              <div className="space-y-2">
                {implicitRefs.map((ref, idx) => (
                  <ReferenceItem
                    key={`implicit-${idx}`}
                    reference={ref}
                    status={referenceStatus[ref]}
                    getStageIcon={getStageIcon}
                    getStageLabel={getStageLabel}
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        <style jsx>{`
          .loader {
            animation: spin 1s linear infinite;
          }
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
          .custom-scrollbar::-webkit-scrollbar {
            width: 6px;
          }
          .custom-scrollbar::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 3px;
          }
          .custom-scrollbar::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 3px;
          }
          .custom-scrollbar::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.3);
          }
        `}</style>
      </div>
    </div>
  );
}

function ReferenceItem({ reference, status, getStageIcon, getStageLabel }) {
  if (!status) {
    return (
      <div className="bg-white/5 rounded-lg p-3 border border-white/10">
        <div className="text-white/80 text-sm font-mono">{reference}</div>
      </div>
    );
  }

  const isComplete = status.status === 'complete';
  const isError = status.status === 'error';

  return (
    <div className={`bg-white/5 rounded-lg p-3 border transition-all ${isComplete ? 'border-green-400/50' : isError ? 'border-red-400/50' : 'border-white/10'
      }`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="text-white/90 text-sm font-mono truncate mb-1">
            {reference}
          </div>
          {status.stage && !isComplete && !isError && (
            <div className="flex items-center gap-2 text-xs text-white/60">
              {getStageIcon(status.stage, status.cached?.[status.stage])}
              <span>{getStageLabel(status.stage)}</span>
              {status.cached?.[status.stage] && (
                <span className="text-green-400">(cached)</span>
              )}
            </div>
          )}
          {isError && status.error && (
            <div className="flex items-center gap-2 text-xs text-red-400">
              <AlertCircle className="w-4 h-4" />
              <span>{status.error}</span>
            </div>
          )}
        </div>
        <div className="flex-shrink-0">
          {isComplete && <CheckCircle className="w-5 h-5 text-green-400" />}
          {isError && <AlertCircle className="w-5 h-5 text-red-400" />}
          {!isComplete && !isError && <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />}
        </div>
      </div>
    </div>
  );
}

export default Loader;