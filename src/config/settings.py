"""
Centralized configuration for the app
"""

import os

# Cache settings
CACHE_DIR = os.path.join(os.getcwd(), 'data', 'cache')
CACHE_DB_PATH = os.path.join(CACHE_DIR, 'analysis_cache.db')
os.makedirs(CACHE_DIR, exist_ok=True)

# Modes
DEFAULT_ANALYSIS_MODE = 'Fast'  # 'Fast' or 'Deep'
SUPPORTED_MODES = ['Fast', 'Deep']

# Timeouts (seconds)
TIMEOUTS = {
    'Fast': {
        'extraction': 12.0,
        'embedding': 8.0,
        'enrichment': 8.0,
    },
    'Deep': {
        'extraction': 20.0,
        'embedding': 15.0,
        'enrichment': 15.0,
    }
}

# Performance caps
MAX_ENRICH_VARIANTS_PER_ITEM = 5  # original + 4 expansions
MAX_PAIRS_PER_CATEGORY = 3000     # cap comparisons per category

# Gemini API settings
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODELS = {
    'extraction_pro': 'gemini-2.0-pro',
    'extraction_flash': 'gemini-2.0-flash',
    'embedding': 'models/text-embedding-004',
    'embedding_fallback': 'models/embedding-001',
    'enrichment': 'gemini-2.0-flash',
    'recommendations': 'gemini-2.0-flash',
    'dynamic_weights': 'gemini-2.0-pro',
    'missing_skills': 'gemini-2.0-pro'
}

# Rate limiting
RATE_LIMIT_MIN_INTERVAL = 0.5  # seconds between API calls
RATE_LIMIT_MAX_RETRIES = 3
RATE_LIMIT_BASE_SLEEP = 1.0  # base sleep time for exponential backoff
RATE_LIMIT_ENRICHMENT_RETRIES = 2
RATE_LIMIT_ENRICHMENT_BASE_SLEEP = 0.75

# Matching thresholds
MATCHING_THRESHOLDS = {
    'Fast': {
        'technical': 0.55,
        'soft': 0.55,
        'methodologies': 0.55,
        'experience_education': 0.75
    },
    'Deep': {
        'technical': 0.50,
        'soft': 0.50,
        'methodologies': 0.50,
        'experience_education': 0.70
    }
}

# Match type thresholds
MATCH_TYPE_THRESHOLDS = {
    'exact': 0.85,
    'semantic': 0.70,
    'partial': 0.50
}

# Scoring weights
SCORING_WEIGHTS = {
    'technical_skills': 0.40,
    'soft_skills': 0.25,
    'methodologies': 0.20,
    'experience_education': 0.15
}

# Hybrid matching weights
HYBRID_WEIGHTS = {
    'semantic': 0.7,
    'keyword': 0.3
}

# BM25 parameters
BM25_K1 = 1.5
BM25_B = 0.75

# Education/Experience processing
DEGREE_KEYWORDS = [
    'diplome', 'diplôme', 'licence', 'license', 'master', 'mastère', 'bachelor', 'ingenieur',
    'ingénieur', 'phd', 'doctorat', 'maitrise', 'maîtrise', 'msc', 'bsc', 'bac', 'bac+5', 'm1', 'm2'
]

ROLE_KEYWORDS = [
    'engineer', 'ingénieur', 'ingenieur', 'développeur', 'developer', 'data scientist', 'analyst',
    'analyste', 'manager', 'lead', 'intern', 'stagiaire', 'chef de projet', 'responsable', 'architect',
    'consultant', 'technicien', 'technician', 'researcher', 'chercheur'
]

EDUCATION_CONNECTOR_KEYWORDS = [' - ', ' — ', '–', ' at ', ' chez ', ' à ', ' @ ']

EDUCATION_CONTEXT_KEYWORDS = [
    'diplome', 'diplomee', 'diplome(e)', 'diplome(s)', 'diplomee(s)', 'diplomee(e)', 'diplomee(e)s',
    'diplomee(e)s', 'diplomee', 'diplome', 'diplôme', 'diplômé', 'diplômée', 'diplômé(e)',
    'ecole', 'école', 'grande ecole', 'universite', 'université', 'formation', 'specialite', 'spécialité',
    'bac', 'bac+1', 'bac+2', 'bac+3', 'bac+4', 'bac+5', 'bac +1', 'bac +2', 'bac +3', 'bac +4', 'bac +5',
    'master', 'licence', 'ingenieur', 'ingénieur', 'msc', 'bsc', 'phd', 'degree', 'bachelor', 'masters',
    'diploma', 'major in', 'specialization', 'speciality'
]

INTERNSHIP_PROJECT_KEYWORDS = [
    'stagiaire', 'stage', 'intern', 'internship', 'apprentice', 'apprentissage', 'alternance',
    'projet', 'project', 'pfe', 'capstone'
]

# Fit level thresholds
FIT_LEVEL_THRESHOLDS = {
    'Excellent': 80,
    'Good': 60,
    'Fair': 40,
    'Poor': 0
}


# Domain aliases/synonyms for better matching (expand over time)
# Key is canonical term -> list of aliases/variants/acronyms
TECH_ALIASES = {
    'slam': [
        'simultaneous localization and mapping',
        'simultaneous localisation and mapping',
        'vslam', 'visual slam', 'lidar slam', 'graph slam'
    ],
    'lidar': ['li dar', 'li-dar', 'laser scanning', 'laser radar', 'velodyne'],
    'ros2': ['ros 2', 'robot operating system 2'],
    'ros': ['robot operating system', 'ros1', 'ros 1'],
    'navigation': ['robot navigation', 'autonomous navigation', 'localization and navigation'],
    'motion planning': ['path planning', 'trajectory planning', 'planning and controls', 'planning & controls'],
    'perception': ['computer vision', 'cv', 'visual perception', 'scene perception'],
    'sensor fusion': ['multi-sensor fusion', 'sensor data fusion', 'sensor integration'],
    'kalman filter': ['ekf', 'ukf', 'extended kalman filter', 'unscented kalman filter'],
    'point cloud': ['pointcloud', 'point clouds', 'pcl', 'pcl library'],
    'opencv': ['open cv'],
}


