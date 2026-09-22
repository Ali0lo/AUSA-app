/**
 * Client library and zero-latency local fallback calculation engine for
 * DİM (State Examination Center - Dövlət İmtahan Mərkəzi) 700-point score simulation
 * and historical admission cutoff matching.
 */

export type DimGroup = "I qrup" | "II qrup" | "III qrup" | "IV qrup" | "V qrup";
export type SubGroup = "RK" | "RI" | "DT" | "TC" | "NONE";
export type ChanceLevel = "SAFE" | "REALISTIC" | "TARGET" | "ASPIRATIONAL";

export interface SubjectQuestionInput {
  subject_key: string;
  subject_name: string;
  closed_correct: number;
  closed_incorrect: number;
  open_points: number;
  max_closed: number;
  max_open_points: number;
  max_scaled_points: number;
  direct_score?: number | null;
}

export interface SubjectScoreResult {
  subject_key: string;
  subject_name: string;
  net_closed: number;
  open_points: number;
  total_raw: number;
  max_raw: number;
  scaled_score: number;
  max_scaled: number;
  percentage: number;
}

export interface BuraxilisInput {
  native_language: SubjectQuestionInput;
  mathematics: SubjectQuestionInput;
  foreign_language: SubjectQuestionInput;
  direct_total_score?: number | null;
}

export interface BlokInput {
  subject_1?: SubjectQuestionInput | null;
  subject_2?: SubjectQuestionInput | null;
  subject_3?: SubjectQuestionInput | null;
  direct_total_score?: number | null;
}

export interface DimCalculationRequest {
  group: DimGroup;
  subgroup: SubGroup;
  buraxilis: BuraxilisInput;
  blok?: BlokInput | null;
}

export interface DimScoreBreakdown {
  group: DimGroup;
  subgroup: SubGroup;
  buraxilis_score: number;
  blok_score: number;
  total_score: number;
  max_total: number;
  percentage: number;
  buraxilis_subjects: SubjectScoreResult[];
  blok_subjects: SubjectScoreResult[];
  clears_bhos_benchmark: boolean;
  passed_competition_minimum: boolean;
}

export interface SpecialtyRecommendation {
  program_code: string;
  university_name: string;
  department_name: string;
  group_name: string;
  scholarship_type: string;
  cutoff_2025: number;
  cutoff_2024?: number | null;
  cutoff_2023?: number | null;
  three_year_trend?: string | null;
  candidate_score: number;
  score_delta: number;
  chance_level: ChanceLevel;
  is_bhos: boolean;
  requires_650_rule: boolean;
}

/** Where the cutoffs behind a recommendation list came from.
 *
 * An empty list has more than one cause, and they are not interchangeable: the score may
 * have matched nothing, the deployment may hold no cutoff history at all, or the API may
 * have been unreachable and left us on the small offline excerpt. Rendering all three as
 * "no specialties found" states a finding we have not earned. */
export type CutoffCorpusStatus = "available" | "unavailable" | "fallback";

export interface DimRecommendationResponse {
  score_breakdown: DimScoreBreakdown;
  corpus_status?: CutoffCorpusStatus;
  corpus_note?: string | null;
  total_matched: number;
  safe_count: number;
  realistic_count: number;
  target_count: number;
  aspirational_count: number;
  recommendations: SpecialtyRecommendation[];
}

export interface RecommendRequest {
  group: DimGroup;
  subgroup: SubGroup;
  candidate_score?: number | null;
  calculation_request?: DimCalculationRequest | null;
  university_filter?: string | null;
  chance_filter?: ChanceLevel | null;
  search_query?: string | null;
  limit?: number;
}

export interface SubgroupMeta {
  code: string;
  name: string;
  subjects: string[];
}

export interface GroupMetadata {
  group: DimGroup;
  name: string;
  description: string;
  subgroups: SubgroupMeta[];
  max_buraxilis: number;
  max_blok: number;
  max_total: number;
}

export const DIM_GROUPS_META: GroupMetadata[] = [
  {
    group: "I qrup",
    name: "I İxtisas Qrupu",
    description: "Dəqiq və texniki elmlər, mühəndislik, IT və kompüter elmləri",
    subgroups: [
      {
        code: "RI",
        name: "Riyaziyyat - İnformatika (Rİ)",
        subjects: ["Riyaziyyat (150 bal)", "Fizika (150 bal)", "İnformatika (100 bal)"],
      },
      {
        code: "RK",
        name: "Riyaziyyat - Kimya (RK)",
        subjects: ["Riyaziyyat (150 bal)", "Fizika (150 bal)", "Kimya (100 bal)"],
      },
    ],
    max_buraxilis: 300,
    max_blok: 400,
    max_total: 700,
  },
  {
    group: "II qrup",
    name: "II İxtisas Qrupu",
    description: "İqtisadiyyat, idarəetmə, maliyyə, biznes və beynəlxalq münasibətlər",
    subgroups: [
      {
        code: "NONE",
        name: "Standart",
        subjects: ["Riyaziyyat (150 bal)", "Coğrafiya (150 bal)", "Tarix (100 bal)"],
      },
    ],
    max_buraxilis: 300,
    max_blok: 400,
    max_total: 700,
  },
  {
    group: "III qrup",
    name: "III İxtisas Qrupu",
    description: "Humanitar, filologiya, hüquqşünaslıq, təhsil və pedaqogika",
    subgroups: [
      {
        code: "DT",
        name: "Dil - Tarix (DT)",
        subjects: ["Azərbaycan dili (150 bal)", "Tarix (150 bal)", "Ədəbiyyat (100 bal)"],
      },
      {
        code: "TC",
        name: "Tarix - Coğrafiya (TC)",
        subjects: ["Azərbaycan dili (150 bal)", "Tarix (150 bal)", "Coğrafiya (100 bal)"],
      },
    ],
    max_buraxilis: 300,
    max_blok: 400,
    max_total: 700,
  },
  {
    group: "IV qrup",
    name: "IV İxtisas Qrupu",
    description: "Təbii və tibb elmləri: Tibb, stomatologiya, əczaçılıq, biologiya, kimya",
    subgroups: [
      {
        code: "NONE",
        name: "Standart",
        subjects: ["Biologiya (150 bal)", "Kimya (150 bal)", "Fizika (100 bal)"],
      },
    ],
    max_buraxilis: 300,
    max_blok: 400,
    max_total: 700,
  },
  {
    group: "V qrup",
    name: "V İxtisas Qrupu",
    description: "Xüsusi qabiliyyət tələb edən ixtisaslar (Musiqi, incəsənət, dizayn, idman)",
    subgroups: [
      {
        code: "NONE",
        name: "Buraxılış + Qabiliyyət",
        subjects: ["Buraxılış imtahanı (300 bal)", "Xüsusi Qabiliyyət imtahanı"],
      },
    ],
    max_buraxilis: 300,
    max_blok: 100,
    max_total: 400,
  },
];

export function getDefaultBuraxilisInput(): BuraxilisInput {
  return {
    native_language: {
      subject_key: "native_language",
      subject_name: "Azərbaycan dili",
      closed_correct: 18,
      closed_incorrect: 2,
      open_points: 12,
      max_closed: 20,
      max_open_points: 20,
      max_scaled_points: 100,
    },
    mathematics: {
      subject_key: "mathematics",
      subject_name: "Riyaziyyat",
      closed_correct: 12,
      closed_incorrect: 1,
      open_points: 14,
      max_closed: 13,
      max_open_points: 19,
      max_scaled_points: 100,
    },
    foreign_language: {
      subject_key: "foreign_language",
      subject_name: "Xarici dil (İngilis dili)",
      closed_correct: 20,
      closed_incorrect: 2,
      open_points: 12,
      max_closed: 22,
      max_open_points: 16,
      max_scaled_points: 100,
    },
  };
}

export function getDefaultBlokInput(group: DimGroup, subgroup: SubGroup = "RI"): BlokInput {
  if (group === "I qrup") {
    if (subgroup === "RK") {
      return {
        subject_1: {
          subject_key: "math_g1",
          subject_name: "Riyaziyyat",
          closed_correct: 20,
          closed_incorrect: 2,
          open_points: 12,
          max_closed: 22,
          max_open_points: 16,
          max_scaled_points: 150,
        },
        subject_2: {
          subject_key: "physics_g1",
          subject_name: "Fizika",
          closed_correct: 18,
          closed_incorrect: 3,
          open_points: 10,
          max_closed: 22,
          max_open_points: 16,
          max_scaled_points: 150,
        },
        subject_3: {
          subject_key: "chemistry_g1",
          subject_name: "Kimya",
          closed_correct: 19,
          closed_incorrect: 2,
          open_points: 11,
          max_closed: 22,
          max_open_points: 16,
          max_scaled_points: 100,
        },
      };
    }
    return {
      subject_1: {
        subject_key: "math_g1",
        subject_name: "Riyaziyyat",
        closed_correct: 20,
        closed_incorrect: 2,
        open_points: 12,
        max_closed: 22,
        max_open_points: 16,
        max_scaled_points: 150,
      },
      subject_2: {
        subject_key: "physics_g1",
        subject_name: "Fizika",
        closed_correct: 18,
        closed_incorrect: 3,
        open_points: 10,
        max_closed: 22,
        max_open_points: 16,
        max_scaled_points: 150,
      },
      subject_3: {
        subject_key: "informatics_g1",
        subject_name: "İnformatika",
        closed_correct: 20,
        closed_incorrect: 1,
        open_points: 13,
        max_closed: 22,
        max_open_points: 16,
        max_scaled_points: 100,
      },
    };
  } else if (group === "II qrup") {
    return {
      subject_1: {
        subject_key: "math_g2",
        subject_name: "Riyaziyyat",
        closed_correct: 19,
        closed_incorrect: 2,
        open_points: 11,
        max_closed: 22,
        max_open_points: 16,
        max_scaled_points: 150,
      },
      subject_2: {
        subject_key: "geography_g2",
        subject_name: "Coğrafiya",
        closed_correct: 20,
        closed_incorrect: 2,
        open_points: 12,
        max_closed: 22,
        max_open_points: 16,
        max_scaled_points: 150,
      },
      subject_3: {
        subject_key: "history_g2",
        subject_name: "Tarix",
        closed_correct: 18,
        closed_incorrect: 3,
        open_points: 10,
        max_closed: 22,
        max_open_points: 16,
        max_scaled_points: 100,
      },
    };
  } else if (group === "III qrup") {
    if (subgroup === "TC") {
      return {
        subject_1: {
          subject_key: "azerbaijani_g3",
          subject_name: "Azərbaycan dili",
          closed_correct: 20,
          closed_incorrect: 2,
          open_points: 12,
          max_closed: 22,
          max_open_points: 16,
          max_scaled_points: 150,
        },
        subject_2: {
          subject_key: "history_g3",
          subject_name: "Tarix",
          closed_correct: 19,
          closed_incorrect: 2,
          open_points: 11,
          max_closed: 22,
          max_open_points: 16,
          max_scaled_points: 150,
        },
        subject_3: {
          subject_key: "geography_g3",
          subject_name: "Coğrafiya",
          closed_correct: 18,
          closed_incorrect: 3,
          open_points: 10,
          max_closed: 22,
          max_open_points: 16,
          max_scaled_points: 100,
        },
      };
    }
    return {
      subject_1: {
        subject_key: "azerbaijani_g3",
        subject_name: "Azərbaycan dili",
        closed_correct: 20,
        closed_incorrect: 2,
        open_points: 12,
        max_closed: 22,
        max_open_points: 16,
        max_scaled_points: 150,
      },
      subject_2: {
        subject_key: "history_g3",
        subject_name: "Tarix",
        closed_correct: 19,
        closed_incorrect: 2,
        open_points: 11,
        max_closed: 22,
        max_open_points: 16,
        max_scaled_points: 150,
      },
      subject_3: {
        subject_key: "literature_g3",
        subject_name: "Ədəbiyyat",
        closed_correct: 18,
        closed_incorrect: 3,
        open_points: 10,
        max_closed: 22,
        max_open_points: 16,
        max_scaled_points: 100,
      },
    };
  } else if (group === "IV qrup") {
    return {
      subject_1: {
        subject_key: "biology_g4",
        subject_name: "Biologiya",
        closed_correct: 20,
        closed_incorrect: 2,
        open_points: 12,
        max_closed: 22,
        max_open_points: 16,
        max_scaled_points: 150,
      },
      subject_2: {
        subject_key: "chemistry_g4",
        subject_name: "Kimya",
        closed_correct: 19,
        closed_incorrect: 2,
        open_points: 11,
        max_closed: 22,
        max_open_points: 16,
        max_scaled_points: 150,
      },
      subject_3: {
        subject_key: "physics_g4",
        subject_name: "Fizika",
        closed_correct: 18,
        closed_incorrect: 3,
        open_points: 10,
        max_closed: 22,
        max_open_points: 16,
        max_scaled_points: 100,
      },
    };
  }
  return {
    subject_1: {
      subject_key: "qabiliyyet_g5",
      subject_name: "Xüsusi Qabiliyyət",
      closed_correct: 0,
      closed_incorrect: 0,
      open_points: 75,
      max_closed: 0,
      max_open_points: 100,
      max_scaled_points: 100,
    },
  };
}

/**
 * Client-side local subject score calculator.
 */
export function calculateLocalSubjectScore(inp: SubjectQuestionInput): SubjectScoreResult {
  if (inp.direct_score !== undefined && inp.direct_score !== null) {
    const capped = Math.min(inp.max_scaled_points, Math.max(0, inp.direct_score));
    return {
      subject_key: inp.subject_key,
      subject_name: inp.subject_name,
      net_closed: 0,
      open_points: 0,
      total_raw: capped,
      max_raw: inp.max_scaled_points,
      scaled_score: Math.round(capped * 10) / 10,
      max_scaled: inp.max_scaled_points,
      percentage: Math.round((capped / inp.max_scaled_points) * 1000) / 10,
    };
  }

  const netClosed = Math.max(0, inp.closed_correct - inp.closed_incorrect * 0.25);
  const openPts = Math.min(inp.max_open_points, inp.open_points);
  const totalRaw = netClosed + openPts;
  const maxRaw = inp.max_closed + inp.max_open_points;

  const scaled = maxRaw > 0 ? (totalRaw / maxRaw) * inp.max_scaled_points : 0;
  const clampedScaled = Math.min(inp.max_scaled_points, Math.max(0, scaled));
  const roundedScaled = Math.round(clampedScaled * 10) / 10;
  const percentage = Math.round((roundedScaled / inp.max_scaled_points) * 1000) / 10;

  return {
    subject_key: inp.subject_key,
    subject_name: inp.subject_name,
    net_closed: Math.round(netClosed * 100) / 100,
    open_points: Math.round(openPts * 10) / 10,
    total_raw: Math.round(totalRaw * 100) / 100,
    max_raw: maxRaw,
    scaled_score: roundedScaled,
    max_scaled: inp.max_scaled_points,
    percentage,
  };
}

/**
 * Client-side local total score calculator for zero-latency slider updates.
 */
export function calculateLocalTotalDimScore(req: DimCalculationRequest): DimScoreBreakdown {
  const buraxilisSubjs = [
    calculateLocalSubjectScore(req.buraxilis.native_language),
    calculateLocalSubjectScore(req.buraxilis.mathematics),
    calculateLocalSubjectScore(req.buraxilis.foreign_language),
  ];

  let buraxilisTotal: number;
  if (req.buraxilis.direct_total_score !== undefined && req.buraxilis.direct_total_score !== null) {
    buraxilisTotal = Math.min(300, Math.max(0, req.buraxilis.direct_total_score));
  } else {
    buraxilisTotal = buraxilisSubjs.reduce((acc, s) => acc + s.scaled_score, 0);
    buraxilisTotal = Math.min(300, Math.max(0, buraxilisTotal));
  }

  const defaultBlok = getDefaultBlokInput(req.group, req.subgroup);
  const blokInp = req.blok || defaultBlok;
  const blokSubjs: SubjectScoreResult[] = [];

  if (blokInp.subject_1) blokSubjs.push(calculateLocalSubjectScore(blokInp.subject_1));
  if (blokInp.subject_2) blokSubjs.push(calculateLocalSubjectScore(blokInp.subject_2));
  if (blokInp.subject_3) blokSubjs.push(calculateLocalSubjectScore(blokInp.subject_3));

  let blokTotal: number;
  if (blokInp.direct_total_score !== undefined && blokInp.direct_total_score !== null) {
    blokTotal = Math.min(400, Math.max(0, blokInp.direct_total_score));
  } else {
    blokTotal = blokSubjs.reduce((acc, s) => acc + s.scaled_score, 0);
    blokTotal = Math.min(400, Math.max(0, blokTotal));
  }

  const total = Math.round(Math.min(700, buraxilisTotal + blokTotal) * 10) / 10;
  const percentage = Math.round((total / 700) * 1000) / 10;

  return {
    group: req.group,
    subgroup: req.subgroup,
    buraxilis_score: Math.round(buraxilisTotal * 10) / 10,
    blok_score: Math.round(blokTotal * 10) / 10,
    total_score: total,
    max_total: 700,
    percentage,
    buraxilis_subjects: buraxilisSubjs,
    blok_subjects: blokSubjs,
    clears_bhos_benchmark: total >= 650,
    passed_competition_minimum: total >= 150,
  };
}

// Built-in curated historical cutoffs dataset for offline/fast UI fallback
export const CURATED_FALLBACK_RECOMMENDATIONS: Record<DimGroup, SpecialtyRecommendation[]> = {
  "I qrup": [
    {
      program_code: "ada-cs-g1",
      university_name: "ADA",
      department_name: "Kompüter elmləri (tədris ingilis dilində)",
      group_name: "I qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 692.6,
      cutoff_2024: 686.0,
      cutoff_2023: 679.5,
      three_year_trend: "+6.6",
      candidate_score: 640.0,
      score_delta: -52.6,
      chance_level: "ASPIRATIONAL",
      is_bhos: false,
      requires_650_rule: false,
    },
    {
      program_code: "bhos-cyber-g1",
      university_name: "Baku Higher Oil School (BANM / BHOS)",
      department_name: "İnformasiya təhlükəsizliyi (tədris ingilis dilində)",
      group_name: "I qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 681.0,
      cutoff_2024: 687.1,
      cutoff_2023: 682.0,
      three_year_trend: "-6.1",
      candidate_score: 640.0,
      score_delta: -41.0,
      chance_level: "ASPIRATIONAL",
      is_bhos: true,
      requires_650_rule: false,
    },
    {
      program_code: "bhos-cs-g1",
      university_name: "Baku Higher Oil School (BANM / BHOS)",
      department_name: "Kompüter elmləri",
      group_name: "I qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 672.8,
      cutoff_2024: 673.5,
      cutoff_2023: 668.0,
      three_year_trend: "-0.7",
      candidate_score: 640.0,
      score_delta: -32.8,
      chance_level: "TARGET",
      is_bhos: true,
      requires_650_rule: false,
    },
    {
      program_code: "bhos-ce-g1",
      university_name: "Baku Higher Oil School (BANM / BHOS)",
      department_name: "Kompüter mühəndisliyi",
      group_name: "I qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 662.2,
      cutoff_2024: 673.0,
      cutoff_2023: 665.0,
      three_year_trend: "-10.8",
      candidate_score: 640.0,
      score_delta: -22.2,
      chance_level: "TARGET",
      is_bhos: true,
      requires_650_rule: false,
    },
    {
      program_code: "bhos-data-g1",
      university_name: "Baku Higher Oil School (BANM / BHOS)",
      department_name: "Data analitikası",
      group_name: "I qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 658.1,
      cutoff_2024: 655.0,
      cutoff_2023: 650.0,
      three_year_trend: "+3.1",
      candidate_score: 640.0,
      score_delta: -18.1,
      chance_level: "TARGET",
      is_bhos: true,
      requires_650_rule: false,
    },
    {
      program_code: "unec-it-g1",
      university_name: "UNEC",
      department_name: "İnformasiya texnologiyaları",
      group_name: "I qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 624.9,
      cutoff_2024: 618.0,
      cutoff_2023: 605.0,
      three_year_trend: "+6.9",
      candidate_score: 640.0,
      score_delta: 15.1,
      chance_level: "REALISTIC",
      is_bhos: false,
      requires_650_rule: false,
    },
    {
      program_code: "bdu-cs-g1",
      university_name: "BDU",
      department_name: "Kompüter elmləri",
      group_name: "I qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 602.4,
      cutoff_2024: 595.0,
      cutoff_2023: 588.0,
      three_year_trend: "+7.4",
      candidate_score: 640.0,
      score_delta: 37.6,
      chance_level: "SAFE",
      is_bhos: false,
      requires_650_rule: false,
    },
    {
      program_code: "bmu-ce-g1",
      university_name: "BMU",
      department_name: "Kompüter mühəndisliyi",
      group_name: "I qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 588.3,
      cutoff_2024: 580.0,
      cutoff_2023: 572.0,
      three_year_trend: "+8.3",
      candidate_score: 640.0,
      score_delta: 51.7,
      chance_level: "SAFE",
      is_bhos: false,
      requires_650_rule: false,
    },
    {
      program_code: "adnsu-se-g1",
      university_name: "ADNSU",
      department_name: "Proqram mühəndisliyi",
      group_name: "I qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 565.0,
      cutoff_2024: 558.0,
      cutoff_2023: 549.0,
      three_year_trend: "+7.0",
      candidate_score: 640.0,
      score_delta: 75.0,
      chance_level: "SAFE",
      is_bhos: false,
      requires_650_rule: false,
    },
  ],
  "II qrup": [
    {
      program_code: "ada-fin-g2",
      university_name: "ADA",
      department_name: "Maliyyə (tədris ingilis dilində)",
      group_name: "II qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 668.5,
      cutoff_2024: 660.0,
      cutoff_2023: 652.0,
      three_year_trend: "+8.5",
      candidate_score: 600.0,
      score_delta: -68.5,
      chance_level: "ASPIRATIONAL",
      is_bhos: false,
      requires_650_rule: false,
    },
    {
      program_code: "unec-ise-g2",
      university_name: "UNEC",
      department_name: "Beynəlxalq İqtisadiyyat Məktəbi (İngilis dili)",
      group_name: "II qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 645.0,
      cutoff_2024: 638.0,
      cutoff_2023: 630.0,
      three_year_trend: "+7.0",
      candidate_score: 600.0,
      score_delta: -45.0,
      chance_level: "ASPIRATIONAL",
      is_bhos: false,
      requires_650_rule: false,
    },
    {
      program_code: "unec-fin-g2",
      university_name: "UNEC",
      department_name: "Maliyyə",
      group_name: "II qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 595.2,
      cutoff_2024: 588.0,
      cutoff_2023: 579.0,
      three_year_trend: "+7.2",
      candidate_score: 600.0,
      score_delta: 4.8,
      chance_level: "REALISTIC",
      is_bhos: false,
      requires_650_rule: false,
    },
    {
      program_code: "bdu-ir-g2",
      university_name: "BDU",
      department_name: "Beynəlxalq münasibətlər",
      group_name: "II qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 572.0,
      cutoff_2024: 565.0,
      cutoff_2023: 555.0,
      three_year_trend: "+7.0",
      candidate_score: 600.0,
      score_delta: 28.0,
      chance_level: "REALISTIC",
      is_bhos: false,
      requires_650_rule: false,
    },
    {
      program_code: "bmu-econ-g2",
      university_name: "BMU",
      department_name: "İqtisadiyyat",
      group_name: "II qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 540.0,
      cutoff_2024: 532.0,
      cutoff_2023: 520.0,
      three_year_trend: "+8.0",
      candidate_score: 600.0,
      score_delta: 60.0,
      chance_level: "SAFE",
      is_bhos: false,
      requires_650_rule: false,
    },
  ],
  "III qrup": [
    {
      program_code: "bdu-law-g3",
      university_name: "BDU",
      department_name: "Hüquqşünaslıq (tədris ingilis dilində)",
      group_name: "III qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 664.5,
      cutoff_2024: 660.3,
      cutoff_2023: 630.3,
      three_year_trend: "+4.2",
      candidate_score: 600.0,
      score_delta: -64.5,
      chance_level: "ASPIRATIONAL",
      is_bhos: false,
      requires_650_rule: false,
    },
    {
      program_code: "ada-ir-g3",
      university_name: "ADA",
      department_name: "Beynəlxalq münasibətlər (İngilis dili)",
      group_name: "III qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 642.0,
      cutoff_2024: 635.0,
      cutoff_2023: 625.0,
      three_year_trend: "+7.0",
      candidate_score: 600.0,
      score_delta: -42.0,
      chance_level: "ASPIRATIONAL",
      is_bhos: false,
      requires_650_rule: false,
    },
    {
      program_code: "adpu-phil-g3",
      university_name: "ADPU",
      department_name: "Azərbaycan dili və ədəbiyyatı müəllimliyi",
      group_name: "III qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 580.0,
      cutoff_2024: 572.0,
      cutoff_2023: 560.0,
      three_year_trend: "+8.0",
      candidate_score: 600.0,
      score_delta: 20.0,
      chance_level: "REALISTIC",
      is_bhos: false,
      requires_650_rule: false,
    },
    {
      program_code: "bdu-jour-g3",
      university_name: "BDU",
      department_name: "Jurnalistika",
      group_name: "III qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 525.0,
      cutoff_2024: 518.0,
      cutoff_2023: 510.0,
      three_year_trend: "+7.0",
      candidate_score: 600.0,
      score_delta: 75.0,
      chance_level: "SAFE",
      is_bhos: false,
      requires_650_rule: false,
    },
  ],
  "IV qrup": [
    {
      program_code: "atu-med-eng-g4",
      university_name: "ATU",
      department_name: "Müalicə işi (tədris ingilis dilində)",
      group_name: "IV qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 683.7,
      cutoff_2024: 681.4,
      cutoff_2023: 667.8,
      three_year_trend: "+2.3",
      candidate_score: 620.0,
      score_delta: -63.7,
      chance_level: "ASPIRATIONAL",
      is_bhos: false,
      requires_650_rule: false,
    },
    {
      program_code: "atu-dent-g4",
      university_name: "ATU",
      department_name: "Stomatologiya",
      group_name: "IV qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 635.0,
      cutoff_2024: 628.0,
      cutoff_2023: 615.0,
      three_year_trend: "+7.0",
      candidate_score: 620.0,
      score_delta: -15.0,
      chance_level: "TARGET",
      is_bhos: false,
      requires_650_rule: false,
    },
    {
      program_code: "bdu-bio-g4",
      university_name: "BDU",
      department_name: "Biologiya",
      group_name: "IV qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 550.0,
      cutoff_2024: 542.0,
      cutoff_2023: 530.0,
      three_year_trend: "+8.0",
      candidate_score: 620.0,
      score_delta: 70.0,
      chance_level: "SAFE",
      is_bhos: false,
      requires_650_rule: false,
    },
  ],
  "V qrup": [
    {
      program_code: "adra-des-g5",
      university_name: "ADRA",
      department_name: "Dizayn (Qrafik dizayn)",
      group_name: "V qrup",
      scholarship_type: "dövlət sifarişli",
      cutoff_2025: 220.0,
      cutoff_2024: 215.0,
      cutoff_2023: 205.0,
      three_year_trend: "+5.0",
      candidate_score: 250.0,
      score_delta: 30.0,
      chance_level: "SAFE",
      is_bhos: false,
      requires_650_rule: false,
    },
  ],
};

/**
 * Fetch statutory group metadata from backend with local fallback.
 */
export async function fetchDimGroups(): Promise<GroupMetadata[]> {
  try {
    const res = await fetch("/api/v1/dim/groups");
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // network or dev fallback
  }
  return DIM_GROUPS_META;
}

/**
 * Call backend calculate endpoint with local calculation fallback.
 */
export async function calculateDimScore(req: DimCalculationRequest): Promise<DimScoreBreakdown> {
  try {
    const res = await fetch("/api/v1/dim/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // network or dev fallback
  }
  return calculateLocalTotalDimScore(req);
}

/**
 * Call backend recommend endpoint with local filtering fallback.
 */
export async function fetchSpecialtyRecommendations(
  req: RecommendRequest,
  scoreBreakdown?: DimScoreBreakdown
): Promise<DimRecommendationResponse> {
  try {
    const res = await fetch("/api/v1/dim/recommend", {
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

  // Local fallback evaluation
  const breakdown =
    scoreBreakdown ||
    (req.calculation_request
      ? calculateLocalTotalDimScore(req.calculation_request)
      : calculateLocalTotalDimScore({
          group: req.group,
          subgroup: req.subgroup,
          buraxilis: {
            ...getDefaultBuraxilisInput(),
            direct_total_score: req.candidate_score ? (req.candidate_score * 300) / 700 : undefined,
          },
          blok: {
            ...getDefaultBlokInput(req.group, req.subgroup),
            direct_total_score: req.candidate_score ? (req.candidate_score * 400) / 700 : undefined,
          },
        }));

  const candScore = req.candidate_score || breakdown.total_score;
  const list = CURATED_FALLBACK_RECOMMENDATIONS[req.group] || [];

  let safeCount = 0;
  let realisticCount = 0;
  let targetCount = 0;
  let aspirationalCount = 0;

  const adjusted = list
    .map((item) => {
      const delta = Math.round((candScore - item.cutoff_2025) * 10) / 10;
      let chance: ChanceLevel;
      if (delta >= 30) {
        chance = "SAFE";
        safeCount++;
      } else if (delta >= 0) {
        chance = "REALISTIC";
        realisticCount++;
      } else if (delta >= -35) {
        chance = "TARGET";
        targetCount++;
      } else {
        chance = "ASPIRATIONAL";
        aspirationalCount++;
      }
      return {
        ...item,
        candidate_score: candScore,
        score_delta: delta,
        chance_level: chance,
      };
    })
    .filter((item) => {
      if (req.university_filter && !item.university_name.toLowerCase().includes(req.university_filter.toLowerCase())) {
        return false;
      }
      if (
        req.search_query &&
        !item.department_name.toLowerCase().includes(req.search_query.toLowerCase()) &&
        !item.university_name.toLowerCase().includes(req.search_query.toLowerCase())
      ) {
        return false;
      }
      if (req.chance_filter && item.chance_level !== req.chance_filter) {
        return false;
      }
      return true;
    });

  const tierOrder: Record<ChanceLevel, number> = {
    SAFE: 0,
    REALISTIC: 1,
    TARGET: 2,
    ASPIRATIONAL: 3,
  };
  adjusted.sort((a, b) => tierOrder[a.chance_level] - tierOrder[b.chance_level] || b.cutoff_2025 - a.cutoff_2025);

  return {
    score_breakdown: breakdown,
    // The API did not answer, so these came from the offline excerpt below, not from the
    // full cutoff history. The student is told rather than left to assume otherwise.
    corpus_status: "fallback",
    corpus_note:
      "Keçid balı bazası ilə əlaqə qurulmadı. Aşağıdakılar kiçik oflayn siyahıdan götürülüb " +
      "(mənbə: sec.az/kecid-ballari), tam bazadan deyil.",
    total_matched: adjusted.length,
    safe_count: safeCount,
    realistic_count: realisticCount,
    target_count: targetCount,
    aspirational_count: aspirationalCount,
    recommendations: adjusted.slice(0, req.limit || 50),
  };
}
