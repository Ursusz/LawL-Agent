import pytest
from unittest.mock import patch, MagicMock
from fastapi import UploadFile
import sys
import os

from src.process_file import process_file
from src import parse_documents, extract_references, search_laws
from src.models import gemini_reference_extractor

@pytest.mark.asyncio
async def test_implicit_reference_extraction():
    # Mock file upload
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test_doc.txt"
    mock_file.read.return_value = b"Discutam despre codul muncii si alte aspecte."
    
    # Mock parse_documents
    with patch('src.parse_documents.parse_file', return_value="Discutam despre codul muncii si alte aspecte."):
        # Mock extract_references (regex) - should return empty or irrelevant for this test
        with patch('src.extract_references.extract_law_references', return_value=[]):
            # Mock gemini_reference_extractor
            with patch('src.models.gemini_reference_extractor.extract_implicit_references', return_value=["Legea nr. 53/2003"]):
                # Mock search_laws to avoid actual processing
                with patch('src.search_laws.find_laws', return_value={}) as mock_find_laws:
                    
                    result = await process_file(mock_file)
                    
                    # Verify that find_laws was called with the standardized reference
                    # "Legea nr. 53/2003" standardizes to "LEGE_53_2003"
                    expected_ref = "LEGE_53_2003"
                    
                    # Check the arguments passed to find_laws
                    args, _ = mock_find_laws.call_args
                    extracted_refs = args[0]
                    
                    assert expected_ref in extracted_refs
                    assert result['filename'] == "test_doc.txt"

@pytest.mark.asyncio
async def test_merge_references():
    # Mock file upload
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test_doc.txt"
    mock_file.read.return_value = b"Text with both references."
    
    # Mock parse_documents
    with patch('src.parse_documents.parse_file', return_value="Text with both references."):
        # Mock extract_references (regex) - returns one ref
        with patch('src.extract_references.extract_law_references', return_value=["Legea_1_2011"]):
            # Mock gemini_reference_extractor - returns another ref
            with patch('src.models.gemini_reference_extractor.extract_implicit_references', return_value=["Legea nr. 53/2003"]):
                # Mock search_laws
                with patch('src.search_laws.find_laws', return_value={}) as mock_find_laws:
                    
                    await process_file(mock_file)
                    
                    args, _ = mock_find_laws.call_args
                    extracted_refs = args[0]
                    
                    assert "Legea_1_2011" in extracted_refs
                    assert "LEGE_53_2003" in extracted_refs
                    assert len(extracted_refs) == 2

@pytest.mark.asyncio
async def test_fallback_implicit_reference():
    # Mock file upload
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test_doc.txt"
    mock_file.read.return_value = b"Text with non-standard reference."
    
    # Mock parse_documents
    with patch('src.parse_documents.parse_file', return_value="Text with non-standard reference."):
        # Mock extract_references (regex) - returns nothing
        with patch('src.extract_references.extract_law_references', return_value=[]):
            # Mock gemini_reference_extractor - returns a reference that won't standardize
            with patch('src.models.gemini_reference_extractor.extract_implicit_references', return_value=["Codul Fiscal"]):
                # Mock search_laws
                with patch('src.search_laws.find_laws', return_value={}) as mock_find_laws:
                    
                    await process_file(mock_file)
                    
                    args, _ = mock_find_laws.call_args
                    extracted_refs = args[0]
                    
                    # Should contain "Codul_Fiscal" (sanitized) since it doesn't standardize
                    assert "Codul_Fiscal" in extracted_refs
