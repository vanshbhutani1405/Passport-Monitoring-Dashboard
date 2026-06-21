import sys
import os
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.post import Post
from app.models.analysis import Analysis

if __name__ == "__main__":
    load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))
    
    db = SessionLocal()
    
    try:
        print("--- DATABASE AUDIT ---")
        total_posts = db.query(Post).count()
        print(f"1. Total posts count: {total_posts}")
        
        total_analyses = db.query(Analysis).count()
        print(f"2. Total analysis records count: {total_analyses}")
        
        total_summaries = db.query(Analysis).filter(Analysis.summary.isnot(None)).count()
        print(f"3. Total posts with summaries: {total_summaries}")
        
        total_no_summaries = total_posts - total_summaries
        print(f"4. Total posts without summaries: {total_no_summaries}")
        
        print("\n5. Example Analysis row from database:")
        example_analysis = db.query(Analysis).first()
        if example_analysis:
            print(f"  - Analysis ID: {example_analysis.id}")
            print(f"  - Post ID: {example_analysis.post_id}")
            print(f"  - Language: {example_analysis.language}")
            print(f"  - Category: {example_analysis.category}")
            print(f"  - Sentiment: {example_analysis.sentiment}")
            print(f"  - Summary: {repr(example_analysis.summary)}")
            print(f"  - Is gibberish: {example_analysis.is_gibberish}")
        else:
            print("  No analysis records found!")
        
        print("\n--- CHECKING ANALYSIS MODEL AND POST RELATION ---")
        print("Checking Post model:")
        example_post_with_analysis = db.query(Post).filter(Post.analysis.isnot(None)).first()
        if example_post_with_analysis:
            print(f"  - Post ID: {example_post_with_analysis.id}")
            print(f"  - Post has analysis: {example_post_with_analysis is not None and example_post_with_analysis.analysis is not None}")
            if example_post_with_analysis.analysis:
                print(f"  - Post analysis.category: {example_post_with_analysis.analysis.category}")
                print(f"  - Post analysis.sentiment: {example_post_with_analysis.analysis.sentiment}")
                print(f"  - Post analysis.summary: {repr(example_post_with_analysis.analysis.summary)}")
        else:
            print("  No post with analysis found!")
            
    finally:
        db.close()
