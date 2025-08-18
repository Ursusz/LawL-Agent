import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom'

function FileUpload({ setLoading }) {
  const [dragActive, setDragActive] = useState(false);
  const navigate = useNavigate();

  const handleFiles = async (files) => {
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
      console.error("Error sending files:", error);
      navigate('/results', { state: { error: "An error occured during upload." } })
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
      onDragLeave={(e) => { e.preventDefault(); setDragActive(false); }}
      onDrop={handleDrop}
      className={`w-full max-w-lg h-48 flex flex-col items-center justify-center border-4 border-dashed rounded-lg
        ${dragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300 bg-white'} transition-colors`}
    >

      <input
        id="file-upload-input"
        type="file"
        multiple
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />

      <label
        htmlFor="file-upload-input"
        className="cursor-pointer px-4 py-2 w-full max-w-lg h-48 flex flex-row items-center justify-center"
      >
        <p className="text-gray-500 mb-2">Click or drag files to upload</p>
      </label>
    </div>
  );
}

export default FileUpload;