export const isNotNull = <T>(value: T): value is Exclude<T, null> => value !== null;

export const isNotUndefined = <T>(value: T): value is Exclude<T, undefined> => value !== undefined;

export const isNotNullish = <T>(value: T): value is Exclude<T, null | undefined> =>
  value !== null && value !== undefined;
