export interface CuratedUniversityDetail {
  name: string;
  countryCode: string;
  countryName: string;
  acceptedQualifications: string[];
  unlockRoutes: { mechanism: string; timeMonths: number; description: string }[];
  languageMinima: { test: string; minScore?: number; notes?: string }[];
  entranceExams: { test: string; minScore?: number; notes?: string }[];
  gpaMinimum?: { score: number; scale: string; notes?: string };
  tuition: { amount?: number; currency?: string; notes: string };
  applicationFee?: { amount: number; currency: string };
  deadline?: string;
  portal?: string;
  documentsRequired: string;
  notes: string;
  sourceUrl: string;
  provenance: string;
  lastChecked: string;
}

export const CURATED_UNIVERSITIES: CuratedUniversityDetail[] = [
  {
    name: "Bogazici University",
    countryCode: "TR",
    countryName: "Turkey",
    acceptedQualifications: ["attestat"],
    unlockRoutes: [
      {
        mechanism: "Direct application on attestat with TR-YÖS or SAT",
        timeMonths: 0,
        description: "Direct entry on secondary school certificate. Diploma alone does not suffice: requires TR-YÖS or SAT."
      }
    ],
    languageMinima: [
      { test: "IELTS", minScore: 6.5, notes: "Academic 6.5 overall with 6.5 writing, or TOEFL iBT 79 with writing 22." }
    ],
    entranceExams: [
      { test: "TR-YÖS", minScore: 450, notes: "TR-YÖS minimum 450. SAT alternative: 1350/1600 (Math 700) for Engineering; 1200-1300 for other faculties." }
    ],
    tuition: {
      notes: "International student tuition is not stated on this admissions page (unknown, not free)."
    },
    applicationFee: { amount: 100, currency: "EUR" },
    portal: "Bogazici Office of International Relations",
    documentsRequired: "High school diploma, certified translation, official exam score (TR-YÖS or SAT), English proficiency score, application fee receipt.",
    notes: "Graduates of any institution equivalent to a Turkish high school may apply. One of SAT, TR-YÖS or GCE A Levels is required in addition to the diploma.",
    sourceUrl: "https://intl.bogazici.edu.tr/required-documents-undergraduate-application",
    provenance: "claude-extracted",
    lastChecked: "2026-09-02"
  },
  {
    name: "Istanbul Technical University",
    countryCode: "TR",
    countryName: "Turkey",
    acceptedQualifications: ["attestat"],
    unlockRoutes: [
      {
        mechanism: "Direct application on secondary school diploma",
        timeMonths: 0,
        description: "Direct entry with secondary school diploma equivalent to Turkish high school plus accepted exam score."
      }
    ],
    languageMinima: [
      { test: "English proficiency", notes: "English proficiency required at registration or 1 year of English prep at ITU." }
    ],
    entranceExams: [
      { test: "ITU accepted exam", notes: "Application must carry one of the exam or diploma scores ITU lists; specific list and minima not readable from page." }
    ],
    tuition: {
      notes: "Tuition not stated on this page (unknown, not free)."
    },
    portal: "ITU Registrar",
    documentsRequired: "High school diploma, transcript, passport copy, accepted entrance exam score.",
    notes: "Direct application on a secondary school curriculum equivalent to a Turkish high school.",
    sourceUrl: "https://www.sis.itu.edu.tr/EN/student/intenational-students/application.php",
    provenance: "claude-extracted",
    lastChecked: "2026-09-02"
  },
  {
    name: "Technical University of Munich",
    countryCode: "DE",
    countryName: "Germany",
    acceptedQualifications: ["feststellungspruefung", "one_year_university"],
    unlockRoutes: [
      {
        mechanism: "Studienkolleg + Feststellungsprüfung",
        timeMonths: 12,
        description: "Attend a 1-year Studienkolleg course in Germany and pass the Feststellungsprüfung assessment exam."
      },
      {
        mechanism: "1 year at a recognised Azerbaijani university",
        timeMonths: 12,
        description: "Completing 1 full academic year at an accredited university in Azerbaijan provides subject-restricted direct entry to German universities."
      }
    ],
    languageMinima: [
      { test: "German", notes: "Instruction in German. B2/C1 German required for Studienkolleg / degree entry." }
    ],
    entranceExams: [
      { test: "Feststellungsprüfung", notes: "University qualification assessment examination after preparatory course." }
    ],
    tuition: {
      notes: "Public universities in Bavaria charge administrative fees; non-EU tuition introduced recently varies by programme and is not stated here."
    },
    portal: "TUMonline (via uni-assist VPD first)",
    documentsRequired: "uni-assist Vorprüfungsdokumentation (VPD) required BEFORE applying to TUM, certified diploma copies, sworn translation.",
    notes: "An 11-year school-leaving certificate does not grant direct entry. Grants direct admission only after Studienkolleg or 1 university year.",
    sourceUrl: "https://www.tum.de/en/studies/application/application-info-portal/higher-education-entrance-qualification/international-higher-education-entrance-qualification/",
    provenance: "claude-extracted",
    lastChecked: "2026-09-02"
  },
  {
    name: "Heidelberg University",
    countryCode: "DE",
    countryName: "Germany",
    acceptedQualifications: ["feststellungspruefung", "one_year_university"],
    unlockRoutes: [
      {
        mechanism: "Internationales Studienzentrum (Studienkolleg)",
        timeMonths: 12,
        description: "Two-semester preparatory course leading to the Feststellungsprüfung exam."
      },
      {
        mechanism: "1 year at an Azerbaijani university",
        timeMonths: 12,
        description: "One completed year of university study in Azerbaijan provides direct admission to related subjects."
      }
    ],
    languageMinima: [
      { test: "German CEFR", minScore: 2, notes: "German CEFR B2+ required AT APPLICATION for the Studienkolleg, not only at enrolment." }
    ],
    entranceExams: [
      { test: "Feststellungsprüfung", notes: "Entrance test for Studienkolleg and exit examination." }
    ],
    tuition: {
      notes: "Baden-Württemberg tuition of €1,500/semester for non-EU students applies generally, but not confirmed on this page."
    },
    portal: "heiCO (uni-assist VPD required)",
    documentsRequired: "uni-assist VPD (valid 1 year), secondary school certificate with apostille, sworn German/English translation, B2+ German certificate.",
    notes: "uni-assist VPD required and valid one year. B2+ German required at application.",
    sourceUrl: "https://www.uni-heidelberg.de/en/study/application-enrolment/study-requirements/studienkolleg-and-feststellungsprufung/admission-to-the-preparatory-course-studienkolleg-application-documents",
    provenance: "claude-extracted",
    lastChecked: "2026-09-02"
  },
  {
    name: "LMU Munich",
    countryCode: "DE",
    countryName: "Germany",
    acceptedQualifications: ["feststellungspruefung", "one_year_university"],
    unlockRoutes: [
      {
        mechanism: "Studienkolleg München",
        timeMonths: 12,
        description: "Preparatory course at Studienkolleg München followed by Feststellungsprüfung."
      },
      {
        mechanism: "1 year at an Azerbaijani university",
        timeMonths: 12,
        description: "1 completed year of higher education in home country opens direct subject-restricted admission."
      }
    ],
    languageMinima: [
      { test: "German CEFR", minScore: 2, notes: "B2-level German required to begin preparatory course in Bavaria." }
    ],
    entranceExams: [
      { test: "Feststellungsprüfung", notes: "Final examination at conclusion of Studienkolleg." }
    ],
    tuition: {
      notes: "Tuition and administrative fees not stated on this page (unknown, not free)."
    },
    portal: "LMU International Office",
    documentsRequired: "School-leaving certificate, certified translation, proof of B2 German, university entrance qualification evidence.",
    notes: "Requires a qualification equivalent to German Abitur; foreign 11-year certificate requires Studienkolleg or 1-year university.",
    sourceUrl: "https://www.lmu.de/en/study/degree-students/prerequisites/",
    provenance: "claude-extracted",
    lastChecked: "2026-09-02"
  },
  {
    name: "University of Cambridge",
    countryCode: "GB",
    countryName: "United Kingdom",
    acceptedQualifications: ["one_year_university", "a_level", "ib"],
    unlockRoutes: [
      {
        mechanism: "One year at a recognised Azerbaijani university",
        timeMonths: 12,
        description: "Cambridge explicitly documents that first year of undergraduate study outside the UK can be considered for undergraduate admission."
      },
      {
        mechanism: "A Levels or International Baccalaureate",
        timeMonths: 24,
        description: "A*A*A or equivalent IB diploma."
      }
    ],
    languageMinima: [
      { test: "IELTS / TOEFL", notes: "English language proficiency required (typically IELTS 7.5 with 7.0 in all elements); page references separate English policy." }
    ],
    entranceExams: [
      { test: "Subject Admissions Assessment", notes: "Course-specific written assessment (e.g. ESAT, TMUA)." }
    ],
    tuition: {
      notes: "International fees vary by course (£25,000–£65,000/year); not stated on this country-specific entry page."
    },
    portal: "UCAS",
    documentsRequired: "UCAS application, academic transcripts, My Cambridge Application supplementary questionnaire, written work / assessment.",
    notes: "Cambridge does not accept the attestat for direct entry. Formally accepts 'first year of undergraduate study outside the UK'.",
    sourceUrl: "https://www.undergraduate.study.cam.ac.uk/international-students/international-entry-requirements",
    provenance: "claude-extracted",
    lastChecked: "2026-09-02"
  },
  {
    name: "University of Manchester",
    countryCode: "GB",
    countryName: "United Kingdom",
    acceptedQualifications: ["one_year_university", "foundation_year", "a_level", "ib"],
    unlockRoutes: [
      {
        mechanism: "One year at an Azerbaijani university (First-year transfer)",
        timeMonths: 12,
        description: "Manchester's official Azerbaijan page confirms: may accept applicants who complete year 1 of an undergraduate degree in Azerbaijan into year 1 of bachelor study."
      },
      {
        mechanism: "Integrated Foundation Year / INTO Manchester",
        timeMonths: 12,
        description: "Completion of an approved foundation year programme."
      }
    ],
    languageMinima: [
      { test: "CEFR", notes: "B2 is the UKVI minimum; individual faculties require higher (typically IELTS 6.5–7.0)." }
    ],
    entranceExams: [],
    gpaMinimum: { score: 80, scale: "100", notes: "Foundation route requires 80% overall with 80%+ in relevant subjects (e.g. Maths & Physics)." },
    tuition: {
      notes: "International tuition fees not stated on this page (unknown, not free)."
    },
    portal: "UCAS",
    documentsRequired: "UCAS application, certified high school diploma & transcripts, translation, English test certificate, academic reference.",
    notes: "Attestat is not accepted for direct entry. Both 1-year university and foundation year routes are documented.",
    sourceUrl: "https://www.manchester.ac.uk/study/international/country-specific-information/azerbaijan/entry-requirements/",
    provenance: "claude-extracted",
    lastChecked: "2026-09-02"
  },
  {
    name: "UCL",
    countryCode: "GB",
    countryName: "United Kingdom",
    acceptedQualifications: ["foundation_year", "a_level", "ib"],
    unlockRoutes: [
      {
        mechanism: "UCL Undergraduate Preparatory Certificates (UPC)",
        timeMonths: 12,
        description: "UCL's international foundation year for students whose school qualification is not accepted for direct entry."
      }
    ],
    languageMinima: [
      { test: "English test", notes: "IELTS or equivalent; UPC entry requires 5.5–6.0 depending on course stream." }
    ],
    entranceExams: [
      { test: "UPC Entrance Test & Interview", notes: "Critical thinking and subject-specific entrance tests." }
    ],
    gpaMinimum: { score: 4.5, scale: "5.0", notes: "Orta Təhsil Haqqında Attestat accepted for UPC entry at minimum 4.5 overall and 5 in each required subject." },
    tuition: {
      notes: "Tuition not stated on this page (unknown, not free)."
    },
    portal: "UCL CLIE direct for UPC / UCAS for degree",
    documentsRequired: "Attestat transcript, English test result, personal statement, academic reference, portfolio (for UPC Architecture).",
    notes: "Attestat not accepted for direct undergraduate entry. UPC foundation requires 4.5/5.0 on attestat.",
    sourceUrl: "https://www.ucl.ac.uk/languages-international-education/preparation-courses/upc-foundation/entry-requirements/country",
    provenance: "claude-extracted",
    lastChecked: "2026-09-02"
  },
  {
    name: "University of Edinburgh",
    countryCode: "GB",
    countryName: "United Kingdom",
    acceptedQualifications: ["foundation_year", "a_level", "ib"],
    unlockRoutes: [
      {
        mechanism: "University of Edinburgh International Foundation Programme (IFP)",
        timeMonths: 12,
        description: "1-year on-campus foundation programme preparing for degree entry."
      }
    ],
    languageMinima: [
      { test: "IELTS", minScore: 5.5, notes: "IELTS 5.5 with no band below 5.5 for IFP entry. Degree entry requires higher (typically 6.5–7.0)." }
    ],
    entranceExams: [],
    tuition: {
      notes: "Tuition not stated on country page (unknown, not free)."
    },
    portal: "UCAS",
    documentsRequired: "UCAS application, certificate of secondary education, transcript, IELTS certificate, personal statement.",
    notes: "Applicants with Certificate of Secondary Education normally required to complete an approved foundation programme.",
    sourceUrl: "https://www.ed.ac.uk/studying/international/country/asia/central-west-asia/other-countries",
    provenance: "claude-extracted",
    lastChecked: "2026-09-02"
  },
  {
    name: "Tsinghua University",
    countryCode: "CN",
    countryName: "China",
    acceptedQualifications: ["attestat"],
    unlockRoutes: [
      {
        mechanism: "Direct application on high school diploma",
        timeMonths: 0,
        description: "Senior high school graduation certificate is accepted directly without foundation year."
      }
    ],
    languageMinima: [
      { test: "TOEFL or IELTS", notes: "Required for non-native English speakers applying to English-taught programmes. No minimum stated on page." }
    ],
    entranceExams: [
      { test: "HSK", minScore: 5, notes: "HSK level 5 or above (60+ in Listening, Reading, Writing) for Chinese-taught courses. Must reach HSK 5 within year 1." }
    ],
    tuition: {
      notes: "Tuition not stated on this page (unknown, not free)."
    },
    portal: "Tsinghua International Undergraduate Admissions",
    documentsRequired: "High school graduation certificate, official transcripts, language test scores, personal statement, two recommendation letters.",
    notes: "Applicant must be a foreign citizen aged 18 or above. Chinese-taught requires HSK 5; English-taught requires TOEFL/IELTS.",
    sourceUrl: "https://international.join-tsinghua.edu.cn/Admission1/Eligibility.htm",
    provenance: "claude-extracted",
    lastChecked: "2026-09-02"
  },
  {
    name: "Harbin Institute of Technology",
    countryCode: "CN",
    countryName: "China",
    acceptedQualifications: ["attestat"],
    unlockRoutes: [
      {
        mechanism: "Direct entry on high school diploma",
        timeMonths: 0,
        description: "Direct admission on attestat for both Chinese-taught and English-taught programmes."
      }
    ],
    languageMinima: [
      { test: "IELTS", minScore: 6.0, notes: "For English-taught: IELTS 6.0 (no subtest <5.5) or TOEFL iBT 80. Chinese-taught: HSK 4 total 210+." }
    ],
    entranceExams: [
      { test: "HSK", minScore: 4, notes: "Level 4 with 210+ for Chinese-taught programmes." }
    ],
    tuition: {
      amount: 20000,
      currency: "CNY",
      notes: "CNY 20,000/year for Chinese-taught programmes; CNY 26,000/year for English-taught."
    },
    applicationFee: { amount: 400, currency: "CNY" },
    deadline: "2026-07-15",
    portal: "https://hit.at0086.cn/student",
    documentsRequired: "High school diploma, official transcripts, language proficiency certificate, physical examination record, passport copy.",
    notes: "Direct entry on diploma. Applicants must be under 30 (or under 25 for HIT Scholarship).",
    sourceUrl: "https://studyathit.hit.edu.cn/18358/list.htm",
    provenance: "claude-extracted",
    lastChecked: "2026-09-02"
  },
  {
    name: "Zhejiang University",
    countryCode: "CN",
    countryName: "China",
    acceptedQualifications: ["attestat"],
    unlockRoutes: [
      {
        mechanism: "Direct entry on senior high school diploma",
        timeMonths: 0,
        description: "Direct entry on diploma and transcript without a foundation year."
      }
    ],
    languageMinima: [
      { test: "TOEFL or IELTS", notes: "Required for non-native English speakers for English-taught programmes; no minimum stated." }
    ],
    entranceExams: [
      { test: "HSK", notes: "Required for Chinese-taught programmes; level published per major in undergraduate catalogue." }
    ],
    tuition: {
      notes: "Tuition varies by major and is not stated on this page (unknown, not free)."
    },
    applicationFee: { amount: 800, currency: "CNY" },
    deadline: "2026-02-28",
    portal: "https://intlstudent.zju.edu.cn/",
    documentsRequired: "Senior high school diploma, full transcripts, language certificate, personal statement, passport copy.",
    notes: "Applicants must be under 25. General deadline 28 February 2026.",
    sourceUrl: "https://iczu.zju.edu.cn/admissionsen/2024/1030/c68988a2981659/page.htm",
    provenance: "claude-extracted",
    lastChecked: "2026-09-02"
  }
];

export interface CountryFallbackInfo {
  code: string;
  name: string;
  directAcceptedOnAttestat: boolean;
  schoolingComparison: string;
  commonUnlockRoutes: string[];
  visaDepositRecorded?: { amount: number; currency: string; period: string; mechanism: string };
  dpFundingSummary: string;
  scholarshipsSummary: string;
  curatedUniversitiesInRepo: string[];
}

export const COUNTRY_FALLBACKS: Record<string, CountryFallbackInfo> = {
  TR: {
    code: "TR",
    name: "Turkey",
    directAcceptedOnAttestat: true,
    schoolingComparison: "11-year secondary education is directly recognised by Turkish higher education institutions (ÖSYM / YÖK).",
    commonUnlockRoutes: ["Direct admission on attestat", "TR-YÖS entrance exam (sat twice a year)", "SAT (required by top public universities like Boğaziçi/ODTÜ)"],
    dpFundingSummary: "The State Programme funds 106 bachelor places and 286 master's places in Turkey for 2026.",
    scholarshipsSummary: "Türkiye Bursları offers full funding for bachelor applicants under 21 (applications 10 Jan – 20 Feb).",
    curatedUniversitiesInRepo: ["Bogazici University", "Istanbul Technical University"]
  },
  DE: {
    code: "DE",
    name: "Germany",
    directAcceptedOnAttestat: false,
    schoolingComparison: "German Abitur is 12 or 13 years. Azerbaijani 11-year attestat alone grants access to Studienkolleg (preparatory course), not direct university entry.",
    commonUnlockRoutes: [
      "1 year of completed study at a recognised Azerbaijani university (opens direct subject-restricted admission)",
      "1-year Studienkolleg course in Germany + Feststellungsprüfung (FSP) assessment exam"
    ],
    visaDepositRecorded: {
      amount: 11904,
      currency: "EUR",
      period: "per year",
      mechanism: "Blocked bank account (Sperrkonto) prior to visa issuance"
    },
    dpFundingSummary: "The State Programme funds 27 bachelor places and 189 master's places in Germany.",
    scholarshipsSummary: "Public universities are tuition-free. DAAD grants are almost entirely for master's and PhD levels.",
    curatedUniversitiesInRepo: ["Technical University of Munich", "Heidelberg University", "LMU Munich"]
  },
  GB: {
    code: "GB",
    name: "United Kingdom",
    directAcceptedOnAttestat: false,
    schoolingComparison: "UK degree entry requires 12/13 years of schooling (A Levels/IB). The attestat alone is not accepted for direct entry to undergraduate programmes.",
    commonUnlockRoutes: [
      "1 year of study at an accredited Azerbaijani university (accepted for direct entry at Manchester, Cambridge)",
      "1-year approved international foundation year programme (e.g. UCL UPC, Edinburgh IFP)"
    ],
    dpFundingSummary: "The State Programme funds 161 bachelor places and 382 master's places in the UK.",
    scholarshipsSummary: "Chevening is strictly for master's applicants with 2,800 documented work hours. Bachelor scholarships are rare; self-funded fees range £18,000–£45,000/year.",
    curatedUniversitiesInRepo: ["University of Cambridge", "University of Manchester", "UCL", "University of Edinburgh"]
  },
  US: {
    code: "US",
    name: "United States",
    directAcceptedOnAttestat: false,
    schoolingComparison: "US high school is 12 years. 11-year attestat applicants are evaluated holistically; SAT/ACT or community college transfer often recommended.",
    commonUnlockRoutes: [
      "Direct application with strong SAT/ACT and extracurricular record (holistic review)",
      "2-year Community College associate degree transfer"
    ],
    dpFundingSummary: "The State Programme funds ZERO (0) bachelor places in the USA, and 289 master's places.",
    scholarshipsSummary: "US bachelor scholarships are university-specific merit or need-based aid. No government bilateral awards exist for bachelor level.",
    curatedUniversitiesInRepo: []
  },
  PL: {
    code: "PL",
    name: "Poland",
    directAcceptedOnAttestat: true,
    schoolingComparison: "Attestat with apostille and sworn Polish translation is accepted directly for university admission.",
    commonUnlockRoutes: ["Direct entry with secondary school certificate and English certificate (IELTS/TOEFL)"],
    dpFundingSummary: "The State Programme funds ZERO (0) bachelor places and 8 master's places in Poland.",
    scholarshipsSummary: "NAWA Banach scholarship is for master's only (humanities & social sciences for Azerbaijanis). Bachelor tuition is affordable (~€2,000–€4,000/year).",
    curatedUniversitiesInRepo: []
  },
  CN: {
    code: "CN",
    name: "China",
    directAcceptedOnAttestat: true,
    schoolingComparison: "Attestat is accepted directly for university admissions.",
    commonUnlockRoutes: [
      "Direct entry on attestat with HSK (for Chinese-taught) or IELTS (for English-taught)",
      "CSC-funded scholarship route (CSC bachelor requires Chinese-taught and CSCA exam)"
    ],
    dpFundingSummary: "The State Programme funds 307 bachelor places (the largest destination by bachelor quota) and 538 master's places.",
    scholarshipsSummary: "Chinese Government Scholarship (CSC) funds tuition, stipend and accommodation; bachelor CSC recipients must study in Chinese.",
    curatedUniversitiesInRepo: ["Tsinghua University", "Harbin Institute of Technology", "Zhejiang University"]
  }
};

export const KNOWN_UNIVERSITY_COUNTRY: Record<string, string> = {
  "Harvard University": "US",
  "Massachusetts Institute of Technology": "US",
  "Stanford University": "US",
  "University of Oxford": "GB",
  "University of Cambridge": "GB",
  "Imperial College London": "GB",
  "University of Manchester": "GB",
  "UCL": "GB",
  "University of Edinburgh": "GB",
  "University of Warsaw": "PL",
  "Warsaw University of Technology": "PL",
  "Bogazici University": "TR",
  "Istanbul Technical University": "TR",
  "Middle East Technical University": "TR",
  "Bilkent University": "TR",
  "Koc University": "TR",
  "Sabanci University": "TR",
  "Technical University of Munich": "DE",
  "Heidelberg University": "DE",
  "LMU Munich": "DE",
  "Tsinghua University": "CN",
  "Harbin Institute of Technology": "CN",
  "Zhejiang University": "CN",
  "Peking University": "CN"
};

