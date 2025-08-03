// Remove types from T that are assignable to U
export type Diff<T extends object, U extends object> = {
  [K in keyof T as K extends keyof U ? never : K]: T[K];
};
