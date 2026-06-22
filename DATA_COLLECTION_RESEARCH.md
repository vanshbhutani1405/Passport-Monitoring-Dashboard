# Engineering Decisions & Platform Constraints

## Data Collection Strategy

One of the biggest challenges while building the Passport Monitoring Dashboard was collecting passport-related discussions from multiple online platforms.

The assignment mentions monitoring content across major social platforms. During development, I explored multiple approaches and technologies to achieve this.

---

## Reddit Integration

Initially, Reddit was selected as a primary data source because it contains a large volume of public discussions, user experiences, complaints, and passport-related queries.

Implementation work completed:

* Reddit ingestion service
* Reddit API integration using PRAW
* Keyword-based search pipeline
* Data normalization layer

However, during development Reddit updated its API access policies and significantly restricted public access and usage limits.

As a result, although Reddit integration code exists within the repository, it was not included in the final production pipeline to ensure reliability and compliance with platform restrictions.

---

## Exploration of Additional Platforms

The original goal was to support additional social platforms such as:

* X (Twitter)
* Instagram
* LinkedIn
* Reddit
* YouTube
* News Sources

To achieve this, several scraping and data collection solutions were evaluated.

### BeautifulSoup

Evaluated for:

* HTML parsing
* Static webpage extraction

Limitations encountered:

* Modern social platforms heavily rely on JavaScript rendering
* Content often unavailable in initial HTML response
* Anti-bot protection mechanisms

Result:

Not suitable for reliable large-scale social media collection.

---

### Scrapling

Evaluated for:

* Dynamic website scraping
* Improved extraction capabilities

Limitations encountered:

* Platform restrictions
* Dynamic authentication flows
* Rate limiting
* Frequent structural changes in social platforms

Result:

Could not provide stable access to major social media platforms.

---

### Apify

Evaluated for:

* Ready-made social media actors
* Cloud-based scraping infrastructure
* Large-scale data collection

Advantages:

* Simplified scraper deployment
* Reduced maintenance effort
* Strong ecosystem

Limitations encountered:

* Dependency on external services
* Platform-level restrictions still apply
* Some actors were unreliable for long-term production use

Result:

Explored extensively but not selected for the final implementation.

---

## Why Instagram, X (Twitter), and LinkedIn Were Not Included

A significant engineering challenge was that major social platforms have increasingly restricted public data access through:

* Authentication requirements
* Anti-scraping protections
* API restrictions
* Rate limits
* Compliance requirements

Even when technically possible, maintaining a stable and compliant scraping pipeline for these platforms would require substantial infrastructure and ongoing maintenance.

For this reason, the final solution focuses on sources that provide stable and reliable access.

---

## Final Production Data Sources

The final production pipeline uses:

### YouTube

Used for:

* Public discussions
* Passport-related informational content
* User-generated experiences

Integrated using:

* YouTube Data API v3

---

### Google News

Used for:

* Official announcements
* News articles
* Government updates
* Public information

Integrated using:

* RSS feeds
* News aggregation endpoints

---

## Architectural Decision

Rather than tightly coupling the system to specific platforms, the application was designed around a generic ingestion architecture.

Benefits:

* Easier future expansion
* Cleaner system design
* Improved maintainability
* Platform-independent processing pipeline

This allows new data sources to be added without modifying the downstream AI processing, clustering, translation, analytics, or dashboard components.

---

## Future Expansion

The ingestion architecture is intentionally extensible and can support additional data sources in the future whenever stable and compliant access mechanisms become available.

Potential future integrations include:

* Reddit (if access conditions improve)
* Additional public discussion forums
* Government announcement feeds
* Enterprise social monitoring providers
* Real-time streaming sources

---

## Conclusion

Building a multi-source monitoring platform requires balancing technical feasibility, platform restrictions, reliability, and maintainability.

While several collection strategies were explored, the final implementation prioritizes stable, compliant, and production-friendly data sources while maintaining an architecture that can easily expand in the future.
