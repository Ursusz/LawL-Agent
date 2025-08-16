import React from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

function Results() {
    const location = useLocation();
    const { results } = location.state || {};
    const navigate = useNavigate();

    return (
        <div>
            <button onClick={() => navigate('/')}><p className='font-semibold mb-2 text-2xl absolute top-4 right-4 bg-green-500 text-white rounded-lg pl-1 pr-1'>Home</p></button>
            {results ? (
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
                                    <span> {item.error || 'No reference has been found or processed.'}</span>
                                )}
                            </li>
                        ))}
                    </ul>
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