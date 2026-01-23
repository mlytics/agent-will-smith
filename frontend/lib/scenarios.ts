/**
 * Scenario definitions for conversation analytics.
 * Each scenario represents a user persona with specific financial characteristics.
 */

export interface Scenario {
  id: string;
  name: string;
  icon: string;
  shortDesc: string;
  persona: string | null;
}

export const SCENARIOS: Scenario[] = [
  {
    id: "cxo_wealth",
    name: "高階主管資產規劃",
    icon: "👔",
    shortDesc: "52歲 CFO・資產規劃",
    persona: `你是一位 52 歲的科技公司 CFO。
• 年收入約 800 萬台幣
• 流動資產約 3000 萬
• 想在 55 歲前退休
• 對投資有經驗，但想了解更多稅務優化的方式
• 關心資產傳承和退休後的現金流`,
  },
  {
    id: "young_starter",
    name: "年輕小資族入門",
    icon: "👩‍💻",
    shortDesc: "28歲工程師・理財入門",
    persona: `你是一位 28 歲的軟體工程師。
• 月薪約 6 萬台幣
• 剛開始想理財，但不知道從何開始
• 對風險比較保守，想先存到第一桶金
• 對股票和基金有興趣但不太懂
• 希望能有系統地學習理財`,
  },
  {
    id: "retiree_stable",
    name: "退休族穩健配置",
    icon: "👴",
    shortDesc: "62歲退休教師・穩定領息",
    persona: `你是一位 62 歲剛退休的高中教師。
• 有退休金每月約 5 萬
• 另有積蓄約 500 萬
• 想要穩定的被動收入
• 非常保守，不想承擔太多風險
• 關心醫療保險和長照規劃`,
  },
  {
    id: "family_education",
    name: "雙薪家庭子女規劃",
    icon: "👨‍👩‍👧",
    shortDesc: "38歲夫妻・教育基金",
    persona: `你是一對 38 歲的雙薪夫妻。
• 家庭年收入約 200 萬台幣
• 有一個 5 歲的小孩
• 想規劃小孩的教育基金
• 也關心家庭保障和房貸規劃
• 風險承受度中等`,
  },
  {
    id: "free_form",
    name: "自由對話",
    icon: "💬",
    shortDesc: "不設限・隨意聊",
    persona: null,
  },
];

/**
 * Retrieves a scenario by its ID.
 * @param id - The scenario identifier
 * @returns The matching scenario or undefined if not found
 */
export function getScenario(id: string): Scenario | undefined {
  return SCENARIOS.find((s) => s.id === id);
}
