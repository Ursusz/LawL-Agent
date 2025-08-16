import React, { useState } from 'react';

function FileUpload({ setResults }) {
  const [dragActive, setDragActive] = useState(false);

  const handleFiles = async (files) => {
    const formData = new FormData();
    Array.from(files).forEach(file => {
        formData.append('files', file);
    });

    try {
        const response = await fetch('http://localhost:8000/search', {
            method: 'POST',
            body: formData,
    });

    if (!response.ok) {
      throw new Error(`Eroare HTTP! Status: ${response.status}`);
    }

    const results = await response.json();
    setResults(results);
  } catch (error) {
    console.error("Error sending files:", error);
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
      <p className="text-gray-500 mb-2">Click or drag files to upload</p>
      <input
        type="file"
        multiple
        className="absolute w-full h-full opacity-0 cursor-pointer"
        onChange={(e) => handleFiles(e.target.files)}
      />
    </div>
  );
}

export default FileUpload;