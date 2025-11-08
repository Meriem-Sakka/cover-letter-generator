# Cover Letter Generator

AI-powered cover letter generation tool that creates personalized cover letters tailored to your resume and job descriptions using Google Gemini API.

## Features

- **Resume Parsing**: Extract text from PDF and images (JPG/PNG) using OCR
- **AI-Generated Cover Letters**: Powered by Google Gemini API with customizable tone and language
- **Job Fit Analysis**: Advanced matching algorithm with embeddings-based similarity scoring
- **A/B Testing**: Generate and compare multiple cover letter variations
- **Interview Prep**: Get personalized interview questions and talking points
- **Multi-language Support**: English, French, and Arabic
- **Export Options**: PDF export for cover letters and analysis reports
- **History Management**: Save and retrieve previous cover letters

## Quick Start

### Prerequisites

- Python 3.8+
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))
- Tesseract OCR (for image-based resumes)

### Installation

1. **Clone and setup**
   ```bash
   git clone https://github.com/yourusername/cover-letter-generator.git
   cd cover-letter-generator
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Install Tesseract OCR**
   - **Windows**: [Download installer](https://github.com/UB-Mannheim/tesseract/wiki)
   - **macOS**: `brew install tesseract`
   - **Linux**: `sudo apt-get install tesseract-ocr`

3. **Configure environment**
   Create a `.env` file:
   ```bash
   GEMINI_API_KEY=your_api_key_here
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

## Usage

1. Upload your resume (PDF, JPG, or PNG)
2. Paste the job description
3. Customize tone, language, and add instructions
4. Generate your personalized cover letter
5. Review job fit analysis and recommendations
6. Export as PDF or save to history

## Project Structure

```
cover-letter-generator/
├── app.py                 # Main Streamlit application
├── src/
│   ├── core/             # Business logic (AI generation, job fit, resume parsing)
│   ├── services/         # External integrations (Gemini API, A/B testing, interview prep)
│   ├── analyzers/        # Analysis algorithms (matching, scoring)
│   ├── models/           # Data models
│   ├── utils/            # Utilities (normalization, prompts, cache, UI helpers)
│   └── config/           # Configuration
├── data/                  # Runtime data (cache, database)
└── output/                # Generated files (PDFs)
```

## Configuration

Configuration is managed in `src/config/settings.py`:
- API timeouts and model selection
- Scoring weights and matching thresholds
- Cache settings

## Dependencies

Key dependencies:
- `streamlit` - Web UI framework
- `google-generativeai` - Gemini API client
- `sentence-transformers` - Embeddings for matching
- `reportlab` - PDF generation
- `pdfplumber`, `pytesseract` - Document parsing

See `requirements.txt` for complete list.

## Notes

- Only resume text and job description are sent to the Gemini API
- Tesseract OCR must be installed and available on PATH for image processing
- Local SQLite databases are created in the `data/` directory
- Generated PDFs are saved in the `output/` directory

## License

MIT License

---

**Built with Streamlit and Google Gemini AI**
