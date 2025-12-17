import json
import os
from . import cloud_file_management

MAPPING_FILE_NAME = "law_reference_mappings.json"

# In-memory cache for mappings to avoid repeated Drive calls
_mappings_cache = None
_cache_loaded = False

def load_law_mappings(force_reload=False):
    """Load the law reference mappings from Google Drive.
    
    Args:
        force_reload: If True, bypass cache and reload from Drive
    
    Returns a dictionary mapping sanitized references to normalized references.
    Example: {"Codul_fiscal": "LEGE_227_2015"}
    """
    global _mappings_cache, _cache_loaded
    
    # Return cached mappings if available and not forcing reload
    if not force_reload and _cache_loaded:
        return _mappings_cache if _mappings_cache is not None else {}
    
    try:
        # Check if mapping file exists in cloud
        file_info = cloud_file_management.search_file_in_cloud(MAPPING_FILE_NAME)
        
        if file_info:
            print(f"Loading law mappings from cloud: {MAPPING_FILE_NAME}")
            content = cloud_file_management.download_file_content(file_info['id'])
            if content:
                mappings = json.loads(content)
                print(f"Loaded {len(mappings)} law mappings")
                _mappings_cache = mappings
                _cache_loaded = True
                return mappings
        
        print("No law mappings file found in cloud, starting with empty mappings")
        _mappings_cache = {}
        _cache_loaded = True
        return {}
    except Exception as e:
        print(f"Error loading law mappings: {e}")
        # Do not cache failure, so we can retry
        _mappings_cache = None
        _cache_loaded = False
        return {}


def save_law_mappings(mappings):
    """Save the law reference mappings to Google Drive.
    
    Args:
        mappings: Dictionary mapping sanitized references to normalized references
    """
    global _mappings_cache
    
    try:
        # Save to temporary file
        temp_dir = "../TMP"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        temp_path = os.path.join(temp_dir, MAPPING_FILE_NAME)
        with open(temp_path, 'w') as f:
            json.dump(mappings, f, indent=2, ensure_ascii=False)
        
        # Update existing file or create new one (prevents duplicates)
        file_id = cloud_file_management.update_file_in_cloud(temp_path)
        print(f"Saved {len(mappings)} law mappings to cloud")
        
        # Update cache
        _mappings_cache = mappings
        
        return file_id
    except Exception as e:
        print(f"Error saving law mappings: {e}")
        return None


def add_law_mapping(sanitized_ref, normalized_ref):
    """Add a new mapping from sanitized reference to normalized reference.
    
    Args:
        sanitized_ref: The sanitized reference (e.g., "Codul_fiscal")
        normalized_ref: The normalized reference (e.g., "LEGE_227_2015")
    """
    if not sanitized_ref or not normalized_ref or sanitized_ref == normalized_ref:
        return
    
    # Lowercase for case-insensitive lookups
    sanitized_ref_lower = sanitized_ref.lower()
    
    mappings = load_law_mappings()
    
    # Only update if mapping doesn't exist or is different
    if sanitized_ref_lower not in mappings or mappings[sanitized_ref_lower] != normalized_ref:
        mappings[sanitized_ref_lower] = normalized_ref
        print(f"Adding mapping: {sanitized_ref} -> {normalized_ref}")
        save_law_mappings(mappings)


def get_normalized_reference(sanitized_ref):
    """Get the normalized reference for a sanitized reference.
    
    Args:
        sanitized_ref: The sanitized reference (e.g., "Codul_fiscal")
    
    Returns:
        The normalized reference if found, None otherwise
    """
    # Lowercase for case-insensitive lookups
    sanitized_ref_lower = sanitized_ref.lower()
    
    mappings = load_law_mappings()
    normalized = mappings.get(sanitized_ref_lower)
    if normalized:
        print(f"Found mapping: {sanitized_ref} -> {normalized}")
    return normalized

