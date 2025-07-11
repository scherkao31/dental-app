# 🦷 Dental AI Assistant Suite

A comprehensive AI-powered dental practice management system with specialized LLMs for different dental workflows.

## 🚀 Features

### 🤖 Specialized AI Assistants
- **Dental Brain**: Treatment planning and clinical decision support
- **Swiss Law**: Legal compliance and regulations for Swiss dental practices
- **Invisalign**: Orthodontic treatment planning and case selection
- **Patient Education**: Automated generation of patient-friendly educational content
- **Scheduling AI**: Intelligent appointment rescheduling with autonomous decision making

### 📋 Practice Management
- **Patient Management**: Complete patient records and treatment history
- **Appointment Scheduling**: Drag-and-drop calendar with conflict detection
- **Treatment Planning**: Interactive treatment sequences with cost estimation
- **Financial Management**: Devis generation, invoicing, and payment tracking
- **Document Generation**: Automated PDFs for treatment plans and patient education

### 🔍 Advanced RAG System
- **Knowledge Base**: 66+ dental knowledge articles
- **Clinical Cases**: 11+ real clinical cases for reference
- **Semantic Search**: Intelligent retrieval of relevant information
- **Multi-modal Context**: Combines cases, knowledge, and patient data

### 🎯 Key Capabilities
- **Autonomous Scheduling**: AI makes intelligent rescheduling decisions
- **Treatment Sequencing**: Automated treatment plan generation
- **Cost Estimation**: Swiss TARMED pricing integration
- **Patient Education**: Personalized educational documents
- **PowerPoint Generation**: Automated treatment presentations

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **AI**: OpenAI GPT-4 with specialized prompts
- **Database**: SQLite with custom ORM
- **Search**: Vector embeddings with cosine similarity
- **PDF Generation**: ReportLab
- **PowerPoint**: python-pptx

## 📦 Installation

### Prerequisites
- Python 3.8+
- OpenAI API key
- Git

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd PART_MAROC_JUIN
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. **Initialize the database**
   ```bash
   python database_manager.py
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   Open your browser and go to `http://localhost:5001`

## 🎮 Usage

### Getting Started
1. **Select a specialized AI tab** based on your needs
2. **Input your query** in natural language (French supported)
3. **Review AI suggestions** with relevant references
4. **Generate documents** (treatment plans, devis, education materials)
5. **Manage scheduling** with autonomous AI decisions

### Example Queries
- **Dental Brain**: "Plan de ttt pour la 24: 24 dém. CC + TR 3 canaux + MA + CC"
- **Scheduling**: "Je ne serai pas là mardi 15/7, reprogramme tous mes RDV"
- **Swiss Law**: "Quelles sont les obligations légales pour un dentiste en Suisse?"
- **Invisalign**: "Critères de sélection pour un cas Invisalign complexe"

## 📁 Project Structure

```
PART_MAROC_JUIN/
├── app.py                 # Main Flask application
├── database_manager.py    # Database operations
├── rag_system.py         # RAG and search functionality
├── static/
│   ├── app.js            # Frontend JavaScript
│   ├── style.css         # Styling
│   └── index.html        # Main HTML template
├── DATA/
│   ├── KNOWLEDGE_JSON/   # Knowledge base articles
│   ├── TRAITEMENTS_JSON/ # Clinical cases
│   └── TARMED_JSON/      # Swiss pricing data
├── templates/            # HTML templates
└── requirements.txt      # Python dependencies
```

## 🔧 Configuration

### Specialized LLMs
Each AI assistant has specialized prompts and context:
- **Dental Brain**: Clinical decision support with treatment planning
- **Swiss Law**: Legal compliance and regulatory guidance
- **Invisalign**: Orthodontic treatment planning
- **Patient Education**: Patient-friendly explanations

### RAG System
- **Knowledge Base**: Dental articles and procedures
- **Clinical Cases**: Real treatment examples
- **Semantic Search**: Vector-based similarity matching
- **Context Combination**: Multi-source information retrieval

## 🚨 Important Notes

### Security
- Never commit API keys or sensitive data
- Use environment variables for configuration
- Database files are excluded from version control

### Data Privacy
- Patient data is stored locally
- No patient information is sent to external APIs
- GDPR compliance considerations included

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is proprietary software for dental practice management.

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the logs for error messages
3. Ensure all dependencies are installed
4. Verify OpenAI API key is configured

## 🔄 Recent Updates

- ✅ Fixed educational content generation errors
- ✅ Improved modal closing functionality
- ✅ Enhanced RAG system with better case retrieval
- ✅ Added autonomous scheduling decisions
- ✅ Implemented comprehensive error handling

---

**Built with ❤️ for modern dental practices** 