# FlyOS: Intelligent Cash Flow Optimization for E-commerce

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2.4-black?logo=next.js&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5.2-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.2.2-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Anthropic AI](https://img.shields.io/badge/Anthropic_AI-Claude-orange?logo=anthropic&logoColor=white)](https://www.anthropic.com/)

## Overview

FlyOS is a sophisticated commerce operating system designed to empower e-commerce businesses, particularly those with direct-to-consumer (DTC) models, by rapidly identifying and resolving cash flow inefficiencies. Developed during the Wayflyer × Fin Hackathon in London (June 3–5, 2026), FlyOS provides actionable insights to liberate trapped capital from inventory and outstanding purchase orders, transforming raw data into immediate financial recovery strategies.

## Features

- **Intelligent Cash Leak Detection:** Analyzes 24 months of DTC data to pinpoint exact sources of trapped cash, such as slow-moving inventory or delayed payments.
- **Actionable Recommendations:** Generates ranked, evidence-backed actions to recover cash, prioritizing impact and feasibility.
- **Automated Outreach:** Facilitates one-click email campaign generation (via LLM) for engaging with suppliers or customers to expedite cash recovery.
- **Data-Driven Validation:** Incorporates 20 reconciliation checks to ensure data integrity and accuracy before presenting insights.
- **Historical Backtesting:** Provides a robust backtesting engine to validate the effectiveness of cash recovery algorithms against historical data.
- **User-Friendly Interface:** A modern Next.js frontend for intuitive data ingestion, validation, and insight visualization.

## Tech Stack

FlyOS leverages a robust and modern technology stack to deliver high performance and scalability:

- **Backend:**
  - **Python 3.9+:** Core programming language.
  - **FastAPI:** High-performance web framework for building APIs.
  - **Pandas:** Data manipulation and analysis for cash engine logic.
  - **Uvicorn:** ASGI server for running the FastAPI application.
  - **Anthropic AI (Claude):** Utilized for generating explanations and email copy, ensuring numbers never directly touch the LLM.

- **Frontend:**
  - **Next.js:** React framework for building server-rendered and static web applications.
  - **npm:** Package manager for JavaScript dependencies.
  - **TypeScript:** Strongly typed superset of JavaScript for enhanced code quality.

## Getting Started

Follow these steps to set up and run FlyOS locally.

### Prerequisites

- Python 3.9+
- Node.js (LTS version) & npm
- An Anthropic API Key (for Claude integration)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/MuhammadHaseebRafique/FlyOS.git
    cd FlyOS
    ```

2.  **Prepare your data:**
    Place your Pretty Fly DTC data (CSVs) into the `./data/` directory.

3.  **Backend Setup:**
    ```bash
    cd backend
    pip install -r requirements.txt
    cp .env.example .env # Add your ANTHROPIC_API_KEY to the .env file
    uvicorn main:app --reload --port 8000
    ```

4.  **Frontend Setup:**
    ```bash
    cd ../frontend
    npm install
    npm run dev
    ```

5.  **Access the Application:**
    Open your browser and navigate to `http://localhost:3000`.
    Follow the on-screen prompts to ingest data, validate, and discover cash leaks.

## Architecture

FlyOS employs a clear separation of concerns, ensuring data integrity and efficient processing:

```mermaid
graph TD
    A[Pretty Fly CSVs (21 files)] --> B(DataLoader)
    B --> C{validate.py}
    C -- 20 reconciliation checks --> D(cash_engine.py - Pandas)
    D --> E(FastAPI - Port 8000)
    E <--> F(Next.js - Port 3000)
    F --> G(Claude API - Explanations + Email Copy)
```

### Key Design Principles:

-   **Computational Integrity:** All numerical computations and financial analyses are performed by Pandas, ensuring that sensitive financial data never directly interacts with the LLM.
-   **Data Validation First:** The system enforces strict data validation (20 reconciliation checks) before any analysis is performed. The UI is blocked if validation fails, preventing erroneous insights.
-   **Temporal Consistency:** The system operates with a defined 
temporal context, with "Today" set to 2026-06-01 for consistent dataset interpretation.
-   **Core Data Model:** The cash computation is driven by four essential tables: `bank_transactions`, `inventory_movements`, `po_line_items`, and `line_items`.
-   **Credibility through Backtesting:** A robust backtest engine provides historical proof of the algorithm's efficacy, enhancing trust in its recommendations.

## Project Structure

```
FlyOS/
├── backend/                # FastAPI backend application
│   ├── main.py             # Main FastAPI application
│   ├── cash_engine.py      # Pandas-based cash flow analysis engine
│   ├── validate.py         # Data validation and reconciliation logic
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js frontend application
│   ├── pages/              # React pages
│   ├── components/         # Reusable React components
│   └── package.json        # Node.js dependencies
├── data/                   # Placeholder for Pretty Fly CSV data
├── docs/                   # Project documentation (PRD, TRD, SE, DEMO_SCRIPT)
├── prompts/                # Prompts used for Cursor Chat development
├── .env.example            # Example environment variables
├── LICENSE                 # Project license
└── README.md               # This README file
```

## Documentation

Detailed documentation for FlyOS can be found in the `docs/` directory:

-   [`docs/PRD.md`](docs/PRD.md) — Product Requirements Document
-   [`docs/TRD.md`](docs/TRD.md) — Technical Requirements Document
-   [`docs/SE.md`](docs/SE.md) — Software Engineering Specification
-   [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) — Judge Demo Walkthrough Script

## Contributing

We welcome contributions to FlyOS! Please refer to the `docs/CONTRIBUTING.md` (if available) for guidelines on how to contribute.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For any inquiries or further information, please contact Muhammad Haseeb Rafique.

---

## Acknowledgements

This project was developed as part of the Wayflyer × Fin Hackathon 2026. Special thanks to the organizers and mentors for their support.

## Disclaimer

The data used in this project is fictional and for demonstration purposes only.
