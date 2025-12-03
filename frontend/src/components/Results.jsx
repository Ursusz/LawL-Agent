import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Copy, Check } from 'lucide-react';

function parse_law_title(law_title) {
  return (law_title.charAt(0).toUpperCase() + law_title.slice(1).toLowerCase()).replace('_', ' ').replace(/_/g, '/')
}

function renderTextWithLinks(text) {
  if (!text) return null;

  // Regex to find URLs (starting with http/https)
  const urlRegex = /(https?:\/\/[^\s]+)/g;

  const parts = text.split(urlRegex);

  return parts.map((part, index) => {
    if (part.match(urlRegex)) {
      return (
        <a
          key={index}
          href={part}
          target="_blank"
          rel="noreferrer"
          className="text-blue-400 hover:text-blue-300 underline break-all"
          onClick={(e) => e.stopPropagation()} // Prevent parent click handlers
        >
          {part}
        </a>
      );
    }
    return part;
  });
}

function Results() {
  const location = useLocation();
  const { results, extractedText } = location.state || {};
  const navigate = useNavigate();
  const [openFile, setOpenFile] = useState({});
  const [openLaw, setOpenLaw] = useState({});
  const [openLawText, setOpenLawText] = useState({});
  const [openArticle, setOpenArticle] = useState({});
  const [openSummaryArticle, setOpenSummaryArticle] = useState({});
  const [openLawSummary, setOpenLawSummary] = useState({});
  const [openLawSimplified, setOpenLawSimplified] = useState({});
  const [openUrlSource, setOpenUrlSource] = useState({});
  const [openExtractedText, setOpenExtractedText] = useState({});
  const [copiedStates, setCopiedStates] = useState({});

  const handleCopy = async (text, key) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedStates({ ...copiedStates, [key]: true });
      setTimeout(() => {
        setCopiedStates(prev => ({ ...prev, [key]: false }));
      }, 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleCopyAllReferences = async (item) => {
    if (!item.law_details) return;

    let allText = '';
    Object.entries(item.law_details).forEach(([lawRef, law_details]) => {
      if (law_details.ERROR) return;

      allText += `# ${parse_law_title(lawRef)}\n\n`;

      if (law_details.law) {
        allText += `## ⚖️ Lege\n${law_details.law}\n\n`;
      }
      if (law_details.law_summary) {
        allText += `## 📋 Sumar Lege\n${law_details.law_summary}\n\n`;
      }
      if (law_details.relevant_article) {
        allText += `## 📜 Articol Relevant\n${law_details.relevant_article}\n\n`;
      }
      if (law_details.articles_summary) {
        allText += `## ✏️ Sumar Articol\n${law_details.articles_summary}\n\n`;
      }
      if (law_details.law_simplified) {
        allText += `## 🙂 Lege Simplificata\n${law_details.law_simplified}\n\n`;
      }

      allText += '---\n\n';
    });

    await handleCopy(allText.trim(), `all-${item.filename}`);
  };

  return (
    <div
      className="fixed inset-0 overflow-y-auto"
      style={{
        backgroundImage: 'url("/background.jpg")',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundAttachment: 'fixed',
      }}
    >
      {/* Dark overlay */}
      <div className="absolute inset-0 bg-black/20 pointer-events-none"></div>

      {/* Content wrapper */}
      <div className="relative z-10 min-h-screen flex flex-col">
        <div className="flex-1 p-6">
          {/* Home Button */}
          <button
            onClick={() => navigate('/')}
            style={{ backgroundColor: 'hsla(138, 29%, 25%, 1)' }}
            className="fixed top-4 right-4 font-semibold text-lg text-white rounded-lg px-4 py-2 hover:opacity-90 transition-opacity z-20"
          >
            Home
          </button>

          {/* Alert Box */}
          <div
            className="border-l-4 text-white p-4 mb-6 max-w-6xl mx-auto rounded-md"
            style={{
              backgroundColor: 'hsla(33, 49%, 25%, 0.95)',
              backdropFilter: 'blur(10px)',
              borderLeftColor: 'hsla(138, 29%, 25%, 1)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
            role="alert"
          >
            <p className="font-bold text-center text-lg">Atenție!</p>
            <p className="text-sm text-center mt-2">
              Acest instrument folosește inteligența artificială pentru a procesa și a sumariza informații.
              Ca orice instrument de acest tip, poate conține erori și omisiuni.
              Informațiile prezentate aici nu înlocuiesc o documentare juridică aprofundată și nu au valoare legală.
              Nu ne asumăm responsabilitatea pentru acuratețea datelor furnizate.
            </p>
          </div>

          {/* Results Container */}
          {results ? (
            <div className="space-y-4 max-w-6xl mx-auto">
              <h2 className="text-3xl font-bold mb-6 text-white drop-shadow-lg" style={{ color: 'hsla(33, 49%, 25%, 1)' }}>
                Referințe legale găsite:
              </h2>

              {results.map((item, i) => (
                <div
                  key={i}
                  className="rounded-xl overflow-hidden transition-shadow hover:shadow-lg"
                  style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                  }}
                >
                  {/* File Header */}
                  <div className="flex items-center border-b border-white/20">
                    <button
                      className="flex-1 text-left font-bold text-xl px-6 py-4 transition-colors"
                      style={{
                        backgroundColor: 'hsla(33, 49%, 25%, 0.1)',
                        color: 'hsla(33, 49%, 25%, 1)'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'hsla(33, 49%, 25%, 0.15)'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'hsla(33, 49%, 25%, 0.1)'}
                      onClick={() => setOpenFile({ ...openFile, [i]: !openFile[i] })}
                    >
                      📄 {item.originalFileName || item.filename}
                    </button>
                    {item.law_details && Object.keys(item.law_details).length > 0 && (
                      <button
                        onClick={() => handleCopyAllReferences(item)}
                        className="px-4 py-4 transition-colors"
                        style={{
                          backgroundColor: 'hsla(33, 49%, 25%, 0.1)',
                          color: 'hsla(33, 49%, 25%, 1)'
                        }}
                      >
                        {copiedStates[`all-${item.filename}`] ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
                      </button>
                    )}
                  </div>

                  {/* File Content */}
                  {openFile[i] && (
                    <div className="p-6 space-y-4">
                      {/* Extracted Text Sub-dropdown */}
                      {extractedText && (
                        <div className="rounded-lg overflow-hidden" style={{ border: '1px solid hsla(138, 29%, 25%, 0.3)' }}>
                          <div className="flex items-center">
                            <button
                              className="flex-1 text-left font-semibold px-4 py-3 transition-colors duration-200"
                              style={{
                                backgroundColor: 'hsla(138, 29%, 25%, 0.15)',
                                color: 'hsla(33, 49%, 25%, 1)'
                              }}
                              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'hsla(138, 29%, 25%, 0.25)'}
                              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'hsla(138, 29%, 25%, 0.15)'}
                              onClick={() => setOpenExtractedText({ ...openExtractedText, [i]: !openExtractedText[i] })}
                            >
                              📝 Extracted Text Preview
                            </button>
                            <button
                              onClick={() => handleCopy(extractedText, `extracted-text-${i}`)}
                              className="px-3 py-3 transition-colors"
                              style={{
                                backgroundColor: 'hsla(138, 29%, 25%, 0.15)',
                                color: 'hsla(33, 49%, 25%, 1)'
                              }}
                            >
                              {copiedStates[`extracted-text-${i}`] ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                            </button>
                          </div>
                          {openExtractedText[i] && (
                            <div className="p-4" style={{ backgroundColor: 'hsla(138, 29%, 25%, 0.08)' }}>
                              <pre className="whitespace-pre-wrap font-mono text-sm" style={{ color: 'hsla(30, 5%, 43%, 1)' }}>
                                {extractedText}
                              </pre>
                            </div>
                          )}
                        </div>
                      )}

                      {/* References Section */}
                      {item.references?.length > 0 && (
                        <p className="text-sm" style={{ color: 'hsla(30, 5%, 43%, 1)' }}>
                          <span className="font-semibold">Referințe:</span> {item.references.map(ref => parse_law_title(ref)).join(', ')}
                        </p>
                      )}

                      {/* Law Details */}
                      {item.law_details && Object.keys(item.law_details).length > 0 ? (
                        <div className="space-y-3">
                          {Object.entries(item.law_details).map(([lawRef, law_details]) => (
                            <div key={lawRef} className="rounded-lg overflow-hidden" style={{ border: '1px solid hsla(138, 29%, 25%, 0.3)' }}>
                              <div className="flex items-center">
                                <button
                                  className="flex-1 text-left font-semibold px-4 py-3 transition-colors duration-200"
                                  style={{
                                    backgroundColor: 'hsla(138, 29%, 25%, 0.15)',
                                    color: 'hsla(33, 49%, 25%, 1)'
                                  }}
                                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'hsla(138, 29%, 25%, 0.25)'}
                                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'hsla(138, 29%, 25%, 0.15)'}
                                  onClick={() => setOpenLaw(openLaw === lawRef ? null : lawRef)}
                                >
                                  📜 {parse_law_title(lawRef)}
                                </button>
                                {!law_details.ERROR && (
                                  <button
                                    onClick={() => {
                                      const lawText = `# ${parse_law_title(lawRef)}\n\n` +
                                        (law_details.law ? `## ⚖️ Lege\n${law_details.law}\n\n` : '') +
                                        (law_details.law_summary ? `## 📋 Sumar Lege\n${law_details.law_summary}\n\n` : '') +
                                        (law_details.relevant_article ? `## 📜 Articol Relevant\n${law_details.relevant_article}\n\n` : '') +
                                        (law_details.articles_summary ? `## ✏️ Sumar Articol\n${law_details.articles_summary}\n\n` : '') +
                                        (law_details.law_simplified ? `## 🙂 Lege Simplificata\n${law_details.law_simplified}` : '');
                                      handleCopy(lawText.trim(), `law-${lawRef}`);
                                    }}
                                    className="px-3 py-3 transition-colors"
                                    style={{
                                      backgroundColor: 'hsla(138, 29%, 25%, 0.15)',
                                      color: 'hsla(33, 49%, 25%, 1)'
                                    }}
                                  >
                                    {copiedStates[`law-${lawRef}`] ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                  </button>
                                )}
                              </div>

                              {openLaw === lawRef && (
                                <div className="p-4 space-y-2" style={{ backgroundColor: 'hsla(138, 29%, 25%, 0.08)' }}>
                                  {law_details.ERROR ? (
                                    <div
                                      className="p-4 rounded text-white font-semibold"
                                      style={{ backgroundColor: 'hsla(0, 100%, 50%, 0.8)' }}
                                    >
                                      EROARE GEMINI: {law_details.ERROR}
                                    </div>
                                  ) : (
                                    <>
                                      {/* Url sursa lege */}
                                      <button
                                        className="w-full text-left font-semibold px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded"
                                        onClick={() => setOpenUrlSource({
                                          ...openUrlSource,
                                          [lawRef]: !openUrlSource[lawRef]
                                        })}
                                      >
                                        🔗 URL
                                      </button>
                                      {openUrlSource[lawRef] && (
                                        <div className="ml-4 mt-1 space-y-1">
                                          <p className='p-4 bg-gray-300 rounded text-justify'>
                                            {law_details?.url ? (
                                              <a href={law_details.url} target="_blank" rel="noreferrer">
                                                {law_details.url}
                                              </a>
                                            ) : 'No url available'}
                                          </p>
                                        </div>
                                      )}

                                      {/* Full Law Text */}
                                      <div className="flex items-center gap-2">
                                        <button
                                          className="flex-1 text-left font-semibold px-3 py-2 rounded transition-colors"
                                          style={{
                                            backgroundColor: 'hsla(30, 5%, 43%, 0.15)',
                                            color: 'hsla(33, 49%, 25%, 1)'
                                          }}
                                          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'hsla(30, 5%, 43%, 0.25)'}
                                          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'hsla(30, 5%, 43%, 0.15)'}
                                          onClick={() => setOpenLawText({
                                            ...openLawText,
                                            [lawRef]: !openLawText[lawRef]
                                          })}
                                        >
                                          ⚖️ Lege
                                        </button>
                                        <button
                                          onClick={() => handleCopy(law_details.law, `lawText-${lawRef}`)}
                                          className="px-2 py-2 rounded transition-colors"
                                          style={{
                                            backgroundColor: 'hsla(30, 5%, 43%, 0.15)',
                                            color: 'hsla(33, 49%, 25%, 1)'
                                          }}
                                        >
                                          {copiedStates[`lawText-${lawRef}`] ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                        </button>
                                      </div>
                                      {openLawText[lawRef] && (
                                        <div className="ml-4 mt-2 p-4 rounded text-justify max-h-96 overflow-y-auto" style={{ backgroundColor: 'hsla(30, 5%, 43%, 0.1)' }}>
                                          <p style={{ color: 'hsla(30, 5%, 43%, 1)', whiteSpace: 'pre-wrap' }}>
                                            {renderTextWithLinks(law_details.law)}
                                          </p>
                                        </div>
                                      )}

                                      {/* Law Summary */}
                                      <div className="flex items-center gap-2">
                                        <button
                                          className="flex-1 text-left font-semibold px-3 py-2 rounded transition-colors"
                                          style={{
                                            backgroundColor: 'hsla(138, 29%, 25%, 0.2)',
                                            color: 'hsla(33, 49%, 25%, 1)'
                                          }}
                                          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'hsla(138, 29%, 25%, 0.3)'}
                                          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'hsla(138, 29%, 25%, 0.2)'}
                                          onClick={() => setOpenLawSummary({
                                            ...openLawSummary,
                                            [lawRef]: !openLawSummary[lawRef]
                                          })}
                                        >
                                          📋 Sumar Lege
                                        </button>
                                        <button
                                          onClick={() => handleCopy(law_details.law_summary, `lawSummary-${lawRef}`)}
                                          className="px-2 py-2 rounded transition-colors"
                                          style={{
                                            backgroundColor: 'hsla(138, 29%, 25%, 0.2)',
                                            color: 'hsla(33, 49%, 25%, 1)'
                                          }}
                                        >
                                          {copiedStates[`lawSummary-${lawRef}`] ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                        </button>
                                      </div>
                                      {openLawSummary[lawRef] && (
                                        <div className="ml-4 mt-2 p-4 rounded text-justify max-h-96 overflow-y-auto" style={{ backgroundColor: 'hsla(138, 29%, 25%, 0.1)' }}>
                                          <p style={{ color: 'hsla(30, 5%, 43%, 1)' }}>
                                            {law_details.law_summary}
                                          </p>
                                        </div>
                                      )}

                                      {/* Relevant Articles (Top 5) */}
                                      <div className="flex items-center gap-2">
                                        <button
                                          className="flex-1 text-left font-semibold px-3 py-2 rounded transition-colors"
                                          style={{
                                            backgroundColor: 'hsla(30, 5%, 43%, 0.15)',
                                            color: 'hsla(33, 49%, 25%, 1)'
                                          }}
                                          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'hsla(30, 5%, 43%, 0.25)'}
                                          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'hsla(30, 5%, 43%, 0.15)'}
                                          onClick={() => setOpenArticle({
                                            ...openArticle,
                                            [lawRef]: !openArticle[lawRef]
                                          })}
                                        >
                                          📜 Articole Relevante (Top 5)
                                        </button>
                                        <button
                                          onClick={() => {
                                            const allArticles = law_details.relevant_articles
                                              ?.map((art, idx) => `${idx + 1}. [Score: ${art.score.toFixed(2)}]\n${art.text}`)
                                              .join('\n\n---\n\n') || law_details.relevant_article || '';
                                            handleCopy(allArticles, `article-${lawRef}`);
                                          }}
                                          className="px-2 py-2 rounded transition-colors"
                                          style={{
                                            backgroundColor: 'hsla(30, 5%, 43%, 0.15)',
                                            color: 'hsla(33, 49%, 25%, 1)'
                                          }}
                                        >
                                          {copiedStates[`article-${lawRef}`] ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                        </button>
                                      </div>
                                      {openArticle[lawRef] && (
                                        <div className="ml-4 mt-2 space-y-3 max-h-96 overflow-y-auto">
                                          {law_details.relevant_articles && law_details.relevant_articles.length > 0 ? (
                                            law_details.relevant_articles.map((article, idx) => (
                                              <div
                                                key={idx}
                                                className="p-4 rounded text-justify"
                                                style={{
                                                  backgroundColor: idx === 0 ? 'hsla(30, 5%, 43%, 0.15)' : 'hsla(30, 5%, 43%, 0.1)',
                                                  border: idx === 0 ? '2px solid hsla(33, 49%, 25%, 0.3)' : 'none'
                                                }}
                                              >
                                                <div className="flex items-center justify-between mb-2">
                                                  <span className="font-semibold text-sm" style={{ color: 'hsla(33, 49%, 25%, 1)' }}>
                                                    #{idx + 1} {idx === 0 && '(Folosit pentru sumar)'}
                                                  </span>
                                                  <span
                                                    className="px-2 py-1 rounded text-xs font-mono"
                                                    style={{
                                                      backgroundColor: 'hsla(138, 29%, 25%, 0.2)',
                                                      color: 'hsla(33, 49%, 25%, 1)'
                                                    }}
                                                  >
                                                    Score: {article.score.toFixed(2)}
                                                  </span>
                                                </div>
                                                <p style={{ color: 'hsla(30, 5%, 43%, 1)' }}>
                                                  {article.text}
                                                  {article.text.includes('(din Anexa)') && (
                                                    <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                                      Anexă
                                                    </span>
                                                  )}
                                                </p>
                                              </div>
                                            ))
                                          ) : (
                                            <div className="p-4 rounded text-justify" style={{ backgroundColor: 'hsla(30, 5%, 43%, 0.1)' }}>
                                              <p style={{ color: 'hsla(30, 5%, 43%, 1)' }}>
                                                {law_details.relevant_article || 'No relevant articles found.'}
                                              </p>
                                            </div>
                                          )}
                                        </div>
                                      )}

                                      {/* Article Summary */}
                                      <div className="flex items-center gap-2">
                                        <button
                                          className="flex-1 text-left font-semibold px-3 py-2 rounded transition-colors"
                                          style={{
                                            backgroundColor: 'hsla(138, 29%, 25%, 0.2)',
                                            color: 'hsla(33, 49%, 25%, 1)'
                                          }}
                                          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'hsla(138, 29%, 25%, 0.3)'}
                                          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'hsla(138, 29%, 25%, 0.2)'}
                                          onClick={() => setOpenSummaryArticle({
                                            ...openSummaryArticle,
                                            [lawRef]: !openSummaryArticle[lawRef]
                                          })}
                                        >
                                          ✏️ Sumar Articol
                                        </button>
                                        <button
                                          onClick={() => handleCopy(law_details.articles_summary, `articleSummary-${lawRef}`)}
                                          className="px-2 py-2 rounded transition-colors"
                                          style={{
                                            backgroundColor: 'hsla(138, 29%, 25%, 0.2)',
                                            color: 'hsla(33, 49%, 25%, 1)'
                                          }}
                                        >
                                          {copiedStates[`articleSummary-${lawRef}`] ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                        </button>
                                      </div>
                                      {openSummaryArticle[lawRef] && (
                                        <div className="ml-4 mt-2 p-4 rounded text-justify max-h-96 overflow-y-auto" style={{ backgroundColor: 'hsla(138, 29%, 25%, 0.1)' }}>
                                          <p style={{ color: 'hsla(30, 5%, 43%, 1)' }}>
                                            {law_details.articles_summary}
                                          </p>
                                        </div>
                                      )}

                                      {/* Simplified Law */}
                                      <div className="flex items-center gap-2">
                                        <button
                                          className="flex-1 text-left font-semibold px-3 py-2 rounded transition-colors"
                                          style={{
                                            backgroundColor: 'hsla(138, 29%, 25%, 0.3)',
                                            color: 'hsla(225, 100%, 99%, 1)'
                                          }}
                                          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'hsla(138, 29%, 25%, 0.4)'}
                                          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'hsla(138, 29%, 25%, 0.3)'}
                                          onClick={() => setOpenLawSimplified({
                                            ...openLawSimplified,
                                            [lawRef]: !openLawSimplified[lawRef]
                                          })}
                                        >
                                          🙂 Lege Simplificata
                                        </button>
                                        <button
                                          onClick={() => handleCopy(law_details.law_simplified, `lawSimplified-${lawRef}`)}
                                          className="px-2 py-2 rounded transition-colors"
                                          style={{
                                            backgroundColor: 'hsla(138, 29%, 25%, 0.3)',
                                            color: 'hsla(225, 100%, 99%, 1)'
                                          }}
                                        >
                                          {copiedStates[`lawSimplified-${lawRef}`] ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                        </button>
                                      </div>
                                      {openLawSimplified[lawRef] && (
                                        <div className="ml-4 mt-2 p-4 rounded text-justify max-h-96 overflow-y-auto" style={{ backgroundColor: 'hsla(138, 29%, 25%, 0.15)' }}>
                                          <p style={{ color: 'hsla(225, 100%, 99%, 1)' }}>
                                            {law_details.law_simplified}
                                          </p>
                                        </div>
                                      )}
                                    </>
                                  )}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <span className="text-lg font-semibold" style={{ color: 'hsla(33, 49%, 25%, 1)' }}>
                          {item.error || 'No references have been processed.'}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center min-h-[300px]">
              <div
                className="p-8 text-white rounded-lg shadow-lg"
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  backdropFilter: 'blur(20px)',
                  WebkitBackdropFilter: 'blur(20px)',
                  border: '2px solid rgba(255, 255, 255, 0.3)',
                  boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                }}
              >
                <p className="text-lg font-semibold">No results have been found.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Results;
