"""
Prompt templates for Gemini API calls
Language-specific prompts for extraction and recommendations
"""

GEMINI_PROMPTS = {
    'en': {
        'job_extraction': """You are an expert at analyzing job descriptions. Extract structured information with CONTEXTUAL AWARENESS and SEMANTIC UNDERSTANDING.

CRITICAL RULES:
1. PRESERVE SENTENCE INTEGRITY: Do NOT split sentences mid-meaning. If a requirement spans multiple lines or contains a list, extract it as ONE coherent item.
2. UNDERSTAND CONTEXT: "Strong technical experience in X, Y, Z" should extract "X", "Y", "Z" as technical skills, NOT split the sentence.
3. DETECT RELATIONSHIPS: Phrases like "experience in", "proficiency with", "knowledge of" indicate skills, not experience requirements.
4. SEMANTIC CLUSTERING: Group related skills together when they appear in the same context (e.g., "navigation, motion planning, SLAM" from one sentence should stay together).

EXTRACTION GUIDELINES:
- Technical skills: Any technologies, tools, languages, frameworks, systems. Include complete skill names even if part of a longer sentence.
- Soft skills: Interpersonal, communication, leadership abilities
- Methodologies: Processes, frameworks, approaches (Agile, Scrum, DevOps, etc.)
- Education: Degree requirements, certifications, educational background needed
- Experience: Years of experience, specific industry/domain experience (NOT skill experience - that goes in technical_skills)

EXAMPLES:
Input: "Strong technical experience in at least one of: navigation, motion planning and controls, SLAM, perception/computer vision"
Should extract: technical_skills: ["navigation", "motion planning and controls", "SLAM", "perception/computer vision"]

Input: "5+ years of software engineering experience"
Should extract: experience: ["5+ years of software engineering experience"]

Return ONLY valid JSON in this exact format:
{{
    "technical_skills": ["complete skill name", "another skill", ...],
    "soft_skills": ["skill1", "skill2", ...],
    "methodologies": ["method1", "method2", ...],
    "education": ["requirement1", "requirement2", ...],
    "experience": ["requirement1", "requirement2", ...]
}}

Job Description: {text}""",
        
        'cv_extraction': """You are an expert at analyzing resumes. Extract structured information with CONTEXTUAL AWARENESS to capture both explicit skills AND implicit skills from experience/projects.

CRITICAL RULES:
1. EXTRACT SKILLS FROM CONTEXT: If someone worked on "autonomous navigation systems", extract related technical skills like "SLAM", "motion planning", "perception" even if not explicitly listed.
2. PRESERVE PROJECT CONTEXT: Extract skills mentioned in project descriptions and experience sections.
3. INFER FROM EXPERIENCE: If resume mentions "developed computer vision pipeline", extract "computer vision" as a technical skill.
4. COMPLETE SKILL NAMES: Keep full, coherent skill names (e.g., "motion planning and controls", not split fragments).

EXTRACTION GUIDELINES:
- Technical skills: From explicit lists AND from project/experience descriptions
- Soft skills: Interpersonal, communication, leadership (from descriptions, not just lists)
- Methodologies: Processes used (from experience descriptions, not just skill sections)
- Education: Degrees, certifications, courses, academic background
- Experience: Job titles, roles, project descriptions (include enough context to understand what skills were used)

EXAMPLES:
If resume says: "Developed SLAM system for autonomous robots using ROS2"
Extract: technical_skills should include ["SLAM", "ROS2", "autonomous systems"]

If resume says: "5 years as Software Engineer working with Python, Docker, Kubernetes"
Extract: technical_skills: ["Python", "Docker", "Kubernetes"] AND experience: ["5 years as Software Engineer"]

Return ONLY valid JSON in this exact format:
{{
    "technical_skills": ["complete skill name", "another skill", ...],
    "soft_skills": ["skill1", "skill2", ...],
    "methodologies": ["method1", "method2", ...],
    "education": ["item1", "item2", ...],
    "experience": ["item1 with context", "item2 with context", ...]
}}

Candidate Profile: {text}""",
        
        'recommendations': """Based on the job fit analysis, provide specific, actionable recommendations for the candidate to improve their fit for this role. Focus on:

1. Missing critical skills that should be learned
2. Skills that need better highlighting in the resume
3. Experience gaps that should be addressed
4. Specific examples or projects to add

Return ONLY valid JSON in this exact format:
{{
    "learn_skills": ["skill1", "skill2", ...],
    "highlight_skills": ["skill1", "skill2", ...],
    "add_experience": ["experience1", "experience2", ...],
    "specific_examples": ["example1", "example2", ...]
}}

Job Requirements: {job_skills}
Candidate Skills: {candidate_skills}
Fit Scores: {fit_scores}""",
        
        'enrichment': """Generate related terms and close synonyms for each of the following items. Return ONLY valid compact JSON mapping each original item to an array of related terms.

Items: {items}""",
        
        'dynamic_weights': """Given this job description, estimate relative importance (percentages summing to 100) of: technical_skills, soft_skills, methodologies, experience_education. Return ONLY JSON like {{"technical_skills":40,"soft_skills":25,"methodologies":20,"experience_education":15}}.

Job Description: {job_text}""",
        
        'missing_skills': """From the lists below, identify critical missing or underrepresented skills from the candidate compared to the job. Return ONLY JSON as {{"missing":[...]}} with concise skill names.

Job: {job_skills}
Candidate: {candidate_skills}"""
    },
    
    'fr': {
        'job_extraction': """Analysez cette description de poste et extrayez les informations structurées au format JSON. Concentrez-vous sur l'identification de :

1. Compétences techniques (langages de programmation, frameworks, outils, technologies)
2. Compétences comportementales (communication, leadership, travail d'équipe, etc.)
3. Méthodologies (agile, scrum, devops, etc.)
4. Exigences d'éducation (diplômes, certifications)
5. Exigences d'expérience (années, expérience spécifique)

Retournez UNIQUEMENT du JSON valide dans ce format exact :
{{
    "technical_skills": ["compétence1", "compétence2", ...],
    "soft_skills": ["compétence1", "compétence2", ...],
    "methodologies": ["méthode1", "méthode2", ...],
    "education": ["exigence1", "exigence2", ...],
    "experience": ["exigence1", "exigence2", ...]
}}

Description du poste : {text}""",
        
        'cv_extraction': """Analysez ce profil de candidat/CV et extrayez les informations structurées au format JSON. Concentrez-vous sur l'identification de :

1. Compétences techniques (langages de programmation, frameworks, outils, technologies)
2. Compétences comportementales (communication, leadership, travail d'équipe, etc.)
3. Méthodologies (agile, scrum, devops, etc.)
4. Éducation (diplômes, certifications, cours)
5. Expérience (années, expérience spécifique, réalisations)

Retournez UNIQUEMENT du JSON valide dans ce format exact :
{{
    "technical_skills": ["compétence1", "compétence2", ...],
    "soft_skills": ["compétence1", "compétence2", ...],
    "methodologies": ["méthode1", "méthode2", ...],
    "education": ["élément1", "élément2", ...],
    "experience": ["élément1", "élément2", ...]
}}

Profil du candidat : {text}""",
        
        'recommendations': """Basé sur l'analyse d'adéquation du poste, fournissez des recommandations spécifiques et actionables pour que le candidat améliore son adéquation pour ce rôle. Concentrez-vous sur :

1. Compétences critiques manquantes qui devraient être apprises
2. Compétences qui doivent être mieux mises en évidence dans le CV
3. Lacunes d'expérience qui doivent être comblées
4. Exemples ou projets spécifiques à ajouter

Retournez UNIQUEMENT du JSON valide dans ce format exact :
{{
    "learn_skills": ["compétence1", "compétence2", ...],
    "highlight_skills": ["compétence1", "compétence2", ...],
    "add_experience": ["expérience1", "expérience2", ...],
    "specific_examples": ["exemple1", "exemple2", ...]
}}

Exigences du poste : {job_skills}
Compétences du candidat : {candidate_skills}
Scores d'adéquation : {fit_scores}""",
        
        'enrichment': """Générez des termes connexes et des synonymes proches pour chacun des éléments suivants. Retournez UNIQUEMENT du JSON compact valide mappant chaque élément original à un tableau de termes connexes.

Éléments : {items}""",
        
        'dynamic_weights': """Étant donné cette description de poste, estimez l'importance relative (pourcentages totalisant 100) de : technical_skills, soft_skills, methodologies, experience_education. Retournez UNIQUEMENT du JSON comme {{"technical_skills":40,"soft_skills":25,"methodologies":20,"experience_education":15}}.

Description du poste : {job_text}""",
        
        'missing_skills': """À partir des listes ci-dessous, identifiez les compétences critiques manquantes ou sous-représentées du candidat par rapport au poste. Retournez UNIQUEMENT du JSON sous la forme {{"missing":[...]}} avec des noms de compétences concis.

Poste : {job_skills}
Candidat : {candidate_skills}"""
    }
}

