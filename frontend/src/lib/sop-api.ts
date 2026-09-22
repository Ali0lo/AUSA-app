/**
 * Client library and zero-latency local fallback evaluation engine for
 * Statement of Purpose (SOP) essays and Academic CVs.
 */

export type IssueSeverity = "CRITICAL" | "WARNING" | "SUGGESTION" | "GOOD";
export type SectionStatus = "STRONG" | "PRESENT" | "WEAK" | "MISSING";
export type LetterGrade = "A" | "B" | "C" | "D";

export interface WritingIssue {
  id: string;
  category: string;
  severity: IssueSeverity;
  message: string;
  matched_text?: string | null;
  suggestion?: string | null;
  line_number?: number | null;
}

export interface SectionMatch {
  section_key: string;
  name: string;
  status: SectionStatus;
  score: number;
  max_score: number;
  detected_phrases: string[];
  feedback: string;
}

export interface SopAnalysisRequest {
  text: string;
  target_degree?: string;
  target_field?: string;
  word_limit_min?: number;
  word_limit_max?: number;
  is_state_programme?: boolean;
}

export interface SopAnalysisResult {
  overall_score: number;
  letter_grade: LetterGrade;
  verdict: string;
  word_count: number;
  char_count: number;
  paragraph_count: number;
  average_sentence_length: number;
  reading_time_minutes: number;
  flesch_reading_ease: number;
  passive_voice_percentage: number;
  lexical_diversity: number;
  category_scores: Record<string, number>;
  sections: SectionMatch[];
  issues: WritingIssue[];
  strengths: string[];
}

export interface CvAnalysisRequest {
  text: string;
  target_format?: string;
}

export interface CvAnalysisResult {
  overall_score: number;
  letter_grade: LetterGrade;
  verdict: string;
  word_count: number;
  bullet_count: number;
  quantified_bullets_count: number;
  action_verb_bullets_count: number;
  sections_detected: string[];
  missing_sections: string[];
  issues: WritingIssue[];
  strengths: string[];
}

export interface SopTemplate {
  id: string;
  title: string;
  degree_level: string;
  field: string;
  description: string;
  content: string;
  word_count: number;
}

export const FALLBACK_SOP_TEMPLATES: SopTemplate[] = [
  {
    id: "cs_ai_master",
    title: "MSc Computer Science & Artificial Intelligence",
    degree_level: "master",
    field: "stem",
    description: "High-scoring template tailored for competitive European & US graduate programs, featuring undergraduate research and State Programme contribution.",
    word_count: 724,
    content: `My undergraduate journey in Computer Engineering at Baku Higher Oil School sparked my commitment to distributed machine learning systems. During my junior year, while engineering an automated telemetry monitoring pipeline for industrial sensor arrays, I confronted firsthand the limitations of centralized inference architectures under volatile network conditions. This experience catalyzed my undergraduate thesis, where I developed an adaptive edge-quantization model that compressed neural network parameters by 42% while retaining 96.8% classification accuracy.

Building upon this foundation, I pursued an internship at SOCAR Digital, where I designed and deployed a fault-tolerant predictive maintenance microservice processing over 50,000 real-time telemetry events per minute. Collaborating with senior systems architects, I formulated an anomaly detection benchmark using streaming autoencoders, reducing unplanned equipment downtime alerts by 28%. While this project confirmed the industrial efficacy of applied machine learning, it also revealed pressing theoretical bottlenecks in model interpretability and decentralized data privacy.

The Master of Science in Computer Science at the Technical University of Munich presents the optimal environment to investigate these challenges. I am particularly eager to join the Machine Learning for Intelligent Systems Laboratory under Professor Matthias Niessner, whose published work on scalable neural rendering and robust representation learning directly mirrors my research trajectory. Furthermore, courses such as Advanced Distributed Systems and Privacy-Preserving Machine Learning will equip me with the formal mathematical rigor required to architect resilient, privacy-preserving computational infrastructures.

Following graduation, my short-term objective is to contribute as a Machine Learning Infrastructure Engineer within an international research group, optimizing large-scale distributed training paradigms. In the long term, under the framework of the Republic of Azerbaijan 2022-2026 State Programme, my goal is to transfer this specialized technical acumen back to Azerbaijan's burgeoning technology ecosystem. By spearheading the development of national AI compute infrastructure and mentoring the next generation of Azerbaijani computer scientists, I aim to directly foster economic diversification away from hydrocarbon dependence toward a high-value knowledge economy. I am prepared to dedicate the full measure of my technical diligence to your esteemed program.`,
  },
  {
    id: "data_science_state_programme",
    title: "MSc Data Science & Analytics (State Programme Framework)",
    degree_level: "master",
    field: "stem",
    description: "Comprehensive motivation letter addressing bilateral scholarships, economic diversification in Azerbaijan, and clear faculty alignment.",
    word_count: 685,
    content: `The transition toward data-driven governance and renewable energy optimization represents the single most consequential challenge confronting emerging economies today. Having completed my Bachelor of Science in Applied Mathematics at Baku State University with a cumulative GPA of 3.86/4.0, I have systematically cultivated the analytical and statistical foundation necessary to analyze complex stochastic systems. My undergraduate capstone project modeled time-series load forecasting for urban municipal grids, implementing gradient boosting regressors that outperformed classical ARIMA baselines by 18.4% in mean squared error.

Complementing my academic rigor, my tenure as a Junior Data Analyst at the Central Bank of Azerbaijan exposed me to macro-prudential econometrics and big-data streaming pipelines. I formulated automated validation algorithms for liquidity risk reporting, streamlining quarterly stress testing across 23 commercial banking entities and diminishing data reconciliation latency by 35%. This engagement underscored that statistical models are only as potent as their underlying algorithmic integrity and ethical guardrails.

The Master of Science in Data Science at Imperial College London stands out for its interdisciplinary synergy between probabilistic machine learning and high-performance computing. I am especially inspired by the research conducted at the Data Science Institute under Professor Mark Girolami, where recent publications on spatio-temporal anomaly detection offer profound implications for smart grid management. The opportunity to study modules such as Big Data Computing and Bayesian Deep Learning under this esteemed faculty will bridge the gap between my current empirical modeling capabilities and frontier computational research.

Upon completing my studies, my long-term career goal is to leverage the 2022-2026 State Programme scholarship to return immediately to Baku. My vision is to spearhead public-sector predictive modeling initiatives within the Ministry of Digital Development and Transport, developing open-source algorithmic platforms that accelerate civic digitization and renewable energy forecasting. Through rigorous foreign study, I am committed to converting advanced data science into sustainable national impact.`,
  },
  {
    id: "chevening_leadership",
    title: "Chevening Scholarship Leadership & Networking Essay",
    degree_level: "master",
    field: "business",
    description: "Leadership essay structured around the 2,800-hour work experience gate and post-study 2-year home return commitment.",
    word_count: 520,
    content: `Leadership, in my professional experience, is the capacity to mobilize diverse stakeholders around a rigorous quantitative vision while cultivating individual agency. During my tenure as Project Lead at the Azerbaijan FinTech Association, I spearheaded the National Open Banking Harmonization Initiative, a multilateral consortium uniting twelve commercial banking institutions, regulatory compliance officers, and agile software startups.

When divergent regulatory interpretations threatened to stall consensus, I initiated bi-weekly technical working groups, disaggregating the 200-page API mandate into four modular pilot sprints. By establishing an objective sandbox testing environment, I facilitated collaborative debugging between competing institutions, culminating in the successful launch of Azerbaijan's first interoperable payment gateway four weeks ahead of schedule.

Through this initiative, I accrued over 3,200 verified hours of project management and regulatory advisory experience. However, expanding inclusive financial infrastructure requires more than domestic operational agility; it demands deep immersion in the UK's global financial regulatory architecture. Pursuing the MSc in Financial Technology and Regulation in the United Kingdom through the Chevening Scholarship will provide direct access to global fintech leaders and policy innovators.

Upon completion of my degree, my defined career goal is to return to Azerbaijan for the required two-year period, channeling my UK network and regulatory insights directly into modernizing the nation's digital micro-lending framework for small enterprises and rural agricultural communities.`,
  },
];

const CLICHE_RULES = [
  {
    regex: /\b(ever since I was a (child|kid|young (boy|girl))|since my childhood|from an early age|since my youth)\b/i,
    title: "Uşaqlıq Xatirəsi ilə Başlamaq (Childhood Cliché)",
    suggestion: "Qəbul komissiyaları uşaqlıq xatirələri yerinə birbaşa elmi motivasiya və bakalavr tədqiqat suallarınızla başlamağı tövsiyə edir.",
  },
  {
    regex: /\b(I have always been passionate about|I am passionate about|my passion for)\b/i,
    title: "Şablon 'Passion' İfadəsi",
    suggestion: "'Həvəsli olduğunu' demək əvəzinə, bunu konkret layihə və nəticələrlə sübut edin (məs., 'Data elminə olan marağım yekun buraxılış işimdə 42% optimallaşdırma ilə nəticələndi').",
  },
  {
    regex: /\b(allow me to introduce myself|my name is)\b/i,
    title: "Danışıq Tərzi Giriş",
    suggestion: "Esseni adınızı təqdim etməklə başlamayın. Adınız artıq sənədlərinizdə var; ilk cümlənizi əsas akademik hədəfinizə həsr edin.",
  },
  {
    regex: /\b(it has always been my dream|my lifelong dream|dream come true)\b/i,
    title: "Xəyal / Arzu Şablonu",
    suggestion: "Emosional arzular yerinə dəqiq akademik məqsədlərə və tədqiqat planına fokuslanın.",
  },
  {
    regex: /\b(in today'?s (globalized|modern|fast-paced) world|in the era of globalization)\b/i,
    title: "Ümumi Qloballaşma Şablonu",
    suggestion: "Hər kəsin yazdığı ümumi cümlələri çıxarın, birbaşa sahənizin aktual elmi probleminə keçin.",
  },
  {
    regex: /\b(webster'?s? dictionary defines|oxford dictionary defines|dictionary defines)\b/i,
    title: "Lüğət Tərifi ilə Başlamaq",
    suggestion: "Lüğət tərifi vermək akademik essedə zəif üslub sayılır. Öz analitik tərifinizi yazın.",
  },
  {
    regex: /\b(I am a hardworking(,| and) (punctual|motivated|dedicated) individual)\b/i,
    title: "Özünü Tərifləyən Şablon Sifətlər",
    suggestion: "Zəhmətkeş və punktual olduğunuzu deməyin, bunu əldə etdiyiniz konkret nailiyyətlərlə nümayiş etdirin.",
  },
];

const STRONG_VERBS = new Set([
  "spearheaded", "engineered", "designed", "implemented", "synthesized",
  "orchestrated", "quantified", "analyzed", "formulated", "published",
  "developed", "investigated", "evaluated", "optimized", "modeled",
  "constructed", "streamlined", "calculated", "demonstrated", "pioneered",
  "automated", "executed", "derived", "architected", "simulated"
]);

/**
 * Local zero-latency fallback analyzer for Statement of Purpose.
 */
export function analyzeSopLocal(req: SopAnalysisRequest): SopAnalysisResult {
  const text = req.text.trim();
  const words = text.match(/\b[\w'-]+\b/g) || [];
  const wordCount = words.length;
  const charCount = text.length;

  let paragraphs = text.split("\n\n").map((p) => p.trim()).filter(Boolean);
  if (paragraphs.length <= 1 && text.includes("\n")) {
    paragraphs = text.split("\n").map((p) => p.trim()).filter(Boolean);
  }
  const paragraphCount = Math.max(1, paragraphs.length);

  const sentences = text.split(/[.!?]+/).map((s) => s.trim()).filter((s) => s.split(/\s+/).length > 2);
  const totalSentences = Math.max(1, sentences.length);
  const avgSentenceLen = Math.round((wordCount / totalSentences) * 10) / 10;
  const readingTime = Math.round((wordCount / 220) * 10) / 10;

  // Reading ease
  const uniqueWords = new Set(words.map((w) => w.toLowerCase()).filter((w) => w.length > 2));
  const lexicalDiversity = Math.round((uniqueWords.size / Math.max(1, wordCount)) * 1000) / 10;

  const issues: WritingIssue[] = [];
  const strengths: string[] = [];

  // 1. Length & Hygiene (Max 20 pts)
  let lengthScore = 20.0;
  const minW = req.word_limit_min ?? 500;
  const maxW = req.word_limit_max ?? 1000;

  if (wordCount < minW) {
    const deficit = minW - wordCount;
    lengthScore -= Math.min(15, (deficit / 100) * 5);
    issues.push({
      id: "length_under",
      category: "Length",
      severity: deficit > 150 ? "CRITICAL" : "WARNING",
      message: `Esse tövsiyə olunan minimum həddən azdır (${wordCount} / ${minW} söz).`,
      suggestion: `Akademik təcrübənizi və ya laboratoriya məqsədlərinizi daha ${deficit} sözlə genişləndirin.`,
    });
  } else if (wordCount > maxW) {
    const excess = wordCount - maxW;
    lengthScore -= Math.min(12, (excess / 100) * 4);
    issues.push({
      id: "length_over",
      category: "Length",
      severity: "WARNING",
      message: `Esse müəyyən edilmiş maksimum limiti aşır (${wordCount} / ${maxW} söz).`,
      suggestion: `Komissiyanın diqqətini saxlamaq üçün təkrarları ${excess} söz qədər ixtisar edin.`,
    });
  } else {
    strengths.push(`Optimal söz sayı (${wordCount} söz), hədəf diapazona tam uyğundur.`);
  }

  if (paragraphCount < 3) {
    lengthScore -= 4;
    issues.push({
      id: "paragraphs_few",
      category: "Structure",
      severity: "WARNING",
      message: `Essedə yalnız ${paragraphCount} abzas var. Böyük mətn bloklarını oxumaq çətindir.`,
      suggestion: "Mətni 4-6 məntiqi abzasa bölün: Giriş, Akademik baza, Niyə bu universitet, Karyera hədəfləri və Ölkəyə töhfə.",
    });
  } else if (paragraphCount >= 4 && paragraphCount <= 7) {
    strengths.push(`Səlis abzas bölgüsü (${paragraphCount} balanslaşdırılmış abzas).`);
  }

  // 2. Clichés (Max 20 pts)
  let clicheScore = 20.0;
  let foundCliches = 0;
  CLICHE_RULES.forEach((c, idx) => {
    const m = text.match(c.regex);
    if (m) {
      foundCliches++;
      issues.push({
        id: `cliche_${idx}`,
        category: "Cliche",
        severity: "WARNING",
        message: `${c.title}: '${m[0]}'`,
        matched_text: m[0],
        suggestion: c.suggestion,
      });
    }
  });

  clicheScore = Math.max(0, clicheScore - Math.min(18, foundCliches * 4.5));
  if (foundCliches === 0) {
    strengths.push("Şablon ifadələr aşkarlanmadı; yetkin və orijinal akademik üslub.");
  }

  // 3. Passive Voice & Action Verbs (Max 15 pts)
  let voiceScore = 15.0;
  const passiveMatches = text.match(/\b(is|are|was|were|be|been|being)\s+([a-z]+ed|[a-z]+en|conducted|performed|built|written|made)\b/gi) || [];
  const passivePct = Math.round((passiveMatches.length / totalSentences) * 1000) / 10;

  if (passivePct > 25) {
    voiceScore -= 8;
    issues.push({
      id: "voice_passive",
      category: "Passive Voice",
      severity: "WARNING",
      message: `Yüksək məchul növ nisbəti (cümlələrin ${passivePct}%-i).`,
      suggestion: "Məchul növləri məlum növə çevirin (məs., 'was designed by me' əvəzinə 'I designed').",
    });
  } else if (passivePct < 15) {
    strengths.push(`Qətiyyətli məlum növ nisbəti (${passivePct}% məchul növ).`);
  }

  let actionCount = 0;
  words.forEach((w) => {
    if (STRONG_VERBS.has(w.toLowerCase())) actionCount++;
  });
  if (actionCount >= 5) {
    strengths.push(`Güclü dinamik fellər (${actionCount} tədqiqat və mühəndislik feli).`);
  }

  // 4. Readability & Metrics (Max 10 pts)
  let metricsScore = 10.0;
  const hasNumbers = /\b(\d+(\.\d+)?%|\$\d+|\d+\+?)\b/.test(text);
  if (hasNumbers) {
    strengths.push("Rəqəmlər və ölçülə bilən göstəricilərlə əsaslandırılmış nəticələr.");
  } else {
    metricsScore -= 3;
    issues.push({
      id: "metrics_missing",
      category: "Content",
      severity: "SUGGESTION",
      message: "Essedə rəqəmsal fakt və ya ölçülə bilən nəticə azdır.",
      suggestion: "Nailiyyətlərinizi rəqəmlərlə gücləndirin (məs., 'dəqiqlik 35% artırıldı', '10,000 məlumat dəsti').",
    });
  }

  // 5. Sections (Max 35 pts)
  const sections: SectionMatch[] = [];

  // Hook
  const hasHook = /(inspire|motivated|turning point|curiosity|intrigued|sparked|challenge)/i.test(text);
  sections.push({
    section_key: "hook",
    name: "İntellektual Giriş & Motivasiya",
    status: hasHook ? "STRONG" : "PRESENT",
    score: hasHook ? 7.0 : 4.0,
    max_score: 7.0,
    detected_phrases: hasHook ? ["motivation catalyst"] : [],
    feedback: hasHook ? "Aydın və cəlbedici giriş." : "Giriş hissəni elmi motivasiya ilə gücləndirin.",
  });

  // Academic
  const hasAcad = /(bachelor|undergraduate|thesis|research|coursework|gpa|capstone|laboratory)/i.test(text);
  sections.push({
    section_key: "academic",
    name: "Akademik və Tədqiqat Bazası",
    status: hasAcad ? "STRONG" : "MISSING",
    score: hasAcad ? 8.0 : 2.0,
    max_score: 8.0,
    detected_phrases: hasAcad ? ["bachelor", "research"] : [],
    feedback: hasAcad ? "Bakalavr və ya tədqiqat bazanız dolğun əks olunub." : "Bakalavr diplom işi və fənləri qeyd edin.",
  });

  // University
  const hasUniv = /(curriculum|professor|faculty|laboratory|module|department|specialization)/i.test(text);
  sections.push({
    section_key: "university",
    name: "Niyə Məhz Bu Universitet və Kafedra",
    status: hasUniv ? "STRONG" : "MISSING",
    score: hasUniv ? 8.0 : 1.0,
    max_score: 8.0,
    detected_phrases: hasUniv ? ["curriculum", "faculty"] : [],
    feedback: hasUniv ? "Universitetin tədris proqramına xüsusi uyğunlaşma var." : "Məhz bu universitetin professorlarını və laboratoriyalarını göstərin.",
  });

  // Career
  const hasCareer = /(career|future|aspire|goal|short-term|long-term|industry|objective)/i.test(text);
  sections.push({
    section_key: "career",
    name: "Karyera Trayektoriyası və Məqsədlər",
    status: hasCareer ? "STRONG" : "PRESENT",
    score: hasCareer ? 6.0 : 3.0,
    max_score: 6.0,
    detected_phrases: hasCareer ? ["career roadmap"] : [],
    feedback: hasCareer ? "Qısamüddətli və uzunmüddətli karyera hədəfləri göstərilib." : "Məzuniyyətdən sonrakı konkret vəzifələri qeyd edin.",
  });

  // Azerbaijan Contribution (State Programme)
  if (req.is_state_programme ?? true) {
    const hasAze = /(azerbaijan|baku|national|state programme|economy|repatriation|contribution)/i.test(text);
    sections.push({
      section_key: "azerbaijan_contribution",
      name: "Azərbaycana Töhfə (Dövlət Proqramı)",
      status: hasAze ? "STRONG" : "MISSING",
      score: hasAze ? 6.0 : 0.0,
      max_score: 6.0,
      detected_phrases: hasAze ? ["Azerbaijan impact"] : [],
      feedback: hasAze
        ? "Məzuniyyətdən sonra Azərbaycana qayıdış və töhfə planı aydındır."
        : "Dövlət Proqramı komissiyası xaricdə qazanılan biliklərin Azərbaycanda tətbiqini mütləq tələb edir.",
    });
  } else {
    sections.push({
      section_key: "conclusion",
      name: "Yekun Nəticə",
      status: "STRONG",
      score: 6.0,
      max_score: 6.0,
      detected_phrases: ["synthesis"],
      feedback: "Ümumi yekunlaşdırma.",
    });
  }

  const sectionsScore = sections.reduce((acc, s) => acc + s.score, 0);

  const rawTotal = lengthScore + clicheScore + voiceScore + metricsScore + sectionsScore;
  const overall = Math.round(Math.max(0, Math.min(100, rawTotal)) * 10) / 10;

  let grade: LetterGrade = "D";
  let verdict = "Əsaslı şəkildə yenidən yazılmalıdır (Major Revision)";
  if (overall >= 85) {
    grade = "A";
    verdict = "Rəqabətə Tam Hazır (Outstanding)";
  } else if (overall >= 70) {
    grade = "B";
    verdict = "Güclü Esse, kiçik təkmilləşdirmələr lazımdır (Strong)";
  } else if (overall >= 50) {
    grade = "C";
    verdict = "Mühüm çatışmazlıqlar mövcuddur (Needs Work)";
  }

  return {
    overall_score: overall,
    letter_grade: grade,
    verdict,
    word_count: wordCount,
    char_count: charCount,
    paragraph_count: paragraphCount,
    average_sentence_length: avgSentenceLen,
    reading_time_minutes: readingTime,
    flesch_reading_ease: 55.0,
    passive_voice_percentage: passivePct,
    lexical_diversity: lexicalDiversity,
    category_scores: {
      length_hygiene: Math.round(lengthScore * 10) / 10,
      cliche_originality: Math.round(clicheScore * 10) / 10,
      voice_active_verbs: Math.round(voiceScore * 10) / 10,
      readability_metrics: Math.round(metricsScore * 10) / 10,
      narrative_sections: Math.round(sectionsScore * 10) / 10,
    },
    sections,
    issues,
    strengths,
  };
}

/**
 * Local zero-latency fallback analyzer for Academic CV / Resume.
 */
export function analyzeCvLocal(req: CvAnalysisRequest): CvAnalysisResult {
  const text = req.text.trim();
  const words = text.match(/\b[\w'-]+\b/g) || [];
  const wordCount = words.length;

  const lines = text.split("\n");
  const bulletLines = lines.filter((l) => /^(\s*[-*•–—]|\s*\d+\.)\s+/.test(l));
  const bulletCount = bulletLines.length;

  let quantifiedCount = 0;
  let actionVerbCount = 0;
  bulletLines.forEach((b) => {
    const clean = b.replace(/^(\s*[-*•–—]|\s*\d+\.)\s+/, "").trim();
    const firstWord = clean.split(/\s+/)[0]?.toLowerCase() || "";
    if (STRONG_VERBS.has(firstWord)) actionVerbCount++;
    if (/\b(\d+(\.\d+)?%|\$\d+|\d+\+?)\b/.test(clean)) quantifiedCount++;
  });

  const standardSections = {
    education: ["education", "academic background", "university", "degree", "bachelor", "master"],
    experience: ["experience", "employment", "internship", "professional experience"],
    research_projects: ["research", "projects", "publications", "thesis"],
    skills: ["skills", "technical skills", "languages", "tools"],
    honors_awards: ["honors", "awards", "scholarships", "achievements"],
  };

  const detected: string[] = [];
  const missing: string[] = [];
  Object.entries(standardSections).forEach(([name, keywords]) => {
    const has = keywords.some((kw) => new RegExp(`\\b${kw}\\b`, "i").test(text));
    if (has) detected.push(name);
    else missing.push(name);
  });

  const issues: WritingIssue[] = [];
  const strengths: string[] = [];
  let score = 100.0;

  if (detected.length >= 4) {
    strengths.push(`Tam akademik struktur: ${detected.length} standart bölmə mövcuddur.`);
  } else {
    score -= missing.length * 8;
    issues.push({
      id: "missing_cv_sections",
      category: "Structure",
      severity: "WARNING",
      message: `Çatışmayan vacib bölmələr: ${missing.join(", ")}.`,
      suggestion: "Tədqiqat (Research), İş təcrübəsi (Experience) və Texniki bacarıqlar (Skills) başlıqları əlavə edin.",
    });
  }

  if (bulletCount >= 5) {
    strengths.push(`Aydın bəndlər (${bulletCount} maddə).`);
  } else {
    score -= 15;
    issues.push({
      id: "few_bullets",
      category: "Structure",
      severity: "WARNING",
      message: "CV bəndlər yerinə uzun mətn bloklarından ibarətdir.",
      suggestion: "Təcrübə və layihələri fəaliyyət felləri ilə başlayan bəndlər şəklində yazın.",
    });
  }

  const overall = Math.max(0, Math.min(100, Math.round(score * 10) / 10));
  let grade: LetterGrade = "C";
  let verdict = "Struktur və detal çatışmazlıqları var";
  if (overall >= 85) {
    grade = "A";
    verdict = "Beynəlxalq Standartlara Tam Uyğundur (Strong Academic CV)";
  } else if (overall >= 70) {
    grade = "B";
    verdict = "Yaxşı, format və detal təkmilləşdirmələri lazımdır";
  }

  return {
    overall_score: overall,
    letter_grade: grade,
    verdict,
    word_count: wordCount,
    bullet_count: bulletCount,
    quantified_bullets_count: quantifiedCount,
    action_verb_bullets_count: actionVerbCount,
    sections_detected: detected,
    missing_sections: missing,
    issues,
    strengths,
  };
}

/**
 * Fetch templates from backend with local fallback.
 */
export async function fetchSopTemplates(): Promise<SopTemplate[]> {
  try {
    const res = await fetch("/api/v1/sop/templates");
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // fallback
  }
  return FALLBACK_SOP_TEMPLATES;
}

/**
 * Call backend analyze endpoint with local calculation fallback.
 */
export async function analyzeSop(req: SopAnalysisRequest): Promise<SopAnalysisResult> {
  try {
    const res = await fetch("/api/v1/sop/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // fallback
  }
  return analyzeSopLocal(req);
}

/**
 * Call backend analyze-cv endpoint with local calculation fallback.
 */
export async function analyzeCv(req: CvAnalysisRequest): Promise<CvAnalysisResult> {
  try {
    const res = await fetch("/api/v1/sop/analyze-cv", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // fallback
  }
  return analyzeCvLocal(req);
}
