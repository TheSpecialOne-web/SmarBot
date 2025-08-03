import { Dispatch, SetStateAction, useState } from "react";

export const useLocalStorage = <T,>(key: string, initialValue: T) => {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(error);
      return initialValue;
    }
  });

  const setValue: Dispatch<SetStateAction<T>> = value => {
    const newValue = value instanceof Function ? value(storedValue) : value;
    try {
      setStoredValue(newValue);
      window.localStorage.setItem(key, JSON.stringify(newValue));
    } catch (error) {
      console.error(error);
    }
  };

  return [storedValue, setValue] as const;
};
