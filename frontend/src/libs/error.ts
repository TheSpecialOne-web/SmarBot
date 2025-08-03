import axios from "axios";

export const getErrorMessage = (e: unknown): string | null => {
  if (axios.isAxiosError(e) && typeof e.response?.data?.error === "string") {
    return e.response.data.error;
  } else {
    return null;
  }
};
