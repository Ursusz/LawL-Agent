import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Cloud } from 'lucide-react';

export default function FileUpload({ setLoading }) {
  const [dragActive, setDragActive] = useState(false);
  const navigate = useNavigate();

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = async (files) => {
    if (!files || files.length === 0) return;

    const formData = new FormData();
    Array.from(files).forEach(file => {
      formData.append('files', file);
    });

    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/search', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const results = await response.json();
      navigate('/results', { state: { results: results } });
    } catch (error) {
      console.error('Error sending files:', error);
      navigate('/results', { state: { error: 'An error occurred during upload.' } });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 flex flex-col items-center justify-center p-4 gap-8"
      style={{
        backgroundImage: 'url("/background.jpg")',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
    >
      {/* Dark overlay for better glass effect */}
      {/*<div className="absolute inset-0 bg-black/20"></div>*/}

      {/* Title with hover animation */}
      <div className="relative z-10">
        <h1 className="text-5xl font-bold text-white transition-all duration-300 hover:scale-110 hover:drop-shadow-lg cursor-default">
          LawL Agent
        </h1>
      </div>

      {/* Glassmorphic card - centered square */}
      <div
        className={`relative w-96 h-96 rounded-3xl transition-all duration-300 cursor-pointer ${
          dragActive
            ? 'bg-white/20 border-white/60 scale-105'
            : 'bg-white/10 border-white/20 hover:bg-white/15'
        }`}
        style={{
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '2px solid rgba(255, 255, 255, 0.3)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
        }}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
      >
        <input
          id="file-upload-input"
          type="file"
          multiple
          onChange={handleChange}
          className="hidden"
        />

        <label
          htmlFor="file-upload-input"
          className="flex flex-col items-center justify-center w-full h-full cursor-pointer"
        >
          <div className="text-center flex flex-col items-center justify-center">
            <Cloud className="w-16 h-16 mb-6 text-white/70" strokeWidth={1.5} />

            <h2 className="text-2xl font-bold text-white mb-3">Upload File</h2>

            <p className="text-white/80 text-sm mb-2">
              Drag your file here.
            </p>

            <p className="text-white/60 text-xs mb-4">
              or click to browse
            </p>

            <p className="text-cyan-300 text-xs font-medium">
              Supports: PNG, JPG, PDF, JPEG
            </p>
          </div>
        </label>
      </div>
    </div>
  );
}