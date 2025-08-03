import { useCallback, useState } from "react";

export const useCopy = () => {
  const [isCopied, setIsCopied] = useState(false);

  const copy = useCallback(async (text: string) => {
    await navigator.clipboard.writeText(text);
    setIsCopied(true);
  }, []);

  const reset = useCallback(() => {
    setIsCopied(false);
  }, []);

  return {
    isCopied,
    copy,
    reset,
  };
};
