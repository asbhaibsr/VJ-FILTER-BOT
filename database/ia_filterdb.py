# Don't Remove Credit @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re, base64, json
import difflib
from struct import pack
from pyrogram.file_id import FileId
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from info import FILE_DB_URI, SEC_FILE_DB_URI, DATABASE_NAME, COLLECTION_NAME, MULTIPLE_DATABASE, USE_CAPTION_FILTER, MAX_B_TN

# First Database For File Saving 
client = MongoClient(FILE_DB_URI)
db = client[DATABASE_NAME]
col = db[COLLECTION_NAME]

# Second Database For File Saving
sec_client = MongoClient(SEC_FILE_DB_URI)
sec_db = sec_client[DATABASE_NAME]
sec_col = sec_db[COLLECTION_NAME]


async def save_file(media):
    """Save file in the database."""
    
    file_id, _ = unpack_new_file_id(media.file_id)
    file_name = clean_file_name(media.file_name)
    new_file_name = f"@asbhai_bsr {file_name}"
    
    file = {
        'file_id': file_id,
        'file_name': new_file_name,
        'file_size': media.file_size,
        'caption': media.caption.html if media.caption else None
    }

    if is_file_already_saved(file_id, file_name):
        return False, 0

    try:
        col.insert_one(file)
        print(f"{file_name} is successfully saved.")
        return True, 1
    except DuplicateKeyError:
        print(f"{file_name} is already saved.")
        return False, 0
    except:
        if MULTIPLE_DATABASE:
            try:
                sec_col.insert_one(file)
                print(f"{file_name} is successfully saved.")
                return True, 1
            except DuplicateKeyError:
                print(f"{file_name} is already saved.")
                return False, 0
        else:
            print("Your Current File Database Is Full, Turn On Multiple Database Feature And Add Second File Mongodb To Save File.")

def clean_file_name(file_name):
    """Clean and format the file name."""
    file_name = re.sub(r"(_|\-|\.|\+)", " ", str(file_name)) 
    unwanted_chars = ['[', ']', '(', ')', '{', '}']
    
    for char in unwanted_chars:
        file_name = file_name.replace(char, '')
        
    return ' '.join(filter(lambda x: not x.startswith('@') and not x.startswith('http') and not x.startswith('www.') and not x.startswith('t.me'), file_name.split()))

def is_file_already_saved(file_id, file_name):
    """Check if the file is already saved in either collection."""
    found1 = {'file_name': file_name}
    found = {'file_id': file_id}

    for collection in [col, sec_col]:
        if collection.find_one(found1) or collection.find_one(found):
            print(f"{file_name} is already saved.")
            return True
            
    return False

async def get_search_results(chat_id, query, file_type=None, max_results=10, offset=0, filter=False):
    """For given query return (results, next_offset, total_results)"""
    
    query = query.strip()
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]') 
    
    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        regex = query

    filter_dict = {'file_name': regex}
    files = []

    # --- 1. First Try: Exact/Strict Search ---
    if MULTIPLE_DATABASE:
        # Fetch more than needed so we can deduplicate properly
        fetch_limit = max_results * 2
        cursor1 = col.find(filter_dict).sort('$natural', -1).skip(offset).limit(fetch_limit)
        cursor2 = sec_col.find(filter_dict).sort('$natural', -1).skip(offset).limit(fetch_limit)
        seen_ids = set()
        for file in cursor1:
            fid = file.get('file_id')
            if fid not in seen_ids:
                seen_ids.add(fid)
                files.append(file)
        for file in cursor2:
            fid = file.get('file_id')
            if fid not in seen_ids:
                seen_ids.add(fid)
                files.append(file)
        files = files[:max_results]
    else:
        cursor = col.find(filter_dict).sort('$natural', -1).skip(offset).limit(max_results)
        for file in cursor: files.append(file)

    if MULTIPLE_DATABASE:
        # Count unique results across both DBs
        ids1 = set(f['file_id'] for f in col.find(filter_dict, {'file_id': 1}))
        ids2 = set(f['file_id'] for f in sec_col.find(filter_dict, {'file_id': 1}))
        total_results = len(ids1 | ids2)
    else:
        total_results = col.count_documents(filter_dict)

    if files:
        next_offset = "" if (offset + max_results) >= total_results else (offset + max_results)
        return files, next_offset, total_results

    # --- 2. Second Try: Broader Fuzzy Search (If Exact Failed) ---
    
    if len(query) > 0:
        first_char = query[0]
        try:
            start_regex = re.compile(f'^{re.escape(first_char)}', flags=re.IGNORECASE)
        except:
            return [], "", 0
            
        loose_filter = {'file_name': start_regex}
        
        # Fetch Candidates (Limit 300 per DB to avoid lag)
        candidates = []
        if MULTIPLE_DATABASE:
            c1 = list(col.find(loose_filter).sort('$natural', -1).limit(300))
            c2 = list(sec_col.find(loose_filter).sort('$natural', -1).limit(300))
            seen_ids = set()
            for file in c1 + c2:
                fid = file.get('file_id')
                if fid not in seen_ids:
                    seen_ids.add(fid)
                    candidates.append(file)
        else:
            candidates = list(col.find(loose_filter).sort('$natural', -1).limit(300))

        final_files = []
        for file in candidates:
            # 1. Normal Similarity
            ratio = difflib.SequenceMatcher(None, query.lower(), file['file_name'].lower()).ratio()
            
            # 2. No-Space Similarity (e.g. "kal ki" vs "kalki")
            ratio2 = difflib.SequenceMatcher(None, query.replace(" ", "").lower(), file['file_name'].replace(" ", "").lower()).ratio()
            
            # Max Score
            score = max(ratio, ratio2)
            
            # Threshold: 50%
            if score >= 0.50:
                final_files.append((file, score))

        # Sort by score
        final_files.sort(key=lambda x: x[1], reverse=True)
        
        # Extract files
        sorted_files = [x[0] for x in final_files]
        
        # Pagination Logic for Fuzzy Results
        total_results = len(sorted_files)
        files = sorted_files[offset:offset+max_results]
        
        next_offset = "" if (offset + max_results) >= total_results else (offset + max_results)
        
        return files, next_offset, total_results

    return [], "", 0

async def get_bad_files(query, file_type=None, use_filter=False):
    """For given query return (results, next_offset)"""
    query = query.strip()
    
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = rf'(\b|[.+-_]){query}(\b|[.+-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[s.+-_]')
    
    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except re.error:
        return [], 0

    filter_criteria = {'file_name': regex}
    if USE_CAPTION_FILTER:
        filter_criteria = {'$or': [filter_criteria, {'caption': regex}]}

    def count_documents(collection):
        return collection.count_documents(filter_criteria)

    total_results = (count_documents(col) + count_documents(sec_col) if MULTIPLE_DATABASE else count_documents(col))

    def find_documents(collection):
        return list(collection.find(filter_criteria))

    files = (find_documents(col) + find_documents(sec_col) if MULTIPLE_DATABASE else find_documents(col))

    return files, total_results

async def get_file_details(query):
    return col.find_one({'file_id': query}) or sec_col.find_one({'file_id': query})

def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0
    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0
            r += bytes([i])
    return base64.urlsafe_b64encode(r).decode().rstrip("=")
    
def unpack_new_file_id(new_file_id):
    """Return (file_id, file_ref) tuple - file_ref may be empty string"""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    # file_ref for access hash verification (may be empty)
    try:
        file_ref = base64.urlsafe_b64encode(decoded.file_reference or b"").decode().rstrip("=")
    except Exception:
        file_ref = ""
    return file_id, file_ref
