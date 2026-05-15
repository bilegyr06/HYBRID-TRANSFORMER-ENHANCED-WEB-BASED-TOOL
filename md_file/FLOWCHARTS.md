# LitReview AI - System Flowcharts

This document contains comprehensive flowcharts describing the LitReview AI system from multiple perspectives.

---

## 1. User Flow Diagram
**Overview:** Shows the complete user journey through the application, from login to saving reviews.

```mermaid
flowchart TD
    Start([User Visits App]) --> CheckAuth{Authenticated?}
    CheckAuth -->|No| Login[Login Page]
    CheckAuth -->|Yes| Dashboard[Dashboard]
    
    Login --> LoginChoice{User Action}
    LoginChoice -->|Has Account| LoginForm[Enter Credentials]
    LoginChoice -->|New User| Register[Register Page]
    
    Register --> RegisterForm[Fill Registration]
    RegisterForm --> RegSuccess{Registration<br/>Successful?}
    RegSuccess -->|No| Register
    RegSuccess -->|Yes| Login
    
    LoginForm --> LoginSuccess{Login<br/>Successful?}
    LoginSuccess -->|No| Login
    LoginSuccess -->|Yes| Dashboard
    
    Dashboard --> DashChoice{User Action}
    DashChoice -->|Upload & Process| Upload[Upload Page]
    DashChoice -->|View Reviews| MyReviews[My Reviews Page]
    DashChoice -->|Settings| Settings[Settings Page]
    DashChoice -->|Logout| Start
    
    Upload --> FileUpload[Select & Upload Files]
    FileUpload --> Processing[Processing Loader]
    Processing --> Results[Results Page]
    
    Results --> ResultChoice{User Action}
    ResultChoice -->|Save Review| SaveReview[Enter Review Title]
    ResultChoice -->|Go Back| Upload
    ResultChoice -->|View Reviews| MyReviews
    
    SaveReview --> SaveSuccess{Review<br/>Saved?}
    SaveSuccess -->|Yes| MyReviews
    SaveSuccess -->|No| Results
    
    MyReviews --> ReviewChoice{User Action}
    ReviewChoice -->|View Review| Results
    ReviewChoice -->|Back to Upload| Upload
    ReviewChoice -->|Dashboard| Dashboard
```

**Key Points:**
- User must authenticate before accessing any app features
- Main hub is the Dashboard with three primary actions
- Upload flow: File upload → Processing → Results → Save review
- Reviews can be viewed from multiple entry points
- Logout returns user to login state

---

## 2. Data Flow Diagram
**Overview:** Illustrates how data moves between the frontend, backend, database, and processing services.

```mermaid
graph TB
    User["👤 User"]
    FE["🎨 Frontend<br/>React + TypeScript"]
    API["⚙️ FastAPI Backend"]
    DB[("🗄️ Database<br/>SQLAlchemy")]
    TextRank["🔍 TextRank"]
    BART["📝 BART"]
    ROUGE["📊 ROUGE"]
    
    User -->|Input| FE
    
    FE -->|Auth Requests| API
    FE -->|Process/Save| API
    FE -->|Fetch Reviews| API
    
    API -->|Query/Store| DB
    API -->|JWT Token| FE
    API -->|Results| FE
    
    API -->|Text| TextRank
    API -->|Text| BART
    API -->|Summaries| ROUGE
    
    TextRank -->|Sentences| API
    BART -->|Summary| API
    ROUGE -->|Scores| API
    
    FE -->|Display| User
```

**Key API Endpoints:**
- **Authentication:** `POST /register` • `POST /login` • `GET /users/me` • `POST /logout`
- **Processing:** `POST /reviews/process`
- **Management:** `POST /reviews/save` • `GET /reviews` • `GET /reviews/{id}`

**Processing Services:**
- **TextRank:** Extracts key sentences (extractive summarization)
- **BART:** Generates new summaries (abstractive summarization)  
- **ROUGE:** Calculates quality metrics and scores

**Key Endpoints:**
- **Authentication:** `POST /register`, `POST /login`, `GET /users/me`, `POST /logout`
- **Reviews:** `POST /reviews/process`, `POST /reviews/save`, `GET /reviews`, `GET /reviews/{id}`

**Processing Pipeline:**
- TextRank → Extracts key sentences from documents
- BART → Generates abstractive summaries
- ROUGE → Calculates quality metrics

---

## 3. Full Architecture Diagram
**Overview:** Comprehensive view of all system layers, components, and their relationships.

```mermaid
flowchart TB
    subgraph Frontend["🎨 Frontend Layer"]
        App[App.tsx<br/>Main Router]
        Auth["Auth Pages<br/>(Login/Register)"]
        Dashboard["Dashboard<br/>Navigation Hub"]
        Upload["Upload Page<br/>File Handler"]
        Results["Results Page<br/>Display Output"]
        Reviews["My Reviews<br/>List & View"]
        Settings["Settings<br/>User Prefs"]
        
        App --> Auth
        App --> Dashboard
        Dashboard --> Upload
        Dashboard --> Reviews
        Dashboard --> Settings
        Upload --> Results
        Results --> Results
    end
    
    subgraph Backend["⚙️ Backend Layer"]
        Routes["API Routes<br/>(FastAPI)"]
        Auth_Service["Auth Service<br/>(JWT)"]
        Review_Service["Review Service<br/>(Save/Fetch)"]
        Process_Service["Processing Service<br/>(Orchestrate)"]
        
        Routes --> Auth_Service
        Routes --> Review_Service
        Routes --> Process_Service
    end
    
    subgraph Processing["🔬 Processing Layer"]
        TextRank_Svc["TextRank Service<br/>(Extractive)"]
        BART_Svc["BART Service<br/>(Abstractive)"]
        ROUGE_Svc["ROUGE Calculator<br/>(Metrics)"]
        TFIDF_Svc["TFIDF Service<br/>(Keywords)"]
        
        Process_Service --> TextRank_Svc
        Process_Service --> BART_Svc
        Process_Service --> ROUGE_Svc
        Process_Service --> TFIDF_Svc
    end
    
    subgraph Database["🗄️ Data Layer"]
        Users["Users Table"]
        Reviews_Table["Reviews Table"]
        Sessions["Sessions/Auth"]
    end
    
    Frontend -->|API Calls| Backend
    Backend -->|Query/Store| Database
    Backend -.->|Process Text| Processing
    Processing -->|Results| Backend
    Backend -->|JSON Response| Frontend
```

**Component Breakdown:**

### Frontend Layer (React + TypeScript)
- **App.tsx:** Main router managing page navigation
- **Auth Pages:** Login and registration pages
- **Dashboard:** Central hub with navigation to all features
- **Upload Page:** File selection and upload handler
- **Results Page:** Display processing results and summaries
- **My Reviews:** View and manage saved reviews
- **Settings:** User preferences and account info

### Backend Layer (FastAPI)
- **API Routes:** HTTP endpoint handlers
- **Auth Service:** JWT token management and user authentication
- **Review Service:** Database operations for reviews (save, retrieve)
- **Processing Service:** Orchestrates document processing workflow

### Processing Layer
- **TextRank Service:** Extracts key sentences (extractive summarization)
- **BART Service:** Generates abstractive summaries
- **ROUGE Calculator:** Computes quality metrics
- **TFIDF Service:** Identifies key themes and topics

### Database Layer (SQLAlchemy)
- **Users Table:** User accounts and credentials
- **Reviews Table:** Saved reviews with metadata
- **Sessions/Auth:** Authentication tokens and sessions

---

## 4. Processing Pipeline
**Overview:** Step-by-step workflow for processing input documents into complete reviews.

```mermaid
flowchart TD
    Input["📄 Input: Multiple<br/>Text Documents"]
    Input --> Preprocess["Preprocessing<br/>• Tokenization<br/>• Cleaning"]
    
    Preprocess --> Split["Split into Sentences"]
    Split --> Extract["Extractive Summary<br/>(TextRank)<br/>• Rank Sentences<br/>• Select Top-K"]
    Split --> Abstract["Abstractive Summary<br/>(BART)<br/>• Generate New Sentences"]
    
    Extract --> ExtractOut["Key Sentences"]
    Abstract --> AbstractOut["Synthesized Summary"]
    
    ExtractOut --> Metrics["Calculate Metrics<br/>(ROUGE)"]
    AbstractOut --> Metrics
    
    Metrics --> KeyThemes["Extract Key Themes<br/>(TFIDF)"]
    KeyThemes --> Viz["Generate Metadata<br/>for Visualization"]
    
    Viz --> Output["📊 Output:<br/>Complete Review"]
    Output --> Save["Save to Database"]
    Save --> Display["Return to Frontend"]
```

**Processing Steps:**

1. **Input:** Multiple academic abstracts/papers uploaded by user
2. **Preprocessing:** Text cleaning, tokenization, normalization
3. **Split:** Break documents into individual sentences for analysis
4. **Parallel Processing:**
   - **Extractive:** TextRank ranks and selects most important sentences
   - **Abstractive:** BART generates new, condensed sentences
5. **Metrics:** ROUGE scores evaluate quality of summaries
6. **Theme Extraction:** TFIDF identifies key concepts and themes
7. **Metadata Generation:** Create visualization data
8. **Output:** Complete review with all summaries, metrics, and themes
9. **Storage:** Save to database for future reference
10. **Display:** Return formatted data to frontend

---

## Architecture Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React + TypeScript + Vite | User interface and navigation |
| **Backend** | FastAPI + SQLAlchemy | API endpoints and business logic |
| **Processing** | TextRank, BART, ROUGE, TFIDF | Document analysis and summarization |
| **Database** | SQLAlchemy + Alembic | Data persistence |
| **Authentication** | JWT | User session management |

---

## File References

- **Frontend:** [frontend/src/App.tsx](../frontend/src/App.tsx)
- **Backend:** [backend/src/main.py](../backend/src/main.py)
- **Routes:** [backend/src/api/routes.py](../backend/src/api/routes.py)
- **Services:** [backend/src/services/](../backend/src/services/)
- **Models:** [backend/src/models/](../backend/src/models/)

