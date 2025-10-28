import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

function parse_law_title(law_title) {
  return (law_title.charAt(0).toUpperCase() + law_title.slice(1).toLowerCase()).replace('_', ' ').replace(/_/g, '/')
}

function Results() {
  const location = useLocation();
  const { results } = location.state || {};
  const navigate = useNavigate();
  const [openLaw, setOpenLaw] = useState({});
  const [openLawText, setOpenLawText] = useState({});
  const [openArticle, setOpenArticle] = useState({});
  const [openSummaryArticle, setOpenSummaryArticle] = useState({});
  const [openLawSummary, setOpenLawSummary] = useState({});
  const [openLawSimplified, setOpenLawSimplified] = useState({});

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
                  className="rounded-xl p-6 transition-shadow hover:shadow-lg"
                  style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                  }}
                >
                  <h3 className="font-bold text-xl mb-3" style={{ color: 'hsla(33, 49%, 25%, 1)' }}>
                    {item.filename}
                  </h3>

                  {item.references?.length > 0 && (
                    <p className="text-sm mb-4" style={{ color: 'hsla(30, 5%, 43%, 1)' }}>
                      <span className="font-semibold">Referințe:</span> {item.references.map(ref => parse_law_title(ref)).join(', ')}
                    </p>
                  )}

                  {item.law_details && Object.keys(item.law_details).length > 0 ? (
                    <div className="space-y-3">
                      {Object.entries(item.law_details).map(([lawRef, law_details]) => (
                        <div key={lawRef} className="rounded-lg overflow-hidden" style={{ border: '1px solid hsla(138, 29%, 25%, 0.3)' }}>
                          <button
                            className="w-full text-left font-semibold px-4 py-3 transition-colors duration-200"
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
                                  {/* Full Law Text */}
                                  <button
                                    className="w-full text-left font-semibold px-3 py-2 rounded transition-colors"
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
                                  {openLawText[lawRef] && (
                                    <div className="ml-4 mt-2 p-4 rounded text-justify" style={{ backgroundColor: 'hsla(30, 5%, 43%, 0.1)' }}>
                                      <p style={{ color: 'hsla(30, 5%, 43%, 1)' }}>
                                        {law_details.law}
                                      </p>
                                    </div>
                                  )}

                                  {/* Law Summary */}
                                  <button
                                    className="w-full text-left font-semibold px-3 py-2 rounded transition-colors"
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
                                  {openLawSummary[lawRef] && (
                                    <div className="ml-4 mt-2 p-4 rounded text-justify" style={{ backgroundColor: 'hsla(138, 29%, 25%, 0.1)' }}>
                                      <p style={{ color: 'hsla(30, 5%, 43%, 1)' }}>
                                        {law_details.law_summary}
                                      </p>
                                    </div>
                                  )}

                                  {/* Most Relevant Article */}
                                  <button
                                    className="w-full text-left font-semibold px-3 py-2 rounded transition-colors"
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
                                    📜 Articol Relevant
                                  </button>
                                  {openArticle[lawRef] && (
                                    <div className="ml-4 mt-2 p-4 rounded text-justify" style={{ backgroundColor: 'hsla(30, 5%, 43%, 0.1)' }}>
                                      <p style={{ color: 'hsla(30, 5%, 43%, 1)' }}>
                                        {law_details.relevant_article}
                                      </p>
                                    </div>
                                  )}

                                  {/* Article Summary */}
                                  <button
                                    className="w-full text-left font-semibold px-3 py-2 rounded transition-colors"
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
                                  {openSummaryArticle[lawRef] && (
                                    <div className="ml-4 mt-2 p-4 rounded text-justify" style={{ backgroundColor: 'hsla(138, 29%, 25%, 0.1)' }}>
                                      <p style={{ color: 'hsla(30, 5%, 43%, 1)' }}>
                                        {law_details.articles_summary}
                                      </p>
                                    </div>
                                  )}

                                  {/* Simplified Law */}
                                  <button
                                    className="w-full text-left font-semibold px-3 py-2 rounded transition-colors"
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
                                  {openLawSimplified[lawRef] && (
                                    <div className="ml-4 mt-2 p-4 rounded text-justify" style={{ backgroundColor: 'hsla(138, 29%, 25%, 0.15)' }}>
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