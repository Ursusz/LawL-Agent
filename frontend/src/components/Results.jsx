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
  const [openUrlSource, setOpenUrlSource] = useState({});

  return (
    <div className="p-6">
      <button
        onClick={() => navigate('/')}
        className="font-semibold text-lg absolute top-4 right-4 bg-green-500 text-white rounded-lg px-3 py-1"
      >
        Home
      </button>

      <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-1000 p-4 mb-6 max-w-6xl mx-auto" role="alert">
        <p className="font-bold text-center text-lg">Atenție!</p>
        <p className="text-sm text-center">
          Acest instrument folosește inteligența artificială pentru a procesa și a sumariza informații.
          Ca orice instrument de acest tip, poate conține erori și omisiuni.
          Informațiile prezentate aici nu înlocuiesc o documentare juridică aprofundată și nu au valoare legală.
          Nu ne asumăm responsabilitatea pentru acuratețea datelor furnizate.
        </p>
      </div>

      {results ? (
        <div className="space-y-4 max-w-6xl mx-auto">
          <h2 className="text-2xl font-semibold">Referințe legale găsite:</h2>

          {results.map((item, i) => (
            <div key={i} className="bg-white shadow-md rounded-xl p-4">
              <h3 className="font-bold text-lg mb-2">{item.filename}</h3>

              {item.references?.length > 0 && (
                <p className="text-sm text-gray-600 mb-2">
                  Referințe: {item.references.map(ref => parse_law_title(ref)).join(', ')}
                </p>
              )}

              {item.law_details && Object.keys(item.law_details).length > 0 ? (
                <div className="space-y-2">
                  {Object.entries(item.law_details).map(([lawRef, law_details]) => (
                    <div key={lawRef} className="border rounded-lg p-2">
                      <button
                        className="w-full text-left font-semibold px-3 py-2 bg-green-100 hover:bg-green-200 rounded-lg"
                        onClick={() => setOpenLaw(openLaw === lawRef ? null : lawRef)}
                      >
                        🔎 {parse_law_title(lawRef)}
                      </button>

                      {openLaw === lawRef && (
                        <div className="p-3 bg-blue-200 rounded-b-lg ml-2 mt-2 space-y-2">
                          {law_details.ERROR ? (
                            <div className="p-4 bg-red-200 text-red-800 rounded">
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
                              {/* Text de lege intreg */}
                              <button
                                className="w-full text-left font-semibold px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded"
                                onClick={() => setOpenLawText({
                                  ...openLawText,
                                  [lawRef]: !openLawText[lawRef]
                                })}
                              >
                                ⚖️ Lege
                              </button>
                              {openLawText[lawRef] && (
                                <div className="ml-4 mt-1 space-y-1">
                                  <p className='p-4 bg-gray-300 rounded text-justify'>
                                    {law_details.law}
                                  </p>
                                </div>
                              )}

                              {/* Text de lege sumarizat */}
                              <button
                                className="w-full text-left font-semibold px-2 py-1 bg-emerald-100 hover:bg-emerald-200 rounded"
                                onClick={() => setOpenLawSummary({
                                  ...openLawSummary,
                                  [lawRef]: !openLawSummary[lawRef]
                                })}
                              >
                                🔎 Sumar Lege
                              </button>
                              {openLawSummary[lawRef] && (
                                <div className="ml-4 mt-1 space-y-1">
                                  <p className='p-4 bg-gray-300 rounded text-justify'>
                                    {law_details.law_summary}
                                  </p>
                                </div>
                              )}

                              {/* Articolul cel mai relevant */}
                              <button
                                className="w-full text-left font-semibold px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded"
                                onClick={() => setOpenArticle({
                                  ...openArticle,
                                  [lawRef]: !openArticle[lawRef]
                                })}
                              >
                                📜 Articol Relevant
                              </button>
                              {openArticle[lawRef] && (
                                <div className="ml-4 mt-1 space-y-1">
                                  <p className='p-4 bg-gray-300 rounded text-justify'>
                                    {law_details.relevant_article}
                                  </p>
                                </div>
                              )}

                              {/* Sumarul articolului cel mai relevant */}
                              <button
                                className="w-full text-left font-semibold px-2 py-1 bg-emerald-100 hover:bg-emerald-200 rounded"
                                onClick={() => setOpenSummaryArticle({
                                  ...openSummaryArticle,
                                  [lawRef]: !openSummaryArticle[lawRef]
                                })}
                              >
                                ✍️ Sumar Articol
                              </button>
                              {openSummaryArticle[lawRef] && (
                                <div className="ml-4 mt-1 space-y-1">
                                  <p className='p-4 bg-gray-300 rounded text-justify'>
                                    {law_details.articles_summary}
                                  </p>
                                </div>
                              )}

                              {/* Lege simplificata */}
                              <button
                                className="w-full text-left font-semibold px-2 py-1 bg-green-300 hover:bg-green-400 rounded"
                                onClick={() => setOpenLawSimplified({
                                  ...openLawSimplified,
                                  [lawRef]: !openLawSimplified[lawRef]
                                })}
                              >
                                🙂 Lege Simplificata
                              </button>
                              {openLawSimplified[lawRef] && (
                                <div className="ml-4 mt-1 space-y-1">
                                  <p className='p-4 bg-gray-300 rounded text-justify'>
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
                <span className="text-red-500">
                  {item.error || 'No references have been processed.'}
                </span>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="p-6 bg-red-500 text-white rounded-lg mt-6 w-full max-w-lg shadow-lg">
          No results have been found.
        </div>
      )}
    </div>
  );
}

export default Results;