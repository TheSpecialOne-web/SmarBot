import { useContext } from "react";

import { AuthContext } from "@/contexts/AuthContext";

export const useUserInfo = () => {
  const { userInfo, fetchUserInfo } = useContext(AuthContext);

  return {
    userInfo,
    fetchUserInfo,
  };
};
