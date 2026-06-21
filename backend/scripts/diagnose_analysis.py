
import sys
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz
from typing import Any

UTC = pytz.UTC

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.post import Post
from app.models.analysis import Analysis
from app.nlp.groq_analyzer import GroqAnalyzer


def print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def check_environment() -> dict[str, Any]:
    print_header("1. Environment Configuration")
    settings = get_settings()
    env_status = {
        "grok_api_key_set": bool(settings.groq_api_key),
        "grok_model": settings.groq_model,
        "analysis_batch_size": settings.analysis_batch_size,
    }
    print(f"  - GROQ_API_KEY set: {env_status['grok_api_key_set']}")
    print(f"  - GROQ_MODEL: {env_status['grok_model']}")
    print(f"  - ANALYSIS_BATCH_SIZE: {env_status['analysis_batch_size']}")
    return env_status


def check_database() -> dict[str, int]:
    print_header("2. Database Stats")
    db = SessionLocal()
    try:
        total_posts = db.query(Post).count()
        total_analyzed = db.query(Analysis).count()
        posts_without_analysis = db.query(Post).outerjoin(Analysis).filter(Analysis.id is None).count()
        db_stats = {
            "total_posts": total_posts,
            "total_analyzed": total_analyzed,
            "pending_analysis": posts_without_analysis,
        }
        print(f"  - Total posts: {db_stats['total_posts']}")
        print(f"  - Total analyzed: {db_stats['total_analyzed']}")
        print(f"  - Pending analysis: {db_stats['pending_analysis']}")
        
        # Check one post
        sample_post = db.query(Post).first()
        if sample_post:
            print("\n  Sample Post:")
            print(f"    - ID: {sample_post.id}")
            print(f"    - Title: {sample_post.title}")
            print(f"    - Has analysis: {bool(sample_post.analysis)}")
        return db_stats
    finally:
        db.close()


def test_groq_analyzer() -> None:
    print_header("3. Testing Groq Analyzer")
    try:
        analyzer = GroqAnalyzer()
        print("  - GroqAnalyzer initialized")
        test_text = """
        Title: Passport renewal wait times reach all-time high
        Content: Many users are complaining about long wait times for passport renewals. The process seems to be taking longer than usual.
        """
        print("\n  Testing with sample text:")
        print("  " + test_text.strip()[:100] + "...")
        result = analyzer.analyze(test_text)
        print("\n  Analysis result:")
        print(f"    - Language: {result.language}")
        print(f"    - Category: {result.category}")
        print(f"    - Sentiment: {result.sentiment}")
        print(f"    - Summary: {repr(result.summary)}")
        print(f"    - Is gibberish: {result.is_gibberish}")
        print("\n  ✅ Groq analyzer test PASSED")
    except Exception as e:
        print(f"\n  ❌ Groq analyzer test FAILED: {type(e).__name__}")
        print(f"\n  Stack Trace:")
        import traceback
        traceback.print_exc()


def test_single_post_analysis() -> None:
    print_header("4. Testing Single Post Analysis")
    db = SessionLocal()
    try:
        post = db.query(Post).outerjoin(Analysis).filter(Analysis.id is None).first()
        if not post:
            print("  - No pending posts to test")
            return
        
        print(f"  Testing post: {post.id}")
        
        # Test Groq
        analyzer = GroqAnalyzer()
        text = analyzer._build_input_text(post)
        print(f"  Input text: {text[:150]}...")
        result = analyzer.analyze(text)
        print(f"  ✓ Analysis result received")
        
        # Test inserting Analysis
        print("  Testing inserting Analysis...")
        analysis = Analysis(
            post_id=post.id,
            language=result.language,
            category=result.category,
            sentiment=result.sentiment,
            summary=result.summary,
            is_gibberish=result.is_gibberish,
            is_duplicate=False,
            analyzed_at=datetime.now(UTC),
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        print("  ✓ Analysis record inserted successfully!")
        
        # Verify the analysis is linked to the post
        updated_post = db.query(Post).get(post.id)
        print(f"  ✓ Post now has analysis: {bool(updated_post.analysis)}")
        print(f"  ✓ Analysis ID: {analysis.id}")
        
        print("\n  ✅ Single post analysis test PASSED")
    except Exception as e:
        db.rollback()
        print(f"\n  ❌ Single post analysis test FAILED: {type(e).__name__}")
        print(f"  Error message: {e}")
        print("\n  Stack Trace:")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def check_analysis_job_manager() -> None:
    print_header("5. Analysis Job Manager Diagnostics")
    from app.services.analysis_job_manager import AnalysisJobManager
    manager = AnalysisJobManager()
    status = manager.get_status()
    print(f"  - Current status: {status.get('status')}")
    print(f"  - Total pending: {status.get('total_posts')}")
    print(f"  - Processed: {status.get('processed')}")
    print(f"  - Successful: {status.get('successful')}")
    print(f"  - Failed: {status.get('failed')}")


def main() -> None:
    print("\n" + "=" * 60)
    print("  PASSPORT MONITOR - ANALYSIS DIAGNOSTICS")
    print("=" * 60)
    
    load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))
    
    check_environment()
    check_database()
    test_groq_analyzer()
    test_single_post_analysis()
    check_analysis_job_manager()
    
    print("\n" + "=" * 60)
    print("  DIAGNOSTICS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()

