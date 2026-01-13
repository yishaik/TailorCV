"""
Module 4: CV Generator

Produces the tailored CV based on mapping, reorganizing and rewriting
while maintaining factual accuracy.
"""
from typing import Optional
from ..models.job_requirements import JobRequirements
from ..models.cv_facts import CVFacts
from ..models.mapping import MappingResult
from ..models.output import (
    TailoredCV,
    TailoredHeader,
    TailoredExperience,
    TailoredExperienceBullet,
    TailoredSkills,
    TailoredEducation,
    TailoredCertification,
    TailoredProject,
    ChangeLogEntry,
    BorderlineItem
)
from ..models.options import StrictnessConfig, STRICTNESS_CONFIGS
from ..utils.llm_client import get_llm_client
from .job_extractor import get_keyword_priority_map
import logging

logger = logging.getLogger(__name__)


SUMMARY_GENERATION_PROMPT = """
Generate a professional summary for a CV tailored to this job.

JOB TITLE: {job_title}
JOB COMPANY: {company}

TOP REQUIREMENTS:
{requirements}

CANDIDATE'S EXPERIENCE:
- Total years: {total_years}
- Current/recent title: {current_title}
- Top skills: {top_skills}
- Key achievements: {key_achievements}

RULES:
1. Maximum 3-4 sentences
2. Front-load with strongest job-relevant qualifications
3. Include 2-3 high-priority keywords naturally: {keywords}
4. Use quantification ONLY from the provided achievements
5. Align title descriptor with the job title

OUTPUT FORMAT:
Return ONLY the summary text, no additional formatting or explanation.
"""


BULLET_REWRITE_PROMPT = """
Rewrite this CV bullet point to better align with the job requirements.

ORIGINAL BULLET:
{original}

JOB-RELEVANT KEYWORDS TO INTEGRATE (if naturally fitting):
{keywords}

JOB RESPONSIBILITIES IT RELATES TO:
{responsibilities}

RULES:
1. Keep ALL facts identical - same numbers, same scope, same outcome
2. Only change language/framing to match job description style
3. Integrate keywords ONLY where they naturally fit
4. Maintain or improve specificity - never make it vaguer
5. Keep bullet concise (max 2 lines)
6. If the original is already well-written, minimal changes are fine

OUTPUT FORMAT:
Return a JSON object:
{{
    "rewritten": "the rewritten bullet text",
    "keywords_used": ["list", "of", "keywords", "integrated"],
    "change_type": "rewrite" | "minimal" | "none",
    "explanation": "brief explanation of changes"
}}
"""


class CVGenerator:
    """Generates tailored CVs from mapping results."""

    def __init__(
        self,
        requirements: JobRequirements,
        cv_facts: CVFacts,
        mapping: MappingResult,
        strictness: str = "moderate",
        user_instructions: Optional[str] = None
    ):
        self.requirements = requirements
        self.cv_facts = cv_facts
        self.mapping = mapping
        self.config = STRICTNESS_CONFIGS.get(strictness, STRICTNESS_CONFIGS["moderate"])
        self.user_instructions = (user_instructions or "").strip()
        self.changes_log: list[ChangeLogEntry] = []
        self.borderline_items: list[BorderlineItem] = []
        self.client = get_llm_client()
    
    async def generate(self) -> tuple[TailoredCV, list[ChangeLogEntry], list[BorderlineItem]]:
        """Generate the complete tailored CV."""
        
        # Generate each section
        header = self._generate_header()
        summary = await self._generate_summary()
        experience = await self._generate_experience()
        skills = self._generate_skills()
        education = self._generate_education()
        certifications = self._generate_certifications()
        projects = self._generate_projects()
        
        cv = TailoredCV(
            header=header,
            summary=summary,
            experience=experience,
            skills=skills,
            education=education,
            certifications=certifications,
            projects=projects
        )
        
        return cv, self.changes_log, self.borderline_items
    
    def _generate_header(self) -> TailoredHeader:
        """Generate tailored header with job-aligned title."""
        
        # Determine appropriate title
        original_title = ""
        if self.cv_facts.experience:
            original_title = self.cv_facts.experience[0].title
        
        # Align title with job if appropriate
        job_title = self.requirements.job_title
        
        # Only use job title if it's reasonably close to original
        # Otherwise use original to avoid fabrication
        aligned_title = original_title or job_title
        
        if original_title and original_title.lower() != job_title.lower():
            self.changes_log.append(ChangeLogEntry(
                section="header",
                change_type="rewrite",
                original=original_title,
                new=aligned_title,
                justification="Kept original title to maintain accuracy",
                confidence="high",
                requires_review=False
            ))
        
        contact = {}
        info = self.cv_facts.personal_info
        if info.email:
            contact["email"] = info.email
        if info.phone:
            contact["phone"] = info.phone
        if info.location:
            contact["location"] = info.location
        if info.linkedin:
            contact["linkedin"] = info.linkedin
        if info.website:
            contact["website"] = info.website
        
        return TailoredHeader(
            name=info.name,
            title=aligned_title,
            contact=contact
        )
    
    async def _generate_summary(self) -> str:
        """Generate a tailored professional summary."""
        
        # Gather data for summary generation
        total_years = sum(
            (exp.duration_months or 0) for exp in self.cv_facts.experience
        ) / 12
        
        current_title = ""
        if self.cv_facts.experience:
            current_title = self.cv_facts.experience[0].title
        
        # Get top skills from CV that match requirements
        keyword_map = get_keyword_priority_map(self.requirements)
        cv_skills = list(self.cv_facts.skills.explicitly_listed)
        top_skills = [s for s in cv_skills if s.lower() in keyword_map][:5]
        if len(top_skills) < 3:
            top_skills.extend(cv_skills[:5 - len(top_skills)])
        
        # Get key achievements (quantified ones first)
        achievements = []
        for exp in self.cv_facts.experience[:2]:  # Recent experiences
            for ach in exp.achievements:
                if ach.quantified:
                    achievements.append(ach.original_text)
        achievements = achievements[:3]
        
        # Get high-priority keywords
        keywords = self.requirements.ats_keywords.high_priority[:5]
        
        # Build requirements summary
        req_summary = "\n".join([
            f"- {r.description}" for r in self.requirements.must_have[:5]
        ])
        
        prompt = SUMMARY_GENERATION_PROMPT.format(
            job_title=self.requirements.job_title,
            company=self.requirements.company or "the company",
            requirements=req_summary,
            total_years=f"{total_years:.1f}",
            current_title=current_title,
            top_skills=", ".join(top_skills),
            key_achievements="; ".join(achievements) if achievements else "Various accomplishments",
            keywords=", ".join(keywords)
        )
        prompt = self._apply_user_instructions(prompt)
        
        summary = await self.client.generate_text(prompt)
        summary = summary.strip().strip('"')
        
        # Log the change
        original_summary = ""
        if self.cv_facts.professional_summary:
            original_summary = self.cv_facts.professional_summary.original_text or ""
        
        self.changes_log.append(ChangeLogEntry(
            section="summary",
            change_type="rewrite",
            original=original_summary,
            new=summary,
            justification="Generated job-aligned summary using only facts from original CV",
            confidence="high",
            requires_review=True
        ))
        
        return summary
    
    async def _generate_experience(self) -> list[TailoredExperience]:
        """Generate tailored experience section."""
        
        # Get keywords to integrate
        keywords = (
            self.requirements.ats_keywords.high_priority +
            self.requirements.ats_keywords.medium_priority
        )[:15]
        
        # Get responsibilities for context
        responsibilities = [r.description for r in self.requirements.responsibilities[:5]]
        
        tailored_experiences = []
        
        for exp in self.cv_facts.experience:
            tailored_bullets = []
            
            # Combine responsibilities and achievements for bullet points
            all_items = []
            
            for resp in exp.responsibilities:
                all_items.append(resp.original_text)
            
            for ach in exp.achievements:
                all_items.append(ach.original_text)
            
            # Score bullets by relevance to job
            scored_items = []
            for item in all_items:
                score = self._score_bullet_relevance(item, keywords)
                scored_items.append((score, item))
            
            # Sort by relevance (most relevant first)
            scored_items.sort(reverse=True, key=lambda x: x[0])
            
            # Rewrite top bullets if needed
            for i, (score, original) in enumerate(scored_items[:6]):  # Keep top 6
                if self.config.allow_reframing != "minimal" and score < 80:
                    # Try to improve the bullet
                    rewritten = await self._rewrite_bullet(original, keywords, responsibilities)
                    tailored_bullets.append(rewritten)
                else:
                    tailored_bullets.append(TailoredExperienceBullet(
                        text=original,
                        keywords_used=self._find_keywords_in_text(original, keywords)
                    ))
            
            # Check if order changed
            original_order = [item for _, item in enumerate(all_items[:6])]
            new_order = [b.text for b in tailored_bullets]
            
            if original_order != new_order:
                self.changes_log.append(ChangeLogEntry(
                    section="experience",
                    change_type="reorder",
                    original=f"Original order for {exp.company}",
                    new="Reordered by job relevance",
                    justification="Most relevant achievements moved to top",
                    confidence="high",
                    requires_review=False
                ))
            
            tailored_experiences.append(TailoredExperience(
                company=exp.company,
                title=exp.title,
                dates=f"{exp.start_date} - {exp.end_date}",
                location=exp.location,
                bullets=tailored_bullets
            ))
        
        return tailored_experiences
    
    def _score_bullet_relevance(self, text: str, keywords: list[str]) -> int:
        """Score a bullet's relevance to the job."""
        score = 50  # Base score
        text_lower = text.lower()
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                score += 10
        
        # Bonus for quantified results
        if any(c.isdigit() for c in text):
            score += 5
        if "%" in text or "$" in text:
            score += 5
        
        return min(score, 100)
    
    async def _rewrite_bullet(
        self,
        original: str,
        keywords: list[str],
        responsibilities: list[str]
    ) -> TailoredExperienceBullet:
        """Rewrite a bullet to better align with job."""
        import json
        
        prompt = BULLET_REWRITE_PROMPT.format(
            original=original,
            keywords=", ".join(keywords[:10]),
            responsibilities="\n".join(f"- {r}" for r in responsibilities[:3])
        )
        prompt = self._apply_user_instructions(prompt)
        
        try:
            response = await self.client.generate_text(prompt)
            
            # Parse JSON response
            if "{" in response:
                start = response.index("{")
                end = response.rindex("}") + 1
                data = json.loads(response[start:end])
                
                rewritten = data.get("rewritten", original)
                keywords_used = data.get("keywords_used", [])
                change_type = data.get("change_type", "none")
                explanation = data.get("explanation", "")
                
                if change_type != "none":
                    self.changes_log.append(ChangeLogEntry(
                        section="experience",
                        change_type="rewrite",
                        original=original,
                        new=rewritten,
                        justification=explanation,
                        confidence="medium" if change_type == "rewrite" else "high",
                        requires_review=change_type == "rewrite"
                    ))
                    
                    if change_type == "rewrite":
                        self.borderline_items.append(BorderlineItem(
                            content=rewritten,
                            category="reframed_significantly",
                            original_evidence=original,
                            risk_level="low",
                            user_prompt=f"Original: '{original}'\nRewritten: '{rewritten}'\nIs this an accurate reframing?"
                        ))
                
                return TailoredExperienceBullet(text=rewritten, keywords_used=keywords_used)
        
        except Exception as e:
            logger.warning(f"Failed to rewrite bullet: {e}")
        
        # Return original if rewrite fails
        return TailoredExperienceBullet(
            text=original,
            keywords_used=self._find_keywords_in_text(original, keywords)
        )
    
    def _find_keywords_in_text(self, text: str, keywords: list[str]) -> list[str]:
        """Find which keywords appear in text."""
        text_lower = text.lower()
        return [kw for kw in keywords if kw.lower() in text_lower]
    
    def _generate_skills(self) -> TailoredSkills:
        """Generate prioritized skills section."""
        
        keyword_map = get_keyword_priority_map(self.requirements)
        all_skills = list(self.cv_facts.skills.explicitly_listed)
        
        # Add inferred skills if allowed
        if self.config.allow_inferred_skills:
            for inferred in self.cv_facts.skills.inferred_from_experience:
                if inferred.skill not in all_skills:
                    all_skills.append(inferred.skill)
        
        # Categorize by priority
        primary = []
        secondary = []
        tools = []
        
        for skill in all_skills:
            priority = keyword_map.get(skill.lower(), None)
            if priority == "high":
                primary.append(skill)
            elif priority in ["medium", "contextual"]:
                secondary.append(skill)
            else:
                tools.append(skill)
        
        # Ensure we have some primary skills
        if not primary and secondary:
            primary = secondary[:5]
            secondary = secondary[5:]
        
        return TailoredSkills(
            primary=primary[:10],
            secondary=secondary[:10],
            tools=tools[:15]
        )
    
    def _generate_education(self) -> list[TailoredEducation]:
        """Generate education section."""
        return [
            TailoredEducation(
                institution=edu.institution,
                degree=edu.degree,
                field=edu.field,
                year=str(edu.graduation_year) if edu.graduation_year else None,
                highlights=edu.achievements[:3]
            )
            for edu in self.cv_facts.education
        ]
    
    def _generate_certifications(self) -> list[TailoredCertification]:
        """Generate certifications section, prioritizing relevant ones."""
        
        # Check which certifications are relevant to job
        relevant_keywords = set(
            kw.lower() for kw in 
            self.requirements.ats_keywords.high_priority +
            self.requirements.ats_keywords.medium_priority
        )
        
        def cert_relevance(cert):
            name_lower = cert.name.lower()
            for kw in relevant_keywords:
                if kw in name_lower:
                    return 0  # High priority
            return 1  # Lower priority
        
        sorted_certs = sorted(self.cv_facts.certifications, key=cert_relevance)
        
        return [
            TailoredCertification(
                name=cert.name,
                issuer=cert.issuer,
                date=cert.date
            )
            for cert in sorted_certs
            if cert.status in ["completed", "in_progress"]
        ]
    
    def _generate_projects(self) -> list[TailoredProject]:
        """Generate projects section if relevant to job."""
        
        # Only include projects with relevant technologies
        relevant_keywords = set(
            kw.lower() for kw in 
            self.requirements.ats_keywords.high_priority +
            self.requirements.ats_keywords.medium_priority
        )
        
        relevant_projects = []
        for proj in self.cv_facts.projects:
            tech_overlap = set(t.lower() for t in proj.technologies) & relevant_keywords
            if tech_overlap or any(kw in proj.description.lower() for kw in relevant_keywords):
                relevant_projects.append(TailoredProject(
                    name=proj.name,
                    description=proj.description,
                    technologies=proj.technologies
                ))
        
        return relevant_projects[:5]

    def _apply_user_instructions(self, prompt: str) -> str:
        if not self.user_instructions:
            return prompt
        return (
            f"{prompt}\n\nUSER INSTRUCTIONS (follow if they do not conflict with the rules):\n"
            f"{self.user_instructions}\n"
        )


async def generate_tailored_cv(
    requirements: JobRequirements,
    cv_facts: CVFacts,
    mapping: MappingResult,
    strictness: str = "moderate",
    user_instructions: Optional[str] = None
) -> tuple[TailoredCV, list[ChangeLogEntry], list[BorderlineItem]]:
    """
    Generate a tailored CV from mapping results.
    
    Args:
        requirements: Parsed job requirements
        cv_facts: Parsed CV facts
        mapping: Requirement-to-evidence mapping
        strictness: Strictness level
    
    Returns:
        Tuple of (tailored CV, changes log, borderline items)
    """
    generator = CVGenerator(requirements, cv_facts, mapping, strictness, user_instructions)
    return await generator.generate()
