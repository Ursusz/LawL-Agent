import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route} from 'react-router-dom';
import FileUpload from './components/FileUpload';
import Results from './components/Results';
import './App.css';


function App() {
  return (
    <Router>
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-6">
        <h1 className="text-4xl font-extrabold mb-6">LawL Agent</h1>
        <Routes>
          <Route path="/" element={<FileUpload />} />
          
          <Route path="/results" element={<Results />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App;
