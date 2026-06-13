import type { TailorResult } from '../types';

export const sampleJobDescription = `Senior Backend Engineer

We are looking for a Senior Backend Engineer to build resilient APIs, improve platform reliability, and work closely with product and frontend engineers. You should have strong Python experience, FastAPI or similar API framework experience, SQL skills, Docker familiarity, and excellent communication. Experience with resume or document processing products is a plus.
`;

export const sampleCvText = `Alex Taylor
alex.taylor@example.com | +1 555 123 4567 | Austin, TX

SUMMARY
Backend engineer with experience building Python APIs, document workflows, and internal tools.

EXPERIENCE
Acme Systems
Senior Software Engineer
2022-01 to present
- Built and maintained FastAPI services for document processing workflows.
- Improved API reliability and reduced support tickets by 35%.
- Worked with Docker, PostgreSQL, and Python in production systems.

Northwind Labs
Software Engineer
2020-01 to 2021-12
- Developed internal APIs and automation tools in Python.
- Collaborated closely with frontend and product teams.

SKILLS
Python, FastAPI, PostgreSQL, Docker, REST APIs, Communication

EDUCATION
BS Computer Science
University of Texas
2019
`;

export const sampleResult: TailorResult = {
  tailored_cv: {
    header: {
      name: 'Alex Taylor',
      title: 'Senior Software Engineer',
      contact: {
        email: 'alex.taylor@example.com',
        phone: '+1 555 123 4567',
        location: 'Austin, TX',
        linkedin: 'https://www.linkedin.com/in/alextaylor',
      },
    },
    summary:
      'Backend engineer with documented experience building Python APIs, improving reliability, and supporting document processing workflows in production.',
    experience: [
      {
        company: 'Acme Systems',
        title: 'Senior Software Engineer',
        dates: '2022-01 - present',
        location: 'Austin, TX',
        bullets: [
          {
            text: 'Built and maintained FastAPI services for document processing workflows.',
            keywords_used: ['Python', 'FastAPI'],
          },
          {
            text: 'Improved API reliability and reduced support tickets by 35%.',
            keywords_used: ['reliability'],
          },
        ],
      },
      {
        company: 'Northwind Labs',
        title: 'Software Engineer',
        dates: '2020-01 - 2021-12',
        location: 'Austin, TX',
        bullets: [
          {
            text: 'Developed internal APIs and automation tools in Python.',
            keywords_used: ['Python'],
          },
          {
            text: 'Collaborated closely with frontend and product teams.',
            keywords_used: ['communication'],
          },
        ],
      },
    ],
    skills: {
      primary: ['Python', 'FastAPI', 'PostgreSQL'],
      secondary: ['Docker', 'REST APIs', 'Communication'],
      tools: ['Git', 'Linux'],
    },
    education: [
      {
        institution: 'University of Texas',
        degree: 'BS',
        field: 'Computer Science',
        year: '2019',
        highlights: ['Graduated with honors'],
      },
    ],
    certifications: [
      {
        name: 'AWS Certified Developer',
        issuer: 'Amazon',
        date: '2023-06',
      },
    ],
    projects: [
      {
        name: 'Document Workflow Engine',
        description: 'Built a document workflow service for internal resume processing.',
        technologies: ['Python', 'FastAPI', 'Docker'],
      },
    ],
  },
  cover_letter: {
    hook: 'I am applying for the Senior Backend Engineer role at Acme Hiring.',
    value_proposition:
      'My experience aligns most strongly with Python APIs and reliability improvements.',
    fit_narrative:
      'The match between the posting and my documented experience is strongest around backend API development and document workflows.',
    closing:
      'Thank you for considering my application. I would welcome a conversation about how my documented experience could support your team.',
  },
  changes_log: [
    {
      section: 'summary',
      change_type: 'rewrite',
      original: 'Backend engineer with experience building Python APIs, document workflows, and internal tools.',
      new: 'Backend engineer with documented experience building Python APIs, improving reliability, and supporting document processing workflows in production.',
      justification: 'Generated job-aligned summary using only facts from original CV',
      confidence: 'high',
      requires_review: true,
    },
  ],
  borderline_items: [
    {
      content: 'Backend engineer with documented experience building Python APIs, improving reliability, and supporting document processing workflows in production.',
      category: 'reframed_significantly',
      original_evidence:
        'Backend engineer with experience building Python APIs, document workflows, and internal tools.',
      risk_level: 'low',
      user_prompt: 'Review the reframed summary for accuracy.',
    },
  ],
  match_score: {
    score: 84,
    breakdown: {
      must_have_component: 56,
      nice_to_have_component: 24,
      bonuses: ['+5 for 3 quantified achievements'],
      penalties: [],
    },
    explanation: 'Strong match - candidate meets most requirements',
  },
  mapping_summary: {
    overall_score: 81,
    must_have_coverage: '4/5',
    nice_to_have_coverage: '2/3',
    strongest_matches: ['Python APIs', 'FastAPI services'],
    critical_gaps: [],
    keywords_present: ['Python', 'FastAPI', 'Docker'],
    keywords_missing: ['Resume parsing'],
  },
};
