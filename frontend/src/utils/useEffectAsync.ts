import { useEffect } from "react";

export type AsyncEffectCallback<T> = (signal: AbortSignal) => Promise<T>;

export const useEffectAsync = <T>(
  effect: AsyncEffectCallback<T>,
  dependencies?: readonly unknown[],
): void => {
  useEffect(() => {
    const abortController = new AbortController();
    effect(abortController.signal);
    return () => abortController.abort();
  }, [dependencies, effect]);
};
