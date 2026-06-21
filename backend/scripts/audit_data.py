import sys
import os
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.post import Post
from app.models.analysis import Analysis

if __name__ == "__main__":
    # Load environment variables
    load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))
    
    db = SessionLocal()
    
    try:
        print("--- DATABASE AUDIT ---")
        total_posts = db.query(Post).count()
        print(f"Total posts: {total_posts}")
        
        total_analyses = db.query(Analysis).count()
        print(f"Total analysis records: {total_analyses}")
        
        total_summaries = db.query(Analysis).filter(Analysis.summary.isnot(None)).count()
        print(f"Total posts with summaries: {total_summaries}")
        
        total_no_summaries = db.query(Post).outerjoin(Analysis).filter((Analysis.id.is_(None)) | (Analysis.summary.is_(None))).count()
        print(f"Total posts without summaries: {total_no_summaries}")
        
        print("\n--- EXAMPLE ANALYSIS ROW ---")
        example_analysis = db.query(Analysis).first()
        if example_analysis:
            print(f"Analysis ID: {example_analysis.id}")
            print(f"Post ID: {example_analysis.post_id}")
            print(f"Language: {example_analysis.language}")
            print(f"Category: {example_analysis.category}")
            print(f"Sentiment: {example_analysis.sentiment}")
            print(f"Summary: {example_analysis.summary}")
            print(f"Analyzed at: {example_analysis.analyzed_at}")
        else:
            print("No analysis records found!")
            
    finally:
        db.close()
