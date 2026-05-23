# Torob Bot Requirements for AfraKala

## Purpose

The Torob bot is a dedicated plugin inside the Afra Automation Platform. Its job is to collect, clean, validate and structure public Torob market data so AfraKala can use it for B2B supplier discovery, competitor monitoring, price analysis and operational decision support.

The bot must not be treated as a simple scraper. It must become a market intelligence module for Torob.

---

## Execution Priority Levels

- P0: Critical foundation. Must exist before real scraping.
- P1: Core Torob extraction and usable business output.
- P2: Advanced analysis and automation.
- P3: Optimization and future expansion.

---

## P0 - Critical Architecture Requirements

### 1. Local Bot Panel Control

All user interaction with the bot must happen through the local bot panel built for AfraKala automation bots.

The user must be able to manage:

- Input data
- Output files
- Execution status
- Schedules
- Speed profiles
- Pause, resume and stop commands
- Logs
- Errors
- Reports

The user should not be required to run Python scripts manually.

### 2. Local Input and Output Storage

All input and output data must stay inside the local bot workspace.

Required local areas:

- input files
- output files
- logs
- reports
- database
- checkpoints
- screenshots or debug artifacts
- configuration files

### 3. Anti-Blocking and Anti-Detection Rules

The bot must respect anti-blocking and anti-detection design from the beginning.

Required behavior:

- Random delays between searches
- Random delays between product pages
- Random delays between seller checks
- Human-like scrolling
- Human-like mouse movement when browser automation is used
- Configurable speed profiles
- Retry with backoff
- Per-domain rate limiting
- Optional proxy support
- Separate browser profile or context per worker
- Error logging for access restriction, captcha, timeout and blocked requests

Speed must never be hardcoded. It must be configurable from the local panel.

### 4. Configurable Scheduling and Speed

The local panel must allow the user to configure:

- Start time
- End time
- Allowed execution days
- Speed profile per time window
- Maximum searches per run
- Maximum products per run
- Maximum sellers per product
- Manual execution
- Scheduled execution
- Pause and resume

Example: the bot may run slowly during sensitive hours and faster during approved low-risk windows.

### 5. Queue-Based Execution

The bot must use a queue-based architecture.

Each job should include:

- Platform: torob
- Search query or product keyword
- Brand
- Model
- Category
- Priority
- Status
- Retry count
- Last error
- Created time
- Updated time

Supported statuses:

- pending
- running
- done
- failed
- skipped
- paused

### 6. Checkpoint Recovery

The bot must continue from the last safe point after crash, internet failure, manual stop or restart.

Checkpoint must store:

- Current query
- Current product
- Current seller
- Page or position index
- Job status
- Retry count
- Last successful save time

---

## P1 - Core Torob Bot Requirements

### 7. Input Requirements

The bot must accept structured input from the local panel and import files.

Required input fields:

- Product name
- Brand
- Model
- Category
- Search query
- Priority
- Active or inactive status
- Maximum result limit
- Optional AfraKala internal product ID
- Optional AfraKala current price
- Internal notes

Only active rows must be processed.

### 8. Product Search on Torob

The bot must search Torob using product names, brands, models and search queries.

For each search, it must identify related product result pages and store raw results before cleaning.

### 9. Product Data Extraction

For each matched Torob product, the bot must extract:

- Product title
- Normalized product title
- Brand if detectable
- Model if detectable
- Category if detectable
- Torob product URL
- Seller count
- Minimum price
- Maximum price
- Market price range
- Availability signal if detectable
- Extraction time

### 10. Seller Data Extraction

For each product, the bot must extract sellers and seller-level data:

- Seller name
- Seller price
- Seller Torob URL
- External shop URL if available
- Warranty text if available
- Seller rating if available
- Verified or trusted status if available
- Seller position in Torob results
- Extraction time

### 11. External Seller Website Crawling

If Torob provides an external seller website, the bot must crawl public pages only.

Pages to inspect:

- Home page
- Contact page
- About page
- Footer
- Header
- Terms or rules page when useful

Extractable data:

- Mobile number
- Landline number
- Email
- Address
- WhatsApp link
- Telegram link
- Instagram link
- Store name
- Public owner or manager name if available
- Brands detected on the site
- Product categories detected on the site

No login-only or private pages may be accessed.

### 12. Supplier Qualification

The bot must classify sellers based on how useful they are for AfraKala B2B work.

Initial classifications:

- Potential wholesaler
- Retail seller
- Official representative candidate
- Importer candidate
- Competitor
- Low-value seller
- Needs manual review

Classification can use website content, seller data, contact quality, price behavior and product variety.

### 13. Price Comparison

For each product, the bot must calculate:

- Minimum market price
- Maximum market price
- Average market price
- Median market price when enough data exists
- Price spread
- Seller distance from minimum price
- Seller distance from average price
- Suspicious low price flag
- Suspicious high price flag

### 14. AfraKala Price Comparison

If AfraKala internal price is available, the bot must compare it with Torob market data.

Required outputs:

- AfraKala price vs minimum market price
- AfraKala price vs average market price
- AfraKala price position: cheaper, close to market, expensive
- Price gap amount
- Price gap percentage

### 15. Price History

The bot must store price history, not only the latest price.

Each price record must include:

- Product reference
- Seller reference
- Price
- Product URL
- Seller URL
- Warranty text if available
- Extraction date and time
- Availability signal if detectable

### 16. Price Change Detection

The bot must detect price changes between runs.

Required fields:

- Previous price
- Current price
- Change amount
- Change percentage
- Increase or decrease status
- Significant change flag

Significant price changes must appear in a dedicated alerts output.

### 17. Duplicate Detection and Merge

The bot must prevent useless duplicate records.

Duplicate signals:

- Same Torob product URL
- Same Torob seller URL
- Same external website domain
- Same phone number
- Same seller name for same product
- Same normalized product title and model

If a duplicate is found, richer and newer data must update the existing record.

### 18. Data Cleaning and Normalization

Before final output, the bot must clean and normalize data.

Required cleaning:

- Normalize Persian and Arabic characters
- Trim extra spaces
- Convert price to numeric value
- Normalize mobile numbers
- Separate landline and mobile numbers
- Normalize URLs and domains
- Mark empty fields consistently
- Remove useless records with no meaningful product or seller data

---

## P1 - Outputs

### 19. Excel Output

The bot must generate structured Excel output with these sheets:

- Torob_Products
- Torob_Sellers
- Torob_Price_History
- Torob_Website_Extraction
- Torob_Duplicate_Report
- Torob_Price_Alerts
- Torob_Failed_Items
- Torob_Summary_Report

### 20. Database Output

The bot must store clean and raw data in a database.

SQLite is acceptable for the first phase. The design must allow future migration to PostgreSQL.

Required tables:

- torob_products
- torob_sellers
- torob_prices
- torob_price_history
- torob_website_extractions
- torob_duplicates
- torob_alerts
- jobs
- run_logs
- errors
- checkpoints

---

## P2 - Advanced Business Intelligence Requirements

### 21. Supplier Scoring

The bot should calculate supplier scores for AfraKala.

Suggested scores:

- Supplier Score
- Wholesale Potential Score
- Reliability Score
- Contactability Score
- Price Advantage Score
- Risk Score

### 22. Competitor Watchlist

The local panel must support a competitor watchlist.

For selected sellers, the bot should track:

- Product coverage
- Price changes
- New products
- Removed products
- Brands added
- Pricing behavior

### 23. Market Opportunity Detection

The bot should detect useful market opportunities such as:

- High price spread products
- Products with many sellers but weak trusted supply
- Products where AfraKala can compete on price
- Products with unstable supply
- Newly active sellers with strong prices

### 24. Warranty-Aware Price Analysis

The bot should not mix all prices blindly.

When possible, it must separate:

- Official warranty
- Shop warranty
- No warranty
- Unknown warranty

Warranty differences must affect price comparison confidence.

### 25. Product Matching with AfraKala Catalog

The bot should support matching Torob products with AfraKala internal products.

Matching signals:

- Brand
- Model
- Product code
- Capacity
- Color
- Warranty
- Normalized title

The bot must not assume two products are identical only because their titles are similar.

### 26. AI-Assisted Analysis

AI analysis may be used for:

- Seller classification
- Website summary
- Wholesaler detection
- Competitor detection
- Brand extraction
- Contact priority recommendation
- Suggested contact reason

AI output must be saved as structured fields, not only free text.

---

## P3 - Dashboard and API Readiness

### 27. Internal API Readiness

The Torob bot output must be ready for future API delivery to Afra Smart Assistant or the local dashboard.

Suggested API concepts:

- Product market summary
- Top supplier candidates
- Price alerts
- Competitor watchlist
- Price history
- Failed jobs

### 28. Operational Monitoring

The local panel should show:

- Running jobs
- Completed jobs
- Failed jobs
- Last run time
- Current speed profile
- Block or captcha events
- Number of products extracted
- Number of sellers extracted
- Number of websites crawled
- Number of price alerts

---

## Boundaries and Safety

The bot may only collect public business and product data.

Allowed:

- Public product data
- Public seller data
- Public prices
- Public shop website links
- Public contact data from seller websites

Not allowed:

- Private user data
- Data from normal Torob search users
- Login-only data
- Circumventing access controls
- Attempts to identify ordinary users searching on Torob

---

## Recommended Implementation Order

### Phase 1 - Foundation

- Local panel integration contract
- Database schema
- Queue manager
- Scheduler
- Configurable speed profiles
- Anti-blocking layer
- Logging and errors
- Checkpoint system

### Phase 2 - Core Torob Extraction

- Torob search job
- Product extraction
- Seller extraction
- Raw data storage
- Clean Excel output

### Phase 3 - Seller Website Crawling

- External website crawler
- Contact extraction
- Social link extraction
- Website extraction output

### Phase 4 - Price Intelligence

- Price comparison
- Price history
- Price change detection
- Alerts
- AfraKala price comparison

### Phase 5 - B2B Intelligence

- Supplier scoring
- Competitor watchlist
- AI-assisted seller classification
- Market opportunity report

### Phase 6 - Dashboard and API Integration

- Local panel status views
- Export controls
- Internal API contracts
- Operational monitoring

---

## First Development Target

The first practical milestone must not be full automation.

The first milestone should prove that the project can:

1. Read Torob jobs from local input.
2. Run with safe speed settings.
3. Extract product and seller data for a small test set.
4. Save raw data, clean data, logs and errors locally.
5. Resume from checkpoint after interruption.

Only after this milestone is stable should advanced AI and competitor intelligence be added.
