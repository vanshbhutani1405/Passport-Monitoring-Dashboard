import sys
import os
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.api.v1.posts import list_posts
from fastapi import Depends

if __name__ == "__main__":
    load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))
    
    db = SessionLocal()
    
    try:
        print("--- TESTING /api/v1/posts ENDPOINT ---")
        response = list_posts(page=1, page_size=5, db=db)
        
        print(f"6. Example API response from /api/v1/posts:")
        print(f"  - Total: {response.total}")
        print(f"  - Page: {response.page}")
        print(f"  - Page size: {response.page_size}")
        
        if len(response.items) > 0:
            first_post = response.items[0]
            print("\n  First post in response:")
            print(f"  - Post ID: {first_post.id}")
            print(f"  - Platform: {first_post.platform}")
            print(f"  - Title: {first_post.title}")
            print(f"  - Content: {first_post.content[:100]}...")
            print(f"7. analysis.summary present? {first_post.analysis is not None and first_post.analysis.summary is not None}")
            if first_post.analysis:
                print(f"  analysis.summary value: {repr(first_post.analysis.summary)}")
            print(f"8. analysis.category present? {first_post.analysis is not None}")
            if first_post.analysis:
                print(f"  analysis.category value: {first_post.analysis.category}")
            print(f"9. analysis.sentiment present? {first_post.analysis is not None}")
            if first_post.analysis:
                print(f"  analysis.sentiment value: {first_post.analysis.sentiment}")
                
    finally:
        db.close()
