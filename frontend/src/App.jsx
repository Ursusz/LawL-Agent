import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import './App.css';

function App() {
  const [results, setResults] = useState(null);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-6">
      <h1 className="text-4xl font-extrabold mb-6">LawL Agent</h1>

      <FileUpload setResults={setResults} />

      {results && (
        <div className="p-6 bg-green-500 text-white rounded-lg mt-6 w-full max-w-lg shadow-lg">
          <h2 className="text-2xl font-semibold mb-2">Results:</h2>
          <ul className="list-disc pl-5">
            {results.map((item, i) => (
              <li key={i}>
                <strong>{item.filename}</strong>:
                <br />
                {item.references && item.references.length > 0 && (
                  <>
                    <p>Referinte gasite: {item.references.join(', ')}</p>
                  </>
                )}
                {item.law_details && Object.keys(item.law_details).length > 0 ? (
                  <ul>
                    {Object.entries(item.law_details).map(([lawRef, lawDetails]) => (
                      <li key={lawRef} className="mt-2">
                        <strong>{lawRef}</strong>: {lawDetails}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <span> {item.error || 'No refference has been found or processed.'}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;
