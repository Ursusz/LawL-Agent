import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route} from 'react-router-dom';
import FileUpload from './components/FileUpload';
import Results from './components/Results';
import Loader from './components/Loader'
import './App.css';


function App() {
  const [loading, setLoading] = useState(false);

  return (
    <Router>
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-6">
        <h1 className="text-4xl font-extrabold mb-6">LawL Agent</h1>
        {loading ? (
          <Loader />
        ) : (
          <Routes>
            <Route path="/" element={<FileUpload setLoading={setLoading} />} />
            <Route path="/results" element={<Results />} />
          </Routes>
        )}
      </div>
    </Router>
  )
}

export default App;
