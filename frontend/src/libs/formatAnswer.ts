import { DataPoint } from "@/orval/models/backend-api";

export const transformAnswer = (answer: string, dataPoints: DataPoint[]): string => {
  const citeNumbers = dataPoints?.map(dp => `cite:${dp.cite_number}`);
  const regex = new RegExp(`\\[(${citeNumbers?.join("|")})\\](?!\\()`, "g");

  const replaceCallback = (match: string, citeNumber: string) => {
    const dataPoint = dataPoints?.find(dp => dp.cite_number === parseInt(citeNumber.split(":")[1]));
    if (!dataPoint) {
      return match;
    }

    return `[${dataPoint.cite_number}](cite:${dataPoint.cite_number})`;
  };

  return answer?.replace(regex, replaceCallback);
};

export const transformAnswerToStringForCopy = (answer: string, dataPoints: DataPoint[]): string => {
  let citationCount = 0;
  // 参照元のタイトルとインデックスのマップ
  const titleToIndexMap: Map<string, number> = new Map();
  const citeNumbers = dataPoints?.map(dp => `cite:${dp.cite_number}`);
  const regex = new RegExp(`\\[(${citeNumbers?.join("|")})\\](?!\\()`, "g");

  const replaceCallback = (match: string, citeNumber: string) => {
    const dataPoint = dataPoints?.find(dp => dp.cite_number === parseInt(citeNumber.split(":")[1]));
    if (!dataPoint) {
      return match;
    }

    let index = titleToIndexMap.get(citeNumber);
    if (typeof index === "undefined") {
      index = citationCount + 1;
      citationCount++;
      titleToIndexMap.set(citeNumber, index);
    }

    return `[引用${index}]`;
  };

  const transformedAnswer = answer?.replace(regex, replaceCallback);
  return transformedAnswer;
};
