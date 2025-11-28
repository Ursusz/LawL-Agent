import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Cloud, X, Check, FileText, Edit2, Shield, AlertTriangle, RotateCcw, Trash2, Redo } from 'lucide-react';
import { extractContent, redactPII, adjustRedactionPositions, processManualEdit } from '../utils/fileProcessor';

export default function FileUpload({ setLoading }) {
  const [dragActive, setDragActive] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [extractedText, setExtractedText] = useState('');
  const [initialExtractedText, setInitialExtractedText] = useState('');
  const [redactedItems, setRedactedItems] = useState([]);
  const [manualEdits, setManualEdits] = useState([]);
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
      setInitialExtractedText(redactedText);
      setPreviousText(redactedText);
      setRedactedItems(items);
      setManualEdits([]);
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
      // Map originalFileName to each result item
      const resultsWithFileName = results.map(item => ({
        ...item,
        originalFileName: originalFileName
      }));
      navigate('/results', { state: { results: resultsWithFileName, extractedText } });
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
    setManualEdits([]);
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

    // Track manual edit if there's actual change
    if (offset !== 0) {
      // Filter out any undone edits from the end (linear history)
      // If we edit while some items are undone, those undone items are lost
      const activeEdits = manualEdits.filter(edit => !edit.isUndone);

      const newManualEdits = processManualEdit(
        activeEdits,
        newText,
        oldText,
        editPosition,
        offset,
        redactedItems, // Before
        updatedItems,   // After
        initialExtractedText // Initial text for original tracking
      );
      setManualEdits(newManualEdits);
    }

    setExtractedText(newText);
    setPreviousText(newText);
    setRedactedItems(updatedItems);
  };

  const handleUndoRedaction = (index, e) => {
    e.stopPropagation();
    const item = redactedItems[index];
    const currentText = extractedText;
    const isRedacted = item.isRedacted !== false; // Default to true

    // Use the stored replacement text (e.g., "CNP: [REDACTED]" or just "[REDACTED]")
    const redactionMarker = item.replacement || '[REDACTED]';

    if (isRedacted) {
      // Undo: Replace redacted text with original
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
      // Redo: Replace original with redacted text
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

    // Always restore original text when removing
    if (isRedacted) {
      newText = currentText.slice(0, item.start) + item.original + currentText.slice(item.end);
      offset = item.original.length - (item.end - item.start);
    } else {
      // If already unredacted, just remove from list (text already shows original)
      newText = currentText;
      offset = 0;
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

  const handleUndoManualEdit = (index, e) => {
    e.stopPropagation();
    const edit = manualEdits[index];

    // Simply restore the text state from before this edit
    // This is stored in redactedItemsBefore's corresponding text state
    // We need to reconstruct the text by undoing this edit

    // Find the text state before this edit by looking at previous edit's after state
    // or initial state if this is the first edit
    let textBeforeThisEdit;
    if (index === 0) {
      textBeforeThisEdit = initialExtractedText;
    } else {
      // Get the text after the previous edit
      const prevEdit = manualEdits[index - 1];
      if (prevEdit.isUndone) {
        // Previous edit is undone, can't redo this one
        return;
      }
      // We need to reconstruct by applying all active edits up to index-1
      textBeforeThisEdit = initialExtractedText;
      for (let i = 0; i < index; i++) {
        const e = manualEdits[i];
        if (!e.isUndone) {
          // Apply edit: remove original, insert replacement
          textBeforeThisEdit = textBeforeThisEdit.slice(0, e.start) + e.replacement + textBeforeThisEdit.slice(e.start + e.original.length);
        }
      }
    }

    setExtractedText(textBeforeThisEdit);
    setPreviousText(textBeforeThisEdit);

    // Restore redacted items
    if (edit.redactedItemsBefore) {
      setRedactedItems(edit.redactedItemsBefore);
    }

    // Mark this edit and all subsequent edits as undone
    const newEdits = manualEdits.map((item, i) => {
      if (i >= index) return { ...item, isUndone: true };
      return item;
    });
    setManualEdits(newEdits);
  };

  const handleRedoManualEdit = (index, e) => {
    e.stopPropagation();
    if (index > 0 && manualEdits[index - 1].isUndone) {
      return;
    }

    const edit = manualEdits[index];

    // Reconstruct text by applying all active edits up to and including this one
    let textAfterThisEdit = initialExtractedText;
    for (let i = 0; i <= index; i++) {
      const e = manualEdits[i];
      // Apply edit: remove original, insert replacement
      textAfterThisEdit = textAfterThisEdit.slice(0, e.start) + e.replacement + textAfterThisEdit.slice(e.start + e.original.length);
    }

    setExtractedText(textAfterThisEdit);
    setPreviousText(textAfterThisEdit);

    // Restore redacted items
    if (edit.redactedItemsAfter) {
      setRedactedItems(edit.redactedItemsAfter);
    }

    // Mark this edit as active
    const newEdits = manualEdits.map((item, i) => {
      if (i === index) return { ...item, isUndone: false };
      return item;
    });
    setManualEdits(newEdits);
  };

  const handleRemoveManualEdit = (index, e) => {
    e.stopPropagation();
    setConfirmRemove({ index, item: manualEdits[index], type: 'edit' });
  };

  const confirmRemoveManualEdit = (e) => {
    e.stopPropagation();
    if (!confirmRemove || confirmRemove.type !== 'edit') return;

    const { index } = confirmRemove;
    const edit = manualEdits[index];
    const currentText = extractedText;

    // Restore original text at [start, end]
    const newText = currentText.slice(0, edit.start) + edit.original + currentText.slice(edit.end);
    const offset = edit.original.length - (edit.end - edit.start);

    // Adjust redacted items
    const updatedItems = adjustRedactionPositions(edit.redactedItemsBefore || redactedItems, edit.start, offset);

    setExtractedText(newText);
    setPreviousText(newText);
    setRedactedItems(updatedItems);

    // Remove from list
    setManualEdits(manualEdits.filter((_, i) => i !== index));
    setConfirmRemove(null);
  };

  const handleItemClick = (item) => {
    if (textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.setSelectionRange(item.start, item.end);
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

              {(redactedItems.length >= 0 || manualEdits.length > 0) && (
                <div className="w-80 bg-black/20 border border-white/10 rounded-xl flex flex-col overflow-hidden">
                  <div className="p-4 border-b border-white/10 bg-white/5">
                    <h4 className="text-white font-medium flex items-center gap-2">
                      <Shield className="w-4 h-4 text-cyan-300" />
                      Changes & Redactions
                    </h4>
                  </div>

                  <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-6">
                    {redactedItems.length > 0 && (
                      <div className="flex flex-col gap-3">
                        <div className="flex items-center gap-2 text-amber-400 font-medium text-xs uppercase tracking-wider">
                          <Shield className="w-3 h-3" />
                          <span>Redacted Items ({redactedItems.length})</span>
                        </div>
                        <div className="flex flex-col gap-2">
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
                                {confirmRemove?.index === index && !confirmRemove?.type ? (
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

                    {manualEdits.length > 0 && (
                      <div className="flex flex-col gap-3">
                        <div className="flex items-center gap-2 text-blue-400 font-medium text-xs uppercase tracking-wider">
                          <Edit2 className="w-3 h-3" />
                          <span>Manual Edits ({manualEdits.length})</span>
                        </div>

                        <div className="flex flex-col gap-2">
                          {manualEdits.map((edit, index) => (
                            <div
                              key={edit.timestamp}
                              onClick={() => handleItemClick(edit)}
                              className={`bg-white/5 rounded-lg p-3 text-xs border border-white/5 hover:border-blue-300/50 hover:bg-white/10 transition-all cursor-pointer group ${edit.isUndone ? 'opacity-50' : ''}`}
                            >
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-white/40 uppercase tracking-wider text-[10px] group-hover:text-blue-300/70 transition-colors">Edit #{index + 1}</span>
                                <Edit2 className="w-3 h-3 text-blue-400/50 group-hover:text-blue-400 transition-colors" />
                              </div>
                              <div className="text-white/60 font-mono text-[10px] mb-2 break-all">
                                {edit.original && <div className="text-red-400">- {edit.original.slice(0, 50)}{edit.original.length > 50 ? '...' : ''}</div>}
                                {edit.replacement && <div className="text-green-400">+ {edit.replacement.slice(0, 50)}{edit.replacement.length > 50 ? '...' : ''}</div>}
                              </div>
                              <div className="flex gap-1">
                                <button
                                  onClick={(e) => edit.isUndone ? handleRedoManualEdit(index, e) : handleUndoManualEdit(index, e)}
                                  className="flex-1 flex items-center justify-center gap-1 px-2 py-1 rounded bg-white/5 hover:bg-blue-500/20 border border-white/10 hover:border-blue-500/50 text-white/60 hover:text-blue-400 transition-all text-[10px]"
                                  title={edit.isUndone ? "Redo this edit" : "Undo this edit and all subsequent edits"}
                                  disabled={edit.isUndone && index > 0 && manualEdits[index - 1].isUndone}
                                >
                                  {edit.isUndone ? (
                                    <>
                                      <Redo className="w-3 h-3" />
                                      <span>Redo</span>
                                    </>
                                  ) : (
                                    <>
                                      <RotateCcw className="w-3 h-3" />
                                      <span>Undo</span>
                                    </>
                                  )}
                                </button>
                                {confirmRemove?.index === index && confirmRemove?.type === 'edit' ? (
                                  <div className="flex-1 flex gap-1 animate-in fade-in duration-200">
                                    <button
                                      onClick={confirmRemoveManualEdit}
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
                                    onClick={(e) => handleRemoveManualEdit(index, e)}
                                    className="flex-1 flex items-center justify-center gap-1 px-2 py-1 rounded bg-white/5 hover:bg-red-500/20 border border-white/10 hover:border-red-500/50 text-white/60 hover:text-red-400 transition-all text-[10px]"
                                    title="Remove from tracking"
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