import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Cloud, X, Check, FileText, Edit2 } from 'lucide-react';
import { extractContent, redactPII } from '../utils/fileProcessor';

export default function FileUpload({ setLoading }) {
  const [dragActive, setDragActive] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [currentFile, setCurrentFile] = useState(null);
  const [extractedText, setExtractedText] = useState('');
  const [originalFileName, setOriginalFileName] = useState('');

  const navigate = useNavigate();

  useEffect(() => {
    console.log('[FileUpload] reviewing changed to:', reviewing);
    console.log('[FileUpload] extractedText length:', extractedText?.length);
  }, [reviewing, extractedText]);

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

    const file = files[0];
    setOriginalFileName(file.name);

    try {
      setProcessing(true);
      setLoading(true);
      console.log('[FileUpload] Starting extraction');

      const text = await extractContent(file);
      const redacted = redactPII(text);
      console.log('[FileUpload] Extraction complete, text length:', redacted?.length);

      setProcessing(false);
      setExtractedText(redacted);
      setCurrentFile(file);
      setLoading(false);

      // Use setTimeout to ensure state updates are processed
      setTimeout(() => {
        console.log('[FileUpload] Setting reviewing to true');
        setReviewing(true);
      }, 100);

    } catch (error) {
      console.error('[FileUpload] Error:', error);
      alert(`Error processing file: ${error.message}`);
      setProcessing(false);
      setLoading(false);
    }
  };

  const handleConfirmUpload = async () => {
    if (!extractedText) return;

    try {
      setLoading(true);

      const timestamp = new Date().getTime();
      const newFileName = `upload_${timestamp}.txt`;
      const newFile = new File([extractedText], newFileName, { type: 'text/plain' });

      const formData = new FormData();
      formData.append('files', newFile);

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
      setReviewing(false);
    }
  };

  const handleCancelReview = () => {
    setReviewing(false);
    setExtractedText('');
    setCurrentFile(null);
    setLoading(false);
  };

  console.log('[FileUpload] Render - reviewing:', reviewing, 'extractedText length:', extractedText?.length);

  return (
    <div
      className="fixed inset-0 flex flex-col items-center justify-center p-4 gap-8"
      style={{
        backgroundImage: 'url("/background.jpg")',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
    >
      <div className="relative z-10">
        <h1 className="text-5xl font-bold text-white transition-all duration-300 hover:scale-110 hover:drop-shadow-lg cursor-default">
          LawL Agent
        </h1>
      </div>

      {!reviewing && (
        <div
          className={`relative w-96 h-96 rounded-3xl transition-all duration-300 cursor-pointer ${dragActive
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
            onChange={handleChange}
            className="hidden"
          />

          <label
            htmlFor="file-upload-input"
            className="flex flex-col items-center justify-center w-full h-full cursor-pointer"
          >
            <div className="text-center flex flex-col items-center justify-center">
              <Cloud className="w-16 h-16 mb-6 text-white/70" strokeWidth={1.5} />

              <h2 className="text-2xl font-bold text-white mb-3">
                {processing ? 'Processing...' : 'Upload File'}
              </h2>

              <p className="text-white/80 text-sm mb-2">
                {processing ? 'Extracting & Anonymizing...' : 'Drag your file here.'}
              </p>

              {!processing && (
                <>
                  <p className="text-white/60 text-xs mb-4">
                    or click to browse
                  </p>
                  <p className="text-cyan-300 text-xs font-medium">
                    Supports: PDF, DOCX, TXT, MD, HTML, RTF, and more
                  </p>
                </>
              )}
            </div>
          </label>
        </div>
      )}

      {reviewing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div
            className="bg-white/10 border border-white/20 rounded-3xl w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl"
            style={{
              backdropFilter: 'blur(30px)',
              WebkitBackdropFilter: 'blur(30px)',
            }}
          >
            <div className="flex items-center justify-between p-6 border-b border-white/10">
              <div className="flex items-center gap-3">
                <FileText className="text-cyan-300 w-6 h-6" />
                <h3 className="text-xl font-bold text-white">Review Extracted Text</h3>
              </div>
              <button
                onClick={handleCancelReview}
                className="p-2 hover:bg-white/10 rounded-full transition-colors text-white/70 hover:text-white"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6 flex-1 overflow-hidden flex flex-col gap-4">
              <div className="flex items-center justify-between text-sm text-white/60">
                <span>Original File: {originalFileName}</span>
                <span className="flex items-center gap-1 text-cyan-300">
                  <Edit2 className="w-3 h-3" />
                  Editable
                </span>
              </div>

              <textarea
                value={extractedText}
                onChange={(e) => setExtractedText(e.target.value)}
                className="w-full h-full min-h-[300px] bg-black/20 border border-white/10 rounded-xl p-4 text-white/90 font-mono text-sm resize-none focus:outline-none focus:border-cyan-300/50 transition-colors"
                placeholder="Extracted text will appear here..."
              />

              <div className="text-xs text-white/40">
                * Personal information (emails, phones) has been automatically redacted. Please verify before uploading.
              </div>
            </div>

            <div className="p-6 border-t border-white/10 flex justify-end gap-4">
              <button
                onClick={handleCancelReview}
                className="px-6 py-2 rounded-xl text-white/80 hover:bg-white/10 transition-colors font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmUpload}
                className="px-6 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-bold transition-all transform hover:scale-105 flex items-center gap-2"
              >
                <Check className="w-4 h-4" />
                Confirm & Upload
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}