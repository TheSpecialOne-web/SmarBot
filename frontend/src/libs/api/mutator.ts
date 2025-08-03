import axios, { AxiosRequestConfig } from "axios";

export const apiInstance = axios.create({
  baseURL: import.meta.env.VITE_EXTERNAL_API_URL,
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json; charset=utf-8",
  },
});

export const useMutator = <T = unknown>(config: AxiosRequestConfig): Promise<T> => {
  return apiInstance(config).then(({ data }) => data);
};
