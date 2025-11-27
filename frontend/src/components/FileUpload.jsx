import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Cloud, X, Check, FileText, Edit2, Shield, AlertTriangle, RotateCcw, Trash2, Redo } from 'lucide-react';
import { extractContent, redactPII, adjustRedactionPositions } from '../utils/fileProcessor';

export default function FileUpload({ setLoading }) {
  const [dragActive, setDragActive] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [currentFile, setCurrentFile] = useState(null);
  const [extractedText, setExtractedText] = useState('');
  const [redactedItems, setRedactedItems] = useState([]);
  const [originalFileName, setOriginalFileName] = useState('');
  const [previousText, setPreviousText] = useState('');
  const [confirmRemove, setConfirmRemove] = useState(null);
  const textareaRef = useRef(null);

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
      const { redactedText, redactedItems: items } = redactPII(text);
      console.log('[FileUpload] Extraction complete, text length:', redactedText?.length);

      setProcessing(false);
      setExtractedText(redactedText);
      setRedactedItems(items);
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
    setRedactedItems([]);
    setCurrentFile(null);
    setLoading(false);
  };

  const handleTextChange = (e) => {
    const newText = e.target.value;
    const oldText = previousText;

    // Find where the change occurred
    let editPosition = -1;
    const minLength = Math.min(oldText.length, newText.length);

    // Find first difference
    for (let i = 0; i < minLength; i++) {
      if (oldText[i] !== newText[i]) {
        editPosition = i;
        break;
      }
    }

    // If no difference found in common part, edit is at the end
    if (editPosition === -1) {
      editPosition = minLength;
    }

    // Calculate offset
    const offset = newText.length - oldText.length;

    // Adjust redaction positions
    const updatedItems = adjustRedactionPositions(redactedItems, editPosition, offset);

    setExtractedText(newText);
    setPreviousText(newText);
    setRedactedItems(updatedItems);
  };

  const handleUndoRedaction = (index, e) => {
    e.stopPropagation();
    const item = redactedItems[index];
    const currentText = extractedText;
    const isRedacted = item.isRedacted !== false; // Default to true

    // Use the stored replacement if available, otherwise fallback based on type
    const redactionMarker = item.replacement || (item.type === 'Email' ? '[EMAIL REDACTED]' : '[PHONE REDACTED]');

    if (isRedacted) {
      // Undo: Replace marker with original
      const newText = currentText.slice(0, item.start) + item.original + currentText.slice(item.end);
      const offset = item.original.length - redactionMarker.length;

      const updatedItems = redactedItems.map((otherItem, i) => {
        if (i === index) {
          return { ...otherItem, isRedacted: false, end: otherItem.start + item.original.length };
        }
        if (otherItem.start >= item.end) {
          return { ...otherItem, start: otherItem.start + offset, end: otherItem.end + offset };
        }
        return otherItem;
      });

      setExtractedText(newText);
      setPreviousText(newText);
      setRedactedItems(updatedItems);
    } else {
      // Redo: Replace original with marker
      const newText = currentText.slice(0, item.start) + redactionMarker + currentText.slice(item.end);
      const offset = redactionMarker.length - item.original.length;

      const updatedItems = redactedItems.map((otherItem, i) => {
        if (i === index) {
          return { ...otherItem, isRedacted: true, end: otherItem.start + redactionMarker.length };
        }
        if (otherItem.start >= item.end) {
          return { ...otherItem, start: otherItem.start + offset, end: otherItem.end + offset };
        }
        return otherItem;
      });

      setExtractedText(newText);
      setPreviousText(newText);
      setRedactedItems(updatedItems);
    }
  };

  const handleRemoveRedaction = (index, e) => {
    e.stopPropagation();
    const item = redactedItems[index];
    setConfirmRemove({ index, item });
  };

  const cancelRemoveRedaction = (e) => {
    e.stopPropagation();
    setConfirmRemove(null);
  };

  const confirmRemoveRedaction = (e) => {
    e.stopPropagation();
    if (!confirmRemove) return;

    const { index, item } = confirmRemove;
    const isRedacted = item.isRedacted !== false;
    const currentText = extractedText;
    let newText = currentText;
    let offset = 0;

    if (isRedacted) {
      newText = currentText.slice(0, item.start) + item.original + currentText.slice(item.end);
      offset = item.original.length - (item.end - item.start);
    }

    const updatedItems = redactedItems
      .filter((_, i) => i !== index)
      .map(otherItem => {
        if (otherItem.start >= item.end) {
          return { ...otherItem, start: otherItem.start + offset, end: otherItem.end + offset };
        }
        return otherItem;
      });

    setExtractedText(newText);
    setPreviousText(newText);
    setRedactedItems(updatedItems);
    setConfirmRemove(null);
  };

  const handleItemClick = (item) => {
    if (textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.setSelectionRange(item.start, item.end);

      // Calculate scroll position to center the selection
      // This is a simple approximation. For better accuracy, we might need more complex logic
      // or rely on the browser's default behavior when focusing selection.
      // However, setSelectionRange often scrolls into view automatically.

      // Let's try blur and focus to force scroll if needed, though setSelectionRange usually works.
      textareaRef.current.blur();
      textareaRef.current.focus();
      textareaRef.current.setSelectionRange(item.start, item.end);
    }
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
            className="bg-white/10 border border-white/20 rounded-3xl w-full max-w-5xl h-[85vh] flex flex-col shadow-2xl"
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

            <div className="flex-1 overflow-hidden flex gap-4 p-6">
              <div className="flex-1 flex flex-col gap-4 overflow-hidden">
                <div className="flex items-center justify-between text-sm text-white/60">
                  <span>Original File: {originalFileName}</span>
                  <span className="flex items-center gap-1 text-cyan-300">
                    <Edit2 className="w-3 h-3" />
                    Editable
                  </span>
                </div>

                <textarea
                  ref={textareaRef}
                  value={extractedText}
                  onChange={handleTextChange}
                  className="w-full h-full bg-black/20 border border-white/10 rounded-xl p-4 text-white/90 font-mono text-sm resize-none focus:outline-none focus:border-cyan-300/50 transition-colors"
                  placeholder="Extracted text will appear here..."
                />
              </div>

              {redactedItems.length > 0 && (
                <div className="w-80 bg-black/20 border border-white/10 rounded-xl p-4 flex flex-col gap-3 overflow-hidden">
                  <div className="flex items-center gap-2 text-amber-400 font-medium pb-2 border-b border-white/10">
                    <Shield className="w-4 h-4" />
                    <span>Redacted Items ({redactedItems.length})</span>
                  </div>

                  <div className="flex-1 overflow-y-auto pr-2 flex flex-col gap-2">
                    {redactedItems.map((item, index) => (
                      <div
                        key={index}
                        onClick={() => handleItemClick(item)}
                        className="bg-white/5 rounded-lg p-3 text-xs border border-white/5 hover:border-cyan-300/50 hover:bg-white/10 transition-all cursor-pointer group"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-white/40 uppercase tracking-wider text-[10px] group-hover:text-cyan-300/70 transition-colors">{item.type}</span>
                          <AlertTriangle className="w-3 h-3 text-amber-400/50 group-hover:text-amber-400 transition-colors" />
                        </div>
                        <div className="text-white/80 font-mono break-all group-hover:text-white transition-colors mb-2">
                          {item.original}
                        </div>
                        <div className="flex gap-1">
                          <button
                            onClick={(e) => handleUndoRedaction(index, e)}
                            className="flex-1 flex items-center justify-center gap-1 px-2 py-1 rounded bg-white/5 hover:bg-blue-500/20 border border-white/10 hover:border-blue-500/50 text-white/60 hover:text-blue-400 transition-all text-[10px]"
                            title={item.isRedacted !== false ? "Restore original text" : "Redact again"}
                          >
                            {item.isRedacted !== false ? (
                              <>
                                <RotateCcw className="w-3 h-3" />
                                <span>Undo</span>
                              </>
                            ) : (
                              <>
                                <Redo className="w-3 h-3" />
                                <span>Redo</span>
                              </>
                            )}
                          </button>
                          {confirmRemove?.index === index ? (
                            <div className="flex-1 flex gap-1 animate-in fade-in duration-200">
                              <button
                                onClick={confirmRemoveRedaction}
                                className="flex-1 flex items-center justify-center p-1 rounded bg-green-500/20 border border-green-500/50 text-green-400 hover:bg-green-500/30 transition-all"
                                title="Confirm remove"
                              >
                                <Check className="w-3 h-3" />
                              </button>
                              <button
                                onClick={cancelRemoveRedaction}
                                className="flex-1 flex items-center justify-center p-1 rounded bg-white/5 border border-white/10 text-white/60 hover:bg-white/10 hover:text-white transition-all"
                                title="Cancel"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={(e) => handleRemoveRedaction(index, e)}
                              className="flex-1 flex items-center justify-center gap-1 px-2 py-1 rounded bg-white/5 hover:bg-red-500/20 border border-white/10 hover:border-red-500/50 text-white/60 hover:text-red-400 transition-all text-[10px]"
                              title="Permanently remove"
                            >
                              <Trash2 className="w-3 h-3" />
                              <span>Remove</span>
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="px-6 pb-2 text-xs text-white/40">
              * Personal information (emails, phones) has been automatically redacted. Please verify before uploading.
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