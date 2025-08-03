import { Order } from "@/components/tables/CustomTable";

export type Comparator<T> = (a: T, b: T) => number;

// 比較関数の生成
export const getComparator = <T>(order: Order, orderBy: keyof T): Comparator<T> => {
  return (a, b) => {
    const aValue = a[orderBy];
    const bValue = b[orderBy];

    // null は最後に表示する
    if (aValue === null && bValue !== null) {
      return 1;
    }
    if (aValue !== null && bValue === null) {
      return -1;
    }
    if (aValue === null && bValue === null) {
      return 0;
    }

    // orderBy が配列またはオブジェクトの場合はソートしない
    if (
      Array.isArray(aValue) ||
      typeof aValue === "object" ||
      Array.isArray(bValue) ||
      typeof bValue === "object"
    ) {
      return 0;
    }

    // 数値の場合は数値比較を行う
    if (typeof aValue === "number" && typeof bValue === "number") {
      return order === "desc" ? bValue - aValue : aValue - bValue;
    }

    // 文字列の場合は文字列比較を行う
    if (typeof aValue === "string" && typeof bValue === "string") {
      // orderBy が created_at の場合は日付比較を行う
      if (orderBy === "created_at" || orderBy === "updated_at") {
        const aTime = new Date(aValue).getTime();
        const bTime = new Date(bValue).getTime();
        return order === "desc" ? bTime - aTime : aTime - bTime;
      }
      return order === "desc" ? bValue.localeCompare(aValue) : aValue.localeCompare(bValue);
    }

    return 0;
  };
};
