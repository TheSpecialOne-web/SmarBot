export const sumBy = <T>(arr: T[], fn: (a: T) => number) => {
  return arr.map(fn).reduce((acc, val) => acc + val, 0);
};
