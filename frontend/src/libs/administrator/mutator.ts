import axios, { AxiosRequestConfig } from "axios";

export const administratorInstance = axios.create({
  baseURL: import.meta.env.VITE_ADMINISTRATOR_API_BASE_URL,
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json; charset=utf-8",
  },
});

export const useMutator = <T = unknown>(config: AxiosRequestConfig): Promise<T> => {
  return administratorInstance(config).then(({ data }) => data);
};
